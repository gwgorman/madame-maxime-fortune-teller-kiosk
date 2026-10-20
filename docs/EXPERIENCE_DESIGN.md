# Guest Experience and Fortune Design

## Purpose

Madame Maxime should feel like a short personal performance, not a form with a
fortune printed afterward. The experience must remain understandable in a loud,
dark party environment and recover without an operator when a guest walks away.

The target is a 45-70 second individual reading. A guest should reach the reveal
within 35 seconds of starting, with no required typing and no more than one
request to repeat spoken input.

## Interaction contract

- Speech makes the performance personal; touch makes it dependable.
- Every spoken question has a large visual answer set and a visible listening
  state.
- Touch is always authoritative when speech and touch disagree.
- The guest may skip the open spoken question and still receive a complete
  fortune.
- No hardware, model, or network failure may strand a guest in a waiting state.
- Cancel is visible throughout the active reading and returns safely to idle.
- All text must be readable at arm's length and all touch targets must tolerate
  imprecise party use.

## Canonical reading

### 1. Quiet watch

The distance sensor watches for a person entering the configured approach
zone. Camera-based person detection may confirm presence, but is not required
to wake the kiosk. Incidental movement must not begin a reading.

### 2. Invitation

Madame Maxime wakes, looks toward the guest, and offers a cached greeting. The
screen presents one large `BEGIN YOUR READING` control. This state times out to
quiet watch if nobody responds.

### 3. Four-card questionnaire

One question appears at a time. Each response is represented by a large,
illustrated card. The microphone may select a card when confidence is high;
the chosen card illuminates briefly so the guest can correct it by touch.

1. **What draws you here?**
   - Love
   - Fortune
   - Adventure
   - Mischief
2. **Choose your nature.**
   - Bold
   - Cautious
   - Curious
   - Chaotic
3. **Choose an omen.**
   - Moon
   - Key
   - Flame
   - Raven
4. **How honest should Madame Maxime be?**
   - Gentle
   - Frank
   - Merciless

The target completion time is 15-25 seconds. Choices are intentionally playful
archetypes rather than sensitive personal questions.

### 4. The guest's question

Madame Maxime asks what question the guest has brought. Listening is visibly
bounded to about ten seconds. The guest may finish early, retry once, or choose
`READ WITHOUT A QUESTION`.

Raw audio is held only long enough to transcribe it. The first production
version extracts a topic and keywords rather than treating a transcript as a
command. A transcript is not required for a successful reading.

### 5. Consultation

The crystal ball and DMX scene begin immediately. This is useful theatre and a
latency mask, not a spinner. The local fortune is prepared first; optional
online enrichment receives a strict deadline and may only replace the local
result when it returns valid output on time.

### 6. Reveal

The completed fortune contains four bounded parts:

1. a short opening tied to the guest's choices;
2. a prediction;
3. a cheeky observation; and
4. a mysterious or ridiculous instruction.

The complete text appears on screen before or with speech. A gold lighting swell
marks the reveal. The guest may replay the spoken fortune once when audio is
enabled, but cannot remain in an unbounded loop.

### 7. Farewell and reset

The screen offers a brief farewell, records anonymous operational statistics,
fades the fixtures to the idle scene, and resets automatically. An abandoned
session follows the same cleanup path.

## Timing budget

| Stage | Target | Hard fallback |
|---|---:|---|
| Wake response | under 0.5 s | Show invitation without camera confirmation |
| Closed-answer speech recognition | 0.3-1.5 s | Guest touches a card |
| Open-question capture | up to 10 s | Skip question |
| Local transcription after speech | 1-3 s, to be measured | Use selected topic only |
| Local fortune construction | under 0.1 s | Preselected complete fortune |
| Optional online enrichment | 2-5 s budget | Keep local fortune |
| Consultation theatre | 4-7 s | Reveal immediately if interrupted |

No guest-facing wait may depend solely on a network request.

## Fortune engine

The first production engine is local and deterministic from a session seed. It
assembles reviewed fragments rather than asking a language model to invent the
entire response:

```text
opening + trait insight + omen bridge + prediction + warning + instruction
```

Fragments carry tags for topic, nature, omen, honesty, tone, group suitability,
and incompatibilities. The engine rejects recently used fortune fingerprints
and awkward combinations. Rare authored outcomes may include a jackpot reading,
an absurdly specific reading, or a theatrical refusal.

Online language generation is an optional enhancer behind a schema and strict
length/content validation. It never receives an image, raw audio, guest name,
or prior guest transcript by default. Its failure is invisible to the guest.

## Camera behavior

Permitted initial uses are deliberately narrow:

- confirm that a person or group is present;
- estimate coarse position so the portrait can appear attentive;
- distinguish an individual from a shared reading;
- derive a low-risk visible observation such as dominant costume color; and
- improve framing and operator diagnostics.

No face recognition, identity matching, demographic inference, emotion
diagnosis, or retained guest imagery is part of the design. Costume observations
must be optional, visible, and phrased so a mistaken observation is playful
rather than insulting.

## Microphone behavior

The reSpeaker array is the primary capture device. Its beamforming, noise
suppression, echo cancellation, USB topology, and AUX playback path must be
verified on the Pi before choosing speech models or confidence thresholds.

The application displays `LISTENING`, `HEARD`, and `PLEASE TAP YOUR ANSWER`
states. It permits one automatic clarification. Persistent uncertainty falls
back to touch without apology loops.

## Privacy and retained data

The idle and invitation screens disclose that camera and microphone processing
occurs during a reading. By default:

- no image or video is saved;
- no raw audio is saved;
- no transcript is retained after the session;
- no face template or identity profile is created unless the guest explicitly
  chooses the separately disclosed `REMEMBER ME TONIGHT` feature; and
- the event journal stores only anonymous choices, timings, outcome fingerprint,
  fallback use, and coarse fault/performance counters.

An operator-only diagnostic mode may save a deliberately initiated test sample,
but it must be visibly marked and disabled in party mode.

Optional return recognition is local, same-event, affirmatively enabled, and
automatically purged at the event cutoff. It stores no photograph, video, raw
audio, or name. A four-symbol return sigil provides a non-biometric alternative.
See [Fortune Content, Return Visits, and API Max](FORTUNE_CONTENT.md).

## Failure and interruption rules

| Failure | Guest-visible recovery |
|---|---|
| Distance sensor unavailable | Camera or large start button wakes Maxime |
| Camera unavailable | Continue without visual observations |
| Microphone unavailable or noisy | Questionnaire becomes touch-only |
| Transcription timeout | Offer retry once, then continue without question |
| Online service unavailable | Reveal the already-prepared local fortune |
| DMX unavailable | Continue with on-screen effects |
| Speaker unavailable | Display the complete reading as text |
| Guest walks away | Cancel work, stop foreground output, reset to quiet watch |
| Application fault | Supervisor restarts the kiosk into a known idle state |

## Decisions awaiting physical hardware

- Exact special-order camera identity, supported modes, and final field of view
- Whether camera confirmation improves approach detection enough to justify its
  idle CPU cost
- reSpeaker capture channels, DSP behavior, acoustic echo cancellation, and AUX
  routing on this Pi
- Best local speech model and measured post-utterance latency
- Reliable VL53L1X thresholds and debounce timing in the finished enclosure
- Ring-light brightness and color temperature that avoid touchscreen and eyewear
  reflections
- Whether costume-color observations remain accurate under each DMX scene

