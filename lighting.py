"""Failure-isolated theatrical lighting scenes for Madame Maxime."""

from __future__ import annotations

import math
import threading
import time


SCENES = {
    "idle": (34, 255, 58, 5),
    "approach": (58, 255, 88, 14),
    "ready": (48, 185, 35, 220),
    "questionnaire": (42, 115, 20, 230),
    "topic": (46, 45, 55, 255),
    "return_prompt": (54, 50, 145, 220),
    "thinking": (62, 20, 42, 255),
    "reveal": (82, 255, 145, 25),
    "farewell": (38, 255, 60, 5),
}


class LightingController:
    """Animate two PAR fixtures while allowing the UI to survive every fault."""

    def __init__(self, enabled: bool = False, client=None) -> None:
        self.enabled = enabled
        self.available = False
        self.error = None
        self.client = client
        self.par_scene = None
        self.par_addresses = ()
        self.current = list(SCENES["idle"])
        self.last_update = time.monotonic()
        self.state_name = "idle"
        self._state_lock = threading.Lock()
        self._stop = threading.Event()
        self._animation_thread = None

    def start(self) -> None:
        if not self.enabled:
            return
        try:
            if self.client is None:
                from dmx_broker import DmxClient

                self.client = DmxClient()
            self.available = True
            self._write(self.current)
            self._stop.clear()
            self._animation_thread = threading.Thread(
                target=self._animate, name="fortune-lighting", daemon=True
            )
            self._animation_thread.start()
        except Exception as exc:
            self.error = str(exc)
            self.available = False

    def _write(self, values) -> None:
        if not self.available:
            return
        try:
            self.client.set_par(round(value) for value in values)
        except Exception as exc:
            self.error = str(exc)
            self.available = False

    def update(self, state_name: str, now: float) -> None:
        if not self.available:
            return
        with self._state_lock:
            self.state_name = state_name

    def _animate(self) -> None:
        """Interpolate lighting independently of the deliberately slow UI."""
        while not self._stop.is_set() and self.available:
            now = time.monotonic()
            with self._state_lock:
                state_name = self.state_name
            self._animate_step(state_name, now)
            self._stop.wait(1.0 / 30.0)

    def _animate_step(self, state_name: str, now: float) -> None:
        target = list(SCENES.get(state_name, SCENES["idle"]))
        if state_name == "thinking":
            target[0] += 15 * (0.5 + 0.5 * math.sin(now * 3.2))
        elif state_name == "reveal":
            target[0] += 12 * (0.5 + 0.5 * math.sin(now * 1.8))
        elapsed = max(0.0, min(0.25, now - self.last_update))
        self.last_update = now
        blend = min(1.0, elapsed * 2.8)
        self.current = [old + (new - old) * blend for old, new in zip(self.current, target)]
        self._write(self.current)

    def stop(self) -> None:
        self._stop.set()
        if self._animation_thread:
            self._animation_thread.join(timeout=1.0)
        if self.client:
            try:
                self.client.blackout_all()
            except Exception as exc:
                self.error = str(exc)
        self.available = False

