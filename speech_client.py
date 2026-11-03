#!/usr/bin/env python3
"""Small CLI/client for the private Madame Maxine speech worker."""

from __future__ import annotations

import argparse
import json
import os
import socket
from pathlib import Path
from collections.abc import Callable

DEFAULT_SOCKET = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")) / "madame-maxime-speech.sock"


def request(payload: dict, timeout: float = 30.0,
            progress: Callable[[dict], None] | None = None) -> dict:
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.settimeout(timeout)
    try:
        client.connect(str(DEFAULT_SOCKET))
        client.sendall(json.dumps(payload).encode("utf-8") + b"\n")
        response = b""
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            response += chunk
            while b"\n" in response:
                line, response = response.split(b"\n", 1)
                if not line:
                    continue
                message = json.loads(line)
                if "event" in message:
                    if progress:
                        progress(message)
                    continue
                return message
        raise RuntimeError("speech service closed without a final response")
    finally:
        client.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--keyword", action="append", default=[])
    parser.add_argument("--start-timeout", type=float, default=15.0)
    parser.add_argument("--max-seconds", type=float, default=8.0)
    args = parser.parse_args()
    payload = {"action": "status"} if args.status else {
        "action": "transcribe", "prompt": args.prompt, "keywords": args.keyword,
        "start_timeout": args.start_timeout, "max_seconds": args.max_seconds,
    }
    response = request(payload)
    print(json.dumps(response, indent=2, sort_keys=True))
    return 0 if response.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
