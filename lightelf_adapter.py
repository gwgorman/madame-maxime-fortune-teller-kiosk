"""Safety-gated LightELF scene API with a no-hardware simulator.

The real BLE transport is deliberately not enabled until a physical projector
has passed discovery, protocol-generation, blackout, and disconnect tests.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


MAX_ARM_SECONDS = 2.0
ASSET_DIR = Path(__file__).with_name("assets") / "laser"


@dataclass(frozen=True)
class LightElfScene:
    name: str
    kind: str
    content: str
    description: str
    color: str = "full"
    size_percent: int = 45

    def __post_init__(self) -> None:
        if self.kind not in {"text", "svg"}:
            raise ValueError(f"unsupported LightELF scene kind: {self.kind}")
        if not 10 <= self.size_percent <= 60:
            raise ValueError("front-laser scenes must remain between 10% and 60% size")


FRONT_SCENES = {
    "welcome": LightElfScene(
        "welcome", "text", "WELCOME", "Short arrival greeting", color="yellow"
    ),
    "party_title": LightElfScene(
        "party_title",
        "text",
        "CIRQUE DU SOIREE",
        "ASCII projection fallback for the Cirque du Soirée title",
        color="full",
        size_percent=35,
    ),
    "big_top": LightElfScene(
        "big_top", "svg", "big_top.svg", "Symmetrical circus tent", color="full"
    ),
    "circus_star": LightElfScene(
        "circus_star", "svg", "circus_star.svg", "Symmetrical circus star"
    ),
    "ferris_wheel": LightElfScene(
        "ferris_wheel",
        "svg",
        "ferris_wheel.svg",
        "Symmetrical Ferris wheel",
        color="cyan",
    ),
}


class LightElfTransport(Protocol):
    def show_text(self, text: str, *, color: str, size_percent: int) -> None: ...

    def show_svg(self, path: Path, *, color: str, size_percent: int) -> None: ...

    def heartbeat(self, *, ttl: float = 1.0) -> None: ...

    def blackout(self) -> None: ...


class SimulatedLightElfTransport:
    """Records operations without opening Bluetooth or enabling a projector."""

    def __init__(self) -> None:
        self.operations: list[tuple] = []

    def show_text(self, text: str, *, color: str, size_percent: int) -> None:
        self.operations.append(("text", text, color, size_percent))

    def show_svg(self, path: Path, *, color: str, size_percent: int) -> None:
        self.operations.append(("svg", path.name, color, size_percent))

    def heartbeat(self, *, ttl: float = 1.0) -> None:
        self.operations.append(("heartbeat", ttl))

    def blackout(self) -> None:
        self.operations.append(("blackout",))


class LightElfController:
    """Allow only named scenes while a short, renewable safety lease is live."""

    def __init__(self, transport: LightElfTransport | None = None) -> None:
        self.transport = transport or SimulatedLightElfTransport()
        self.deadline: float | None = None
        self.active_scene: str | None = None

    @property
    def armed(self) -> bool:
        return self.deadline is not None

    def arm(self, *, now: float | None = None, ttl: float = 1.0) -> None:
        now = time.monotonic() if now is None else now
        self.deadline = now + max(0.1, min(float(ttl), MAX_ARM_SECONDS))

    def heartbeat(self, *, now: float | None = None, ttl: float = 1.0) -> None:
        if not self.armed:
            raise RuntimeError("LightELF heartbeat received while disarmed")
        self.arm(now=now, ttl=ttl)
        self.transport.heartbeat(ttl=min(float(ttl), MAX_ARM_SECONDS))

    def show(self, name: str, *, now: float | None = None) -> None:
        now = time.monotonic() if now is None else now
        if self.deadline is None or now >= self.deadline:
            self.blackout()
            raise RuntimeError("LightELF output requires a live safety lease")
        scene = FRONT_SCENES[name]
        if scene.kind == "text":
            self.transport.show_text(
                scene.content, color=scene.color, size_percent=scene.size_percent
            )
        else:
            path = ASSET_DIR / scene.content
            if not path.is_file():
                raise FileNotFoundError(path)
            self.transport.show_svg(
                path, color=scene.color, size_percent=scene.size_percent
            )
        self.active_scene = name

    def tick(self, *, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        if self.deadline is not None and now >= self.deadline:
            self.blackout()
            return True
        return False

    def blackout(self) -> None:
        self.transport.blackout()
        self.deadline = None
        self.active_scene = None
