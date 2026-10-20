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
- Second PAR: `A030`, channels 30-35

Both fixtures were physically observed responding independently to red, green,
blue, white, and blackout. A cable fault initially hid A001; an isolated
full-red test distinguished that fault from addressing or software trouble.

### Diagnostic history

1. The Pi enumerated the interface and could write to `/dev/ttyUSB0`, but the
   fixtures did not respond.
2. OLA's Open DMX plugin claimed the device and reported Universe 1 correctly,
   but the fixtures still did not respond.
3. Reducing the FTDI latency timer from 16 ms to 1 ms did not fix OLA output.
4. QLC+ 5 on macOS detected `FT232R USB UART (S/N: BG00UVK9)` and immediately
   drove A030 using channels 30-35. This proved the adapter, 5-to-3-pin adapter,
   DMX cable, polarity, address, and fixture.
5. Direct `libftdi` control on the Pi then drove the same fixture successfully,
   first as root and then as the ordinary `ggorman` kiosk user.
6. Both connected fixtures subsequently passed independent RGBW and blackout
   tests from the Pi.

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

The current tested driver and manual test utility live in the transporter
repository until integrated into this runtime. The previous Pi driver was
preserved as:

```text
/home/ggorman/dmx_lighting.py.pre-direct-ftdi-20261019
```

Current manual test:

```bash
python3 /home/ggorman/dmx_lighting.py --test
```

The test starts with blackout, exercises A001 and A030 separately, and ends in
blackout.

## Pending physical verification

- Exact manufacturer/model of the two-unit special-order camera shipment; do
  not assume the earlier Arducam B0354 candidate until the label is inspected
- Camera modes, frame rates, field of view, and low-light behavior
- Microphone-array USB identity, channel topology, beamforming, and echo
  cancellation
- VL53L1X I2C address, useful approach range, and gazebo false-trigger rate
- Ring-light power, color-temperature behavior, and safe mounting
- Final speaker routing and microphone/speaker echo behavior
