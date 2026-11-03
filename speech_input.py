#!/usr/bin/env python3
"""Bounded microphone capture and OpenAI speech-to-text for Madame Maxime.

Raw guest audio and transcripts stay in memory.  The module deliberately has
no dependency on the kiosk UI so it can run in a worker without blocking touch,
lighting, or the session watchdog.
"""

from __future__ import annotations

import argparse
import collections
import io
import os
import subprocess
import time
import wave
from array import array
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Sequence

SAMPLE_RATE = 16_000
CHANNELS = 2
SAMPLE_WIDTH = 2
CHUNK_MS = 20
DEFAULT_DEVICE = "plughw:CARD=Array,DEV=0"
DEFAULT_THRESHOLD = 110
DEFAULT_SECRETS_PATH = Path.home() / ".config" / "madame-maxime" / "secrets.env"
TRANSCRIPTION_URL = "https://api.openai.com/v1/audio/transcriptions"


class SpeechInputError(RuntimeError):
    """A recoverable capture or transcription failure."""


@dataclass(frozen=True)
class CaptureResult:
    wav_bytes: bytes
    speech_seconds: float
    elapsed_seconds: float
    peak: int


def _stereo_to_mono(raw: bytes) -> bytes:
    samples = array("h")
    samples.frombytes(raw)
    if os.sys.byteorder != "little":
        samples.byteswap()
    mono = array("h", ((samples[i] + samples[i + 1]) // 2
                       for i in range(0, len(samples) - 1, 2)))
    if os.sys.byteorder != "little":
        mono.byteswap()
    return mono.tobytes()


def _level(mono: bytes) -> tuple[int, int]:
    samples = array("h")
    samples.frombytes(mono)
    if os.sys.byteorder != "little":
        samples.byteswap()
    if not samples:
        return 0, 0
    peak = max(abs(value) for value in samples)
    mean_square = sum(value * value for value in samples) / len(samples)
    return int(mean_square ** 0.5), peak


def _wav_bytes(pcm: bytes) -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(SAMPLE_WIDTH)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(pcm)
    return output.getvalue()


def record_utterance(
    *,
    device: str = DEFAULT_DEVICE,
    start_timeout: float = 5.0,
    max_seconds: float = 10.0,
    end_silence: float = 1.25,
    pre_roll: float = 1.00,
    threshold: int = DEFAULT_THRESHOLD,
    min_voice: float = 0.20,
    settle_time: float = 0.50,
) -> CaptureResult:
    """Capture one utterance from the reSpeaker and endpoint it locally."""
    frames_per_chunk = SAMPLE_RATE * CHUNK_MS // 1000
    bytes_per_chunk = frames_per_chunk * CHANNELS * SAMPLE_WIDTH
    command = [
        "arecord", "-q", "-D", device, "-t", "raw", "-f", "S16_LE",
        "-r", str(SAMPLE_RATE), "-c", str(CHANNELS),
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.stdout is None:
        process.kill()
        raise SpeechInputError("capture pipe unavailable")

    prebuffer = collections.deque(maxlen=max(1, int(pre_roll * 1000 / CHUNK_MS)))
    captured: list[bytes] = []
    started_at = time.monotonic()
    speech_started: float | None = None
    last_voice: float | None = None
    voiced_seconds = 0.0
    peak = 0
    try:
        while True:
            raw = process.stdout.read(bytes_per_chunk)
            if len(raw) != bytes_per_chunk:
                error = process.stderr.read().decode("utf-8", "replace").strip()
                raise SpeechInputError(error or "microphone capture ended unexpectedly")
            now = time.monotonic()
            mono = _stereo_to_mono(raw)
            rms, chunk_peak = _level(mono)
            peak = max(peak, chunk_peak)

            if speech_started is None:
                prebuffer.append(mono)
                if now - started_at < settle_time:
                    continue
                if rms >= threshold:
                    speech_started = now
                    last_voice = now
                    voiced_seconds = CHUNK_MS / 1000
                    captured.extend(prebuffer)
                    prebuffer.clear()
                elif now - started_at >= start_timeout:
                    raise SpeechInputError("no speech detected")
            else:
                captured.append(mono)
                if rms >= threshold:
                    last_voice = now
                    voiced_seconds += CHUNK_MS / 1000
                if now - speech_started >= max_seconds:
                    break
                if last_voice is not None and now - last_voice >= end_silence:
                    if voiced_seconds >= min_voice:
                        break
                    # Ignore a click, bump, or other short transient and keep
                    # listening inside the original bounded start window.
                    captured.clear()
                    prebuffer.clear()
                    speech_started = None
                    last_voice = None
                    voiced_seconds = 0.0
    finally:
        process.terminate()
        try:
            process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=1.0)

    if speech_started is None or last_voice is None:
        raise SpeechInputError("no speech detected")
    pcm = b"".join(captured)
    return CaptureResult(
        wav_bytes=_wav_bytes(pcm),
        speech_seconds=voiced_seconds,
        elapsed_seconds=time.monotonic() - started_at,
        peak=peak,
    )


