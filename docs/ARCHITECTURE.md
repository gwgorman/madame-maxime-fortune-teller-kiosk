# Architecture

## Goals

Madame Maxime is a reliable unattended kiosk first and an elaborate theatrical
AI character second. Hardware and network integrations are replaceable
adapters around a deterministic session controller and responsive touchscreen
loop.

## Proposed components

```text
Approach sensor ─┐
Touchscreen ─────┼──> Session controller ──> UI renderer
Microphone ──────┤           │
Camera ──────────┘           ├──> Speech/personality adapter
                             ├──> DMX lighting adapter
                             ├──> Audio output adapter
                             └──> Anonymous event journal
```

### Main UI process

Owns drawing, touch input, visible state, timers, and the final decision to
play audio or change lighting. It never waits synchronously for a camera,
network, model, or telemetry response.

### Session controller

Uses explicit bounded states such as idle, approach, greeting, listening,
thinking, speaking, reveal, farewell, and reset. Every state has a timeout and
a safe transition back to idle.

### Hardware adapters

Distance, camera, microphone, audio, and DMX each expose a small interface with
real and simulated implementations. Adapter errors become status events; they
do not terminate the UI.

The ENTTEC interface has exactly one owning process: `dmx_broker.py`. PAR scenes
and laser cues are merged into its 96-channel universe over a private local
Unix datagram socket. Laser cues are blackout unless explicitly armed, use
complete 16-channel frames, and require a matching heartbeat at least once per
second. A missing client heartbeat, Office-console handoff, or kiosk exit
forces laser blackout without disturbing the PAR scene.

The broker runs as a user service, begins with an all-zero universe, uses an
exclusive process lock, and restarts after a fault in 250 ms. A software crash
cannot guarantee instantaneous darkness because some DMX receivers may hold
their last frame until transmission resumes; a physical interlock remains the
required hard safety boundary for a laser installation.

### Personality service

Keeps Madame Maxime's prompts, state, and voice assets separate from the
preserved MAX.sys personality. It returns bounded messages to the UI, which
retains control of playback and interruption.

Speech capture and synthesis remain separate adapters rather than a hosted
agent owning the conversation. See [Speech Recognition and Voice Pipeline](AUDIO_PIPELINE.md).

### Fortune service

Builds a complete local fortune from questionnaire choices, optional transient
speech-derived topic data, reviewed fragment tags, and a session seed. A local
result exists before optional online enrichment begins. Enrichment is bounded,
schema-validated, and never lies on the only path to a reveal.

### Perception service

Owns distance, camera, and microphone workers outside the rendering loop. It
publishes expiring observations rather than exposing devices directly to the
session controller. Camera frames, raw audio, and transcripts are transient by
default; the controller receives only the minimal event or structured result it
needs.

### Event journal

Persists anonymous operational data atomically: session counts, timing,
selected prompt categories, fortune fingerprints, reset/fault events, and
coarse performance. It excludes images, raw audio, and transcripts by default.

## Relationship to the transporter console

The transporter project remains independently launchable and stable. Reusable
components should be extracted deliberately rather than importing the entire
legacy application. The fortune-teller selector may launch or navigate to the
legacy experience, but Transporter never participates in automatic party-page
rotation.

The canonical interaction, latency budget, privacy boundary, and recovery
behavior are specified in [Guest Experience and Fortune Design](EXPERIENCE_DESIGN.md).
