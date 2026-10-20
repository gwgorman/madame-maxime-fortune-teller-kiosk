import unittest

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


if __name__ == "__main__":
    unittest.main()
