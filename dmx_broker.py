#!/usr/bin/env python3
"""Single-owner DMX broker with heartbeat-enforced laser blackout."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import signal
import socket
import sys
import threading
import time
from pathlib import Path

from dmx_lighting import OpenDmxOutput, PAR_ADDRESSES, ParScene, Universe
from laser_cues import LASER_ADDRESS, blackout_channels, cue_channels


BROKER_CHANNELS = 96
DEFAULT_LASER_TTL = 1.0
MAX_LASER_TTL = 2.0


def default_socket_path() -> Path:
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if runtime:
        return Path(runtime) / "madame-maxime-dmx.sock"
    return Path(f"/tmp/madame-maxime-dmx-{os.getuid()}.sock")


class BrokerState:
    """Pure command/state layer; hardware-independent and directly testable."""

    def __init__(self, universe: Universe | None = None) -> None:
        self.universe = universe or Universe(BROKER_CHANNELS)
        self.laser_cue: str | None = None
        self.laser_deadline: float | None = None

    def set_par(self, values) -> None:
        values = tuple(values)
        if len(values) != 4:
            raise ValueError("PAR scene requires master, red, green, and blue")
        scene = ParScene(*values)
        self.universe.set_pars(PAR_ADDRESSES, scene)

    def arm_laser(self, name: str, now: float, ttl: float = DEFAULT_LASER_TTL) -> None:
        ttl = max(0.1, min(float(ttl), MAX_LASER_TTL))
        self.universe.set_channels(LASER_ADDRESS, cue_channels(name, armed=True))
        self.laser_cue = name
        self.laser_deadline = now + ttl

    def heartbeat_laser(self, name: str, now: float, ttl: float = DEFAULT_LASER_TTL) -> None:
        if self.laser_cue != name or self.laser_deadline is None:
            raise ValueError("laser heartbeat does not match an armed cue")
        ttl = max(0.1, min(float(ttl), MAX_LASER_TTL))
        self.laser_deadline = now + ttl

    def blackout_laser(self) -> None:
        self.universe.set_channels(LASER_ADDRESS, blackout_channels())
        self.laser_cue = None
        self.laser_deadline = None

    def blackout_all(self) -> None:
        self.universe.blackout()
        self.laser_cue = None
        self.laser_deadline = None

    def tick(self, now: float) -> bool:
        if self.laser_deadline is not None and now >= self.laser_deadline:
            self.blackout_laser()
            return True
        return False

    def handle(self, message: dict, now: float) -> bool:
        command = message.get("command")
        if command == "par":
            self.set_par(message["values"])
        elif command == "laser_arm":
            self.arm_laser(message["cue"], now, message.get("ttl", DEFAULT_LASER_TTL))
        elif command == "laser_heartbeat":
            self.heartbeat_laser(
                message["cue"], now, message.get("ttl", DEFAULT_LASER_TTL)
            )
        elif command == "laser_blackout":
            self.blackout_laser()
        elif command == "blackout":
            self.blackout_all()
        elif command == "shutdown":
            self.blackout_all()
            return False
        else:
            raise ValueError(f"unknown DMX broker command: {command!r}")
        return True


class DmxClient:
    def __init__(self, socket_path: Path | str | None = None) -> None:
        self.socket_path = str(socket_path or default_socket_path())

    def send(self, command: str, **values) -> None:
        message = json.dumps({"command": command, **values}).encode("utf-8")
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as client:
            client.sendto(message, self.socket_path)

    def set_par(self, values) -> None:
        self.send("par", values=list(values))

    def arm_laser(self, cue: str, ttl: float = DEFAULT_LASER_TTL) -> None:
        self.send("laser_arm", cue=cue, ttl=ttl)

    def heartbeat_laser(self, cue: str, ttl: float = DEFAULT_LASER_TTL) -> None:
        self.send("laser_heartbeat", cue=cue, ttl=ttl)

    def blackout_laser(self) -> None:
        self.send("laser_blackout")

    def blackout_all(self) -> None:
        self.send("blackout")


def serve(socket_path: Path, serial_number: str | None = None) -> None:
    universe = Universe(BROKER_CHANNELS)
    state = BrokerState(universe)
    output = OpenDmxOutput(universe, serial_number) if serial_number else OpenDmxOutput(universe)
    stopping = threading.Event()

    def request_stop(_signum=None, _frame=None) -> None:
        stopping.set()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = socket_path.with_name(f"{socket_path.name}.lock")
    lock_file = lock_path.open("w")
    try:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("another DMX broker already owns this socket") from exc
        os.chmod(lock_path, 0o600)
        if socket_path.exists():
            socket_path.unlink()
        server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        server.bind(str(socket_path))
        os.chmod(socket_path, 0o600)
        server.settimeout(0.05)
        output.start()
        while not stopping.is_set():
            try:
                payload = server.recv(4096)
            except socket.timeout:
                payload = None
            if payload:
                try:
                    message = json.loads(payload.decode("utf-8"))
                    if not isinstance(message, dict):
                        raise ValueError("message must be a JSON object")
                    if not state.handle(message, time.monotonic()):
                        stopping.set()
                except Exception as exc:
                    print(f"DMX broker rejected command: {exc}", file=sys.stderr, flush=True)
            state.tick(time.monotonic())
            if output.error:
                raise RuntimeError(f"DMX transmitter stopped: {output.error}")
    finally:
        state.blackout_all()
        time.sleep(0.12)
        output.stop(blackout=True)
        if "server" in locals():
            server.close()
        if socket_path.exists():
            socket_path.unlink()
        lock_file.close()
        if lock_path.exists():
            lock_path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="Madame Maxime single-owner DMX broker")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--socket", type=Path, default=default_socket_path())
    parser.add_argument("--serial")
    args = parser.parse_args()
    if not args.serve:
        parser.error("no action selected; use --serve")
    serve(args.socket, args.serial)


if __name__ == "__main__":
    main()
