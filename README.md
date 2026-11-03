# Madame Maxime Fortune-Teller Kiosk

A theatrical, touch-first fortune-telling pavilion for Greg Gorman's annual
Halloween party. The experience combines a Raspberry Pi 5, a 1080p
touchscreen, conversational audio, an approach sensor, a camera, and separately
controlled DMX lighting in a vintage French-circus presentation.

Designed and built by Greg Gorman with Max (OpenAI Codex).

## Project status

Hardware bring-up has begun. The production Raspberry Pi still launches the
known-good [Raspberry Pi Transporter Console](https://github.com/gwgorman/raspberry-pi-transporter-console),
which remains available as a legacy attraction and Office telemetry display.
Madame Maxime will not become the boot target until its simulated-hardware path,
explicit legacy-console access, audio routing, and watchdog recovery have all
passed on-Pi testing.

Verified on October 19, 2026:

- ENTTEC Open DMX USB interface identified as FTDI `0403:6001`, serial
  `BG00UVK9`.
- Two six-channel LauceNatz PAR fixtures at DMX addresses `A001` and `A007`.
- Independent red, green, blue, white, and blackout control of both fixtures.
- Direct `libftdi` output works as the ordinary kiosk user.
- OLA and the ordinary Linux serial path do not produce usable output with
  this installation and must not own the adapter.

Verified on November 3, 2026 after migration to Raspberry Pi 5:

- Seeed reSpeaker XVF3800 capture is stable at stereo signed 16-bit/16 kHz;
  both input channels carry valid speech.
- Tzumi SuperBass is the trusted Bluetooth A2DP output while the reSpeaker is
  the persistent PipeWire input.
- `madame-maxime-speech.service` continuously drains the reSpeaker DSP stream,
  applies WebRTC voice classification plus local level/timeout bounds, and
  exposes a private Unix-socket transcription interface.
- OpenAI `gpt-transcribe` returned the exact full test sentence and the exact
  one-word questionnaire answer `Adventure`.
- The live kiosk accepted the spoken questionnaire answer `Mischief`, visibly
  highlighted it, and advanced to the next card. If no usable answer follows,
  the screen falls back to `VOICE UNCLEAR — PLEASE TAP` without blocking touch.
- Raw audio and transcripts remain memory-only during normal operation.

The field-verified direct-FTDI implementation is included as
[`dmx_lighting.py`](dmx_lighting.py). A dedicated
[`dmx_broker.py`](dmx_broker.py) service is the sole owner of the adapter and
merges both PAR fixtures with the small laser at `A057`. Laser cues require a
matching heartbeat and otherwise return to blackout automatically. The
DMX-first built-in library contains 61 named cues organized into durable
circus, transition, geometry, character, Halloween, and seasonal playlists. Only the
physically verified starburst uses automatic rotation; the ordinary party loop
does not depend on Bluetooth, a phone, or uploaded fixture storage. The
original PAR verification record remains
at transporter-console commit
[`04b325b`](https://github.com/gwgorman/raspberry-pi-transporter-console/commit/04b325b).

Related systems:

- [MAX.sys](https://github.com/gwgorman/max-sys) will provide the reusable,
  host-bounded personality/event engine.
- [Gorman Office Console](https://github.com/gwgorman/gorman-office-console) is
  the private everyday telemetry display and is not part of party rotation.

## Intended guest experience

1. A distance sensor notices an approaching guest.
2. Madame Maxime wakes quickly and begins a cached greeting.
3. One oversized touch target starts a bounded reading.
4. The microphone array and optional camera help her respond to the guest or
   group in front of her.
5. A reading contains a prediction, a cheeky observation, and a mysterious
   instruction.
6. Lighting progresses from dim amber/burgundy through violet/deep blue to a
   brief gold reveal, then fades to idle.
7. The kiosk resets automatically for the next guest.

The interface must work in a loud party: large controls, visible
listening/speaking state, touchscreen fallback, barge-in, bounded sessions,
timeouts, and unattended recovery.

## Planned hardware

- Raspberry Pi 5
- Existing 1920x1080 capacitive touchscreen
- Two-unit special-order USB camera purchase; exact delivered model and modes
  remain to be recorded during bring-up (the earlier prototype candidate was
  the Arducam B0354)
- Seeed reSpeaker XVF3800 USB four-microphone array with case
- Pololu VL53L1X time-of-flight distance sensor carrier, product 3415
- NEEWER R12L 12-inch ring light
- ENTTEC Open DMX USB interface, product 70303
- Two LauceNatz 36LED PAR fixtures
- Existing powered AUX speaker

Exact device names and capabilities remain provisional until each device is
physically connected and tested. See [Hardware bring-up](docs/HARDWARE_BRINGUP.md).

## Design contracts

- Lighting, camera, sensor, network, or AI failure must never block the main
  touchscreen loop.
- Every hardware adapter must have a simulated/no-hardware implementation.
- Strobe and fixture program channels remain off unless deliberately enabled.
- Guest sessions are bounded and reset automatically.
- Anonymous operational statistics are persistent from the first usable test.
- Images and conversation transcripts are not retained by default.
- Secrets, private voices, tokens, and generated guest media never enter Git.
- The legacy Transporter remains reachable deliberately, but never appears in
  an automatic party rotation.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Guest experience and fortune design](docs/EXPERIENCE_DESIGN.md)
- [Fortune content, return visits, and API Max](docs/FORTUNE_CONTENT.md)
- [Speech recognition and voice pipeline](docs/AUDIO_PIPELINE.md)
- [Hardware bring-up and verified DMX procedure](docs/HARDWARE_BRINGUP.md)
- [Wonsung 5W-APP laser profile](hardware/wonsung-5w-app/README.md)
- [Unbranded ASIN B0DPMP5K2N laser profile](hardware/unbranded-b0dpmp5k2n/README.md)
- [JERRAY ASIN B0CKX7WRRR wireless DMX transport](hardware/jerray-b0ckx7wrrr/README.md)
- [LightELF Bluetooth integration and front-laser scene plan](docs/LIGHTELF_INTEGRATION.md)
- [Implementation roadmap](docs/ROADMAP.md)

## Development

The first hardware-independent reading is now available. It provides the silent
touchscreen flow, deterministic state machine, simulated approach and return
events, four-card questionnaire, optional question topic, tagged local fortune
construction, rolling repetition avoidance, sequel reading, timeouts, automatic
reset, anonymous atomic event journal, optional failure-isolated DMX scenes,
and asynchronous voice selection for the closed-answer screens. Touch always
overrides an in-flight or recognized voice choice. It deliberately does not
initialize an audio mixer or play sound.

Install Pygame and launch it in a development window:

```bash
sudo apt install python3-pygame
python3 madame_maxime.py --windowed
```

The optional LightELF identity probe requires Debian's maintained BLE client:

```bash
sudo apt install python3-bleak
```

The probe is identity-only and does not contain power or drawing commands.

The front-laser playlist can be compiled and inspected without opening
Bluetooth or producing light:

```bash
python3 lightelf_dry_run.py
```

Inspect the durable built-in DMX library without opening the adapter or
producing light:

```bash
python3 laser_library_report.py
python3 laser_library_report.py --json
```

The real BLE worker is present for staged qualification but remains disabled by
default and is not connected to the kiosk UI. Enabling it requires both an
explicit constructor flag and the exact `MADAME_MAXIME_LIGHTELF_LIVE` operator
interlock documented in [the LightELF integration notes](docs/LIGHTELF_INTEGRATION.md).
Do not enable it until every remaining physical qualification item passes.

Omit `--windowed` for the full-screen kiosk presentation. Press `Esc` or `Q`
to exit. The default journal is
`~/.local/state/madame-maxime/journal.json`; override it with
`MADAME_MAXIME_JOURNAL` during tests.

On the production Pi, install and start the single-owner DMX broker before
using `--dmx`:

```bash
mkdir -p ~/.config/systemd/user
cp systemd/madame-maxime-dmx.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now madame-maxime-dmx.service
python3 madame_maxime.py --dmx
```

The touchscreen remains operational if the broker, adapter, or driver is
unavailable. Stopping the kiosk sends a full-universe blackout; the broker
itself remains available for the next kiosk launch.
The current milestone is intentionally silent: it does not initialize Pygame's
audio mixer and contains no speech or sound playback path. Speech *input* is
available through the independent worker below; pass `--no-voice` for a fully
touch-only launch.

The independent speech worker can be installed without enabling kiosk audio:

```bash
cd ~/madame-maxime
python3 -m venv .venv
.venv/bin/pip install -r requirements-speech.txt
cp systemd/madame-maxime-speech.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now madame-maxime-speech.service
python3 speech_client.py --status
```

The service unit expects that project-local environment at
`~/madame-maxime/.venv`. Provision the API key with
`scripts/configure_openai_key.sh`; it is never stored in this repository.
During each questionnaire card the UI starts one bounded capture, shows
`LISTENING` and `INTERPRETING`, briefly highlights an unambiguous recognized
choice, then advances. Ambiguous, failed, or absent speech produces a visible
touch fallback; it never traps the guest in a retry loop.
Every accepted voice or touch answer also gets a two-second, full-screen
confirmation before the next distinctly colored, prominently numbered card.
This deliberately favors clarity for a loud, distracted party crowd over fast
expert operation.

The `OPERATOR` control opens a protected confirmation panel. `RETURN TO OFFICE
CONSOLE` blackouts and releases the PAR fixtures, closes Madame Maxime, selects
the Office venue with the Network status landing page, and starts the existing
service-managed Gorman Office/Transporter console. `CANCEL` returns to the
current fortune-teller session without changing either application.

## License

MIT. See [LICENSE](LICENSE).
