#!/usr/bin/env python3
"""Static contract check for AmiSandbox M1.2 memory observation."""

from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
WATCHER = ROOT / "tools/amisandbox_memory_watch.py"
IPC_HEADER = ROOT / "src/osdep/amiberry_ipc.h"
IPC_IMPL = ROOT / "src/osdep/amiberry_ipc_socket.cpp"

failures: list[str] = []
for path in (WATCHER, IPC_HEADER, IPC_IMPL):
    if not path.is_file():
        failures.append(f"missing required file: {path.relative_to(ROOT)}")

if not failures:
    watcher = WATCHER.read_text(encoding="utf-8")
    header = IPC_HEADER.read_text(encoding="utf-8")
    impl = IPC_IMPL.read_text(encoding="utf-8")

    try:
        ast.parse(watcher)
    except SyntaxError as exc:
        failures.append(f"watcher syntax error: {exc}")

    required_watcher = [
        "READ_MEM", "memory.change", "memory-changes.jsonl", "old_value",
        "new_value", "DEFAULT_VECTOR_ADDRESSES", "GET_VERSION",
        "AMISANDBOX_ANALYSIS_DIR", "--address", "--width",
    ]
    for token in required_watcher:
        if token not in watcher:
            failures.append(f"watcher missing contract token: {token}")

    if 'CMD_READ_MEM = "READ_MEM"' not in header:
        failures.append("Amiberry IPC header does not expose READ_MEM")

    for token in (
        "Usage: READ_MEM <address> <width(1,2,4)>",
        "get_byte(addr)", "get_word(addr)", "get_long(addr)",
    ):
        if token not in impl:
            failures.append(f"READ_MEM implementation missing: {token}")

if failures:
    for failure in failures:
        print(f"FAIL: {failure}")
    sys.exit(1)

print("PASS: AmiSandbox M1.2 memory observation contract")
