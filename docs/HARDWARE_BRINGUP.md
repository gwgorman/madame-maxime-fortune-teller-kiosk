# Hardware Bring-Up

This document separates verified installation facts from planned hardware.
Update it only after observing the physical device.

## ENTTEC Open DMX USB

Verified October 19, 2026 on the production Raspberry Pi and a macOS test host.

### Identity

- Product: ENTTEC Open DMX USB, part 70303
- USB identity: FTDI FT232R, vendor/product `0403:6001`
- FTDI serial: `BG00UVK9`
- Normal Linux node when idle: `/dev/ttyUSB0`
- Pi packages: `libftdi1-2`, `python3-usb`
- Kiosk user belongs to `plugdev` and can claim the raw USB device without
  running the application as root

### Fixture installation

Two LauceNatz 36LED PAR fixtures use six-channel mode:

| Offset | Function | Static-scene rule |
|---:|---|---|
| 1 | Master brightness | 0-255 |
| 2 | Red | 0-255 |
| 3 | Green | 0-255 |
| 4 | Blue | 0-255 |
| 5 | Strobe | Keep at 0 |
| 6 | Program selector | Keep at 0 |

Installation addresses:

- First PAR: `A001`, channels 1-6
- Second PAR: `A007`, channels 7-12 (moved from A030 on October 21, 2026)

Both fixtures were physically observed responding independently to red, green,
blue, white, and blackout. A cable fault initially hid A001; an isolated
full-red test distinguished that fault from addressing or software trouble.
PAR 2 was reverified at A007 through red, green, blue, white, and blackout on
October 21, 2026.

### Diagnostic history

1. The Pi enumerated the interface and could write to `/dev/ttyUSB0`, but the
   fixtures did not respond.
2. OLA's Open DMX plugin claimed the device and reported Universe 1 correctly,
   but the fixtures still did not respond.
3. Reducing the FTDI latency timer from 16 ms to 1 ms did not fix OLA output.
4. QLC+ 5 on macOS detected `FT232R USB UART (S/N: BG00UVK9)` and immediately
   drove the second fixture at its then-current A030 address using channels
   30-35. This proved the adapter, 5-to-3-pin adapter,
   DMX cable, polarity, address, and fixture.
5. Direct `libftdi` control on the Pi then drove the same fixture successfully,
   first as root and then as the ordinary `ggorman` kiosk user.
6. Both connected fixtures subsequently passed independent RGBW and blackout
   tests from the Pi.
7. On October 22, 2026, the production Pi's single-owner DMX broker passed a
   live end-to-end qualification: A001 illuminated red alone, A007 illuminated
   green alone, and the A057 small laser displayed the reviewed rotating
   starburst cue. Stopping its client heartbeat returned the physical laser to
   blackout automatically while both the broker and Office console remained
   active.

### Required Linux approach

The direct driver:

1. finds USB device `0403:6001`;
2. detaches the `ftdi_sio` kernel driver through PyUSB;
3. opens the adapter by serial with `libftdi`;
4. configures 250000 baud, 8 data bits, no parity, and 2 stop bits;
5. emits the DMX break, mark-after-break, start code, and full channel frame
   continuously;
6. sends blackout before a normal stop; and
7. closes libftdi and restores the kernel driver.

OLA is disabled and stopped because it otherwise competes for the adapter:

```bash
sudo systemctl disable --now olad
```

The tested driver and manual test utility now live in this repository. On the
production Pi, `madame-maxime-dmx.service` is the sole ENTTEC owner and begins
with an all-zero universe. The previous Pi driver was preserved as:

```text
/home/ggorman/dmx_lighting.py.pre-direct-ftdi-20261019
```

Legacy manual PAR test, to be used only while the broker service is stopped:

```bash
python3 /home/ggorman/dmx_lighting.py --test
```

The test starts with blackout, exercises A001 and A007 separately, and ends in
blackout.

Normal applications communicate through `DmxClient`; they must not open the
ENTTEC device directly. The broker transmits 96 channels, covering PAR1 at
A001, PAR2 at A007, and the 16-channel small laser at A057. Laser commands are
unarmed by default and expire unless the client renews a matching heartbeat.

## Pending physical verification

- Exact manufacturer/model of the two-unit special-order camera shipment; do
  not assume the earlier Arducam B0354 candidate until the label is inspected
- Camera modes, frame rates, field of view, and low-light behavior
- Microphone-array USB identity, channel topology, beamforming, and echo
  cancellation
- VL53L1X I2C address, useful approach range, and gazebo false-trigger rate
- Ring-light power, color-temperature behavior, and safe mounting
- Final speaker routing and microphone/speaker echo behavior
