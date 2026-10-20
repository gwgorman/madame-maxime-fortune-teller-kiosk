import json
import tempfile
import unittest
from pathlib import Path

from madame_maxime import OFFICE_SERVICE, launch_office_console


class OperatorHandoffTests(unittest.TestCase):
    def test_office_handoff_preserves_settings_and_starts_service(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "startrek-console.json"
            config.write_text(json.dumps({"bridge_ambience": 72, "max_enabled": True}))
            calls = []

            def runner(command, check):
                calls.append((command, check))

            launch_office_console(config, runner)
            saved = json.loads(config.read_text())
            self.assertEqual(saved["display_mode"], "SHIP STATUS")
            self.assertEqual(saved["status_page"], "NETWORK")
            self.assertEqual(saved["venue_override"], "OFFICE")
            self.assertEqual(saved["bridge_ambience"], 72)
            self.assertTrue(saved["max_enabled"])
            self.assertEqual(calls, [(["systemctl", "--user", "start", OFFICE_SERVICE], True)])


if __name__ == "__main__":
    unittest.main()
