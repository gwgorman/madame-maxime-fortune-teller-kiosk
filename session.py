"""Deterministic, audio-free session controller for Madame Maxime."""

from __future__ import annotations

import enum
import json
import os
import random
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path


class SessionState(enum.Enum):
    IDLE = "idle"
    APPROACH = "approach"
    READY = "ready"
    LISTENING = "listening"
    THINKING = "thinking"
    REVEAL = "reveal"
    FAREWELL = "farewell"


STATE_TIMEOUTS = {
    SessionState.APPROACH: 2.5,
    SessionState.LISTENING: 15.0,
    SessionState.THINKING: 2.4,
    SessionState.REVEAL: 14.0,
    SessionState.FAREWELL: 4.0,
}


FORTUNES = (
    (
        "THE LANTERN BEYOND THE FOG",
        "Before the next new moon, an overlooked invitation will become the evening everyone remembers.",
        "You pretend to distrust omens, yet you came remarkably close to a fortune-telling machine.",
        "When someone offers you the last of something, accept it—and ask one excellent question.",
    ),
    (
        "THE CLOCKWORK COMET",
        "A delayed plan will return with better timing and a much stranger cast of characters.",
        "Your confidence is convincing. Your improvisation is doing most of the actual work.",
        "Carry something red next Tuesday, even if only you know why.",
    ),
    (
        "THE GOLDEN KEY",
        "A door you assumed was decorative will prove surprisingly practical before winter ends.",
        "You are very good at giving advice you have absolutely no intention of following.",
        "Leave a kind note where no reply is expected.",
    ),
    (
        "THE VELVET ORBIT",
        "A familiar person will reveal an unexpected talent at exactly the right moment.",
        "You call it intuition. The rest of us call it noticing everything.",
        "At the next fork in the road, choose the option with the better story.",
    ),
)


@dataclass
class EventJournal:
    path: Path
    data: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.data = {
            "schema": 1,
            "approaches": 0,
            "sessions_started": 0,
            "fortunes_revealed": 0,
            "cancellations": 0,
            "automatic_resets": 0,
            "last_event_at": None,
        }
        try:
            loaded = json.loads(self.path.read_text())
            if loaded.get("schema") == 1:
                self.data.update(loaded)
        except (FileNotFoundError, OSError, ValueError, TypeError):
            pass

    def record(self, key: str) -> None:
        self.data[key] = int(self.data.get(key, 0)) + 1
        self.data["last_event_at"] = int(time.time())
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix="journal-", suffix=".json", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(self.data, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        finally:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


class SessionController:
    def __init__(self, journal: EventJournal, rng: random.Random | None = None) -> None:
        self.journal = journal
        self.rng = rng or random.Random()
        self.state = SessionState.IDLE
        self.entered_at = time.monotonic()
        self.fortune = None

    def _enter(self, state: SessionState, now: float | None = None) -> None:
        self.state = state
        self.entered_at = time.monotonic() if now is None else now

    def approach(self, now: float | None = None) -> bool:
        if self.state is not SessionState.IDLE:
            return False
        self.journal.record("approaches")
        self._enter(SessionState.APPROACH, now)
        return True

    def begin(self, now: float | None = None) -> bool:
        if self.state is not SessionState.READY:
            return False
        self.journal.record("sessions_started")
        self._enter(SessionState.LISTENING, now)
        return True

    def guest_finished(self, now: float | None = None) -> bool:
        if self.state is not SessionState.LISTENING:
            return False
        self._enter(SessionState.THINKING, now)
        return True

    def cancel(self, now: float | None = None) -> None:
        if self.state is not SessionState.IDLE:
            self.journal.record("cancellations")
        self.fortune = None
        self._enter(SessionState.IDLE, now)

    def update(self, now: float | None = None) -> None:
        current = time.monotonic() if now is None else now
        elapsed = current - self.entered_at
        if self.state is SessionState.APPROACH and elapsed >= STATE_TIMEOUTS[self.state]:
            self._enter(SessionState.READY, current)
        elif self.state is SessionState.LISTENING and elapsed >= STATE_TIMEOUTS[self.state]:
            self.journal.record("automatic_resets")
            self._enter(SessionState.FAREWELL, current)
        elif self.state is SessionState.THINKING and elapsed >= STATE_TIMEOUTS[self.state]:
            self.fortune = self.rng.choice(FORTUNES)
            self.journal.record("fortunes_revealed")
            self._enter(SessionState.REVEAL, current)
        elif self.state is SessionState.REVEAL and elapsed >= STATE_TIMEOUTS[self.state]:
            self._enter(SessionState.FAREWELL, current)
        elif self.state is SessionState.FAREWELL and elapsed >= STATE_TIMEOUTS[self.state]:
            self.fortune = None
            self._enter(SessionState.IDLE, current)


def default_journal_path() -> Path:
    override = os.environ.get("MADAME_MAXIME_JOURNAL")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".local" / "state" / "madame-maxime" / "journal.json"
