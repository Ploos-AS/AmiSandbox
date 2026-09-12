#!/usr/bin/env python3
"""Prepare and finalize disposable removable-media working copies for AmiSandbox.

M2.4 deliberately uses a full per-session copy, not block-level COW. The source
image is treated as immutable evidence; only the working copy is intended to be
mounted writable by a later analysis launch policy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1
MANIFEST_NAME = "media-manifest.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def analysis_dir_from(args: argparse.Namespace) -> Path:
    value = args.analysis_dir or os.environ.get("AMISANDBOX_ANALYSIS_DIR")
    if not value:
        raise SystemExit("--analysis-dir or AMISANDBOX_ANALYSIS_DIR is required")
    return Path(value).expanduser().resolve()


def prepare(args: argparse.Namespace) -> int:
    source = Path(args.source).expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"source image not found: {source}")

    analysis_dir = analysis_dir_from(args)
    media_dir = analysis_dir / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    suffix = source.suffix if source.suffix else ".img"
    working_name = args.working_name or f"working{suffix}"
    working = (media_dir / working_name).resolve()
    manifest_path = media_dir / MANIFEST_NAME

    if working.exists() and not args.force:
        raise SystemExit(f"working copy already exists: {working}; use --force to replace")

    source_hash = sha256_file(source)
    shutil.copy2(source, working)
    working_hash = sha256_file(working)
    if working_hash != source_hash:
        raise SystemExit("working copy hash mismatch immediately after copy")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "amisandbox_milestone": "m2.4",
        "copy_strategy": "full-copy",
        "prepared_at": utc_now(),
        "source": {
            "path": str(source),
            "sha256": source_hash,
            "size": source.stat().st_size,
        },
        "working": {
            "path": str(working),
            "sha256_initial": working_hash,
            "sha256_final": None,
            "size_initial": working.stat().st_size,
            "size_final": None,
            "mutated": None,
        },
        "source_immutable_expected": True,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(str(working))
    return 0


def finalize(args: argparse.Namespace) -> int:
    analysis_dir = analysis_dir_from(args)
    manifest_path = analysis_dir / "media" / MANIFEST_NAME
    if not manifest_path.is_file():
        raise SystemExit(f"manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise SystemExit("unsupported media manifest schema")

    source = Path(manifest["source"]["path"])
    working = Path(manifest["working"]["path"])
    if not source.is_file() or not working.is_file():
        raise SystemExit("source or working image missing during finalize")

    source_final = sha256_file(source)
    if source_final != manifest["source"]["sha256"]:
        raise SystemExit("source evidence changed during analysis")

    working_final = sha256_file(working)
    initial = manifest["working"]["sha256_initial"]
    manifest["finalized_at"] = utc_now()
    manifest["source"]["sha256_final"] = source_final
    manifest["working"]["sha256_final"] = working_final
    manifest["working"]["size_final"] = working.stat().st_size
    manifest["working"]["mutated"] = working_final != initial
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("mutated=true" if manifest["working"]["mutated"] else "mutated=false")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AmiSandbox M2.4 disposable working-media helper")
    sub = parser.add_subparsers(dest="command", required=True)

    prep = sub.add_parser("prepare", help="copy immutable evidence into a per-session working image")
    prep.add_argument("source", help="original evidence image")
    prep.add_argument("--analysis-dir")
    prep.add_argument("--working-name")
    prep.add_argument("--force", action="store_true")
    prep.set_defaults(func=prepare)

    fin = sub.add_parser("finalize", help="hash source and working image and record mutation state")
    fin.add_argument("--analysis-dir")
    fin.set_defaults(func=finalize)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
