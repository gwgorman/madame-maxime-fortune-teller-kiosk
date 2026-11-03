# Wonsung 5W-APP laser

## Installation status

The fixture is installed at **A073** in **36-channel mode**, occupying DMX
channels 73-108. On 2026-10-26 the Raspberry Pi/ENTTEC controller successfully
produced a bright white horizontal line using a centered, static cue. The rear
emission indicator responded and the optical result was visually confirmed.

The broker controls this fixture independently from the PARs and small laser.
It requires an explicit arm plus a continuing heartbeat and automatically
blacks out after heartbeat expiry. Both documented strobe channels remain
locked to zero in the diagnostic cue.

## Preserved source

The unchanged four-page scan is stored at
[`docs/manuals/Wonsung-5W-APP-DMX-channel-tables-scan.pdf`](../../docs/manuals/Wonsung-5W-APP-DMX-channel-tables-scan.pdf).

SHA-256:
`c9ac340eec89925de62f794b0a92b032fca7b8c9e1d3c015b44b8dc393677270`

The scan covers printed manual pages 13-20. It identifies the fixture as having:

- 16-channel single-pattern mode
- 36-channel dual-pattern mode
- RGB master dimmer and automatic/sound-active trigger
- Geometric, ILD, animated, abstract-line, circle, and dot-line groups
- Pattern/effect selection, color, scan speed, size, position, rotations,
  movement, zoom, drawing, and wave controls
- Dedicated strobe controls only in 36-channel mode (CH11 and CH28)

[`dmx-profile.json`](dmx-profile.json) transcribes the tables into a reusable
machine-readable profile. Manufacturer wording that is ambiguous or apparently
duplicated is retained and marked for physical verification.

## Custom-pattern boundary

The documented DMX personality selects patterns already stored in the fixture
and controls their color, scan speed, size, position, rotation, movement, zoom,
drawing, and wave effects. It does **not** provide channels for streaming a new
vector drawing over DMX.

The `Downloaded ILD programs` group indicates that custom artwork uploaded to
the fixture can subsequently be selected over DMX. Uploading that artwork is a
separate LightELF/BLE operation. The BLE upload protocol and the mapping between
downloaded slots and DMX selector values still require capture and verification.

## Safe future bring-up

1. Confirm the rear panel still reads A073 and 36-channel mode before testing.
2. Mount the unit so every possible beam terminates on a non-reflective surface
   inaccessible to guests. Do not aim toward people, windows, roads, or sky.
3. Verify the key switch, interlock, emergency stop, aperture shutter, and
   behavior after DMX loss before enabling optical output.
4. Start with all slots zero. In 36-channel mode, explicitly keep CH11 and CH28
   at zero to prohibit strobe.
5. Raise only the master dimmer while a static, centered, physically contained
   test pattern is selected.
6. Capture observed behavior for every channel. Do not trust unclear manual
   wording until the physical unit agrees.
7. Add the smaller laser as a separate fixture profile; never assume it shares
   this channel map merely because the controls look similar.

## Integration design

Keep lasers behind a dedicated failure-isolated adapter, separate from the PAR
scene code. The adapter should enforce a safety envelope before emitting a DMX
frame: allowed channels only, strobe locked out by default, bounded position and
size, explicit armed state, heartbeat timeout to blackout, and immediate
blackout during kiosk exit or Office-console handoff.
