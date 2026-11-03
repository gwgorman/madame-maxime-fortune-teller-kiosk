import unittest

from voice_input import VoiceChoiceAdapter, map_choice


class VoiceChoiceTests(unittest.TestCase):
    def test_maps_exact_and_natural_choices(self):
        choices = ("LOVE", "FORTUNE", "ADVENTURE", "MISCHIEF")
        self.assertEqual(map_choice("Adventure.", choices), "ADVENTURE")
        self.assertEqual(map_choice("I choose mischief", choices), "MISCHIEF")
        self.assertEqual(map_choice("fortoon", choices), "FORTUNE")

    def test_maps_multiword_aliases(self):
        self.assertEqual(map_choice("No, not yet.", ("YES", "NOT YET", "IT GOT WORSE")), "NOT YET")
        self.assertEqual(map_choice("It got much worse", ("YES", "NOT YET", "IT GOT WORSE")), "IT GOT WORSE")
        self.assertEqual(map_choice("You choose", ("LOVE", "SURPRISE ME")), "SURPRISE ME")

    def test_rejects_unrelated_or_ambiguous_text(self):
        self.assertIsNone(map_choice("What was the question?", ("LOVE", "WORK", "CHANGE")))
        self.assertIsNone(map_choice("", ("LOVE", "WORK")))

    def test_adapter_emits_result_without_blocking_caller(self):
        calls = []

        def requester(payload, timeout, progress):
            calls.append(payload)
            progress({"event": "captured"})
            return {"ok": True, "text": "Adventure.", "metrics": {"capture_seconds": 1.0}}

        adapter = VoiceChoiceAdapter(requester)
        self.assertTrue(adapter.start("Choose", ("LOVE", "ADVENTURE")))
        adapter.thread.join(1.0)
        events = adapter.poll()
        self.assertEqual(events[0][0], "thinking")
        self.assertEqual(events[1][1]["selected"], "ADVENTURE")
        self.assertEqual(calls[0]["keywords"], ["LOVE", "ADVENTURE"])

    def test_invalidated_result_is_discarded(self):
        def requester(payload, timeout, progress):
            return {"ok": True, "text": "Love.", "metrics": {}}

        adapter = VoiceChoiceAdapter(requester)
        adapter.start("Choose", ("LOVE", "WORK"))
        adapter.invalidate()
        adapter.thread.join(1.0)
        self.assertEqual(adapter.poll(), [])


if __name__ == "__main__":
    unittest.main()
