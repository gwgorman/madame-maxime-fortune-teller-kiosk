"""Safety-bounded built-in cue library for the A057 mirrored animation laser.

This module only describes validated DMX frames and playlists.  It performs no
I/O; the single-owner broker is the sole path to the physical ENTTEC interface.
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
    family: str = "geometry"

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


def _cue(
    name: str, group: int, pattern: int, description: str, *,
    family: str = "geometry",
) -> LaserCue:
    return LaserCue(name, group, pattern, description, family=family)


CUES = {
    "starburst_spin": LaserCue(
        "starburst_spin", 0, 176, "Rotating asterisk/starburst", rotation=160,
        family="circus",
    ),
    "storybook_star": _cue("storybook_star", 0, 184, "Child-drawn star", family="circus"),
    "sun": _cue("sun", 0, 192, "Sun", family="circus"),
    "fan": _cue("fan", 0, 200, "Fan", family="circus"),
    "x_mark": _cue("x_mark", 0, 224, "X"),
    "four_corner_boxes": _cue("four_corner_boxes", 0, 232, "Four corner boxes"),
    "thin_bar": _cue("thin_bar", 0, 240, "Thin rectangular bar", family="transition"),
    "bright_square": _cue("bright_square", 0, 248, "Tiny bright square", family="transition"),

    "big_circle": _cue("big_circle", 25, 8, "Large circle"),
    "two_circles": _cue("two_circles", 25, 16, "Three-circle mirrored projection"),
    "four_circle_diagonal": _cue("four_circle_diagonal", 25, 32, "Eight-circle mirrored projection"),
    "four_circle_square": _cue(
        "four_circle_square", 25, 48,
        "Six-circle mirrored projection; lower circles may clip",
    ),
    "dashed_circle": _cue(
        "dashed_circle", 25, 64,
        "Two solid circles with three dashed circles", family="transition",
    ),
    "quarter_circle": _cue(
        "quarter_circle", 25, 80, "Two quarter-circle arcs", family="transition"
    ),
    "spiral": _cue("spiral", 25, 96, "Two mirrored spirals", family="circus"),
    "three_spirals": _cue(
        "three_spirals", 25, 112,
        "Six pinwheels arranged as two triangles", family="circus",
    ),
    "horizontal_squiggle": _cue(
        "horizontal_squiggle", 25, 128, "Horizontal squiggle", family="transition"
    ),
    "vertical_squiggle": _cue(
        "vertical_squiggle", 25, 144, "Vertical squiggle", family="transition"
    ),
    "pinwheel": _cue("pinwheel", 25, 160, "Two mirrored pinwheels", family="circus"),
    "small_circle_square": _cue(
        "small_circle_square", 25, 176,
        "Two mirrored rings of eight small circles",
    ),
    "quarter_arc_cluster": _cue(
        "quarter_arc_cluster", 25, 192,
        "Four small circles around a quarter arc and bright center, mirrored twice",
        family="circus",
    ),
    "spiral_cone": _cue(
        "spiral_cone", 25, 208, "Vertical tornado / spiral cone", family="circus"
    ),
    "flower": _cue("flower", 25, 224, "Two mirrored flowers", family="circus"),
    "alignment_pattern": _cue("alignment_pattern", 25, 240, "Alignment test pattern"),

    "diagonal_down": _cue(
        "diagonal_down", 50, 0, "Two horizontal lines; internal slot A",
        family="transition",
    ),
    "diagonal_up": _cue(
        "diagonal_up", 50, 16, "Two horizontal lines; internal slot B",
        family="transition",
    ),
    "dashed_diagonal": _cue(
        "dashed_diagonal", 50, 64, "Two six-dash horizontal lines",
        family="transition",
    ),
    "diamond": _cue("diamond", 50, 144, "Two mirrored squares", family="circus"),
    "hexagon": _cue("hexagon", 50, 160, "Two mirrored hexagons"),
    "octagon": _cue("octagon", 50, 176, "Two mirrored octagons"),
    "rounded_octagon": _cue(
        "rounded_octagon", 50, 192, "Two eight-segment dashed circles"
    ),
    "quartered_circle": _cue(
        "quartered_circle", 50, 208, "Two four-segment dashed circles",
        family="transition",
    ),
    "dotted_half_heart": _cue(
        "dotted_half_heart", 50, 224, "Two twelve-segment half-circles",
        family="circus",
    ),
    "half_heart": _cue("half_heart", 50, 240, "Two smooth half-circles"),

    "two_dot_line": _cue(
        "two_dot_line", 75, 0, "Three bright horizontal dots; internal slot A",
        family="transition",
    ),
    "four_dot_line": _cue(
        "four_dot_line", 75, 16, "Three bright horizontal dots; internal slot B",
        family="transition",
    ),
    "six_dot_line": _cue(
        "six_dot_line", 75, 32, "Two horizontal rows of six bright dots",
        family="transition",
    ),
    "eight_dot_line": _cue(
        "eight_dot_line", 75, 48, "Two horizontal rows of eight bright dots",
        family="transition",
    ),
    "ten_dot_line": _cue(
        "ten_dot_line", 75, 64, "Two horizontal rows of sixteen bright dots",
        family="transition",
    ),
    "twelve_dot_line": _cue(
        "twelve_dot_line", 75, 80, "Two fine dotted horizontal lines",
        family="transition",
    ),
    "four_dot_triplets": _cue(
        "four_dot_triplets", 75, 96, "Two horizontal rows of grouped dot triplets",
        family="transition",
    ),
    "dotted_trapezoid": _cue(
        "dotted_trapezoid", 75, 112, "Two dotted triangles", family="circus"
    ),
    "dotted_triangle": _cue(
        "dotted_triangle", 75, 128, "Two fine-dotted triangles", family="circus"
    ),
    "dotted_trapezoid_b": _cue(
        "dotted_trapezoid_b", 75, 144, "Two dotted squares", family="circus"
    ),
    "dotted_circles": _cue("dotted_circles", 75, 160, "Three tiny dotted circles"),
    "dotted_quarter_arcs": _cue(
        "dotted_quarter_arcs", 75, 176,
        "Upper-right dotted quarter-circle, mirrored twice",
        family="transition",
    ),
    "sparse_dotted_semicircle": _cue(
        "sparse_dotted_semicircle", 75, 192,
        "Lower-left and upper-right dotted quarter-arcs, mirrored twice",
        family="transition",
    ),
    "dotted_semicircle": _cue(
        "dotted_semicircle", 75, 208, "Two dotted half-circles", family="transition"
    ),
    "dense_dotted_circle": _cue(
        "dense_dotted_circle", 75, 224, "Two full fine-dotted circles", family="circus"
    ),
    "sparse_dotted_circle": _cue(
        "sparse_dotted_circle", 75, 240, "Two large six-dot circles",
        family="transition",
    ),

    "merry_christmas": _cue(
        "merry_christmas", 100, 0, "Two script Merry Christmas projections",
        family="seasonal",
    ),
    "stocking": _cue("stocking", 100, 16, "Two Christmas stockings", family="seasonal"),
    "snowflake": _cue("snowflake", 100, 32, "Two snowflakes", family="circus"),
    "star_ornament": _cue("star_ornament", 100, 48, "Two star ornaments", family="circus"),
    "bells": _cue("bells", 100, 64, "Two sets of bells", family="seasonal"),
    "star_topper": _cue("star_topper", 100, 80, "Two star tree-toppers", family="circus"),
    "snowflake_b": _cue("snowflake_b", 100, 96, "Two alternate snowflakes", family="seasonal"),
    "gift_teddy": _cue(
        "gift_teddy", 100, 112,
        "Two animated gifts bursting open to reveal teddy bears", family="seasonal",
    ),
    "winter_message": _cue(
        "winter_message", 100, 128, "Two Winter Is Coming messages", family="seasonal"
    ),
    "stocking_b": _cue(
        "stocking_b", 100, 144, "Two candy canes", family="seasonal"
    ),
    "group100_slot_160": _cue(
        "group100_slot_160", 100, 160, "Two Random labels plus Chinese characters"
    ),
    "group100_slot_176": _cue(
        "group100_slot_176", 100, 176, "Two Outdoor labels plus Chinese characters"
    ),
    "group100_slot_192": _cue("group100_slot_192", 100, 192, "Two horizontal lines"),
    "group100_slot_208": _cue(
        "group100_slot_208", 100, 208, "Two script Merry Christmas projections"
    ),
    "group100_slot_224": _cue("group100_slot_224", 100, 224, "Two horizontal lines"),
    "group100_slot_240": _cue("group100_slot_240", 100, 240, "Two horizontal lines"),

    "stork_walk": _cue("stork_walk", 125, 16, "Walking stork", family="character"),
    "eagle_perch": _cue("eagle_perch", 125, 32, "Perched eagle", family="character"),
    "bat_flight": _cue("bat_flight", 125, 96, "Flying bat", family="halloween"),
    "salamander_walk": _cue("salamander_walk", 125, 112, "Crawling salamander", family="character"),
    "sparkle_moose": _cue(
        "sparkle_moose", 125, 128, "Reindeer or moose watching a flying sparkle", family="character"
    ),
    "ghost_peek": _cue("ghost_peek", 125, 144, "Ghost or peeping figure", family="halloween"),
    "dolphin_splash": _cue(
        "dolphin_splash", 125, 160, "Dolphin leaping from water", family="character"
    ),
    "bat_trio": _cue("bat_trio", 125, 192, "One, two, then three flying bats", family="halloween"),
    "cobra_strike": _cue("cobra_strike", 125, 208, "Striking cobra", family="character"),
    "maxime_wave": _cue("maxime_wave", 125, 224, "Girl in a large hat waving", family="character"),
    "vintage_plane": _cue(
        "vintage_plane", 125, 240, "Rotating open-cockpit propeller airplane", family="character"
    ),
    "confused_girl": _cue("confused_girl", 150, 0, "Girl looking, then confused", family="character"),
    "elvis": _cue("elvis", 150, 16, "Singing Elvis", family="character"),
    "circle_slinky": _cue("circle_slinky", 150, 32, "Circle-based slinky effect", family="circus"),
    "candy_cane_reindeer": _cue(
        "candy_cane_reindeer", 150, 48, "Reindeer with a candy cane", family="seasonal"
    ),
    "rotating_cube": _cue("rotating_cube", 150, 64, "Rotating 3D cube", family="circus"),
}


# These lists contain only physically identified built-in slots.  They do not
# arm output and can be inspected or scheduled without touching the fixture.
CIRCUS_LOOP = (
    "starburst_spin", "storybook_star", "sun", "fan", "big_circle",
    "four_circle_square", "spiral", "three_spirals", "pinwheel",
    "quarter_arc_cluster", "spiral_cone", "flower", "diamond", "hexagon", "octagon",
    "dotted_trapezoid", "dotted_triangle", "dotted_trapezoid_b",
    "dotted_half_heart",
    "dense_dotted_circle",
    "snowflake", "star_ornament", "star_topper", "circle_slinky",
    "rotating_cube",
)

TRANSITION_LOOP = (
    "thin_bar", "dashed_circle", "quarter_circle", "horizontal_squiggle",
    "vertical_squiggle", "diagonal_down", "diagonal_up",
    "dashed_diagonal", "quartered_circle", "two_dot_line", "four_dot_line",
    "six_dot_line", "eight_dot_line", "ten_dot_line", "twelve_dot_line",
    "four_dot_triplets", "dotted_quarter_arcs", "sparse_dotted_semicircle",
    "dotted_semicircle", "sparse_dotted_circle",
)

GEOMETRY_LOOP = (
    "x_mark", "four_corner_boxes", "bright_square", "two_circles",
    "four_circle_diagonal", "small_circle_square", "alignment_pattern",
    "rounded_octagon", "half_heart", "dotted_circles",
)

CHARACTER_LOOP = (
    "stork_walk", "eagle_perch", "salamander_walk", "sparkle_moose",
    "dolphin_splash", "cobra_strike", "maxime_wave", "vintage_plane",
    "confused_girl", "elvis",
)

HALLOWEEN_LOOP = ("bat_flight", "ghost_peek", "bat_trio")

SEASONAL_LOOP = (
    "merry_christmas", "stocking", "bells", "snowflake_b", "gift_teddy",
    "winter_message", "stocking_b", "candy_cane_reindeer",
)

DIAGNOSTIC_LOOP = (
    "group100_slot_160", "group100_slot_176", "group100_slot_192",
    "group100_slot_208", "group100_slot_224", "group100_slot_240",
)

PLAYLISTS = {
    "circus": CIRCUS_LOOP,
    "transitions": TRANSITION_LOOP,
    "geometry": GEOMETRY_LOOP,
    "characters": CHARACTER_LOOP,
    "halloween": HALLOWEEN_LOOP,
    "seasonal": SEASONAL_LOOP,
    "diagnostic": DIAGNOSTIC_LOOP,
}


def playlist(name: str) -> tuple[LaserCue, ...]:
    """Resolve a named list without arming or opening the DMX interface."""
    return tuple(CUES[cue_name] for cue_name in PLAYLISTS[name])


def cue_channels(name: str, *, armed: bool = False) -> tuple[int, ...]:
    return CUES[name].channels(armed=armed)


def blackout_channels() -> tuple[int, ...]:
    return (0,) * LASER_CHANNELS
