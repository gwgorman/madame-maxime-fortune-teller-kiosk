"""Small, deterministic subset of the LightELF drawing protocol.

Protocol behavior is adapted from the MIT-licensed aderusha/lightelf_laser
project pinned in docs/LIGHTELF_INTEGRATION.md. This module performs no I/O.
"""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path


PROJECTOR_LIMIT = 400
MAX_POINTS = 180
COLOR_IDS = {"red": 1, "green": 2, "blue": 3, "yellow": 4,
             "cyan": 5, "purple": 6, "magenta": 6, "white": 7, "full": 7}
TOKEN = re.compile(r"[A-Za-z]|[-+]?(?:\d+(?:\.\d*)?|\.\d+)")
FONT_STROKES = {
    "A": ("a", "b", "c", "e", "f", "g"), "C": ("a", "d", "e", "f"),
    "D": ("a", "b", "c", "d", "e", "f"), "E": ("a", "d", "e", "f", "g"),
    "I": ("a", "d", "vu", "vd"), "L": ("d", "e", "f"),
    "M": ("b", "c", "e", "f", "ul", "ur"), "O": ("a", "b", "c", "d", "e", "f"),
    "Q": ("a", "b", "c", "d", "e", "f", "lr"),
    "R": ("a", "b", "e", "f", "g", "lr"), "S": ("a", "c", "d", "f", "g"),
    "U": ("b", "c", "d", "e"), "W": ("b", "c", "e", "f", "ll", "lr"),
}
FONT_SEGMENTS = {
    "a": ((0, 6), (4, 6)), "b": ((4, 6), (4, 3)), "c": ((4, 3), (4, 0)),
    "d": ((0, 0), (4, 0)), "e": ((0, 3), (0, 0)), "f": ((0, 6), (0, 3)),
    "g": ((0, 3), (4, 3)), "vu": ((2, 6), (2, 3)), "vd": ((2, 3), (2, 0)),
    "ul": ((0, 6), (2, 3)), "ur": ((4, 6), (2, 3)),
    "ll": ((0, 0), (2, 3)), "lr": ((2, 3), (4, 0)),
}


def _word(value: int | float) -> bytes:
    value = int(round(value))
    encoded = (0x8000 | -value) if value < 0 else value
    if not 0 <= encoded <= 0xFFFF:
        raise ValueError("coordinate is outside the LightELF word range")
    return encoded.to_bytes(2, "big")


def power_packet(on: bool) -> bytes:
    return bytes.fromhex("B0B1B2B3" + ("FF" if on else "00") + "B4B5B6B7")


def draw_packet(
    segments, *, color: int = 7, steps_per_edge: int = 3,
    transforms: dict[int, int] | None = None,
) -> bytes:
    """Encode bounded continuous strokes in the old-protocol F0 envelope."""
    if not 1 <= int(color) <= 7:
        raise ValueError("color must be a LightELF color index from 1 through 7")
    points: list[tuple[int, int, int]] = []
    for segment in segments:
        if len(segment) < 2:
            continue
        stroke_start = len(points)
        for edge, ((x1, y1), (x2, y2)) in enumerate(zip(segment, segment[1:])):
            for step in range(steps_per_edge):
                if edge and step == 0:
                    continue
                ratio = step / (steps_per_edge - 1)
                x = round(x1 + (x2 - x1) * ratio)
                y = round(y1 + (y2 - y1) * ratio)
                if max(abs(x), abs(y)) > PROJECTOR_LIMIT:
                    raise ValueError("drawing exceeds the bounded projector field")
                points.append((x, y, 0x02 if len(points) == stroke_start else color << 4))
        if len(points) > stroke_start:
            x, y, _ = points[-1]
            points[-1] = (x, y, (color << 4) | 0x03)
    if not points or len(points) > MAX_POINTS:
        raise ValueError(f"drawing must contain 1 through {MAX_POINTS} points")

    payload = bytearray(16)  # 15 config bytes plus unsaved (zero) save tag
    for index, value in (transforms or {}).items():
        if index not in {7, 8}:
            raise ValueError("operator demo permits only the two verified spin fields")
        if not 128 <= int(value) <= 160:
            raise ValueError("operator-demo spin must stay in the slow 128-160 band")
        payload[index] = int(value)
    payload.extend(len(points).to_bytes(2, "big"))
    for x, y, control in points:
        payload.extend(_word(x))
        payload.extend(_word(y))
        payload.append(control)
    return bytes.fromhex("F0F1F2F3") + payload + bytes.fromhex("F4F5F6F7")


