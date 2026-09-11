#!/usr/bin/env python3
"""Static M1 contract check for the AmiSandbox analysis boundary."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

checks = {
    "header": ROOT / "src/amisandbox/analysis_session.h",
    "implementation": ROOT / "src/amisandbox/analysis_session.cpp",
    "entrypoint": ROOT / "src/osdep/main.cpp",
    "m0": ROOT / "docs/AMISANDBOX_M0.md",
}

failures: list[str] = []
for name, path in checks.items():
    if not path.is_file():
        failures.append(f"missing {name}: {path.relative_to(ROOT)}")

if not failures:
    header = checks["header"].read_text(encoding="utf-8")
    impl = checks["implementation"].read_text(encoding="utf-8")
    main = checks["entrypoint"].read_text(encoding="utf-8")

    required_header = ["kEventSchemaVersion", "SessionMetadata", "CpuSnapshot", "AnalysisSession"]
    required_impl = ["session.json", "events.jsonl", "session.start", "session.stop", "cpu.snapshot"]
    required_main = ["AMISANDBOX_ANALYSIS_DIR", "AMISANDBOX_MACHINE_PROFILE", "AMISANDBOX_CONFIG_FINGERPRINT"]

    for token in required_header:
        if token not in header:
            failures.append(f"analysis_session.h missing contract token: {token}")
    for token in required_impl:
        if token not in impl:
            failures.append(f"analysis_session.cpp missing contract token: {token}")
    for token in required_main:
        if token not in main:
            failures.append(f"main.cpp missing runtime boundary: {token}")

if failures:
    for failure in failures:
        print(f"FAIL: {failure}")
    sys.exit(1)

print("PASS: AmiSandbox M1 analysis-session contract")
