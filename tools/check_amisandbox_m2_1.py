#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ethernet = (ROOT / "src" / "ethernet.cpp").read_text(encoding="utf-8")
options = (ROOT / "src" / "include" / "options.h").read_text(encoding="utf-8")
wrapper = (ROOT / "src" / "osdep" / "main.cpp").read_text(encoding="utf-8")
cfgfile = (ROOT / "src" / "cfgfile.cpp").read_text(encoding="utf-8")

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

required_bsdsocket = [
    'const bool analysis_mode = output_dir && *output_dir;',
    'if (analysis_mode)',
    '-cfgparam=bsdsocket_emu=false',
    'effective_argv.insert(effective_argv.begin() + 1, bsdsocket_override.data())',
    'AmiSandbox: forcing bsdsocket_emu=false in analysis mode',
    'metadata.amisandbox_version = "m2.1"',
    'metadata.external_networking_enabled = false',
    'amiberry_main(static_cast<int>(effective_argv.size()), effective_argv.data())',
]
for token in required_bsdsocket:
    if token not in wrapper:
        raise SystemExit(f"FAIL: bsdsocket isolation token missing: {token}")

for token in (
    '_T("bsdsocket_emu"), &p->socket_emu',
    'u->next = temp_lines;',
    'temp_lines = u;',
):
    if token not in cfgfile:
        raise SystemExit(f"FAIL: cfgparam precedence contract missing: {token}")

analysis_pos = wrapper.find('if (analysis_mode)')
override_pos = wrapper.find('-cfgparam=bsdsocket_emu=false')
insert_pos = wrapper.find('effective_argv.insert(', override_pos)
start_pos = wrapper.find('analysis.start(', analysis_pos)
emulator_pos = wrapper.find('amiberry_main(', start_pos)
if min(analysis_pos, override_pos, insert_pos, start_pos, emulator_pos) < 0 or not (
    analysis_pos < override_pos < insert_pos < start_pos < emulator_pos
):
    raise SystemExit('FAIL: authoritative bsdsocket override must be established before session/emulator start')

print('PASS: AmiSandbox M2.1 guest network fail-closed contract')
print('  Ethernet: SLIRP/TAP/PCAP blocked at ethernet_open')
print('  bsdsocket.library: authoritative bsdsocket_emu=false cfgparam in analysis mode')
