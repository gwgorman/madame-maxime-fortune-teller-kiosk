# Roadmap

## Phase 1: safe skeleton

- Full-screen 1920x1080 shell with simulated hardware
- Explicit session state machine and timeouts
- Large start/listen/cancel controls
- Anonymous atomic event journal
- Watchdog and clean restart behavior
- Deliberate route to the legacy Transporter and back

## Phase 2: hardware adapters

- Import the verified direct-FTDI lighting driver
- Discover and characterize the VL53L1X sensor
- Discover camera modes and low-light performance
- Discover reSpeaker channel layout and echo-cancellation behavior
- Confirm final audio device and mixer persistence

## Phase 3: conversation and performance

- Cached approach and greeting audio
- Streaming speech recognition and reply audio
- Touch/typed fallback for noisy conditions
- Barge-in and foreground-audio priority
- Bounded fortune format and repetition avoidance
- Optional, visible camera-based costume observation

## Phase 4: theatrical integration

- Idle amber/burgundy lighting
- Approach rise
- Violet/deep-blue reading scene
- Brief gold reveal
- Farewell fade and automatic reset
- Vintage French-circus graphics and practical accessibility checks

## Phase 5: production qualification

- Long-duration soak test
- Power-loss and reboot recovery
- Network-loss and service-failure tests
- Repeated rapid guest turnover
- Outdoor gazebo audio and sensor tests
- Operator controls, shutdown, and rollback runbook
- Only then change the Pi's boot target
