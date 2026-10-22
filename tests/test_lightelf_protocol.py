import os
import unittest

from lightelf_adapter import ASSET_DIR, FRONT_SCENES
from lightelf_protocol import (
    COLOR_IDS, MAX_POINTS, power_packet, svg_packet, svg_segments, text_packet,
    text_segments,
)
from lightelf_transport import (
    LIVE_INTERLOCK, MAX_LEASE_SECONDS, POWER_SETTLE_SECONDS,
    VISIBLE_LEASE_SECONDS, LightElfBleTransport,
)
from lightelf_dry_run import manifest


class LightElfProtocolTests(unittest.TestCase):
    def test_power_packets_are_fixed(self):
        self.assertEqual(power_packet(True).hex().upper(), "B0B1B2B3FFB4B5B6B7")
        self.assertEqual(power_packet(False).hex().upper(), "B0B1B2B300B4B5B6B7")

    def test_captured_firmware_color_indices_and_timing_are_bounded(self):
        self.assertEqual(
            {name: COLOR_IDS[name] for name in ("red", "green", "blue", "yellow", "cyan", "purple", "white")},
            {"red": 1, "green": 2, "blue": 3, "yellow": 4, "cyan": 5, "purple": 6, "white": 7},
        )
        self.assertLess(0, POWER_SETTLE_SECONDS)
        self.assertLessEqual(VISIBLE_LEASE_SECONDS, MAX_LEASE_SECONDS)

    def test_all_svg_scenes_fit_safety_bounds_and_point_budget(self):
        for scene in FRONT_SCENES.values():
            if scene.kind != "svg":
                continue
            path = ASSET_DIR / scene.content
            segments = svg_segments(path, size_percent=scene.size_percent)
            self.assertTrue(segments)
            self.assertLessEqual(
                max(abs(value) for stroke in segments for point in stroke for value in point),
                240,
            )
            packet = svg_packet(path, color=scene.color, size_percent=scene.size_percent)
            self.assertEqual(packet[:4], bytes.fromhex("F0F1F2F3"))
            self.assertEqual(packet[-4:], bytes.fromhex("F4F5F6F7"))
            self.assertLessEqual(int.from_bytes(packet[20:22], "big"), MAX_POINTS)

    def test_big_top_flag_is_above_the_tent_in_device_coordinates(self):
        scene = FRONT_SCENES["big_top"]
        segments = svg_segments(ASSET_DIR / scene.content, size_percent=scene.size_percent)
        flag_y = min(y for point in segments[0] for _, y in [point])
        tent_roof_y = min(y for point in segments[2] for _, y in [point])
        self.assertLess(flag_y, tent_roof_y)

    def test_approved_text_scenes_fit_safety_bounds_and_point_budget(self):
        for scene in FRONT_SCENES.values():
            if scene.kind != "text":
                continue
            segments = text_segments(scene.content, size_percent=scene.size_percent)
            self.assertTrue(segments)
            self.assertLessEqual(
                max(abs(value) for stroke in segments for point in stroke for value in point),
                240,
            )
            packet = text_packet(
                scene.content, color=scene.color, size_percent=scene.size_percent
            )
            self.assertLessEqual(int.from_bytes(packet[20:22], "big"), MAX_POINTS)

    def test_operator_text_axis_flip_is_limited_to_verified_slow_band(self):
        packet = text_packet("WELCOME", color="yellow", size_percent=45, spin=140)
        self.assertEqual(packet[12], 140)
        other_axis = text_packet(
            "WELCOME", color="yellow", size_percent=45, spin=140, spin_field=7
        )
        self.assertEqual(other_axis[11], 140)
        with self.assertRaises(ValueError):
            text_packet("WELCOME", color="yellow", size_percent=45, spin=200)

    def test_live_transport_requires_two_part_interlock(self):
        old = os.environ.pop("MADAME_MAXIME_LIGHTELF_LIVE", None)
        try:
            self.assertFalse(LightElfBleTransport(enabled=True).enabled)
            os.environ["MADAME_MAXIME_LIGHTELF_LIVE"] = LIVE_INTERLOCK
            self.assertFalse(LightElfBleTransport(enabled=False).enabled)
            self.assertTrue(LightElfBleTransport(enabled=True).enabled)
        finally:
            if old is None:
                os.environ.pop("MADAME_MAXIME_LIGHTELF_LIVE", None)
            else:
                os.environ["MADAME_MAXIME_LIGHTELF_LIVE"] = old

    def test_disabled_transport_refuses_output_without_starting_worker(self):
        transport = LightElfBleTransport(enabled=False)
        with self.assertRaises(RuntimeError):
            transport.show_svg(
                ASSET_DIR / FRONT_SCENES["circus_star"].content,
                color="full",
                size_percent=45,
            )
        self.assertFalse(transport.diagnostic_snapshot["worker_alive"])

    def test_dry_run_covers_every_scene_without_hardware(self):
        rendered = manifest()
        self.assertEqual({item["scene"] for item in rendered}, set(FRONT_SCENES))
        self.assertTrue(all(item["points"] <= MAX_POINTS for item in rendered))


if __name__ == "__main__":
    unittest.main()
