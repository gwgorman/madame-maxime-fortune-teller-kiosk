"""Failure-isolated theatrical lighting scenes for Madame Maxime."""

from __future__ import annotations

import math
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

    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled
        self.available = False
        self.error = None
        self.universe = None
        self.output = None
        self.par_scene = None
        self.current = list(SCENES["idle"])
        self.last_update = time.monotonic()

    def start(self) -> None:
        if not self.enabled:
            return
        try:
            from dmx_lighting import OpenDmxOutput, ParScene, Universe

            self.par_scene = ParScene
            self.universe = Universe()
            self.output = OpenDmxOutput(self.universe)
            self.output.start()
            self.available = True
            self._write(self.current)
        except Exception as exc:
            self.error = str(exc)
            self.available = False

    def _write(self, values) -> None:
        if not self.available:
            return
        scene = self.par_scene(*(round(value) for value in values))
        self.universe.set_par(1, scene)
        self.universe.set_par(30, scene)

    def update(self, state_name: str, now: float) -> None:
        if not self.available:
            return
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
        if self.output.error:
            self.error = self.output.error
            self.available = False

    def stop(self) -> None:
        if self.output:
            try:
                self.output.stop(blackout=True)
            except Exception as exc:
                self.error = str(exc)
        self.available = False

