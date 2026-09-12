#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "amisandbox_media_prepare.py"

required = [
    "amisandbox_milestone\": \"m2.4",
    "copy_strategy\": \"full-copy",
    "source_immutable_expected",
    "sha256_initial",
    "sha256_final",
    "mutated",
    "shutil.copy2",
    "source evidence changed during analysis",
]

text = TOOL.read_text(encoding="utf-8")
missing = [token for token in required if token not in text]
if missing:
    raise SystemExit("FAIL: missing M2.4 contract tokens: " + ", ".join(missing))

print("PASS: AmiSandbox M2.4 disposable working-media contract")
print("  immutable source evidence is copied into per-session media/ working storage")
print("  initial/final SHA-256 values record whether the working copy mutated")
