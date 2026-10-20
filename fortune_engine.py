"""Local, bounded fortune construction for Madame Maxime."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass


QUESTIONS = (
    ("desire", "WHAT DRAWS YOU HERE?", ("LOVE", "FORTUNE", "ADVENTURE", "MISCHIEF")),
    ("nature", "CHOOSE YOUR NATURE", ("BOLD", "CAUTIOUS", "CURIOUS", "CHAOTIC")),
    ("omen", "CHOOSE AN OMEN", ("MOON", "KEY", "FLAME", "RAVEN")),
    ("honesty", "HOW HONEST SHOULD I BE?", ("GENTLE", "FRANK", "MERCILESS")),
)

TOPICS = ("LOVE", "WORK", "CHANGE", "A SECRET", "SURPRISE ME")

OPENINGS = {
    "LOVE": ("The heart has noticed what your good sense keeps editing.", "Affection approaches wearing an inconvenient disguise.", "The crystal finds your romantic judgment entertaining, but not hopeless."),
    "FORTUNE": ("Opportunity is circling, waiting for you to stop checking the door.", "Your luck is awake, overdressed, and asking for better instructions.", "The future shows profit, though perhaps not in the currency you expected."),
    "ADVENTURE": ("The road ahead has removed its warning label.", "A small departure will become a much better story than planned.", "Your horizon is moving closer, which is rarely an innocent development."),
    "MISCHIEF": ("At last, someone with the correct respect for consequences.", "Trouble recognizes one of its more promising apprentices.", "The crystal approves of your intentions and denies all responsibility."),
}

TRAITS = {
    "BOLD": ("You mistake momentum for permission, and it has worked alarmingly often.", "You do not wait for doors to open; you become a structural concern.", "Courage arrives before your plan and somehow gets away with it."),
    "CAUTIOUS": ("Your hesitation is reconnaissance with excellent manners.", "You inspect every bridge twice, then cross the interesting one anyway.", "You prepare for six outcomes and remain annoyed when a seventh appears."),
    "CURIOUS": ("You ask one question more than sensible people, which is why you learn things.", "You pull at loose threads and act surprised when reality comes apart.", "A locked drawer is merely a question with furniture around it."),
    "CHAOTIC": ("Plans become suggestions when you enter the room.", "You call it spontaneity; several witnesses call it an incident.", "Your instincts are excellent and your timing requires supervision."),
}

OMENS = {
    "MOON": ("The Moon favors what is half-hidden and badly timed.", "The Moon shows a truth that improves after midnight.", "Under the Moon, the overlooked detail becomes the entire plot."),
    "KEY": ("The Key does not promise a door; it promises that something has been locked.", "A small permission will open a much larger problem.", "The right key arrives only after you stop forcing the decorative one."),
    "FLAME": ("The Flame says act before courage cools into a committee meeting.", "Something bright is approaching; try not to set it on fire immediately.", "The Flame rewards motion, but it does enjoy watching you improvise."),
    "RAVEN": ("The Raven has news and absolutely no respect for privacy.", "A message will arrive wearing an inconvenient disguise.", "The Raven repeats what you already know, only louder and with feathers."),
}

PREDICTIONS = {
    "LOVE": ("An invitation you nearly decline will place you beside exactly the right stranger.", "Someone familiar will become unexpectedly interesting after one honest sentence.", "A small kindness will be remembered by the person you hoped had noticed it.", "A conversation interrupted tonight will resume somewhere much quieter."),
    "WORK": ("You will be offered responsibility disguised as a compliment.", "A delayed plan will return with better timing and worse shoes.", "The person who asks the simplest question will expose the useful answer.", "A neglected skill will become unexpectedly profitable before spring."),
    "CHANGE": ("Before the season changes, a misplaced object will expose a useful secret.", "A familiar place will produce an unfamiliar opportunity after dark.", "The obstacle has been waiting for an introduction, not a battle.", "A decision made quickly will succeed for reasons you invent afterward."),
    "A SECRET": ("Someone who usually interrupts will finally say the one thing you needed.", "A person you underestimate will remember a detail everyone else ignored.", "The third explanation will be true, though you will unfortunately hear four.", "A harmless confession will rearrange the next three conversations."),
    "SURPRISE ME": ("Within three gatherings, an old joke will become unexpectedly practical.", "A door you assumed was decorative will prove surprisingly useful.", "The next minor inconvenience will introduce a major ally.", "A choice made for the better story will accidentally become the sensible one."),
}

WARNINGS = {
    "GENTLE": (
        "Keep one kindness in reserve for the person who least expects it.",
        "Move carefully when certainty begins speaking too loudly.",
        "Take the long way once; it has something quiet to show you.",
    ),
    "FRANK": (
        "Do not accept advice from anyone holding two identical drinks.",
        "When someone says this will take only a minute, begin timing them.",
        "Do not confuse a group chat with a governing body.",
        "A bargain with free shipping is still a bargain with consequences.",
    ),
    "MERCILESS": (
        "Your worst idea has excellent posture. Do not mistake that for merit.",
        "The problem is not mixed signals. You simply prefer the amusing one.",
        "Stop waiting for a sign; you ignored the previous three.",
        "If the plan requires matching hats, it was never a plan.",
    ),
}

NATURE_SIGILS = {
    "BOLD": "LION",
    "CAUTIOUS": "FOX",
    "CURIOUS": "MOTH",
    "CHAOTIC": "COMET",
}

INSTRUCTIONS = (
    "Before midnight, move one chair and reveal nothing.", "Carry a key that opens nothing until someone asks about it.",
    "Give the next sincere compliment before you have time to improve it.", "Order the thing you never order, then trade it with someone interesting.",
    "When the music changes, turn left and speak to the quietest person there.", "Put something red in an unexpected place and call it strategy.",
    "Tomorrow, answer one harmless question with complete honesty.", "Leave one excellent idea unfinished so it follows you home.",
)

OUTCOME_LINES = {
    "YES": ("Of course it did. Please try to look surprised; I have standards.", "Excellent. Prophecy fulfilled, paperwork avoided.", "Then fate is behaving. That is never reassuring for long."),
    "NOT YET": ("Not yet is the future's favorite loophole.", "Patience. Destiny is dramatic and therefore chronically late.", "The omen remains correct; reality appears understaffed."),
    "IT GOT WORSE": ("Marvelous. Consequences have developed ambition.", "I offered a warning, not immunity. Let us inspect the wreckage.", "Then this is no longer a sequel. It is a franchise."),
}


@dataclass(frozen=True)
class Fortune:
    title: str
    opening: str
    prediction: str
    observation: str
    instruction: str
    fingerprint: str
    choices: dict[str, str]
    topic: str
    visit_number: int = 1
    return_callback: str = ""

    def display_parts(self) -> tuple[str, str, str, str]:
        return self.title, self.prediction, self.observation, self.instruction


class FortuneEngine:
    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()

    def create(self, choices: dict[str, str], topic: str, recent: set[str] | None = None,
               visit_number: int = 1, previous: Fortune | None = None,
               outcome: str | None = None) -> Fortune:
        recent = recent or set()
        for _ in range(100):
            opening = self.rng.choice(OPENINGS[choices["desire"]])
            trait = self.rng.choice(TRAITS[choices["nature"]])
            omen = self.rng.choice(OMENS[choices["omen"]])
            prediction = self.rng.choice(PREDICTIONS[topic])
            warning = self.rng.choice(WARNINGS[choices["honesty"]])
            instruction = self.rng.choice(INSTRUCTIONS)
            callback = ""
            if previous and outcome:
                callback = self.rng.choice(OUTCOME_LINES[outcome])
                opening = callback
                prior = previous.prediction[0].lower() + previous.prediction[1:]
                trait = trait[0].lower() + trait[1:]
                observation = f"Previously, {prior} Now, {trait}"
            else:
                observation = f"{trait} {omen}"
            digest_source = "|".join((opening, prediction, observation, warning, instruction))
            fingerprint = hashlib.sha256(digest_source.encode()).hexdigest()[:16]
            if fingerprint not in recent:
                return Fortune(
                    title=f"THE {choices['omen']} AND THE {NATURE_SIGILS[choices['nature']]}",
                    opening=opening, prediction=prediction,
                    observation=f"{observation} {warning}", instruction=instruction,
                    fingerprint=fingerprint, choices=dict(choices), topic=topic,
                    visit_number=visit_number, return_callback=callback,
                )
        raise RuntimeError("fortune space exhausted for recent-history window")
