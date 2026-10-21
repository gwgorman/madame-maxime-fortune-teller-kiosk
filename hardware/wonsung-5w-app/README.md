# Wonsung 5W-APP laser

This folder is the future integration record for Greg's Wonsung 5W-APP laser.
No live laser output has been tested or added to the kiosk.

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

## Safe future bring-up

1. Record the exact rear-panel label, firmware, configured DMX address, and
   selected 16/36-channel mode.
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