def transcribe(
    wav_bytes: bytes,
    *,
    prompt: str = "",
    keywords: Sequence[str] = ("Madame Maxine",),
    api_key: str | None = None,
    model: str = "gpt-transcribe",
    timeout: tuple[float, float] = (5.0, 20.0),
    session=None,
) -> str:
    """Transcribe one in-memory WAV through OpenAI's bounded HTTP endpoint."""
    key = api_key or load_openai_key()
    if not key:
        raise SpeechInputError("OPENAI_API_KEY is not configured")
    if session is None:
        try:
            import requests
        except ImportError as exc:
            raise SpeechInputError("python3-requests is not installed") from exc
        session = requests
    data: list[tuple[str, str]] = [("model", model), ("language", "en")]
    if prompt:
        data.append(("prompt", prompt))
    for keyword in keywords:
        if keyword.strip():
            data.append(("keywords[]", keyword.strip()))
    try:
        response = session.post(
            TRANSCRIPTION_URL,
            headers={"Authorization": f"Bearer {key}"},
            data=data,
            files={"file": ("utterance.wav", wav_bytes, "audio/wav")},
            timeout=timeout,
        )
        if response.status_code >= 400:
            try:
                error = response.json().get("error", {})
                code = error.get("code") or error.get("type") or f"HTTP {response.status_code}"
                message = str(error.get("message", "request rejected"))
                raise SpeechInputError(f"transcription failed [{code}]: {message}")
            except (ValueError, AttributeError):
                response.raise_for_status()
        text = response.json().get("text", "").strip()
    except SpeechInputError:
        raise
    except Exception as exc:
        raise SpeechInputError(f"transcription failed: {exc}") from exc
    if not text:
        raise SpeechInputError("transcription returned no text")
    return text


def load_openai_key(path: Path = DEFAULT_SECRETS_PATH) -> str:
    """Load only OPENAI_API_KEY from a private operator-owned environment file."""
    from_environment = os.environ.get("OPENAI_API_KEY", "").strip()
    if from_environment:
        return from_environment
    try:
        mode = path.stat().st_mode & 0o777
        if mode & 0o077:
            raise SpeechInputError(f"{path} must have mode 0600")
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            if name.strip() == "OPENAI_API_KEY":
                return value.strip().strip("'\"")
    except FileNotFoundError:
        return ""
    except OSError as exc:
        raise SpeechInputError(f"cannot read {path}: {exc}") from exc
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Test Madame Maxime speech input")
    parser.add_argument("--device", default=os.environ.get("MADAME_MAXIME_CAPTURE_DEVICE", DEFAULT_DEVICE))
    parser.add_argument("--max-seconds", type=float, default=10.0)
    parser.add_argument("--start-timeout", type=float, default=5.0)
    parser.add_argument("--threshold", type=int, default=int(os.environ.get("MADAME_MAXIME_VAD_RMS", str(DEFAULT_THRESHOLD))))
    parser.add_argument("--prompt", default="")
    parser.add_argument("--keyword", action="append", default=[])
    parser.add_argument("--capture-only", action="store_true")
    args = parser.parse_args()
    try:
        result = record_utterance(
            device=args.device,
            max_seconds=args.max_seconds,
            start_timeout=args.start_timeout,
            threshold=args.threshold,
        )
        print(
            f"captured speech={result.speech_seconds:.2f}s "
            f"wait_and_capture={result.elapsed_seconds:.2f}s peak={result.peak}"
        )
        if not args.capture_only:
            transcription_started = time.monotonic()
            keywords = ["Madame Maxine", *args.keyword]
            text = transcribe(result.wav_bytes, prompt=args.prompt, keywords=keywords)
            print(f"transcription_latency={time.monotonic() - transcription_started:.2f}s")
            print(text)
        return 0
    except SpeechInputError as exc:
        print(f"speech input unavailable: {exc}", file=os.sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
