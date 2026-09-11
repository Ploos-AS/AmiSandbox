#!/usr/bin/env python3
"""Static contract check for AmiSandbox M1.1 live CPU sampling."""

from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
SAMPLER = ROOT / "tools/amisandbox_cpu_sampler.py"
IPC_HEADER = ROOT / "src/osdep/amiberry_ipc.h"
IPC_IMPL = ROOT / "src/osdep/amiberry_ipc_socket.cpp"

failures: list[str] = []
for path in (SAMPLER, IPC_HEADER, IPC_IMPL):
    if not path.is_file():
        failures.append(f"missing required file: {path.relative_to(ROOT)}")

if not failures:
    sampler = SAMPLER.read_text(encoding="utf-8")
    header = IPC_HEADER.read_text(encoding="utf-8")
    impl = IPC_IMPL.read_text(encoding="utf-8")

    try:
        ast.parse(sampler)
    except SyntaxError as exc:
        failures.append(f"sampler syntax error: {exc}")

    required_sampler = [
        "GET_CPU_REGS", "cpu.snapshot", "amiberry-ipc", "cpu-snapshots.jsonl",
        "XDG_RUNTIME_DIR", "AMISANDBOX_ANALYSIS_DIR", "--interval-ms", "--instance",
    ]
    for token in required_sampler:
        if token not in sampler:
            failures.append(f"sampler missing contract token: {token}")

    if 'CMD_GET_CPU_REGS = "GET_CPU_REGS"' not in header:
        failures.append("Amiberry IPC header does not expose GET_CPU_REGS")

    for token in ("D%d=%08X", "A%d=%08X", "PC=%08X", "SR=%04X"):
        if token not in impl:
            failures.append(f"GET_CPU_REGS implementation missing: {token}")

if failures:
    for failure in failures:
        print(f"FAIL: {failure}")
    sys.exit(1)

print("PASS: AmiSandbox M1.1 live CPU sampler contract")
