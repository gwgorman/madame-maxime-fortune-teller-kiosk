# LightELF Bluetooth integration

## Purpose

The front-of-house small laser is an independent circus arrival display. Its
initial library contains symmetrical big-top, star, and Ferris-wheel drawings,
plus optional `WELCOME` and `CIRQUE DU SOIREE` text cards. The public event name
remains **Cirque du Soirée**; the ASCII text is only a projector-font fallback.

The mirrored small fixture produces two side-by-side outputs with opposite
handedness. Symmetrical art is therefore the production default. Words are
experiments because one copy will be reversed.

## Upstream protocol reference

The planned BLE transport is based on the MIT-licensed
[`aderusha/lightelf_laser`](https://github.com/aderusha/lightelf_laser)
implementation, reviewed at commit
`d2b11238249dad0d0cb7ae225e2f26aee9b58587`. It documents and implements:

- FF00/FF01/FF02 and FFE0/FFE1 GATT profiles;
- query, notification, challenge, and unlock handling;
- static vector/SVG and text point streams;
- firmware scrolling text and native animations;
- device capability detection and paced BLE writes.

No upstream source has been copied into this repository yet. Before production,
either pin the upstream implementation as a packaged dependency or extract the
minimal transport and protocol modules while preserving its MIT notice.

## Current implementation

`lightelf_adapter.py`, `lightelf_protocol.py`, and `lightelf_transport.py`
provide:

- a named and size-bounded front-laser scene catalog;
- a simulator that never opens Bluetooth;
- an explicit arm lease capped at two seconds;
- heartbeat renewal and automatic blackout;
- rejection of output while disarmed;
- line-art SVG assets designed for the mirrored fixture.
- deterministic SVG and approved line-font packet rendering;
- a persistent BLE worker with an independent two-second maximum lease;
- automatic double-blackout, bounded reconnect attempts, and anonymous JSONL
  event diagnostics;
- a two-part live-output interlock that is disabled by default.

The kiosk does not instantiate the live transport. Merely importing or creating
it produces no Bluetooth traffic; live output requires both `enabled=True` and
`MADAME_MAXIME_LIGHTELF_LIVE=I-ACCEPT-LIVE-LASER-OUTPUT`. Keep that variable
unset until the physical compatibility and safety tests below pass.

`lightelf_dry_run.py` compiles every front-laser scene, reporting byte count,
point count, production status, and a repeatable packet digest without
importing Bleak or opening Bluetooth. The automatic front-laser playlist uses
only decorative circus art. `WELCOME` and `CIRQUE DU SOIREE` remain available
as operator experiments but are excluded from production rotation.

## Small-laser BLE discovery

Read-only discovery on the production Pi succeeded on October 22, 2026:

- advertised name: `TD5322A_V3.1.2BLE`;
- public BLE address: `3E:D9:F7:40:86:00`;
- advertised service: `0000FF00-0000-1000-8000-00805F9B34FB`;
- notification value handle `0x0011`: characteristic `FF01`, properties `0x12`;
- write/notification value handle `0x0014`: characteristic `FF02`, properties
  `0x1c`;
- manufacturer-data key `0x8984`, value `53 22 00 00`.

This exactly matches the upstream common LightELF profile. Service enumeration
completed without pairing, trusting the device, subscribing, querying,
unlocking, writing a characteristic, or changing optical output. The Pi then
disconnected successfully. Nearby `S57` advertisements were identified as
Sonos devices and are unrelated.

`lightelf_probe.py` now implements only the bounded E0/E7 identity challenge
and validates the returned token. Debian packages `python3-bleak` and
`python3-dbus-fast` were installed on the Pi for the supported BlueZ transport.
Early live query sessions received no notification reply, and later connections
timed out while the controller continued advertising. Moving the fixture
improved its observed signal from roughly -80 dBm to -70/-75 dBm and restored
reliable service discovery. An upstream-style single query still received no
reply, which led to the official-app capture below. No power, mode, drawing,
text, or playback packet was sent and no optical change was observed.

An Apple PacketLogger trace of the official iPhone app subsequently established
the firmware-specific sequence without invoking any optical control:

1. subscribe to notifications on FF01;
2. read FF01 once (the returned value is empty);
3. send the 12-byte E0/E7 query to FF02 as an acknowledged write;
4. after roughly three seconds without a reply, resend the *identical* query;
5. receive the large, fragmented query/state reply on FF01 about 100 ms later.

The raw trace is intentionally excluded from Git because an iOS Bluetooth trace
also contains identifiers for unrelated nearby devices. Only this sanitized
target-device sequence is retained in the public repository.

The corrected Pi probe succeeded on October 22, 2026. It received a 483-byte
reply on query attempt 2, validated the challenge token, and reported protocol
generation 2. The reply contains a complete concatenated state stream before
the trailing identity fields, so the early `device_number` and `ota_version`
offsets are retained as raw compatibility diagnostics rather than presented as
human-readable model or firmware numbers. Both kiosk services remained active,
and no optical output was requested or observed.

A later read-only state query reported mode 8 (hand-drawn), text point time 100,
and draw point time 0. The hand-draw engine is therefore already at its
fastest/default timing; visible rebuilds of complex multi-stroke art must be
addressed with a smaller point budget rather than a persistent speed change.

Live optical qualification established the fixture's BLE Y-axis convention and
the renderer was corrected accordingly. The big top then displayed upright.
The Ferris wheel was reduced from 87 to 32 points; during a four-second test it
performed one initial redraw at about one second and then remained stable.
`WELCOME` exposed the decisive dual-output limitation: the left projection was
upright while the right projection was rotated 180 degrees. Both apertures
receive the same complete frame, so ordinary words cannot be made upright in
both directions independently. Text is therefore excluded from the small
front-laser production playlist. Readable party signage is reserved for the
future backyard laser; a purpose-designed rotational ambigram is the only
plausible small-laser exception.

The two hand-draw transform fields at configuration offsets 7 and 8 were also
qualified at slow value 140. Both produce 3-D axis flips: the drawing narrows
to a line, reappears reversed, narrows again, and returns forward. Neither
field performs an in-plane Z-axis rotation. The firmware's stored animations
use a different engine, and DMX channel 10 remains the known true rotation
control for those built-in images. These hand-draw flips remain operator-only.

An additional official-app iPhone trace tested the drawing library's Save
action. Save sent the normal `F0 F1 F2 F3` live-drawing envelope with all 16
configuration bytes zero (including the save-tag byte), streamed the point
data to FF02, and ended with `F7`. It sent no follow-up commit or flash-storage
command. The app therefore retains saved artwork on the phone and replays it
live over BLE; it does not install that artwork into a fixture slot. The raw
trace remains excluded because it includes unrelated nearby Bluetooth
identifiers. Custom art cannot be selected later by DMX without an external
controller streaming it.

For unattended party operation, `laser_cues.py` is therefore the primary
front-laser library. It maps the physically cataloged firmware slots into
durable `circus`, `transitions`, `geometry`, `characters`, `halloween`, and
`seasonal` playlists.
`laser_library_report.py` can inspect that catalog as text or JSON without
opening DMX hardware. BLE drawings remain optional supervised overlays rather
than a startup or recovery dependency.

Review of the pinned upstream connection path confirms that there is no
separate unlock packet. A successfully validated query challenge is the unlock
gate: the client enables command transmission locally only after
`challenge_ok` is true. The Pi's successful identity probe therefore completed
the safe query/unlock qualification. The similarly named device-settings packet
is **not** an unlock command; it can alter the DMX address, orientation,
brightness, password, and other persistent settings and must not be used for
this test.

## Physical qualification gate

1. [x] Record the BLE name, address, and advertised services without enabling
   optical output.
2. [x] Read and validate the firmware response and protocol generation.
3. [x] Confirm the projector accepts the query/challenge unlock gate without
   changing optical state. No separate unlock packet exists in the pinned
   upstream implementation.
4. [x] Terminate the complete double-wide beam envelope on a matte inaccessible
   surface and test a tiny bounded symmetric drawing. On October 22, 2026,
   `lightelf_bounded_test.py` displayed its fixed centered 80-by-80-unit diamond
   for 1.5 seconds; Greg visually confirmed the expected image and blackout.
5. Test BLE disconnect, controller crash, Pi restart, and fixture power cycle.
6. Determine whether DMX blackout overrides BLE output. If not, add a separate
   physical power/interlock layer before unattended use.
7. [x] Confirm drawing storage behavior. Official-app Save uses a zero save tag
   and no device commit command: artwork is phone-local and streamed live, so
   no uploaded fixture slot exists for DMX selection.
8. Only then implement and enable the real transport behind the same adapter.

`lightelf_bounded_test.py` remains a qualification utility, not a general live
transport. It accepts no arbitrary geometry or packet input, requires the exact
`BEAM-AREA-CLEAR` acknowledgement, caps illumination at two seconds, and sends
POWER OFF twice from its cleanup path. A BlueZ D-Bus EOF during the first test's
final disconnect occurred only after both safety writes; the utility now treats
that already-disconnected condition as a clean shutdown.

The same session exposed a separate DMX-bus issue. With the small laser attached
at the end of the DMX chain and in its OFF mode, the two upstream PAR fixtures
flickered independently. Disconnecting the cable from the laser made both PARs
immediately stable; reconnecting the same cable to PAR 2 while leaving its far
end unattached remained stable. This isolates the disturbance to the laser box
in OFF mode rather than the Pi, ENTTEC adapter, PARs, or cable. A proper 120-ohm
DMX terminator on the laser's DMX OUT/THRU connector is the next test. Until that
passes, do not include the small laser on the production PAR daisy chain.

The future backyard laser will use a separate scene catalog and installation
profile. Its proposed `FORTUNE TELLER` direction sign must not be conflated with
the front laser's welcome/circus role.
