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

from fortune_engine import Fortune, FortuneEngine, QUESTIONS, TOPICS


class SessionState(enum.Enum):
    IDLE = "idle"
    APPROACH = "approach"
    READY = "ready"
    QUESTIONNAIRE = "questionnaire"
    TOPIC = "topic"
    RETURN_PROMPT = "return_prompt"
    THINKING = "thinking"
    REVEAL = "reveal"
    FAREWELL = "farewell"


STATE_TIMEOUTS = {
    SessionState.APPROACH: 1.8,
    SessionState.READY: 30.0,
    SessionState.QUESTIONNAIRE: 30.0,
    SessionState.TOPIC: 30.0,
    SessionState.RETURN_PROMPT: 30.0,
    SessionState.THINKING: 3.8,
    SessionState.REVEAL: 30.0,
    SessionState.FAREWELL: 4.0,
}


@dataclass
class EventJournal:
    path: Path
    data: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.data = {
            "schema": 2,
            "approaches": 0,
            "sessions_started": 0,
            "fortunes_revealed": 0,
            "return_visits": 0,
            "cancellations": 0,
            "automatic_resets": 0,
            "last_event_at": None,
            "recent_fingerprints": [],
        }
        try:
            loaded = json.loads(self.path.read_text())
            if loaded.get("schema") in (1, 2):
                loaded["schema"] = 2
                self.data.update(loaded)
        except (FileNotFoundError, OSError, ValueError, TypeError):
            pass

    def _save(self) -> None:
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

    def record(self, key: str) -> None:
        self.data[key] = int(self.data.get(key, 0)) + 1
        self.data["last_event_at"] = int(time.time())
        self._save()

    def remember_fingerprint(self, fingerprint: str) -> None:
        recent = list(self.data.get("recent_fingerprints", []))
        recent.append(fingerprint)
        self.data["recent_fingerprints"] = recent[-150:]
        self._save()

    @property
    def recent_fingerprints(self) -> set[str]:
        return set(self.data.get("recent_fingerprints", []))


class SessionController:
    def __init__(self, journal: EventJournal, rng: random.Random | None = None) -> None:
        self.journal = journal
        self.rng = rng or random.Random()
        self.engine = FortuneEngine(self.rng)
        self.state = SessionState.IDLE
        self.entered_at = time.monotonic()
        self.answers: dict[str, str] = {}
        self.question_index = 0
        self.topic = "SURPRISE ME"
        self.fortune: Fortune | None = None
        self.previous_fortune: Fortune | None = None
        self.return_outcome: str | None = None
        self.returning = False

    def _enter(self, state: SessionState, now: float | None = None) -> None:
        self.state = state
        self.entered_at = time.monotonic() if now is None else now

    @property
    def current_question(self):
        if self.state is not SessionState.QUESTIONNAIRE:
            return None
        return QUESTIONS[self.question_index]

    def approach(self, now: float | None = None, returning: bool = False) -> bool:
        if self.state is not SessionState.IDLE:
            return False
        self.answers = {}
        self.question_index = 0
        self.topic = "SURPRISE ME"
        self.fortune = None
        self.return_outcome = None
        self.returning = bool(returning and self.previous_fortune)
        self.journal.record("approaches")
        if self.returning:
            self.journal.record("return_visits")
        self._enter(SessionState.APPROACH, now)
        return True

    def begin(self, now: float | None = None) -> bool:
        if self.state is not SessionState.READY:
            return False
        self.journal.record("sessions_started")
        self._enter(SessionState.QUESTIONNAIRE, now)
        return True

    def select_answer(self, value: str, now: float | None = None) -> bool:
        question = self.current_question
        if question is None or value not in question[2]:
            return False
        self.answers[question[0]] = value
        self.question_index += 1
        self._enter(SessionState.TOPIC if self.question_index >= len(QUESTIONS) else SessionState.QUESTIONNAIRE, now)
        return True

    def select_topic(self, value: str, now: float | None = None) -> bool:
        if self.state is not SessionState.TOPIC or value not in TOPICS:
            return False
        self.topic = value
        self._enter(SessionState.THINKING, now)
        return True

    def answer_return(self, outcome: str, now: float | None = None) -> bool:
        if self.state is not SessionState.RETURN_PROMPT or outcome not in ("YES", "NOT YET", "IT GOT WORSE"):
            return False
        self.return_outcome = outcome
        self.answers = dict(self.previous_fortune.choices)
        self.topic = self.previous_fortune.topic
        self._enter(SessionState.THINKING, now)
        return True

    def finish_reveal(self, now: float | None = None) -> bool:
        if self.state is not SessionState.REVEAL:
            return False
        self._enter(SessionState.FAREWELL, now)
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
            self._enter(SessionState.RETURN_PROMPT if self.returning else SessionState.READY, current)
        elif self.state is SessionState.THINKING and elapsed >= STATE_TIMEOUTS[self.state]:
            previous = self.previous_fortune if self.returning else None
            visit_number = (previous.visit_number + 1) if previous else 1
            self.fortune = self.engine.create(
                self.answers, self.topic, self.journal.recent_fingerprints,
                visit_number, previous, self.return_outcome,
            )
            self.previous_fortune = self.fortune
            self.journal.remember_fingerprint(self.fortune.fingerprint)
            self.journal.record("fortunes_revealed")
            self._enter(SessionState.REVEAL, current)
        elif self.state is SessionState.REVEAL and elapsed >= STATE_TIMEOUTS[self.state]:
            self._enter(SessionState.FAREWELL, current)
        elif self.state is SessionState.FAREWELL and elapsed >= STATE_TIMEOUTS[self.state]:
            self.fortune = None
            self._enter(SessionState.IDLE, current)
        elif self.state in (SessionState.READY, SessionState.QUESTIONNAIRE, SessionState.TOPIC, SessionState.RETURN_PROMPT):
            if elapsed >= STATE_TIMEOUTS[self.state]:
                self.journal.record("automatic_resets")
                self._enter(SessionState.FAREWELL, current)


def default_journal_path() -> Path:
    override = os.environ.get("MADAME_MAXIME_JOURNAL")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".local" / "state" / "madame-maxime" / "journal.json"
