import unittest

from dmx_broker import BROKER_CHANNELS, BrokerState, MAX_LASER_TTL
from dmx_lighting import Universe
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


if __name__ == "__main__":
    unittest.main()
