#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
wrapper = (ROOT / "src" / "osdep" / "main.cpp").read_text(encoding="utf-8")
options = (ROOT / "src" / "include" / "options.h").read_text(encoding="utf-8")
cfgfile = (ROOT / "src" / "cfgfile.cpp").read_text(encoding="utf-8")

for token in (
    'bool harddrive_read_only;',
    'bool readonly;',
    'struct uaedev_config_data mountconfig[MOUNT_CONFIG_SIZE];',
):
    if token not in options:
        raise SystemExit(f"FAIL: expected host-storage preference missing: {token}")

for token in (
    '_T("harddrive_write_protect"), p->harddrive_read_only',
    'u->next = temp_lines;',
    'temp_lines = u;',
):
    if token not in cfgfile:
        raise SystemExit(f"FAIL: harddrive/cfgparam contract missing: {token}")

required = [
    'const bool analysis_mode = output_dir && *output_dir;',
    'std::string storage_override;',
    '-cfgparam=harddrive_write_protect=true',
    'effective_argv.insert(effective_argv.begin() + 1, storage_override.data())',
    'AmiSandbox: forcing harddrive_write_protect=true in analysis mode',
]
for token in required:
    if token not in wrapper:
        raise SystemExit(f"FAIL: M2.2 host-storage isolation token missing: {token}")

analysis_pos = wrapper.find('if (analysis_mode)')
override_pos = wrapper.find('-cfgparam=harddrive_write_protect=true')
insert_pos = wrapper.find('effective_argv.insert(', override_pos)
start_pos = wrapper.find('analysis.start(', analysis_pos)
emulator_pos = wrapper.find('amiberry_main(', start_pos)
if min(analysis_pos, override_pos, insert_pos, start_pos, emulator_pos) < 0 or not (
    analysis_pos < override_pos < insert_pos < start_pos < emulator_pos
):
    raise SystemExit('FAIL: host-storage write-protect override must be authoritative before session/emulator start')

version_match = re.search(r'metadata\.amisandbox_version = "m(\d+)\.(\d+)"', wrapper)
if not version_match or tuple(map(int, version_match.groups())) < (2, 2):
    raise SystemExit('FAIL: AmiSandbox metadata has not reached M2.2')

print('PASS: AmiSandbox M2.2 host-backed drive read-only contract')
print('  harddrive_write_protect=true is authoritative in analysis mode')
print('  normal Amiberry argv is unchanged outside analysis mode')
