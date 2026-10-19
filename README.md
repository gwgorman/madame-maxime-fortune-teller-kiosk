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
- Two six-channel LauceNatz PAR fixtures at DMX addresses `A001` and `A030`.
- Independent red, green, blue, white, and blackout control of both fixtures.
- Direct `libftdi` output works as the ordinary kiosk user.
- OLA and the ordinary Linux serial path do not produce usable output with
  this installation and must not own the adapter.

The proven DMX implementation currently lives in
[`dmx_lighting.py`](https://github.com/gwgorman/raspberry-pi-transporter-console/blob/main/dmx_lighting.py)
at transporter-console commit
[`04b325b`](https://github.com/gwgorman/raspberry-pi-transporter-console/commit/04b325b).
It will move here when the fortune-teller runtime is ready to consume it.

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
- Arducam B0354 USB camera with Sony IMX291 sensor and 2.8-12 mm lens
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
- [Hardware bring-up and verified DMX procedure](docs/HARDWARE_BRINGUP.md)
- [Implementation roadmap](docs/ROADMAP.md)

## Development

The first hardware-independent shell is now available. It provides the silent
touchscreen flow, deterministic state machine, simulated approach event,
sample fortune reveal, timeouts, automatic reset, and anonymous atomic event
journal. It deliberately does not initialize an audio mixer or play sound.

Install Pygame and launch it in a development window:

```bash
sudo apt install python3-pygame
python3 madame_maxime.py --windowed
```

Omit `--windowed` for the full-screen kiosk presentation. Press `Esc` or `Q`
to exit. The default journal is
`~/.local/state/madame-maxime/journal.json`; override it with
`MADAME_MAXIME_JOURNAL` during tests.

## License

MIT. See [LICENSE](LICENSE).
