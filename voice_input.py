"""Non-blocking spoken-choice adapter for the Madame Maxine UI."""

from __future__ import annotations

import difflib
import queue
import re
import threading

from speech_client import request


ALIASES = {
    "YES": ("YEAH", "YEP", "IT DID", "ALREADY DID"),
    "NOT YET": ("NO", "NOT YET", "NOT SO FAR"),
    "IT GOT WORSE": ("GOT WORSE", "WORSE", "MUCH WORSE"),
    "A SECRET": ("SECRET", "THE SECRET"),
    "SURPRISE ME": ("SURPRISE", "ANYTHING", "YOU CHOOSE"),
}


def normalize(text: str) -> str:
    return " ".join(re.findall(r"[A-Z0-9]+", text.upper()))


def map_choice(transcript: str, choices) -> str | None:
    spoken = normalize(transcript)
    if not spoken:
        return None
    candidates = []
    for choice in choices:
        canonical = normalize(choice)
        phrases = (canonical, *ALIASES.get(canonical, ()))
        if any(normalize(phrase) == spoken for phrase in phrases):
            return choice
        if any(re.search(rf"\b{re.escape(normalize(phrase))}\b", spoken) for phrase in phrases):
            return choice
        score = max(difflib.SequenceMatcher(None, spoken, normalize(phrase)).ratio()
                    for phrase in phrases)
        candidates.append((score, choice))
    candidates.sort(reverse=True)
    if candidates and candidates[0][0] >= 0.70:
        if len(candidates) == 1 or candidates[0][0] - candidates[1][0] >= 0.12:
            return candidates[0][1]
    return None


class VoiceChoiceAdapter:
    """Run one socket request off the render thread and discard stale results."""

    def __init__(self, requester=request) -> None:
        self.requester = requester
        self.events = queue.SimpleQueue()
        self.generation = 0
        self.thread: threading.Thread | None = None

    @property
    def busy(self) -> bool:
        return bool(self.thread and self.thread.is_alive())

    def invalidate(self) -> None:
        self.generation += 1

    def start(self, prompt: str, choices) -> bool:
        if self.busy:
            return False
        self.generation += 1
        generation = self.generation
        choices = tuple(choices)

        def progress(message):
            self.events.put((generation, "thinking", message))

        def worker():
            try:
                response = self.requester({
                    "action": "transcribe",
                    "start_timeout": 8.0,
                    "max_seconds": 6.0,
                    "prompt": f"{prompt} Visible choices: {', '.join(choices)}.",
                    "keywords": list(choices),
                }, timeout=20.0, progress=progress)
                if response.get("ok"):
                    selected = map_choice(response.get("text", ""), choices)
                    self.events.put((generation, "result", {
                        "selected": selected, "text": response.get("text", ""),
                        "metrics": response.get("metrics", {}),
                    }))
                else:
                    self.events.put((generation, "error", response))
            except Exception as exc:
                self.events.put((generation, "error", {"error": str(exc)}))

        self.thread = threading.Thread(target=worker, name="voice-choice", daemon=True)
        self.thread.start()
        return True

    def poll(self):
        current = []
        while True:
            try:
                generation, kind, payload = self.events.get_nowait()
            except queue.Empty:
                break
            if generation == self.generation:
                current.append((kind, payload))
        return current
