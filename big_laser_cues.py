"""Safety-bounded cues for the Wonsung 5W-APP at A073 in 36ch mode."""

from __future__ import annotations


BIG_LASER_ADDRESS = 73
BIG_LASER_CHANNELS = 36


def blackout_channels() -> tuple[int, ...]:
    return (0,) * BIG_LASER_CHANNELS


def safe_geometry_channels(*, armed: bool = False) -> tuple[int, ...]:
    """Return a centered alternate-pattern diagnostic frame."""
    if not armed:
        return blackout_channels()
    return (
        32,   # CH1: conservative diagnostic dimmer, about 12.5 percent
        27,   # CH2: explicitly enabled automatic mode at minimum speed
        0,    # CH3: first geometric group
        10,   # CH4: alternate nonzero static pattern selector
        128,  # CH5: medium bounded pattern size
        128,  # CH6: centered X
        128,  # CH7: centered Y
        0,    # CH8: default white/static color
        0,    # CH9: no color cycling
        63,   # CH10: line scan, upper end of first documented range
        0,    # CH11: STROBE LOCKED OUT
        0,    # CH12: no Z rotation
        0,    # CH13: no X rollover
        0,    # CH14: no Y rollover
        0,    # CH15: no X movement
        0,    # CH16: no Y movement
        0,    # CH17: no zoom
        0,    # CH18: no progressive drawing
        0,    # CH19: no wave
        0,    # CH20: second pattern group disabled
        0,    # CH21: second pattern hidden
        0,    # CH22: second pattern size
        0,    # CH23: second pattern X
        0,    # CH24: second pattern Y
        0,    # CH25: second pattern color
        0,    # CH26: second pattern color speed
        0,    # CH27: second pattern scan speed
        0,    # CH28: STROBE LOCKED OUT
        0,    # CH29: second pattern Z rotation
        0,    # CH30: second pattern X rollover
        0,    # CH31: second pattern Y rollover
        0,    # CH32: second pattern X movement
        0,    # CH33: second pattern Y movement
        0,    # CH34: second pattern zoom
        0,    # CH35: second pattern drawing
        0,    # CH36: second pattern wave
    )


def bright_line_test_channels(*, armed: bool = False) -> tuple[int, ...]:
    """Return the visually verified centered white-line cue at 50 percent."""
    if not armed:
        return blackout_channels()
    values = list(safe_geometry_channels(armed=True))
    values[0] = 128  # CH1: visually verified diagnostic level, about 50 percent
    return tuple(values)


def bright_line_color_channels(color_value: int, *, armed: bool = False) -> tuple[int, ...]:
    """Return the verified bright line with one static documented color."""
    if not armed:
        return blackout_channels()
    if color_value not in (8, 16, 24):
        raise ValueError("diagnostic color must be red, green, or blue")
    values = list(bright_line_test_channels(armed=True))
    values[7] = color_value  # CH8: static color selector
    return tuple(values)


def bright_line_geometry_channels(
    *, size: int = 128, x_position: int = 128, y_position: int = 128,
    armed: bool = False,
) -> tuple[int, ...]:
    """Return the verified white line with bounded size and position."""
    if not armed:
        return blackout_channels()
    if size not in (64, 128, 192):
        raise ValueError("diagnostic size must be small, medium, or large")
    if x_position not in (80, 128, 176) or y_position != 128:
        raise ValueError("diagnostic position is outside the bounded test set")
    values = list(bright_line_test_channels(armed=True))
    values[4] = size
    values[5] = x_position
    values[6] = y_position
    return tuple(values)
