import unittest

from laser_cues import CUES, PLAYLISTS
from laser_library_report import catalog


class LaserLibraryReportTests(unittest.TestCase):
    def test_catalog_contains_every_playlist_and_cue_count(self):
        report = catalog()
        self.assertEqual(report["cue_count"], len(CUES))
        self.assertEqual(set(report["playlists"]), set(PLAYLISTS))
        for name, cue_names in PLAYLISTS.items():
            self.assertEqual(
                [entry["name"] for entry in report["playlists"][name]],
                list(cue_names),
            )


if __name__ == "__main__":
    unittest.main()
