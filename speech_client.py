#!/usr/bin/env python3
"""Small CLI/client for the private Madame Maxine speech worker."""

from __future__ import annotations

import argparse
import json
import socket

from speech_service import DEFAULT_SOCKET


def request(payload: dict, timeout: float = 30.0) -> dict:
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.settimeout(timeout)
    try:
        client.connect(str(DEFAULT_SOCKET))
        client.sendall(json.dumps(payload).encode("utf-8") + b"\n")
        response = b""
        while b"\n" not in response:
            chunk = client.recv(4096)
            if not chunk:
                break
            response += chunk
        return json.loads(response.split(b"\n", 1)[0])
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
