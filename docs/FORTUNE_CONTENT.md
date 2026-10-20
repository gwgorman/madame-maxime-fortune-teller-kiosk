# Fortune Content, Return Visits, and API Max

## Capacity target

Plan for 150 people, 250-350 total readings, and several guests returning two or
more times. No guest should receive the same complete fortune twice, and exact
fortunes should not repeat anywhere within the most recent 150 readings.

The local engine uses reviewed modular content rather than a flat list:

| Component | Initial target | Purpose |
|---|---:|---|
| Arrival lines | 24 | Acknowledge a new or returning guest |
| Trait observations | 32 | Reflect nature and answer style |
| Omen bridges | 24 | Connect Moon, Key, Flame, or Raven |
| Prediction cores | 60 | Supply the main future event |
| Warnings | 36 | Add tension or comedy |
| Instructions | 48 | End with a memorable action |
| Return-visit callbacks | 30 | Reopen a previous reading |
| Outcome reactions | 36 | Respond to Yes, Not Yet, or It Got Worse |
| Rare readings | 18 | Jackpot, refusal, uncanny, and absurd outcomes |

Tags and incompatibility rules matter more than the theoretical combination
count. The content editor must reject tone clashes, repeated imagery, duplicated
punch lines, and combinations that accidentally become cruel.

## Voice rules

Madame Maxime is warm, clever, theatrical, observant, and occasionally wicked.
She speaks with confidence but does not claim supernatural certainty. Her jokes
target indecision, theatrical fate, party behavior, and harmless human vanity.

- `GENTLE`: reassuring, affectionate, lightly mysterious.
- `FRANK`: direct, witty, and specific without humiliation.
- `MERCILESS`: sharper and knowingly dramatic, but never attacks appearance,
  disability, identity, grief, trauma, health, fertility, finances, or addiction.
- Maximum normal reading: 85 spoken words.
- Maximum return callback before the new reading: 35 spoken words.
- Use concrete images and actions; avoid generic horoscope filler.
- Never promise death, illness, pregnancy, wealth, legal outcomes, or disaster.

## Phrase families

### New arrivals

- "Ah. The room changed when you stepped closer. That is usually expensive."
- "Come in. The crystal has been pretending not to watch you."
- "There you are. Fate has been tapping its foot."
- "Stand where I can see you. Mystery is no excuse for poor lighting."
- "Welcome, darling. Choose carefully; destiny remembers bad decisions."
- "You have brought a question. You have also brought complications. Excellent."

### Trait observations

**Bold**

- "You mistake momentum for permission, and it has worked alarmingly often."
- "You do not wait for doors to open. You become a structural concern."

**Cautious**

- "You inspect every bridge twice, then cross the interesting one anyway."
- "Your hesitation is not fear. It is reconnaissance with excellent manners."

**Curious**

- "You pull at loose threads and act surprised when reality comes apart."
- "You ask one question more than sensible people. Keep doing that."

**Chaotic**

- "You call it spontaneity. Several witnesses call it an incident."
- "Plans become suggestions when you enter the room."

### Omen bridges

**Moon**

- "The Moon favors what is half-hidden and badly timed."
- "The Moon shows me a truth that improves after midnight."

**Key**

- "The Key does not promise a door. It promises that something has been locked."
- "A small permission will open a much larger problem."

**Flame**

- "The Flame says act before courage cools into a committee meeting."
- "Something bright is approaching. Try not to set it on fire immediately."

**Raven**

- "The Raven has news and absolutely no respect for privacy."
- "A message will arrive wearing an inconvenient disguise."

### Prediction cores

- "An invitation you nearly decline will place you beside exactly the right
  stranger."
- "Before the season changes, a misplaced object will expose a useful secret."
- "Someone who usually interrupts will finally say the one thing you needed."
- "A delayed plan will return with better timing and worse shoes."
- "You will be offered responsibility disguised as a compliment."
- "A familiar place will produce an unfamiliar opportunity after dark."
- "Within three gatherings, an old joke will become unexpectedly practical."
- "A decision made quickly will succeed for reasons you invent afterward."
- "You will discover that the obstacle has been waiting for an introduction."
- "A person you underestimate will remember a detail everyone else ignored."

### Warnings

