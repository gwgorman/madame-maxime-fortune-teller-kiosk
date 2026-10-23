#!/usr/bin/env python3
"""Print the built-in A057 cue library without opening DMX hardware."""

from __future__ import annotations

import argparse
import json

from laser_cues import CUES, PLAYLISTS


def catalog() -> dict:
    return {
        "cue_count": len(CUES),
        "playlists": {
            name: [
                {
                    "name": cue_name,
                    "description": CUES[cue_name].description,
                    "family": CUES[cue_name].family,
                    "dmx": {
                        "group_ch4": CUES[cue_name].group,
                        "pattern_ch5": CUES[cue_name].pattern,
                        "rotation_ch10": CUES[cue_name].rotation,
                    },
                }
                for cue_name in cue_names
            ]
            for name, cue_names in PLAYLISTS.items()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect the safe built-in small-laser cue library"
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    data = catalog()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return
    print(f"{data['cue_count']} named cues; no DMX output")
    for name, cues in data["playlists"].items():
        print(f"\n{name.upper()} ({len(cues)})")
        for cue in cues:
            dmx = cue["dmx"]
            rotation = f", rotate={dmx['rotation_ch10']}" if dmx["rotation_ch10"] else ""
            print(
                f"  {cue['name']:<24} CH4={dmx['group_ch4']:>3} "
                f"CH5={dmx['pattern_ch5']:>3}{rotation}  {cue['description']}"
            )


if __name__ == "__main__":
    main()
