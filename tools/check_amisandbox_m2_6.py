#!/usr/bin/env python3
"""Static contract check for AmiSandbox M2.6 guest-side media evidence."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "tools" / "amisandbox_guest_media_verify.py"
DOC = ROOT / "docs" / "M2_6_QUALIFICATION.md"


def require(text: str, token: str, label: str) -> None:
    if token not in text:
        raise SystemExit(f"FAIL: {label}: missing {token!r}")


def main() -> int:
    verifier = VERIFY.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")

    for token, label in [
        ('"amisandbox_milestone") != "m2.6"', "M2.6 milestone witness check"),
        ('"mutation_origin") != "guest"', "guest-only origin requirement"),
        ('"trackdisk", "guest-filesystem", "guest-program"', "qualified guest mechanisms"),
        ("immutable source evidence changed", "source immutability failure"),
        ("working image is not recorded as mutated", "working mutation requirement"),
        ("expected guest marker not present in working image", "marker verification"),
        ("guest marker is also present in immutable source image", "source marker exclusion"),
        ("PASS: AmiSandbox M2.6 guest-side media mutation evidence verified", "PASS contract"),
    ]:
        require(verifier, token, label)

    for token, label in [
        ("Status: **IMPLEMENTED — guest runtime qualification pending**", "pending status"),
        ("host-side mutation does not qualify", "host-side exclusion"),
        ("guest-side disk write", "guest write target"),
        ("immutable source", "source evidence requirement"),
    ]:
        require(doc, token, label)

    print("PASS: AmiSandbox M2.6 guest media evidence contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
