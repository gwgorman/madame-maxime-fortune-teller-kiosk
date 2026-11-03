import unittest

from dmx_broker import BROKER_CHANNELS, BrokerState, MAX_LASER_TTL
from dmx_lighting import Universe
from big_laser_cues import (
    BIG_LASER_ADDRESS,
    bright_line_color_channels,
    bright_line_geometry_channels,
    bright_line_test_channels,
    safe_geometry_channels,
)
from laser_cues import LASER_ADDRESS, cue_channels


class DmxBrokerStateTests(unittest.TestCase):
    def setUp(self):
        self.universe = Universe(BROKER_CHANNELS)
        self.state = BrokerState(self.universe)

    def test_par_and_laser_frames_share_one_universe(self):
        self.state.set_par((40, 1, 2, 3))
        self.state.arm_laser("maxime_wave", now=10.0)
        frame = self.universe.snapshot()
        self.assertEqual(frame[1:7], bytes((40, 1, 2, 3, 0, 0)))
        self.assertEqual(frame[7:13], bytes((40, 1, 2, 3, 0, 0)))
        self.assertEqual(frame[LASER_ADDRESS:LASER_ADDRESS + 16], bytes(cue_channels("maxime_wave", armed=True)))

    def test_laser_expires_without_disturbing_pars(self):
        self.state.set_par((40, 1, 2, 3))
        self.state.arm_laser("bat_flight", now=10.0, ttl=0.5)
        self.assertFalse(self.state.tick(10.49))
        self.assertTrue(self.state.tick(10.5))
        frame = self.universe.snapshot()
        self.assertEqual(frame[1:7], bytes((40, 1, 2, 3, 0, 0)))
        self.assertEqual(frame[LASER_ADDRESS:LASER_ADDRESS + 16], bytes(16))

    def test_individual_par_diagnostic_does_not_change_other_fixture(self):
        self.state.set_par((20, 1, 2, 3))
        self.state.set_par_fixture(7, (90, 4, 5, 6))
        frame = self.universe.snapshot()
        self.assertEqual(frame[1:7], bytes((20, 1, 2, 3, 0, 0)))
        self.assertEqual(frame[7:13], bytes((90, 4, 5, 6, 0, 0)))

    def test_individual_par_rejects_unknown_address(self):
        with self.assertRaises(ValueError):
            self.state.set_par_fixture(30, (90, 4, 5, 6))

    def test_heartbeat_extends_only_matching_armed_cue(self):
        self.state.arm_laser("cobra_strike", now=1.0, ttl=0.5)
        self.state.heartbeat_laser("cobra_strike", now=1.4, ttl=0.5)
        self.assertFalse(self.state.tick(1.89))
        self.assertTrue(self.state.tick(1.9))
        with self.assertRaises(ValueError):
            self.state.heartbeat_laser("elvis", now=2.0)

    def test_ttl_is_capped(self):
        self.state.arm_laser("elvis", now=5.0, ttl=999)
        self.assertEqual(self.state.laser_deadline, 5.0 + MAX_LASER_TTL)

    def test_shutdown_blacks_out_everything(self):
        self.state.set_par((40, 1, 2, 3))
        self.state.arm_laser("elvis", now=1.0)
        self.assertFalse(self.state.handle({"command": "shutdown"}, now=1.1))
        self.assertEqual(self.universe.snapshot()[1:], bytes(BROKER_CHANNELS))

    def test_invalid_command_is_rejected(self):
        with self.assertRaises(ValueError):
            self.state.handle({"command": "surprise"}, now=0.0)

    def test_big_laser_safe_frame_is_bounded_and_strobe_locked(self):
        self.state.arm_big_laser("safe_geometry", now=1.0)
        frame = self.universe.snapshot()
        values = frame[BIG_LASER_ADDRESS:BIG_LASER_ADDRESS + 36]
        self.assertEqual(values, bytes(safe_geometry_channels(armed=True)))
        self.assertEqual(values[0], 32)
        self.assertEqual(values[1], 27)
        self.assertEqual(values[3], 10)
        self.assertEqual(values[10], 0)
        self.assertEqual(values[20], 0)
        self.assertEqual(values[27], 0)

    def test_big_laser_expires_without_disturbing_small_laser_or_pars(self):
        self.state.set_par((40, 1, 2, 3))
        self.state.arm_laser("bat_flight", now=1.0, ttl=2.0)
        self.state.arm_big_laser("safe_geometry", now=1.0, ttl=0.5)
        self.assertTrue(self.state.tick(1.5))
        frame = self.universe.snapshot()
        self.assertEqual(frame[1:7], bytes((40, 1, 2, 3, 0, 0)))
        self.assertEqual(
            frame[LASER_ADDRESS:LASER_ADDRESS + 16],
            bytes(cue_channels("bat_flight", armed=True)),
        )
        self.assertEqual(frame[BIG_LASER_ADDRESS:BIG_LASER_ADDRESS + 36], bytes(36))

    def test_big_laser_bright_line_test_is_bounded_and_strobe_locked(self):
        self.state.arm_big_laser("bright_line_test", now=1.0)
        values = self.universe.snapshot()[BIG_LASER_ADDRESS:BIG_LASER_ADDRESS + 36]
        self.assertEqual(values, bytes(bright_line_test_channels(armed=True)))
        self.assertEqual(values[0], 128)
        self.assertEqual(values[10], 0)
        self.assertEqual(values[27], 0)

    def test_big_laser_static_color_tests_change_only_color(self):
        expected = {"bright_line_red": 8, "bright_line_green": 16, "bright_line_blue": 24}
        base = list(bright_line_test_channels(armed=True))
        for cue, color in expected.items():
            self.state.arm_big_laser(cue, now=1.0)
            values = list(self.universe.snapshot()[BIG_LASER_ADDRESS:BIG_LASER_ADDRESS + 36])
            self.assertEqual(values, list(bright_line_color_channels(color, armed=True)))
            self.assertEqual(values[7], color)
            values[7] = base[7]
            self.assertEqual(values, base)

    def test_big_laser_geometry_tests_are_bounded(self):
        expected = {
            "bright_line_small": (64, 128),
            "bright_line_medium": (128, 128),
            "bright_line_large": (192, 128),
            "bright_line_left": (128, 80),
            "bright_line_center": (128, 128),
            "bright_line_right": (128, 176),
        }
        for cue, (size, x_position) in expected.items():
            self.state.arm_big_laser(cue, now=1.0)
            values = self.universe.snapshot()[BIG_LASER_ADDRESS:BIG_LASER_ADDRESS + 36]
            self.assertEqual(
                values,
                bytes(bright_line_geometry_channels(
                    size=size, x_position=x_position, armed=True
                )),
            )
            self.assertEqual(values[10], 0)
            self.assertEqual(values[27], 0)


if __name__ == "__main__":
    unittest.main()
