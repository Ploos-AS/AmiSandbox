#!/usr/bin/env python3
"""Sample live 68k CPU registers from Amiberry IPC into AmiSandbox JSONL.

M1.1 intentionally uses Amiberry's existing GET_CPU_REGS IPC command instead of
patching the generated CPU execution loops. This keeps upstream divergence low
while still collecting real emulator register state.
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

    line = b"".join(chunks).decode("utf-8", errors="strict").splitlines()[0]
    fields = line.split("\t")
    if not fields or fields[0] != "OK":
        raise RuntimeError(line or "empty IPC response")
    return fields[1:]


def parse_cpu_regs(fields: list[str]) -> dict[str, object]:
    values: dict[str, str] = {}
    for field in fields:
        if "=" not in field:
            continue
        key, value = field.split("=", 1)
        values[key] = value

    required = [*(f"D{i}" for i in range(8)), *(f"A{i}" for i in range(8)), "PC", "SR"]
    missing = [name for name in required if name not in values]
    if missing:
        raise ValueError("GET_CPU_REGS missing fields: " + ", ".join(missing))

    return {
        "pc": f"0x{values['PC'].lower()}",
        "sr": f"0x{values['SR'].lower()}",
        "d": [f"0x{values[f'D{i}'].lower()}" for i in range(8)],
        "a": [f"0x{values[f'A{i}'].lower()}" for i in range(8)],
        "usp": f"0x{values['USP'].lower()}" if "USP" in values else None,
        "isp": f"0x{values['ISP'].lower()}" if "ISP" in values else None,
        "flags": {name.lower(): int(values[name]) for name in ("T", "S", "X", "N", "Z", "V", "C") if name in values},
    }


def emit(out: TextIO, sequence: int, data: dict[str, object]) -> None:
    event = {
        "schema_version": SCHEMA_VERSION,
        "sequence": sequence,
        "type": "cpu.snapshot",
        "data": {
            "source": "amiberry-ipc",
            "monotonic_ns": time.monotonic_ns(),
            **data,
        },
    }
    out.write(json.dumps(event, separators=(",", ":")) + "\n")
    out.flush()


def main() -> int:
    parser = argparse.ArgumentParser(description="AmiSandbox M1.1 live 68k CPU sampler")
    parser.add_argument("--socket", type=Path, help="Amiberry Unix socket path")
    parser.add_argument("--instance", type=int, default=0, help="Amiberry IPC instance number (default: 0)")
    parser.add_argument("--interval-ms", type=int, default=DEFAULT_INTERVAL_MS, help="sampling interval in milliseconds")
    parser.add_argument("--count", type=int, default=0, help="number of snapshots; 0 means until interrupted")
    parser.add_argument("--output", type=Path, help="output JSONL path")
    args = parser.parse_args()

    if args.interval_ms < 1:
        parser.error("--interval-ms must be >= 1")
    if args.count < 0:
        parser.error("--count must be >= 0")
    if args.instance < 0 or args.instance > 9:
        parser.error("--instance must be between 0 and 9")

    socket_path = args.socket or default_socket_path(args.instance)
    session_dir = os.environ.get("AMISANDBOX_ANALYSIS_DIR")
    output_path = args.output or (Path(session_dir) / "cpu-snapshots.jsonl" if session_dir else Path("cpu-snapshots.jsonl"))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sequence = 0
    try:
        with output_path.open("a", encoding="utf-8") as out:
            while args.count == 0 or sequence < args.count:
                fields = request(socket_path, "GET_CPU_REGS")
                emit(out, sequence, parse_cpu_regs(fields))
                sequence += 1
                if args.count == 0 or sequence < args.count:
                    time.sleep(args.interval_ms / 1000.0)
    except KeyboardInterrupt:
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
