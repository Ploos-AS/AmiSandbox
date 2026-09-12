#!/usr/bin/env python3
"""Launch AmiSandbox with a disposable writable floppy working copy.

M2.5 composes the M2.4 media preparation helper with Amiberry analysis mode.
The original evidence image is never passed to the emulator. The emulator sees
only the per-session working copy and the core validates that it lives below
<analysis-dir>/media before disabling floppy write protection.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from amisandbox_media_prepare import finalize as media_finalize
from amisandbox_media_prepare import prepare as media_prepare


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AmiSandbox M2.5 disposable-media launcher")
    parser.add_argument("--emulator", required=True, help="path to non-JIT AmiSandbox/Amiberry binary")
    parser.add_argument("--analysis-dir", required=True, help="session analysis output directory")
    parser.add_argument("--source", required=True, help="immutable source ADF/image")
    parser.add_argument("--working-name", help="optional working image basename")
    parser.add_argument("--machine-profile", default="a500", help="analysis metadata machine profile")
    parser.add_argument("--config-fingerprint", default="m2.5-disposable-media")
    parser.add_argument("--force", action="store_true", help="replace an existing working image")
    parser.add_argument("emulator_args", nargs=argparse.REMAINDER, help="arguments passed to emulator after --")
    return parser


def _media_args(args: argparse.Namespace, command: str) -> argparse.Namespace:
    if command == "prepare":
        return argparse.Namespace(
            source=args.source,
            analysis_dir=args.analysis_dir,
            working_name=args.working_name,
            force=args.force,
        )
    return argparse.Namespace(analysis_dir=args.analysis_dir)


def main() -> int:
    args = build_parser().parse_args()
    emulator = Path(args.emulator).expanduser().resolve()
    if not emulator.is_file():
        raise SystemExit(f"emulator not found: {emulator}")

    analysis_dir = Path(args.analysis_dir).expanduser().resolve()
    analysis_dir.mkdir(parents=True, exist_ok=True)

    media_prepare(_media_args(args, "prepare"))
    manifest_path = analysis_dir / "media" / "media-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    working = Path(manifest["working"]["path"])

    env = os.environ.copy()
    env["AMISANDBOX_ANALYSIS_DIR"] = str(analysis_dir)
    env["AMISANDBOX_WRITABLE_MEDIA_COPY"] = "1"
    env["AMISANDBOX_MACHINE_PROFILE"] = args.machine_profile
    env["AMISANDBOX_CONFIG_FINGERPRINT"] = args.config_fingerprint

    forwarded = list(args.emulator_args)
    if forwarded and forwarded[0] == "--":
        forwarded = forwarded[1:]

    command = [
        str(emulator),
        f"-cfgparam=floppy0={working}",
        "-cfgparam=floppy_write_protect=false",
        *forwarded,
    ]

    # Amiberry still requires an X display even for non-interactive analysis
    # launches. On headless CI/appliance hosts, transparently use xvfb-run when
    # it is installed. A real DISPLAY always wins and normal desktop launches
    # remain unchanged.
    if not env.get("DISPLAY"):
        xvfb_run = shutil.which("xvfb-run")
        if xvfb_run:
            command = [xvfb_run, "-a", *command]
            print("AmiSandbox M2.5 display: xvfb-run headless fallback", file=sys.stderr, flush=True)

    print(f"AmiSandbox M2.5 working media: {working}", file=sys.stderr, flush=True)

    result = 70
    try:
        result = subprocess.run(command, env=env, check=False).returncode
    finally:
        media_finalize(_media_args(args, "finalize"))
    return result


if __name__ == "__main__":
    sys.exit(main())
