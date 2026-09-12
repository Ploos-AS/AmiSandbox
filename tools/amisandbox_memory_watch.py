#!/usr/bin/env python3
"""Watch selected Amiga memory locations through Amiberry IPC.

M1.2 deliberately builds on Amiberry's existing READ_MEM IPC command rather
than adding a hot-path memory-write hook. The watcher records a baseline and
emits a JSONL event only when a watched value changes.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import sys
import time
from typing import TextIO

SCHEMA_VERSION = 1
DEFAULT_INTERVAL_MS = 100
DEFAULT_READY_TIMEOUT = 15.0

# 68000 autovectors 25-31: spurious + interrupt levels 1-7.
DEFAULT_VECTOR_ADDRESSES = tuple(range(0x64, 0x80, 4))


def default_socket_path(instance: int = 0) -> Path:
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    base = Path(runtime) / "amiberry" if runtime else Path("/tmp/amiberry")
    suffix = ".sock" if instance == 0 else f"_{instance}.sock"
    return Path(f"{base}{suffix}")


def request(socket_path: Path, command: str, timeout: float = 1.0) -> list[str]:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(timeout)
        client.connect(str(socket_path))
        client.sendall((command + "\n").encode("ascii"))
        chunks: list[bytes] = []
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
            if b"\n" in chunk:
                break

    lines = b"".join(chunks).decode("utf-8", errors="strict").splitlines()
    if not lines:
        raise RuntimeError("empty IPC response")
    fields = lines[0].split("\t")
    if not fields or fields[0] != "OK":
        raise RuntimeError(lines[0])
    return fields[1:]


def wait_until_ready(socket_path: Path, timeout: float = DEFAULT_READY_TIMEOUT) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            request(socket_path, "GET_VERSION", timeout=1.0)
            return
        except (OSError, RuntimeError) as exc:
            last_error = exc
            time.sleep(0.1)
    raise TimeoutError(f"IPC not ready after {timeout:.1f}s: {last_error}")


def parse_address(value: str) -> int:
    address = int(value, 0)
    if address < 0 or address > 0xFFFFFFFF:
        raise argparse.ArgumentTypeError("address must be between 0 and 0xffffffff")
    return address


def read_value(socket_path: Path, address: int, width: int) -> int:
    fields = request(socket_path, f"READ_MEM\t{address:#x}\t{width}")
    if len(fields) != 1:
        raise RuntimeError(f"unexpected READ_MEM response at {address:#x}: {fields!r}")
    return int(fields[0], 0)


def emit_change(
    out: TextIO,
    sequence: int,
    address: int,
    width: int,
    old_value: int,
    new_value: int,
) -> None:
    event = {
        "schema_version": SCHEMA_VERSION,
        "sequence": sequence,
        "type": "memory.change",
        "data": {
            "source": "amiberry-ipc",
            "monotonic_ns": time.monotonic_ns(),
            "address": f"0x{address:08x}",
            "width": width,
            "old_value": f"0x{old_value:0{width * 2}x}",
            "new_value": f"0x{new_value:0{width * 2}x}",
        },
    }
    out.write(json.dumps(event, separators=(",", ":")) + "\n")
    out.flush()


def main() -> int:
    parser = argparse.ArgumentParser(description="AmiSandbox M1.2 selected-memory change watcher")
    parser.add_argument("--socket", type=Path, help="Amiberry Unix socket path")
    parser.add_argument("--instance", type=int, default=0, help="Amiberry IPC instance number (default: 0)")
    parser.add_argument("--address", action="append", type=parse_address, help="address to watch; repeat for multiple addresses")
    parser.add_argument("--width", type=int, choices=(1, 2, 4), default=4, help="READ_MEM width (default: 4)")
    parser.add_argument("--interval-ms", type=int, default=DEFAULT_INTERVAL_MS, help="poll interval in milliseconds")
    parser.add_argument("--count", type=int, default=0, help="number of polling rounds; 0 means until interrupted")
    parser.add_argument("--ready-timeout", type=float, default=DEFAULT_READY_TIMEOUT, help="seconds to wait for IPC readiness")
    parser.add_argument("--output", type=Path, help="output JSONL path")
    args = parser.parse_args()

    if args.interval_ms < 1:
        parser.error("--interval-ms must be >= 1")
    if args.count < 0:
        parser.error("--count must be >= 0")
    if args.instance < 0 or args.instance > 9:
        parser.error("--instance must be between 0 and 9")
    if args.ready_timeout <= 0:
        parser.error("--ready-timeout must be > 0")

    addresses = tuple(dict.fromkeys(args.address or DEFAULT_VECTOR_ADDRESSES))
    socket_path = args.socket or default_socket_path(args.instance)
    session_dir = os.environ.get("AMISANDBOX_ANALYSIS_DIR")
    output_path = args.output or (Path(session_dir) / "memory-changes.jsonl" if session_dir else Path("memory-changes.jsonl"))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        wait_until_ready(socket_path, args.ready_timeout)
        previous = {address: read_value(socket_path, address, args.width) for address in addresses}
        sequence = 0
        rounds = 0
        with output_path.open("a", encoding="utf-8") as out:
            while args.count == 0 or rounds < args.count:
                for address in addresses:
                    current = read_value(socket_path, address, args.width)
                    old = previous[address]
                    if current != old:
                        emit_change(out, sequence, address, args.width, old, current)
                        sequence += 1
                        previous[address] = current
                rounds += 1
                if args.count == 0 or rounds < args.count:
                    time.sleep(args.interval_ms / 1000.0)
    except KeyboardInterrupt:
        return 0
    except (OSError, RuntimeError, ValueError, TimeoutError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
