#!/usr/bin/env python3
"""One-shot, fixed-geometry LightELF optical qualification test.

This utility deliberately exposes no arbitrary packet or geometry arguments.
It draws a tiny centered diamond for at most two seconds and sends POWER OFF
twice in a finally block. It is not the production BLE transport.
"""

from __future__ import annotations

import argparse
import asyncio
import secrets

from lightelf_probe import (
    DEFAULT_ADDRESS,
    NOTIFY_UUID,
    WRITE_UUID,
    parse_query_reply,
    query_packet,
)


POWER_ON = bytes.fromhex("B0B1B2B3FFB4B5B6B7")
POWER_OFF = bytes.fromhex("B0B1B2B300B4B5B6B7")
MAX_DURATION = 2.0


def _word(value: int) -> bytes:
    encoded = (0x8000 | -value) if value < 0 else value
    return int(encoded).to_bytes(2, "big")


def tiny_diamond_packet() -> bytes:
    # Old-protocol F0 frame: 15 zeroed configuration bytes, save-tag zero,
    # then a single 80 x 80 projector-unit closed stroke centered at (0, 0).
    vertices = ((0, -40), (40, 0), (0, 40), (-40, 0), (0, -40))
    points: list[tuple[int, int, int]] = []
    for edge, ((x1, y1), (x2, y2)) in enumerate(zip(vertices, vertices[1:])):
        for step in range(5):
            if edge and step == 0:
                continue
            ratio = step / 4
            x = round(x1 + (x2 - x1) * ratio)
            y = round(y1 + (y2 - y1) * ratio)
            control = 0x02 if not points else 0x70
            points.append((x, y, control))
    x, y, _ = points[-1]
    points[-1] = (x, y, 0x73)  # lit final point plus old-firmware stop marker

    payload = bytearray(16)
    payload.extend(len(points).to_bytes(2, "big"))
    for x, y, control in points:
        payload.extend(_word(x))
        payload.extend(_word(y))
        payload.append(control)
    return bytes.fromhex("F0F1F2F3") + payload + bytes.fromhex("F4F5F6F7")


async def _write_chunks(client, packet: bytes, *, acknowledged: bool) -> None:
    for offset in range(0, len(packet), 20):
        await client.write_gatt_char(
            WRITE_UUID, packet[offset : offset + 20], response=acknowledged
        )
        await asyncio.sleep(0.03)


async def run(address: str, duration: float) -> None:
    from bleak import BleakClient, BleakScanner

    challenge = secrets.token_bytes(4)
    response = bytearray()
    reply_ready = asyncio.Event()

    def receive(_sender, data: bytearray) -> None:
        response.extend(data)
        if response.endswith(bytes.fromhex("E4E5E6E7")):
            reply_ready.set()

    device = await BleakScanner.find_device_by_address(address, timeout=10.0)
    if device is None:
        raise RuntimeError(f"LightELF device {address} is not advertising")

    client = BleakClient(device, timeout=10.0)
    powered = False
    try:
        await client.connect()
        await client.start_notify(NOTIFY_UUID, receive)
        await client.read_gatt_char(NOTIFY_UUID)
        query = query_packet(challenge)
        for attempt in range(1, 4):
            await client.write_gatt_char(WRITE_UUID, query, response=True)
            try:
                await asyncio.wait_for(reply_ready.wait(), timeout=3.0)
                break
            except TimeoutError:
                if attempt == 3:
                    raise
                response.clear()
                reply_ready.clear()
        parsed = parse_query_reply(bytes(response), challenge, attempt)
        if not parsed.challenge_ok:
            raise RuntimeError("LightELF query challenge validation failed")

        await _write_chunks(client, POWER_ON, acknowledged=False)
        powered = True
        await _write_chunks(client, tiny_diamond_packet(), acknowledged=False)
        await asyncio.sleep(min(max(duration, 0.25), MAX_DURATION))
    finally:
        if client.is_connected and powered:
            await _write_chunks(client, POWER_OFF, acknowledged=False)
            await asyncio.sleep(0.1)
            await _write_chunks(client, POWER_OFF, acknowledged=False)
        if client.is_connected:
            try:
                await client.disconnect()
            except (EOFError, ConnectionError):
                # BlueZ can close its D-Bus side immediately after the device
                # accepts POWER OFF. The safety writes have already completed;
                # a disappearing connection must not disguise that outcome.
                pass


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--address", default=DEFAULT_ADDRESS)
    parser.add_argument("--duration", type=float, default=1.5)
    parser.add_argument("--confirm", required=True)
    args = parser.parse_args()
    if args.confirm != "BEAM-AREA-CLEAR":
        raise SystemExit("Refusing output: pass --confirm BEAM-AREA-CLEAR")
    asyncio.run(run(args.address, args.duration))
    print("bounded diamond sent; double power-off completed")


if __name__ == "__main__":
    main()
