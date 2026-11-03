#!/usr/bin/env python3
"""Persistent reSpeaker capture worker for Madame Maxine.

The USB/DSP stream stays open and is drained continuously.  Clients request a
single bounded utterance over a private Unix socket; raw audio never leaves
memory and only the transcript plus coarse diagnostics are returned.
"""

from __future__ import annotations

import collections
import json
import os
import socket
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from speech_input import (
    CHANNELS,
    CHUNK_MS,
    DEFAULT_DEVICE,
    DEFAULT_THRESHOLD,
    SAMPLE_RATE,
    SAMPLE_WIDTH,
    SpeechInputError,
    _level,
    _stereo_to_mono,
    _wav_bytes,
    transcribe,
)

try:
    import webrtcvad
except ImportError as exc:
    raise SystemExit("webrtcvad is required; install requirements-speech.txt") from exc


DEFAULT_SOCKET = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")) / "madame-maxime-speech.sock"


@dataclass(frozen=True)
class Frame:
    sequence: int
    pcm: bytes
    rms: int
    peak: int
    when: float


class PersistentMicrophone:
    def __init__(self, device: str = DEFAULT_DEVICE, ring_seconds: float = 3.0) -> None:
        self.device = device
        self.frames = collections.deque(maxlen=int(ring_seconds * 1000 / CHUNK_MS))
        self.condition = threading.Condition()
        self.sequence = 0
        self.failure = ""
        # Mode 1 preserves short/soft questionnaire answers; the independent
        # RMS gate and minimum voiced duration still reject room transients.
        self.vad = webrtcvad.Vad(1)
        self.process: subprocess.Popen | None = None
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        command = [
            "arecord", "-q", "-D", self.device, "-t", "raw", "-f", "S16_LE",
            "-r", str(SAMPLE_RATE), "-c", str(CHANNELS),
        ]
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.thread = threading.Thread(target=self._drain, name="respeaker-capture", daemon=True)
        self.thread.start()
        deadline = time.monotonic() + 3.0
        with self.condition:
            while not self.frames and not self.failure:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise SpeechInputError("reSpeaker did not produce audio frames")
                self.condition.wait(remaining)
        if self.failure:
            raise SpeechInputError(self.failure)

    def close(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=1.0)

    def _drain(self) -> None:
        assert self.process is not None and self.process.stdout is not None
        size = SAMPLE_RATE * CHUNK_MS // 1000 * CHANNELS * SAMPLE_WIDTH
        try:
            while True:
                raw = self.process.stdout.read(size)
                if len(raw) != size:
                    error = ""
                    if self.process.stderr:
                        error = self.process.stderr.read().decode("utf-8", "replace").strip()
                    raise SpeechInputError(error or "reSpeaker stream ended")
                mono = _stereo_to_mono(raw)
                rms, peak = _level(mono)
                with self.condition:
                    self.sequence += 1
                    self.frames.append(Frame(self.sequence, mono, rms, peak, time.monotonic()))
                    self.condition.notify_all()
        except Exception as exc:
            with self.condition:
                self.failure = str(exc)
                self.condition.notify_all()

    def latest_sequence(self) -> int:
        with self.condition:
            return self.sequence

    def is_voice(self, frame: Frame, threshold: int) -> bool:
        return frame.rms >= threshold and self.vad.is_speech(frame.pcm, SAMPLE_RATE)

    def next_frame(self, after: int, timeout: float = 1.0) -> Frame:
        deadline = time.monotonic() + timeout
        with self.condition:
            while True:
                if self.failure:
                    raise SpeechInputError(self.failure)
                for frame in self.frames:
                    if frame.sequence > after:
                        return frame
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise SpeechInputError("timed out waiting for microphone frame")
                self.condition.wait(remaining)


def capture_from_stream(
    microphone: PersistentMicrophone,
    *,
    start_timeout: float = 8.0,
    max_seconds: float = 10.0,
    end_silence: float = 1.25,
    pre_roll: float = 1.0,
    threshold: int = DEFAULT_THRESHOLD,
    min_voice: float = 0.20,
) -> tuple[bytes, dict]:
    started_at = time.monotonic()
    pre_roll_frames = max(1, int(pre_roll * 1000 / CHUNK_MS))
    # Begin inside the continuously drained ring so speech started during the
    # UI transition (or immediately after a remote GO cue) is not discarded.
    sequence = max(0, microphone.latest_sequence() - pre_roll_frames)
    prebuffer = collections.deque(maxlen=pre_roll_frames)
    captured: list[bytes] = []
    speech_started = None
    last_voice = None
    voiced_seconds = 0.0
    peak = 0
    while True:
        frame = microphone.next_frame(sequence)
        sequence = frame.sequence
        now = frame.when
        peak = max(peak, frame.peak)
        if speech_started is None:
            prebuffer.append(frame.pcm)
            if microphone.is_voice(frame, threshold):
                speech_started = now
                last_voice = now
                voiced_seconds = CHUNK_MS / 1000
                captured.extend(prebuffer)
                prebuffer.clear()
            elif now - started_at >= start_timeout:
                raise SpeechInputError("no speech detected")
        else:
            captured.append(frame.pcm)
            if microphone.is_voice(frame, threshold):
                last_voice = now
                voiced_seconds += CHUNK_MS / 1000
            if now - speech_started >= max_seconds:
                break
            if last_voice is not None and now - last_voice >= end_silence:
                if voiced_seconds >= min_voice:
                    break
                captured.clear()
                prebuffer.clear()
                speech_started = None
                last_voice = None
                voiced_seconds = 0.0
    return _wav_bytes(b"".join(captured)), {
        "voice_seconds": round(voiced_seconds, 3),
        "capture_seconds": round(time.monotonic() - started_at, 3),
        "peak": peak,
    }


def handle_request(microphone: PersistentMicrophone, request: dict, progress=None) -> dict:
    if request.get("action") == "status":
        return {"ok": True, "streaming": not bool(microphone.failure), "sequence": microphone.latest_sequence()}
    if request.get("action") != "transcribe":
        raise SpeechInputError("unknown action")
    wav, metrics = capture_from_stream(
        microphone,
        start_timeout=float(request.get("start_timeout", 8.0)),
        max_seconds=float(request.get("max_seconds", 10.0)),
        threshold=int(request.get("threshold", DEFAULT_THRESHOLD)),
    )
    if progress:
        progress({"event": "captured", "metrics": metrics})
    began = time.monotonic()
    text = transcribe(
        wav,
        prompt=str(request.get("prompt", "")),
        keywords=["Madame Maxine", *[str(item) for item in request.get("keywords", [])]],
    )
    metrics["transcription_seconds"] = round(time.monotonic() - began, 3)
    return {"ok": True, "text": text, "metrics": metrics}


def serve(path: Path = DEFAULT_SOCKET) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    microphone = PersistentMicrophone()
    microphone.start()
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(path))
    os.chmod(path, 0o600)
    server.listen(4)
    try:
        while True:
            connection, _ = server.accept()
            with connection:
                try:
                    payload = b""
                    while b"\n" not in payload and len(payload) < 65536:
                        chunk = connection.recv(4096)
                        if not chunk:
                            break
                        payload += chunk
                    request = json.loads(payload.split(b"\n", 1)[0])
                    def send_progress(message):
                        connection.sendall(json.dumps(message).encode("utf-8") + b"\n")

                    response = handle_request(microphone, request, send_progress)
                except Exception as exc:
                    response = {"ok": False, "error": str(exc)}
                connection.sendall(json.dumps(response).encode("utf-8") + b"\n")
    finally:
        server.close()
        microphone.close()
        try:
            path.unlink()
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    serve()
