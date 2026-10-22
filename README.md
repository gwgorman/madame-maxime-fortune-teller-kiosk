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

The field-verified direct-FTDI implementation is included as
[`dmx_lighting.py`](dmx_lighting.py). A dedicated
[`dmx_broker.py`](dmx_broker.py) service is the sole owner of the adapter and
merges both PAR fixtures with the small laser at `A057`. Laser cues require a
matching heartbeat and otherwise return to blackout automatically. The
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
- [Implementation roadmap](docs/ROADMAP.md)

## Development

The first hardware-independent reading is now available. It provides the silent
touchscreen flow, deterministic state machine, simulated approach and return
events, four-card questionnaire, optional question topic, tagged local fortune
construction, rolling repetition avoidance, sequel reading, timeouts, automatic
reset, anonymous atomic event journal, and optional failure-isolated DMX scenes.
It deliberately does not initialize an audio mixer or play sound.

Install Pygame and launch it in a development window:

```bash
sudo apt install python3-pygame
python3 madame_maxime.py --windowed
```

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
audio mixer and contains no speech or sound playback path.

The `OPERATOR` control opens a protected confirmation panel. `RETURN TO OFFICE
CONSOLE` blackouts and releases the PAR fixtures, closes Madame Maxime, selects
the Office venue with the Network status landing page, and starts the existing
service-managed Gorman Office/Transporter console. `CANCEL` returns to the
current fortune-teller session without changing either application.

## License

MIT. See [LICENSE](LICENSE).
