"""Safety-interlocked LightELF BLE transport; live output is off by default."""

from __future__ import annotations

import asyncio
import json
import os
import queue
import secrets
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from lightelf_probe import (
    DEFAULT_ADDRESS, NOTIFY_UUID, WRITE_UUID, parse_query_reply, query_packet,
)
from lightelf_protocol import power_packet, svg_packet, text_packet


LIVE_INTERLOCK = "I-ACCEPT-LIVE-LASER-OUTPUT"
MAX_LEASE_SECONDS = 2.0


class LightElfBleTransport:
    """Persistent BLE worker with a transport-local fail-closed lease.

    Construction is harmless. The worker cannot start unless both the explicit
    constructor flag and process environment interlock are present.
    """

    def __init__(
        self,
        *,
        address: str = DEFAULT_ADDRESS,
        enabled: bool = False,
        diagnostic_path: Path | None = None,
    ) -> None:
        self.address = address
        self.enabled = bool(enabled and os.getenv("MADAME_MAXIME_LIGHTELF_LIVE") == LIVE_INTERLOCK)
        self._commands: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None
        self._lease_deadline = 0.0
        self._output_active = False
        self._last_error: str | None = None
        self._events: list[dict] = []
        self._diagnostic_path = diagnostic_path or (
            Path(os.getenv("XDG_STATE_HOME", Path.home() / ".local" / "state"))
            / "madame-maxime" / "lightelf.jsonl"
        )

    def _record(self, event: str, ok: bool) -> None:
        item = {
            "time": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "ok": bool(ok),
        }
        self._events.append(item)
        try:
            self._diagnostic_path.parent.mkdir(parents=True, exist_ok=True)
            with self._diagnostic_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(item, separators=(",", ":")) + "\n")
        except OSError:
            # Diagnostics are never allowed to interfere with blackout.
            pass

    @property
    def diagnostic_snapshot(self) -> dict:
        return {
            "enabled": self.enabled,
            "worker_alive": bool(self._thread and self._thread.is_alive()),
            "lease_active": self._lease_deadline > time.monotonic(),
            "output_active": self._output_active,
            "last_error": self._last_error,
            "events": list(self._events[-20:]),
        }

    def _require_enabled(self) -> None:
        if not self.enabled:
            raise RuntimeError("live LightELF output is disabled by the operator interlock")

    def _start(self) -> None:
        self._require_enabled()
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=lambda: asyncio.run(self._worker()), daemon=True)
        self._thread.start()

    def _submit(self, name: str, payload=None, timeout: float = 45.0) -> None:
        self._start()
        result: queue.Queue = queue.Queue(maxsize=1)
        self._commands.put((name, payload, result))
        ok, detail = result.get(timeout=timeout)
        if not ok:
            raise RuntimeError(detail)

    def show_svg(self, path: Path, *, color: str, size_percent: int) -> None:
        packet = svg_packet(path, color=color, size_percent=size_percent)
        self._submit("show", packet)

    def show_text(self, text: str, *, color: str, size_percent: int) -> None:
        packet = text_packet(text, color=color, size_percent=size_percent)
        self._submit("show", packet)

    def heartbeat(self, *, ttl: float = 1.0) -> None:
        self._submit("heartbeat", min(max(float(ttl), 0.1), MAX_LEASE_SECONDS))

    def blackout(self) -> None:
        if self._thread and self._thread.is_alive():
            self._submit("blackout", timeout=30.0)

    def close(self) -> None:
        if self._thread and self._thread.is_alive():
            self._submit("close", timeout=30.0)
            self._thread.join(timeout=30.0)

    async def _write(self, client, packet: bytes, *, acknowledged: bool = False) -> None:
        for offset in range(0, len(packet), 20):
            await client.write_gatt_char(
                WRITE_UUID, packet[offset:offset + 20], response=acknowledged
            )
            await asyncio.sleep(0.03)

    async def _connect(self):
        from bleak import BleakClient, BleakScanner
        device = await BleakScanner.find_device_by_address(self.address, timeout=10.0)
        if device is None:
            raise RuntimeError("LightELF is not advertising")
        client = BleakClient(device, timeout=10.0)
        response = bytearray()
        ready = asyncio.Event()
        challenge = secrets.token_bytes(4)

        def receive(_sender, data):
            response.extend(data)
            if response.endswith(bytes.fromhex("E4E5E6E7")):
                ready.set()

        await client.connect()
        await client.start_notify(NOTIFY_UUID, receive)
        await client.read_gatt_char(NOTIFY_UUID)
        query = query_packet(challenge)
        for attempt in range(1, 4):
            await client.write_gatt_char(WRITE_UUID, query, response=True)
            try:
                await asyncio.wait_for(ready.wait(), timeout=3.0)
                break
            except TimeoutError:
                if attempt == 3:
                    raise
                response.clear()
                ready.clear()
        if not parse_query_reply(bytes(response), challenge, attempt).challenge_ok:
            raise RuntimeError("LightELF challenge validation failed")
        return client

    async def _off(self, client):
        # If the connection vanished while output may still be active, make a
        # bounded reconnection attempt instead of silently declaring blackout.
        if self._output_active and (client is None or not client.is_connected):
            client = await self._connect()
        if self._output_active:
            await self._write(client, power_packet(False))
            await asyncio.sleep(0.1)
            await self._write(client, power_packet(False))
        self._output_active = False
        self._lease_deadline = 0.0
        return client

    async def _worker(self) -> None:
        client = None
        running = True
        while running:
            if self._lease_deadline and time.monotonic() >= self._lease_deadline:
                try:
                    client = await self._off(client)
                    self._record("lease_blackout", True)
                except Exception as exc:
                    self._last_error = type(exc).__name__
                    self._record("lease_blackout", False)
                    self._lease_deadline = time.monotonic() + 0.5
            try:
                name, payload, result = self._commands.get_nowait()
            except queue.Empty:
                await asyncio.sleep(0.05)
                continue
            try:
                if name == "show":
                    if client is None or not client.is_connected:
                        client = await self._connect()
                    await self._write(client, power_packet(True))
                    self._output_active = True
                    self._lease_deadline = time.monotonic() + 1.0
                    await self._write(client, payload)
                elif name == "heartbeat":
                    if not self._lease_deadline:
                        raise RuntimeError("cannot renew an inactive LightELF lease")
                    self._lease_deadline = time.monotonic() + payload
                elif name == "blackout":
                    client = await self._off(client)
                elif name == "close":
                    client = await self._off(client)
                    running = False
                self._record(name, True)
                result.put((True, None))
            except Exception as exc:
                self._last_error = type(exc).__name__
                self._record(name, False)
                result.put((False, f"{type(exc).__name__}: {exc}"))
        if client and client.is_connected:
            try:
                await client.disconnect()
            except (EOFError, ConnectionError):
                pass
