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

`lightelf_adapter.py` provides:

- a named and size-bounded front-laser scene catalog;
- a simulator that never opens Bluetooth;
- an explicit arm lease capped at two seconds;
- heartbeat renewal and automatic blackout;
- rejection of output while disarmed;
- line-art SVG assets designed for the mirrored fixture.

It intentionally contains no live BLE transport. No output is possible through
this adapter until the physical compatibility and safety tests below pass.

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
The first live query session connected, resolved services, subscribed, and sent
the identity envelope but received no notification reply. Later connections
timed out while the controller continued advertising. Moving the fixture
improved its observed signal from roughly -80 dBm to -70/-75 dBm and restored
reliable service discovery. A subsequent probe exactly matched the upstream
notification-settle delay and unacknowledged-write mode, but still received no
reply. No power, mode, drawing, text, or playback packet was sent and no optical
change was observed. Do not repeatedly retry the controller; the next useful
step is to capture the official app's successful query exchange or establish
that this firmware uses a different handshake.

## Physical qualification gate

1. [x] Record the BLE name, address, and advertised services without enabling
   optical output.
2. [ ] Read the firmware response and protocol generation, then confirm the
   projector accepts the upstream query/unlock exchange.
3. Terminate the complete double-wide beam envelope on a matte inaccessible
   surface and test a tiny bounded symmetric drawing.
4. Test BLE disconnect, controller crash, Pi restart, and fixture power cycle.
5. Determine whether DMX blackout overrides BLE output. If not, add a separate
   physical power/interlock layer before unattended use.
6. Confirm whether drawings persist, whether more than one can be stored, and
   whether any DMX-reserved slots select uploaded content.
7. Only then implement and enable the real transport behind the same adapter.

The future backyard laser will use a separate scene catalog and installation
profile. Its proposed `FORTUNE TELLER` direction sign must not be conflated with
the front laser's welcome/circus role.
