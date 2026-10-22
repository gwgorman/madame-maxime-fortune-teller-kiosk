import unittest

from dmx_lighting import PAR_ADDRESSES, ParScene, TRANSMIT_CHANNELS, Universe
from lighting import LightingController, SCENES


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


if __name__ == "__main__":
    unittest.main()
