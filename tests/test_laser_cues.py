import unittest

from laser_cues import (
    CUES,
    PLAYLISTS,
    LASER_CHANNELS,
    MINIMUM_ENABLE,
    SAFE_HORIZONTAL,
    SAFE_SIZE,
    SAFE_VERTICAL,
    blackout_channels,
    cue_channels,
    playlist,
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

    def test_every_playlist_resolves_to_unique_observed_slots(self):
        for name, cue_names in PLAYLISTS.items():
            self.assertTrue(cue_names, name)
            self.assertEqual(len(cue_names), len(set(cue_names)), name)
            resolved = playlist(name)
            self.assertEqual(tuple(cue.name for cue in resolved), cue_names)
            for cue in resolved:
                self.assertIs(CUES[cue.name], cue)

    def test_every_named_cue_belongs_to_exactly_one_playlist(self):
        assignments = [cue_name for names in PLAYLISTS.values() for cue_name in names]
        self.assertEqual(set(assignments), set(CUES))
        self.assertEqual(len(assignments), len(set(assignments)))

    def test_circus_playlist_avoids_text_and_unqualified_rotation(self):
        for cue in playlist("circus"):
            self.assertNotIn("text", cue.description.lower())
            if cue.rotation:
                self.assertEqual(cue.name, "starburst_spin")

    def test_playlist_lookup_rejects_unknown_name(self):
        with self.assertRaises(KeyError):
            playlist("not-a-real-playlist")

    def test_unknown_cue_is_rejected(self):
        with self.assertRaises(KeyError):
            cue_channels("not-a-real-cue", armed=True)


if __name__ == "__main__":
    unittest.main()
