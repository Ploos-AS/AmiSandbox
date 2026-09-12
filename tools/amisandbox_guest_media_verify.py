#!/usr/bin/env python3
"""Verify an AmiSandbox M2.6 guest-side removable-media mutation.

This verifier intentionally does not perform the mutation. It consumes the M2.4/
M2.5 media manifest plus a guest-produced witness file and verifies that:

- immutable source evidence stayed byte-identical,
- the disposable working copy changed,
- the expected marker exists in the working image,
- the same marker is absent at that location in the source image, and
- the witness identifies the mutation as guest-executed.

The actual guest execution mechanism is qualified separately by the M2.6 runtime
workflow; host-side writes must never be used to create the witness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="verify AmiSandbox M2.6 guest media mutation evidence")
    p.add_argument("--analysis-dir", required=True)
    p.add_argument("--witness", required=True, help="guest-produced JSON witness")
    p.add_argument("--offset", required=True, type=lambda value: int(value, 0))
    p.add_argument("--marker-hex", required=True)
    return p


def main() -> int:
    args = parser().parse_args()
    analysis = Path(args.analysis_dir).expanduser().resolve()
    manifest_path = analysis / "media" / "media-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    witness = json.loads(Path(args.witness).read_text(encoding="utf-8"))

    if witness.get("schema_version") != 1:
        raise SystemExit("invalid M2.6 witness schema")
    if witness.get("amisandbox_milestone") != "m2.6":
        raise SystemExit("witness is not for AmiSandbox M2.6")
    if witness.get("mutation_origin") != "guest":
        raise SystemExit("M2.6 requires mutation_origin=guest")
    if witness.get("mechanism") not in {"trackdisk", "guest-filesystem", "guest-program"}:
        raise SystemExit("unsupported or unqualified guest mutation mechanism")

    source = Path(manifest["source"]["path"]).resolve()
    working = Path(manifest["working"]["path"]).resolve()
    marker = bytes.fromhex(args.marker_hex)
    if not marker:
        raise SystemExit("marker must not be empty")

    source_initial = manifest["source"]["sha256_initial"]
    source_final = manifest["source"].get("sha256_final")
    working_initial = manifest["working"]["sha256_initial"]
    working_final = manifest["working"].get("sha256_final")

    if source_final != source_initial or sha256(source) != source_initial:
        raise SystemExit("immutable source evidence changed")
    if not manifest["working"].get("mutated"):
        raise SystemExit("working image is not recorded as mutated")
    if not working_final or working_final == working_initial:
        raise SystemExit("working image hash did not change")
    if sha256(working) != working_final:
        raise SystemExit("working image final hash does not match manifest")

    with source.open("rb") as src, working.open("rb") as wrk:
        src.seek(args.offset)
        wrk.seek(args.offset)
        source_bytes = src.read(len(marker))
        working_bytes = wrk.read(len(marker))

    if working_bytes != marker:
        raise SystemExit("expected guest marker not present in working image")
    if source_bytes == marker:
        raise SystemExit("guest marker is also present in immutable source image")

    if int(witness.get("offset", -1)) != args.offset:
        raise SystemExit("witness offset does not match verified offset")
    if witness.get("marker_hex", "").lower() != args.marker_hex.lower():
        raise SystemExit("witness marker does not match verified marker")

    print("PASS: AmiSandbox M2.6 guest-side media mutation evidence verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
