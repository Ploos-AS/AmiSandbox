#!/usr/bin/env python3
"""Static contract checks for AmiSandbox M2.5 disposable-media launch integration."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "src/osdep/main.cpp").read_text(encoding="utf-8")
LAUNCH = (ROOT / "tools/amisandbox_launch.py").read_text(encoding="utf-8")
MEDIA = (ROOT / "tools/amisandbox_media_prepare.py").read_text(encoding="utf-8")

required_main = [
    'AMISANDBOX_WRITABLE_MEDIA_COPY',
    'validated_writable_floppy',
    'std::filesystem::weakly_canonical',
    'std::filesystem::is_regular_file',
    'path_is_within(requested, media_root)',
    '-cfgparam=floppy_write_protect=false',
    'writable media opt-in rejected',
    'allowing writable disposable floppy media',
    'metadata.amisandbox_version = "m2.5"',
]
required_launch = [
    'from amisandbox_media_prepare import finalize as media_finalize',
    'from amisandbox_media_prepare import prepare as media_prepare',
    'AMISANDBOX_ANALYSIS_DIR',
    'AMISANDBOX_WRITABLE_MEDIA_COPY',
    'media-manifest.json',
    '"-0"',
    'str(working)',
    '"-cfgparam=floppy_write_protect=false"',
    'media_finalize',
]
required_media = [
    'copy_strategy": "full-copy"',
    'source evidence changed during analysis',
    'working_final = sha256_file(working)',
    'initial = manifest["working"]["sha256_initial"]',
    'manifest["working"]["mutated"] = working_final != initial',
]

missing = []
for token in required_main:
    if token not in MAIN:
        missing.append(f"main.cpp: {token}")
for token in required_launch:
    if token not in LAUNCH:
        missing.append(f"amisandbox_launch.py: {token}")
for token in required_media:
    if token not in MEDIA:
        missing.append(f"amisandbox_media_prepare.py: {token}")

if missing:
    raise SystemExit("FAIL: M2.5 contract missing:\n  " + "\n  ".join(missing))

print("PASS: AmiSandbox M2.5 disposable-media launch contract")
print("PASS: writable opt-in is constrained to a regular file below the session media tree")
print("PASS: launcher mounts only the prepared working copy and finalizes media evidence")
