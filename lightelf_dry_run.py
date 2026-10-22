#!/usr/bin/env python3
"""Render the complete front-laser playlist without opening Bluetooth."""

from __future__ import annotations

import hashlib
import json

from lightelf_adapter import ASSET_DIR, FRONT_SCENES
from lightelf_protocol import svg_packet, text_packet


def manifest() -> list[dict]:
    result = []
    for name, scene in FRONT_SCENES.items():
        if scene.kind == "text":
            packet = text_packet(
                scene.content, color=scene.color, size_percent=scene.size_percent
            )
        else:
            packet = svg_packet(
                ASSET_DIR / scene.content,
                color=scene.color,
                size_percent=scene.size_percent,
            )
        result.append({
            "scene": name,
            "kind": scene.kind,
            "description": scene.description,
            "size_percent": scene.size_percent,
            "production": scene.production,
            "packet_bytes": len(packet),
            "points": int.from_bytes(packet[20:22], "big"),
            "sha256": hashlib.sha256(packet).hexdigest(),
        })
    return result


if __name__ == "__main__":
    print(json.dumps({"hardware_opened": False, "scenes": manifest()}, indent=2))