def _path_segments(path_data: str) -> list[list[tuple[float, float]]]:
    tokens = TOKEN.findall(path_data)
    result: list[list[tuple[float, float]]] = []
    stroke: list[tuple[float, float]] = []
    command = ""
    cursor = (0.0, 0.0)
    origin = cursor
    index = 0
    while index < len(tokens):
        if tokens[index].isalpha():
            command = tokens[index]
            index += 1
        if command in {"M", "L"}:
            point = (float(tokens[index]), float(tokens[index + 1]))
            index += 2
            if command == "M":
                if len(stroke) > 1:
                    result.append(stroke)
                stroke = [point]
                origin = point
                command = "L"
            else:
                stroke.append(point)
            cursor = point
        elif command == "H":
            cursor = (float(tokens[index]), cursor[1])
            stroke.append(cursor)
            index += 1
        elif command == "V":
            cursor = (cursor[0], float(tokens[index]))
            stroke.append(cursor)
            index += 1
        elif command in {"Z", "z"}:
            stroke.append(origin)
            command = ""
        else:
            raise ValueError(f"unsupported SVG path command: {command!r}")
    if len(stroke) > 1:
        result.append(stroke)
    return result


def svg_segments(path: Path, *, size_percent: int) -> list[list[tuple[int, int]]]:
    """Convert the repository's intentionally simple SVG assets to laser space."""
    if not 10 <= int(size_percent) <= 60:
        raise ValueError("scene size must stay between 10 and 60 percent")
    root = ET.parse(path).getroot()
    viewbox = [float(value) for value in root.attrib["viewBox"].split()]
    left, top, width, height = viewbox
    raw: list[list[tuple[float, float]]] = []
    for element in root.iter():
        name = element.tag.rsplit("}", 1)[-1]
        if name == "path":
            raw.extend(_path_segments(element.attrib.get("d", "")))
        elif name == "circle":
            cx, cy = float(element.attrib["cx"]), float(element.attrib["cy"])
            radius = float(element.attrib["r"])
            raw.append([
                (cx + radius * math.cos(2 * math.pi * i / 8),
                 cy + radius * math.sin(2 * math.pi * i / 8))
                for i in range(9)
            ])
    scale = (PROJECTOR_LIMIT * 2 * size_percent / 100) / max(width, height)
    center_x, center_y = left + width / 2, top + height / 2
    # This firmware's BLE drawing coordinates use screen-style positive Y down,
    # matching SVG. Do not apply the usual Cartesian Y-axis inversion.
    return [[(round((x - center_x) * scale), round((y - center_y) * scale))
             for x, y in stroke] for stroke in raw]


def svg_packet(path: Path, *, color: str, size_percent: int) -> bytes:
    return draw_packet(
        svg_segments(path, size_percent=size_percent),
        color=COLOR_IDS[color],
        # SVG curves have already been converted to short line segments. One
        # device point per vertex avoids doubling the galvo workload and making
        # complex drawings visibly rebuild stroke by stroke.
        steps_per_edge=2,
    )


def text_segments(text: str, *, size_percent: int) -> list[list[tuple[int, int]]]:
    """Render the approved uppercase projector fallback font within bounds."""
    text = text.upper()
    unsupported = set(text) - set(FONT_STROKES) - {" "}
    if unsupported:
        raise ValueError(f"unsupported LightELF text characters: {sorted(unsupported)}")
    if not 10 <= int(size_percent) <= 60:
        raise ValueError("scene size must stay between 10 and 60 percent")
    advance = 5.5
    raw_width = max(4.0, len(text) * advance - 1.5)
    target_width = PROJECTOR_LIMIT * 2 * size_percent / 100
    scale = min(target_width / raw_width, target_width / 6.0)
    left = -raw_width * scale / 2
    top = -3 * scale
    segments = []
    for index, char in enumerate(text):
        x_offset = left + index * advance * scale
        for name in FONT_STROKES.get(char, ()):
            (x1, y1), (x2, y2) = FONT_SEGMENTS[name]
            segments.append([
                (round(x_offset + x1 * scale), round(top + (6 - y1) * scale)),
                (round(x_offset + x2 * scale), round(top + (6 - y2) * scale)),
            ])
    return segments


def text_packet(
    text: str, *, color: str, size_percent: int, spin: int | None = None,
    spin_field: int = 8,
) -> bytes:
    return draw_packet(
        text_segments(text, size_percent=size_percent),
        color=COLOR_IDS[color],
        steps_per_edge=2,
        transforms={spin_field: spin} if spin is not None else None,
    )
