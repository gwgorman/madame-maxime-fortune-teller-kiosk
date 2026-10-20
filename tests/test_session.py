import json
import random
import tempfile
import unittest
from pathlib import Path

from fortune_engine import QUESTIONS
from session import EventJournal, SessionController, SessionState


class SessionControllerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "journal.json"
        self.controller = SessionController(EventJournal(self.path), random.Random(4))

    def tearDown(self):
        self.temporary.cleanup()

    def complete_questionnaire(self, start=13.0):
        now = start
        for _key, _prompt, values in QUESTIONS:
            self.assertTrue(self.controller.select_answer(values[0], now))
            now += 1
        self.assertEqual(self.controller.state, SessionState.TOPIC)
        self.assertTrue(self.controller.select_topic("SURPRISE ME", now))
        return now

    def test_complete_silent_reading(self):
        self.assertTrue(self.controller.approach(10.0))
        self.controller.update(11.9)
        self.assertEqual(self.controller.state, SessionState.READY)
        self.assertTrue(self.controller.begin(12.0))
        thinking_at = self.complete_questionnaire()
        self.controller.update(thinking_at + 3.9)
        self.assertEqual(self.controller.state, SessionState.REVEAL)
        self.assertIsNotNone(self.controller.fortune)
        self.assertEqual(len(self.controller.answers), 4)
        self.assertTrue(self.controller.finish_reveal(thinking_at + 4.0))
        self.controller.update(thinking_at + 8.1)
        self.assertEqual(self.controller.state, SessionState.IDLE)

    def test_return_visit_reuses_prior_reading_context(self):
        self.controller.approach(0.0)
        self.controller.update(2.0)
        self.controller.begin(2.1)
        thinking_at = self.complete_questionnaire(3.0)
        self.controller.update(thinking_at + 4.0)
        first = self.controller.fortune
        self.controller.finish_reveal(thinking_at + 4.1)
        self.controller.update(thinking_at + 8.2)
        self.assertTrue(self.controller.approach(thinking_at + 9.0, returning=True))
        self.controller.update(thinking_at + 11.0)
        self.assertEqual(self.controller.state, SessionState.RETURN_PROMPT)
        self.assertTrue(self.controller.answer_return("IT GOT WORSE", thinking_at + 11.1))
        self.controller.update(thinking_at + 15.0)
        self.assertEqual(self.controller.state, SessionState.REVEAL)
        self.assertEqual(self.controller.fortune.visit_number, 2)
        self.assertNotEqual(self.controller.fortune.fingerprint, first.fingerprint)
        self.assertNotEqual(self.controller.fortune.prediction, first.prediction)
        self.assertEqual(self.controller.fortune.title, "THE MOON RETURNS")
        self.assertTrue(self.controller.fortune.return_callback)

    def test_questionnaire_timeout_recovers(self):
        self.controller.approach(0.0)
        self.controller.update(2.0)
        self.controller.begin(3.0)
        self.controller.update(34.0)
        self.assertEqual(self.controller.state, SessionState.FAREWELL)
        self.controller.update(39.0)
        self.assertEqual(self.controller.state, SessionState.IDLE)

    def test_journal_is_persistent_and_anonymous(self):
        self.controller.approach(1.0)
        stored = json.loads(self.path.read_text())
        self.assertEqual(stored["schema"], 2)
        self.assertEqual(stored["approaches"], 1)
        self.assertNotIn("transcript", stored)
        self.assertNotIn("image", stored)
        self.assertNotIn("name", stored)

    def test_invalid_actions_do_not_change_state(self):
        self.assertFalse(self.controller.begin(1.0))
        self.assertFalse(self.controller.select_answer("LOVE", 1.0))
        self.assertFalse(self.controller.select_topic("WORK", 1.0))
        self.assertEqual(self.controller.state, SessionState.IDLE)


if __name__ == "__main__":
    unittest.main()
