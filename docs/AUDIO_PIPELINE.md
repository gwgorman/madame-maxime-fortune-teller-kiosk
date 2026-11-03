# Speech Recognition and Voice Pipeline

## Decision

- **Capture and turn control:** local on the Raspberry Pi
- **Speech-to-text:** OpenAI `gpt-transcribe`
- **Text-to-speech:** ElevenLabs using the approved Madame Maxime voice
- **Static dialogue:** pre-rendered and cached locally
- **Dynamic fortunes:** generated through ElevenLabs' HTTP streaming endpoint
- **Offline/no-network behavior:** touch questionnaire, on-screen fortune, and
  cached dialogue where appropriate

The kiosk does not delegate the conversation loop to a hosted voice agent. The
Pi remains authoritative for listening windows, interruption, state changes,
timeouts, lighting, playback, and fallback.

## Audio path

```text
reSpeaker microphones
    -> reSpeaker DSP / beamforming / noise suppression / echo cancellation
    -> PipeWire/ALSA capture device
    -> local level gate and voice-activity detection
    -> bounded in-memory mono PCM buffer
    -> OpenAI transcription
    -> answer mapper or transient topic summary
    -> local fortune engine
    -> optional API Max text enrichment
    -> ElevenLabs streaming TTS
    -> PipeWire/ALSA playback
    -> reSpeaker 3.5 mm AUX output
    -> powered speaker
```

All reSpeaker channel, format, DSP, and routing assumptions remain provisional
until physical bring-up.

### Current Pi 5 bring-up

The Seeed reSpeaker XVF3800 is field-verified as a standard USB Audio Class
device with native stereo, signed 16-bit, 16 kHz capture. Both capture channels
contain valid signal. `speech_input.py` records that stable hardware endpoint,
downmixes once to mono in memory, applies local level gating with one-second
pre-roll, WebRTC voice classification, and bounded silence endpointing, then
submits an in-memory WAV to the
ordinary transcription endpoint. Normal operation writes neither audio nor
transcripts to disk.

The quiet-office baseline measured on November 3, 2026 was RMS 73 median and
99 maximum in 20 ms windows. After WebRTC voice classification was added, the
energy floor was set to RMS 110 so soft and off-axis one-word answers are not
lost; WebRTC remains responsible for rejecting chair and handling noise. The
floor is exposed as `MADAME_MAXIME_VAD_RMS` for gazebo calibration rather than
treated as a production assumption.

The output path is independently field-verified over Bluetooth A2DP to the
Tzumi SuperBass speaker. The reSpeaker remains the PipeWire default source.

## Listening behavior

The UI opens the microphone only during an explicit visible `LISTENING` state.
It retains a short rolling prebuffer so the first syllable is not clipped.

Provisional capture rules:

- mono PCM after the reSpeaker's processed channel;
- resample only once, at the STT boundary;
- one second of in-memory pre-roll (field-adjusted to preserve quieter opening
  words before the level gate fires);
- ignore the first 150-250 ms after Maxime stops speaking while echo
  cancellation settles;
- begin speech after a calibrated energy/VAD threshold;
- end an answer after 1.25 seconds of speech-free audio (field-adjusted after
  the shorter provisional gap clipped natural pauses between words);
- cap closed answers at four seconds;
- cap the open question at ten seconds; and
- never save the raw capture unless operator diagnostic mode was deliberately
  enabled before the test.

The final values must be measured with the actual speaker, gazebo noise, and
reSpeaker DSP rather than copied from desktop defaults.

## Closed-answer transcription

For the four questionnaire screens, record one short utterance and submit it to
`gpt-transcribe` with English selected and a small context hint containing
only the visible choices. Normalize the result and map common variants to the
four choices.

Example:

```text
Visible choices: Love, Fortune, Adventure, Mischief.
Expected input is one of those choices or a short natural phrase selecting one.
```

An answer is accepted by voice only when mapping confidence and acoustic
quality pass calibrated thresholds. The selected card illuminates and remains
correctable by touch. Low confidence immediately changes the prompt to
`PLEASE TAP YOUR ANSWER`; it does not send the guest through repeated apology
loops.

The first on-Pi end-to-end acceptance test passed on November 3, 2026: a real
touch started the questionnaire, the guest spoke `Mischief`, the correct choice
highlighted, and the state machine advanced. The next unanswered card safely
settled on `VOICE UNCLEAR — PLEASE TAP`. Capture and network transcription run
off the Pygame thread, and a touch invalidates any stale result before applying
the touched choice.

