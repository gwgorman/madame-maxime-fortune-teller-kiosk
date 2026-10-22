import unittest

from dmx_lighting import PAR_ADDRESSES, ParScene, TRANSMIT_CHANNELS, Universe
from lighting import LightingController, SCENES


class FakeDmxClient:
    def __init__(self):
        self.par_updates = []
        self.blackout_count = 0

    def set_par(self, values):
        self.par_updates.append(tuple(values))

    def blackout_all(self):
        self.blackout_count += 1


class LightingControllerTests(unittest.TestCase):
    def test_disabled_adapter_is_safe(self):
        lighting = LightingController(enabled=False)
        lighting.start()
        lighting.update("reveal", 10.0)
        lighting.stop()
        self.assertFalse(lighting.available)
        self.assertIsNone(lighting.error)

    def test_all_session_scenes_are_bounded(self):
        for values in SCENES.values():
            self.assertEqual(len(values), 4)
            self.assertTrue(all(0 <= value <= 255 for value in values))

    def test_fixture_group_update_reaches_one_snapshot_together(self):
        universe = Universe()
        scene = ParScene(50, 120, 30, 200)
        universe.set_pars(PAR_ADDRESSES, scene)
        frame = universe.snapshot()
        self.assertEqual(frame[1:7], bytes(scene.channels()))
        self.assertEqual(frame[7:13], bytes(scene.channels()))
        self.assertEqual(len(frame), TRANSMIT_CHANNELS + 1)

    def test_enabled_controller_uses_broker_client_and_blacks_out(self):
        client = FakeDmxClient()
        lighting = LightingController(enabled=True, client=client)
        lighting.start()
        lighting.update("reveal", 10.0)
        lighting._stop.set()
        lighting.stop()
        self.assertTrue(client.par_updates)
        self.assertEqual(client.blackout_count, 1)
        self.assertFalse(lighting.available)

    def test_broker_failure_is_isolated(self):
        class BrokenClient(FakeDmxClient):
            def set_par(self, values):
                raise FileNotFoundError("DMX broker unavailable")

        lighting = LightingController(enabled=True, client=BrokenClient())
        lighting.start()
        self.assertFalse(lighting.available)
        self.assertIn("broker unavailable", lighting.error)
        lighting.stop()


if __name__ == "__main__":
    unittest.main()
