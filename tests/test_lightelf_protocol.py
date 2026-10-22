import os
import unittest

from lightelf_adapter import ASSET_DIR, FRONT_SCENES
from lightelf_protocol import (
    MAX_POINTS, power_packet, svg_packet, svg_segments, text_packet, text_segments,
)
from lightelf_transport import LIVE_INTERLOCK, LightElfBleTransport
from lightelf_dry_run import manifest


class LightElfProtocolTests(unittest.TestCase):
    def test_power_packets_are_fixed(self):
        self.assertEqual(power_packet(True).hex().upper(), "B0B1B2B3FFB4B5B6B7")
        self.assertEqual(power_packet(False).hex().upper(), "B0B1B2B300B4B5B6B7")

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
