# Unbranded dual-direction laser - ASIN B0DPMP5K2N

This folder records Greg's unbranded 16-channel indoor RGB animation laser,
identified by Amazon ASIN `B0DPMP5K2N`. Greg has physically confirmed that its
internal mirror produces two side-by-side beams from the front face, making the
effective output envelope approximately double-wide. One side is the mirrored
inverse of the other, which is especially visible in asymmetric shapes and
movement. No live output has been tested or integrated into the kiosk.

Configured DMX address: `A057` (channels 57-72), physically set by Greg on
October 21, 2026.

On October 21, 2026, a bounded live test sent the minimum documented CH1 enable
value with dynamic functions disabled. The fixture displayed a static
horizontal line and then returned to complete darkness under DMX blackout.
This verifies address response, minimum static output, and blackout only.
Shapes, movement, scan bounds, mirror geometry, DMX-loss behavior, and the
remaining controls have not yet been physically validated.

Additional bounded testing identified CH5 value 208 as a radiation/fallout-style
symbol and CH5 value 176 as an asterisk/starburst. Continuous CH10 rotation of
the starburst looked smooth and useful. Combined rotation with CH13/14 position
changes looked twisted and unstable through the mirrored optical path; wider
position travel also clipped at the sides and distorted shapes toward the
bottom. Production cues should therefore keep X/Y position fixed and use
rotation-only motion unless a later calibration proves a clean bounded range.

Observed rotating patterns in static graphics group 1:

| CH5 | Observed shape |
|---:|---|
| 176 | Asterisk/starburst |
| 184 | Child-drawn star |
| 192 | Sun |
| 200 | Fan |
| 208 | Radiation/fallout-style symbol |
| 216 | Y |
| 224 | X |
| 232 | Four small boxes, one in each corner |
| 240 | Thin rectangular bar |
| 248 | Tiny bright square |

The star, sun, and fan are initial circus-scene candidates.

## Preserved source

The unchanged two-page scan is stored at
[`docs/manuals/Unbranded-B0DPMP5K2N-DMX-channel-tables-scan.pdf`](../../docs/manuals/Unbranded-B0DPMP5K2N-DMX-channel-tables-scan.pdf).

SHA-256:
`5ba8b7539e8cf556227452cfa4ab85eb674b0694c0533786aa110cd322f01b46`

[`dmx-profile.json`](dmx-profile.json) is the machine-readable transcription of
all 16 channels and every documented value range.

## Distinguishing characteristics

- One 16-channel DMX mode only
- Indoor RGB unit with 15 kpps galvo scanner and documented +/-25-degree scan
- Red 660 nm, green 532 nm, blue 450 nm
- CH1 is both laser enable and dimmer; 0-9 is the documented off range
- Static and ILDA groups, dynamic/random effects, segmented colors, scaling,
  rotation, flip, position, wave, and gradual-drawing controls
- No separately documented DMX strobe channel
- Internal mirror creates two simultaneous, side-by-side front outputs
- One output is mirror-inverted relative to the other; shapes have opposite
  handedness and movement appears mirrored across the pair

## Future bring-up constraints

1. Treat this as one double-wide envelope containing two side-by-side beam
   paths. Mount and terminate the entire envelope on a matte, non-reflective
   surface inaccessible to guests before enabling CH1.
2. Record the exact rear-panel label, serial markings, key-switch/interlock
   behavior, and response to DMX loss. The configured address is `A057`.
3. Start with all channels zero and verify CH1 0-9 produces no optical output.
4. Select a small, static pattern and centered positions before cautiously
   raising CH1 above 9.
5. Verify that movement, scale, rotation, flip, wave, and drawing controls cannot
   move either side of the combined double-wide output beyond its physical
   termination area.
6. Map the actual inversion axis and observe every motion mode across both
   halves. A motion that appears safe on one side may travel toward the edge on
   the mirrored side.
7. Keep sound-active and random-effect ranges disabled in production unless a
   separately bounded scene has been physically validated.
8. Use a dedicated failure-isolated laser adapter with heartbeat blackout. The
   Office-console handoff and every kiosk shutdown must force CH1 to zero before
   releasing DMX.

This fixture must remain a separate profile from the Wonsung 5W-APP. Similar
RGB/pattern concepts do not imply compatible channel numbers or ranges.
