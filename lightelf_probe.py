#!/usr/bin/env python3
"""Identity-only LightELF BLE probe; incapable of enabling optical output.

Protocol formulas are adapted from the MIT-licensed aderusha/lightelf_laser
project at commit d2b11238249dad0d0cb7ae225e2f26aee9b58587.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import secrets
from dataclasses import asdict, dataclass


DEFAULT_ADDRESS = "3E:D9:F7:40:86:00"
NOTIFY_UUID = "0000FF01-0000-1000-8000-00805F9B34FB"
WRITE_UUID = "0000FF02-0000-1000-8000-00805F9B34FB"
QUERY_START = bytes.fromhex("E0E1E2E3")
QUERY_END = bytes.fromhex("E4E5E6E7")


@dataclass(frozen=True)
class QueryReply:
    reply_bytes: int
    challenge_ok: bool
    device_on: bool
    device_type: int
    protocol_version: int
    device_number: int
    user_number: int
    ota_version_raw: int


def expected_challenge(random_bytes: bytes) -> bytes:
    if len(random_bytes) != 4:
        raise ValueError("query challenge requires exactly four bytes")
    b0 = (((random_bytes[0] + 55) >> 1) - 10) & 0xFF
    b1 = (7 + ((random_bytes[1] - 68) << 1)) & 0xFF
    b2 = (15 + ((random_bytes[2] + 97) >> 1)) & 0xFF
    b3 = (87 + ((random_bytes[3] - 127) >> 1)) & 0xFF
    return bytes((b0, b1, b2, b3))


def query_packet(random_bytes: bytes) -> bytes:
    if len(random_bytes) != 4:
        raise ValueError("query requires exactly four random bytes")
    return QUERY_START + random_bytes + QUERY_END


def parse_query_reply(response: bytes, random_bytes: bytes) -> QueryReply:
    if len(response) < 12:
        raise ValueError("query reply is too short")
    token = response[-12:-8]
    challenge_ok = token in {expected_challenge(random_bytes), bytes.fromhex("8AC5624F")}
    return QueryReply(
        reply_bytes=len(response),
        challenge_ok=challenge_ok,
        device_on=response[-8] != 0,
        device_type=response[-7],
        protocol_version=response[-6],
        device_number=response[4],
        user_number=response[-5],
        ota_version_raw=int.from_bytes(response[5:7], "big"),
    )


async def _probe_async(address: str, timeout: float) -> QueryReply:
    """Perform only notification setup and the LightELF identity query."""
    try:
        from bleak import BleakClient
    except ImportError as exc:
        raise RuntimeError("python3-bleak is required for the identity probe") from exc

    challenge = secrets.token_bytes(4)
    response = bytearray()
    reply_ready = asyncio.Event()

    def receive(_sender, data: bytearray) -> None:
        response.extend(data)
        if response.endswith(QUERY_END):
            reply_ready.set()

    async with BleakClient(address, timeout=timeout) as client:
        await client.start_notify(NOTIFY_UUID, receive)
        try:
            await client.start_notify(WRITE_UUID, receive)
        except Exception:
            pass
        # The identity packet is one short write. An acknowledged write is more
        # reliable on direct BlueZ and cannot trigger the large-frame timing
        # issue that requires unacknowledged writes for drawings.
        await client.write_gatt_char(WRITE_UUID, query_packet(challenge), response=True)
        await asyncio.wait_for(reply_ready.wait(), timeout=timeout)
    parsed = parse_query_reply(bytes(response), challenge)
    if not parsed.challenge_ok:
        raise RuntimeError("LightELF query challenge validation failed")
    return parsed


def probe(address: str, timeout: float = 10.0) -> QueryReply:
    return asyncio.run(_probe_async(address, timeout))


def main() -> None:
    parser = argparse.ArgumentParser(description="Identity-only LightELF BLE probe")
    parser.add_argument("--address", default=DEFAULT_ADDRESS)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()
    print(json.dumps(asdict(probe(args.address, args.timeout)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
