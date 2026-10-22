# Roadmap

## Phase 1: safe skeleton

- Full-screen 1920x1080 shell with simulated hardware
- Explicit session state machine and timeouts
- Large start/listen/cancel controls
- Anonymous atomic event journal
- Watchdog and clean restart behavior
- [x] Protected operator handoff to the legacy Office/Transporter console
- Portrait-led silent simulator and full state-machine rehearsal

## Phase 1A: hardware-independent reading

- [x] Four-card questionnaire with touch-only operation
- [x] Local tagged-fragment fortune engine
- [x] Fortune fingerprint and recent-repetition avoidance
- [x] Consultation and reveal animation with optional real lighting cues
- [x] Explicit cancel, abandoned-session, and timeout paths
- [x] Anonymous timing and fallback counters from the first test
- [x] Initial authored phrase corpus and 350-reading simulation
- [x] Return-visit flow using a simulated returning visitor and prior outcome
- [ ] Expand and editorially review the production phrase corpus
- [ ] Add opt-in visitor signatures after camera bring-up

## Phase 2: hardware adapters

- [x] Import the verified direct-FTDI lighting driver
- Discover and characterize the VL53L1X sensor
- Discover camera modes and low-light performance
- Discover reSpeaker channel layout and echo-cancellation behavior
- Confirm final audio device and mixer persistence
- Benchmark local voice activity detection and an optional offline transcription
  fallback with recorded synthetic/noisy test input
- Benchmark OpenAI transcription and ElevenLabs streaming TTS end to end
- Pre-render and approve all predictable dialogue into a versioned manifest

## Phase 3: conversation and performance

- Cached approach and greeting audio
- Streaming speech recognition and reply audio
- Touch fallback for noisy conditions; no guest typing required
- Barge-in and foreground-audio priority
- Bounded fortune format and repetition avoidance
- Optional, visible camera-based costume observation
- Opt-in same-event return recognition, explicit purge, and return-sigil fallback

## Phase 4: theatrical integration

- Idle amber/burgundy lighting
- Approach rise
- Violet/deep-blue reading scene
- Brief gold reveal
- Farewell fade and automatic reset
- Vintage French-circus graphics and practical accessibility checks
- [x] Physically catalog the small laser's static and ILDA graphics libraries
- [x] Define named, unarmed-by-default, safety-bounded small-laser cues
- [x] Add the single-owner DMX broker and heartbeat-enforced laser arming
- [x] Deploy and qualify the broker on the Pi with controlled fixture tests
- [x] Add a simulated, safety-leased LightELF adapter and front circus catalog
- [x] Discover and verify the small laser's LightELF BLE profile read-only
- [ ] Query/unlock and physically qualify the LightELF protocol without output
- [ ] Add the real BLE transport only after disconnect and blackout testing
- [ ] Integrate reviewed laser cues with fortune-teller states

## Phase 5: production qualification

- Long-duration soak test
- Power-loss and reboot recovery
- Network-loss and service-failure tests
- Repeated rapid guest turnover
- Outdoor gazebo audio and sensor tests
- Operator controls, shutdown, and rollback runbook
- Only then change the Pi's boot target