- "Do not accept advice from anyone holding two identical drinks."
- "Beware of flattering emails sent before breakfast."
- "When someone says this will only take a minute, begin timing them."
- "Avoid decorative ladders and sincere people named after cities."
- "The third explanation is the true one; unfortunately, you will hear four."
- "If the plan requires matching hats, ask one more question."
- "A bargain with free shipping is still a bargain with consequences."
- "Do not confuse a group chat with a governing body."

### Mysterious instructions

- "Before midnight, move one chair and reveal nothing."
- "Carry a key that opens nothing until someone asks about it."
- "Give the next sincere compliment before you have time to improve it."
- "Order the thing you never order, then trade it with someone interesting."
- "When the music changes, turn left and speak to the quietest person there."
- "Put something red in an unexpected place and call it strategy."
- "Tomorrow, answer one harmless question with complete honesty."
- "Leave one excellent idea unfinished so it follows you home."

## Return recognition

Return recognition is optional and limited to the current event. At the end of
a first reading, the guest may choose:

```text
REMEMBER ME TONIGHT
Maxime will keep a private mathematical face signature and this fortune until
4:00 AM. No photograph, video, or voice recording is saved.

[REMEMBER ME]   [NO, THANK YOU]
```

`REMEMBER ME` is an affirmative action, not a preselected default. The local
record contains only a random visitor identifier, encrypted face embedding,
prior questionnaire choices, fortune text/fingerprint, visit count, and
timestamps. It never leaves the Pi and is automatically destroyed at the event
cutoff or by an operator purge. A non-biometric alternative may issue a
four-symbol return sigil that the guest can enter on the touchscreen.

On a possible match, confidence must exceed the calibrated threshold. An
uncertain match produces no recognition claim. A mistaken confident greeting
can be dismissed with `NOT ME`, which deletes no other person's record and
continues as a new visitor.

### First return

- "Back so soon? Either destiny moved quickly or you ignored me efficiently."
- "I remember you. The Raven was quite pleased with itself afterward."
- "Again? Very well. Tell me—did the invitation appear, or are we still blaming
  free will?"
- "You returned. Good. I dislike unresolved prophecies almost as much as vague
  apologies."
- "The crystal remembers your Key. I remember your expression when I mentioned
  the matching hats."

The screen shows a compact callback to the previous fortune and asks:

```text
HAS IT COME TRUE?
[YES]   [NOT YET]   [IT GOT WORSE]
```

### Outcome reactions

**Yes**

- "Of course it did. Please try to look surprised; I have standards."
- "Excellent. Prophecy fulfilled, paperwork avoided."
- "Then the future is behaving. That is never reassuring for long."
- "You see? Fate listens when properly supervised."

**Not yet**

- "Not yet is the future's favorite loophole."
- "Patience. Destiny is dramatic and therefore chronically late."
- "Then we shall adjust the forecast, not the confidence."
- "Interesting. The omen remains correct; reality appears understaffed."

**It got worse**

- "Marvelous. Consequences have developed ambition."
- "I offered a warning, not immunity. Let us inspect the wreckage."
- "Worse is still movement. Admittedly, in a discouraging direction."
- "Then this is no longer a sequel. It is a franchise."

### Third and later visits

- "At this point you are not consulting fate. You are micromanaging it."
- "Third reading. The crystal has opened a tab for you."
- "You again. I have upgraded your destiny to an ongoing investigation."
- "The veil recognizes you. The veil also recommends hydration."
- "Another consultation? Very well, but fate is billing by the subplot."

Later readings should reference only one earlier detail, then move forward. They
must not repeat the whole prior performance or reveal one guest's history while
another person is standing in the recognition zone.

## API Max role

API Max may tighten wording, connect a transient spoken topic to the selected
symbols, or write a return-visit sequel. API Max never controls session state,
recognition, lighting, recording, deletion, or whether a reading completes.

The local engine prepares a complete fallback before the request begins. The API
receives structured text only—never an image, face embedding, raw audio, name,
or stable identity—and has a strict deadline. Output is schema-validated,
content-filtered, length-limited, and discarded on any failure.

The production system prompt is maintained in
[`prompts/api_max_system.txt`](../prompts/api_max_system.txt).

