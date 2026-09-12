#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[1]
main = (root / "src/osdep/main.cpp").read_text(encoding="utf-8")

required = [
    'const char* output_dir = std::getenv("AMISANDBOX_ANALYSIS_DIR")',
    'if (output_dir && *output_dir)',
    '#ifdef JIT',
    'analysis mode requires a non-JIT build',
    'return 78;',
    'metadata.amisandbox_version = "m2.0";',
    'metadata.jit_enabled = false;',
]

missing = [needle for needle in required if needle not in main]
if missing:
    raise SystemExit("FAIL: AmiSandbox M2.0 contract missing: " + ", ".join(missing))

jit_guard = main.index('#ifdef JIT')
session_start = main.index('analysis.start(output_dir')
if jit_guard > session_start:
    raise SystemExit("FAIL: JIT guard occurs after analysis session start")

print("PASS: AmiSandbox M2.0 fail-closed JIT isolation contract")
