import unittest

from laser_cues import (
    CUES,
    LASER_CHANNELS,
    MINIMUM_ENABLE,
    SAFE_HORIZONTAL,
    SAFE_SIZE,
    SAFE_VERTICAL,
    blackout_channels,
    cue_channels,
)


class LaserCueTests(unittest.TestCase):
    def test_unarmed_cues_are_blackout(self):
        for name in CUES:
            self.assertEqual(cue_channels(name), blackout_channels())

    def test_every_armed_cue_obeys_safe_frame_contract(self):
        for cue in CUES.values():
            frame = cue.channels(armed=True)
            self.assertEqual(len(frame), LASER_CHANNELS)
            self.assertEqual(frame[0], MINIMUM_ENABLE)
            self.assertEqual(frame[5], 0)
            self.assertEqual(frame[7], SAFE_SIZE)
            self.assertEqual(frame[8], 0)
            self.assertEqual(frame[10:12], (0, 0))
            self.assertEqual(frame[12], SAFE_HORIZONTAL)
            self.assertEqual(frame[13], SAFE_VERTICAL)
            self.assertEqual(frame[14:16], (0, 0))

    def test_only_verified_starburst_uses_rotation(self):
        rotating = {cue.name for cue in CUES.values() if cue.rotation}
        self.assertEqual(rotating, {"starburst_spin"})

    def test_unknown_cue_is_rejected(self):
        with self.assertRaises(KeyError):
            cue_channels("not-a-real-cue", armed=True)


if __name__ == "__main__":
    unittest.main()
