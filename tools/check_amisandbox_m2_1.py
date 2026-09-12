#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ethernet = (ROOT / "src" / "ethernet.cpp").read_text(encoding="utf-8")
options = (ROOT / "src" / "include" / "options.h").read_text(encoding="utf-8")

required_ethernet = [
    'AMISANDBOX_ANALYSIS_DIR',
    'static bool amisandbox_analysis_mode()',
    'if (amisandbox_analysis_mode())',
    'AmiSandbox: guest Ethernet blocked in analysis mode',
    'return 0;',
    'UAENET_SLIRP',
    'UAENET_SLIRP_INBOUND',
    'UAENET_PCAP',
    'UAENET_TAP',
]

for token in required_ethernet:
    if token not in ethernet:
        raise SystemExit(f"FAIL: ethernet isolation token missing: {token}")

for token in ('bool socket_emu;', 'bool sana2;'):
    if token not in options:
        raise SystemExit(f"FAIL: expected network preference missing: {token}")

open_pos = ethernet.find('int ethernet_open')
guard_pos = ethernet.find('if (amisandbox_analysis_mode())', open_pos)
switch_pos = ethernet.find('switch (ndd->type)', open_pos)
if min(open_pos, guard_pos, switch_pos) < 0 or not (open_pos < guard_pos < switch_pos):
    raise SystemExit('FAIL: analysis guard must run before any Ethernet backend switch/open')

print('PASS: AmiSandbox M2.1a guest Ethernet fail-closed contract')
print('NOTE: direct bsdsocket.library emulation remains M2.1b and M2.1 is not yet qualified')