## Open-question transcription

The guest's optional question is captured for at most ten seconds and sent as a
single bounded transcription request. The local application extracts or asks
API Max to reduce it to a short, non-sensitive topic summary. Raw audio and the
full transcript are discarded after the reading.

The initial implementation should use the ordinary transcription endpoint,
not a persistent realtime conversation. A short, complete utterance is easier
to bound, retry, inspect, and abandon safely. Realtime transcription can be
tested later if measured latency warrants the extra connection complexity.

## Text-to-speech

### Pre-rendered library

Generate and approve the following before production:

- invitations and questionnaire questions;
- visible-state acknowledgements;
- clarification and touch-fallback lines;
- consent and return-recognition explanations;
- common return-visit callbacks;
- outcome reactions;
- farewell and fault-safe lines; and
- operator test clips.

Store these assets in a versioned local manifest containing phrase identifier,
exact text, voice identifier, model, voice settings, file hash, duration, and
source/provenance. Do not regenerate them at runtime.

### Dynamic readings

Once the complete fortune text is available, call ElevenLabs' HTTP streaming
TTS endpoint with the approved voice. HTTP output streaming is preferred because
the full bounded fortune is already known; a bidirectional WebSocket adds little
value in this path. Start playback after a small jitter buffer and continue as
chunks arrive.

Use ElevenLabs Flash v2.5 for the first latency benchmark. Compare it with the
best-quality model supported by the approved voice before locking production.
Voice quality wins when the difference still fits inside the 4-7 second crystal
consultation scene.

The generated audio may be retained in a temporary, content-hashed session cache
to support one replay. It is deleted at reset unless the exact fortune is part
of an opt-in same-night return record. No generated guest audio enters Git.

## Interruption and echo control

- Touching `CANCEL`, `SKIP`, or an answer stops foreground speech immediately.
- A new physical approach event never interrupts an active reading.
- Barge-in by voice remains disabled until the reSpeaker's acoustic echo
  cancellation is proven with the production speaker.
- When enabled, barge-in requires near-end speech confidence, stops TTS, clears
  queued audio, and returns control to the visible state machine.
- Background music or ambience must use a separate lower-priority playback path
  and duck beneath Maxime.

## Failure behavior

| Failure | Recovery |
|---|---|
| No microphone device | Touch-only questionnaire |
| VAD never starts | Prompt for touch after the bounded window |
| STT timeout or network loss | Map by touch; omit the open question |
| Unmappable transcript | Highlight `PLEASE TAP YOUR ANSWER` |
| TTS timeout | Display full fortune and use a cached reveal cue |
| Partial TTS stream failure | Stop cleanly; keep text visible |
| Playback device lost | Continue visually and flag operator status |
| Echo cancellation inadequate | Disable voice barge-in |

## Credentials

`OPENAI_API_KEY`, `ELEVENLABS_API_KEY`, and the approved ElevenLabs voice ID are
loaded from a root- or service-readable environment file or systemd credentials
on the Pi. The files are excluded from Git, never displayed in the operator UI,
and never written to the event journal. Repository configuration contains only
environment-variable names and safe defaults.

Provision the OpenAI project key directly on the Pi without placing it in a
shell argument, chat, log, or repository:

```bash
cd ~/madame-maxime
./scripts/configure_openai_key.sh
```

The helper uses hidden terminal input and atomically writes only
`~/.config/madame-maxime/secrets.env` with mode `0600`.

## Bring-up and acceptance tests

1. Enumerate every reSpeaker playback/capture endpoint and record its formats.
2. Identify the processed mono capture path and the AUX playback path.
3. Record calibrated test phrases with no speaker output, then with Maxime
   speaking, music playing, and several nearby conversations.
4. Measure first-syllable loss, false VAD starts, endpoint delay, transcript
   accuracy, STT turnaround, TTS time-to-first-audio, and echo return.
5. Test every closed-choice word from multiple positions and speaking volumes.
6. Test touch correction after a deliberate misrecognition.
7. Disconnect the network during listening and during TTS playback.
8. Run at least 100 automated simulated turns and a one-hour live audio soak.

Production targets:

- at least 95% correct mapping for the twelve closed-choice words in controlled
  gazebo tests;
- at least 85% correct mapping with representative party noise;
- under two seconds from end-of-utterance to a closed-choice highlight;
- under three seconds for a short open-question transcript;
- under one second to first dynamic speech after the TTS request begins;
- no audible stale audio after cancel/reset; and
- zero retained raw captures or transcripts after normal session cleanup.

