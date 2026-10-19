import json
import random
import tempfile
import unittest
from pathlib import Path

from session import EventJournal, SessionController, SessionState


class SessionControllerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "journal.json"
        self.controller = SessionController(EventJournal(self.path), random.Random(4))

    def tearDown(self):
        self.temporary.cleanup()

    def test_complete_silent_reading(self):
        self.assertTrue(self.controller.approach(10.0))
        self.controller.update(12.6)
        self.assertEqual(self.controller.state, SessionState.READY)
        self.assertTrue(self.controller.begin(13.0))
        self.assertTrue(self.controller.guest_finished(14.0))
        self.controller.update(16.5)
        self.assertEqual(self.controller.state, SessionState.REVEAL)
        self.assertIsNotNone(self.controller.fortune)
        self.controller.update(30.6)
        self.assertEqual(self.controller.state, SessionState.FAREWELL)
        self.controller.update(34.7)
        self.assertEqual(self.controller.state, SessionState.IDLE)

    def test_listening_timeout_recovers(self):
        self.controller.approach(0.0)
        self.controller.update(3.0)
        self.controller.begin(4.0)
        self.controller.update(20.0)
        self.assertEqual(self.controller.state, SessionState.FAREWELL)
        self.controller.update(25.0)
        self.assertEqual(self.controller.state, SessionState.IDLE)

    def test_journal_is_persistent_and_anonymous(self):
        self.controller.approach(1.0)
        stored = json.loads(self.path.read_text())
        self.assertEqual(stored["approaches"], 1)
        self.assertNotIn("transcript", stored)
        self.assertNotIn("image", stored)

    def test_invalid_actions_do_not_change_state(self):
        self.assertFalse(self.controller.begin(1.0))
        self.assertFalse(self.controller.guest_finished(1.0))
        self.assertEqual(self.controller.state, SessionState.IDLE)


if __name__ == "__main__":
    unittest.main()
