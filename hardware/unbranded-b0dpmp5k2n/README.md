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

Observed patterns in static graphics group 2:

| CH5 | Observed shape |
|---:|---|
| 0 | Big circle |
| 16 | Two small circles |
| 32 | Four circles in a diagonal line |
| 48 | Four circles in a square |
| 64 | Dashed big circle |
| 80 | Quarter-circle arc |
| 96 | Spiral |
| 112 | Three spirals |
| 128 | Horizontal squiggle |
| 144 | Vertical squiggle |
| 160 | Pinwheel |
| 176 | Small circles in a square layout |
| 192 | Half spiral (tentative) |
| 208 | Spiral cone |
| 224 | Flower |
| 240 | Alignment/test pattern |

The pinwheel, spiral cone, and flower are initial circus-scene candidates.

Observed patterns in static graphics group 3:

| CH5 | Observed shape |
|---:|---|
| 0 | Solid diagonal, upper left to lower right |
| 16 | Solid diagonal, lower left to upper right |
| 32 | Two-dash diagonal |
| 48 | Three-dash diagonal |
| 64 | Six-dash diagonal |
| 80 | Eight-dash diagonal |
| 96 | Ten-dash diagonal |
| 112 | Twelve-segment near-solid diagonal with bright dots |
| 128 | Six-dash diagonal |
| 144 | Diamond |
| 160 | Six-sided polygon |
| 176 | Eight-sided polygon |
| 192 | Rounded eight-segment shape |
| 208 | Circle made from four dashes |
| 224 | Half-heart with bright dots on the line |
| 240 | Half-heart |

The diamond, polygons, and half-heart variants may be useful scenic elements.

Observed patterns in static graphics group 4:

| CH5 | Observed shape |
|---:|---|
| 0 | Two-dot horizontal line |
| 16 | Four-dot horizontal line |
| 32 | Six-dot horizontal line |
| 48 | Eight-dot horizontal line |
| 64 | Ten-dot horizontal line |
| 80 | Twelve-dot horizontal line |
| 96 | Four groups of three dots in a horizontal line |
| 112 | Dotted trapezoid |
| 128 | Dotted triangular chip shape |
| 144 | Dotted trapezoid |
| 160 | Two small dotted circles |
| 176 | Two dotted quarter-circles forming a flat S-like diagonal |
| 192 | Dotted semicircle |
| 208 | Dotted semicircle with roughly double the dots |
| 224 | Dense dotted full circle |
| 240 | Sparse dotted circle |

These are primarily transition, texture, and framing elements rather than
recognizable circus pictures.

Observed patterns in static graphics group 5:

| CH5 | Observed shape |
|---:|---|
| 0 | “Merry Christmas” script |
| 16 | Stocking |
| 32 | Snowflake |
| 48 | Star ornament |
| 64 | Bells |
| 80 | Star tree-topper |
| 96 | Snowflake |
| 112 | Wrapped present opening to reveal a teddy bear |
| 128 | “Winter is coming” text |
| 144 | Rough stocking graphic |
| 160 | “Random Outdoor” text followed by Chinese characters |
| 176 | Horizontal line |
| 192 | Horizontal line |
| 208 | Horizontal line |
| 224 | Horizontal line |
| 240 | Dark/no visible output |

Asymmetric group-5 graphics and text initially appeared upside down. Static
CH10 rotation and CH11/CH12 DMX flip trials did not correct them. Pressing both
`Invert-X` and `Invert-Y` on the supplied IR remote corrected the orientation,
and the correction persisted across DMX blackout and a fresh DMX session. The
fixture can therefore remain upright on its feet. Snowflakes, the ornament,
bells, tree-topper, and present/teddy animation are the useful scenic candidates.

Observed ILDA animation category 1 patterns so far:

| CH5 | Observed animation |
|---:|---|
| 0 | Swimming dolphin |
| 16 | Walking stork |
| 32 | Perched eagle |
| 48 | Fighter jets streaking top-to-bottom |
| 64 | Page-a-day calendar changing pages and moving around |
| 80 | Boeing 747 in a flat spin |
| 96 | Flying bat with animated wings |
| 112 | Salamander crawling left-to-right |
| 128 | Reindeer/moose watching a flying sparkle |
| 144 | Ghost or creepy peeping figure |
| 160 | Dolphin leaping from water with a splash |
| 176 | Bird flying through a landscape of trees and mountains |
| 192 | One, then two, then three bats with flapping wings |
| 208 | Striking cobra |
| 224 | Girl wearing a large hat and waving |
| 240 | Open-cockpit propeller airplane slowly rotating about its Z-axis |

The first four were observed before the IR orientation correction and therefore
appeared upside down at the time. Later samples verified that the correction
persisted. The waving girl, cobra, bats, stork, eagle, and vintage airplane are
initial circus/Halloween candidates.

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
