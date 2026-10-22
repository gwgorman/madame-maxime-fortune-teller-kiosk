"""Safety-bounded named cues for the A057 mirrored animation laser.

This module defines validated DMX frames but does not open the ENTTEC interface.
A future single-owner broker will merge these frames with the PAR fixtures.
"""

from __future__ import annotations

from dataclasses import dataclass


LASER_ADDRESS = 57
LASER_CHANNELS = 16
MINIMUM_ENABLE = 10
SAFE_SIZE = 32
SAFE_HORIZONTAL = 64
SAFE_VERTICAL = 56


@dataclass(frozen=True)
class LaserCue:
    name: str
    group: int
    pattern: int
    description: str
    rotation: int = 0

    def channels(self, *, armed: bool = False) -> tuple[int, ...]:
        """Return a complete fixture frame; unarmed output is always blackout."""
        if not armed:
            return (0,) * LASER_CHANNELS
        values = (
            MINIMUM_ENABLE,  # CH1: minimum documented laser enable/dimmer
            0,               # CH2: fixed/default color
            0,               # CH3: no color flow
            self.group,      # CH4: graphics group
            self.pattern,    # CH5: graphics selection
            0,               # CH6: no dynamic/random/sound effects
            0,               # CH7: default internal animation speed
            SAFE_SIZE,       # CH8: reduced tested size
            0,               # CH9: no automatic scaling
            self.rotation,   # CH10: fixed angle or tested rotation speed
            0,               # CH11: no DMX X flip
            0,               # CH12: no DMX Y flip
            SAFE_HORIZONTAL, # CH13: fixed tested horizontal position
            SAFE_VERTICAL,   # CH14: upward-biased tested vertical position
            0,               # CH15: no wave
            0,               # CH16: no gradual drawing
        )
        if any(not 0 <= value <= 255 for value in values):
            raise ValueError(f"cue {self.name!r} contains an invalid DMX value")
        return values


def _cue(name: str, group: int, pattern: int, description: str) -> LaserCue:
    return LaserCue(name, group, pattern, description)


CUES = {
    "starburst_spin": LaserCue(
        "starburst_spin", 0, 176, "Rotating asterisk/starburst", rotation=160
    ),
    "storybook_star": _cue("storybook_star", 0, 184, "Child-drawn star"),
    "sun": _cue("sun", 0, 192, "Sun"),
    "fan": _cue("fan", 0, 200, "Fan"),
    "pinwheel": _cue("pinwheel", 25, 160, "Pinwheel"),
    "spiral_cone": _cue("spiral_cone", 25, 208, "Spiral cone"),
    "flower": _cue("flower", 25, 224, "Flower"),
    "stork_walk": _cue("stork_walk", 125, 16, "Walking stork"),
    "eagle_perch": _cue("eagle_perch", 125, 32, "Perched eagle"),
    "bat_flight": _cue("bat_flight", 125, 96, "Flying bat"),
    "salamander_walk": _cue("salamander_walk", 125, 112, "Crawling salamander"),
    "sparkle_moose": _cue(
        "sparkle_moose", 125, 128, "Reindeer or moose watching a flying sparkle"
    ),
    "ghost_peek": _cue("ghost_peek", 125, 144, "Ghost or peeping figure"),
    "dolphin_splash": _cue(
        "dolphin_splash", 125, 160, "Dolphin leaping from water"
    ),
    "bat_trio": _cue("bat_trio", 125, 192, "One, two, then three flying bats"),
    "cobra_strike": _cue("cobra_strike", 125, 208, "Striking cobra"),
    "maxime_wave": _cue("maxime_wave", 125, 224, "Girl in a large hat waving"),
    "vintage_plane": _cue(
        "vintage_plane", 125, 240, "Rotating open-cockpit propeller airplane"
    ),
    "confused_girl": _cue("confused_girl", 150, 0, "Girl looking, then confused"),
    "elvis": _cue("elvis", 150, 16, "Singing Elvis"),
    "circle_slinky": _cue("circle_slinky", 150, 32, "Circle-based slinky effect"),
    "candy_cane_reindeer": _cue(
        "candy_cane_reindeer", 150, 48, "Reindeer with a candy cane"
    ),
    "rotating_cube": _cue("rotating_cube", 150, 64, "Rotating 3D cube"),
}


def cue_channels(name: str, *, armed: bool = False) -> tuple[int, ...]:
    return CUES[name].channels(armed=armed)


def blackout_channels() -> tuple[int, ...]:
    return (0,) * LASER_CHANNELS
