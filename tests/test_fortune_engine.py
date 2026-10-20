import random
import unittest

from fortune_engine import FortuneEngine


class FortuneEngineTests(unittest.TestCase):
    def test_350_readings_avoid_recent_duplicates(self):
        engine = FortuneEngine(random.Random(2027))
        recent = []
        all_fingerprints = set()
        choices = {"desire": "MISCHIEF", "nature": "CHAOTIC", "omen": "RAVEN", "honesty": "MERCILESS"}
        for _ in range(350):
            fortune = engine.create(choices, "SURPRISE ME", set(recent[-150:]))
            self.assertNotIn(fortune.fingerprint, set(recent[-150:]))
            recent.append(fortune.fingerprint)
            all_fingerprints.add(fortune.fingerprint)
        self.assertGreater(len(all_fingerprints), 300)

    def test_all_choice_combinations_generate(self):
        engine = FortuneEngine(random.Random(7))
        for desire in ("LOVE", "FORTUNE", "ADVENTURE", "MISCHIEF"):
            for nature in ("BOLD", "CAUTIOUS", "CURIOUS", "CHAOTIC"):
                for omen in ("MOON", "KEY", "FLAME", "RAVEN"):
                    choices = {"desire": desire, "nature": nature, "omen": omen, "honesty": "FRANK"}
                    fortune = engine.create(choices, "CHANGE")
                    self.assertTrue(fortune.prediction)
                    self.assertTrue(fortune.instruction)


if __name__ == "__main__":
    unittest.main()
