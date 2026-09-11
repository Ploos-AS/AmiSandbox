# AmiSandbox

**Amiberry Malware Analysis Edition**

AmiSandbox is a malware-analysis-focused fork of [Amiberry](https://github.com/BlitterStudio/amiberry), designed for controlled dynamic analysis of Amiga malware, viruses, suspicious executables, bootblocks, disk images, and related artifacts.

The project keeps the upstream emulator as intact as practical while adding deterministic execution, instrumentation, event capture, artifact collection, and automation for malware research.

> AmiSandbox is an independent fork. Amiberry remains the upstream emulator project.

## Project status

AmiSandbox is under active early development.

Current milestone state:

- **M0 — complete:** project identity, security model, architecture, machine profiles, event/session model, upstream policy.
- **M1 — implemented, qualification pending:** opt-in analysis sessions, `session.json`, versioned JSONL event stream, and CPU snapshot event format.
- **M1.1 — in progress:** live 68k CPU/register snapshot capture from the emulator execution path.

See:

- [`docs/AMISANDBOX_M0.md`](docs/AMISANDBOX_M0.md)
- [`docs/M1_QUALIFICATION.md`](docs/M1_QUALIFICATION.md)

## Goals

AmiSandbox aims to provide a reproducible dynamic-analysis environment for classic Amiga software, including malware that bypasses AmigaOS APIs and interacts directly with memory, exception vectors, disk hardware, or custom chips.

Planned analysis capabilities include:

- CPU/register snapshots and instruction tracing
- memory-write tracing and watchpoints
- exception/vector-table monitoring
- Exec task, process, library, and device activity
- executable loading activity such as `LoadSeg()` and `CreateProc()`
- floppy and hard-disk I/O tracing
- bootblock read/write detection
- pre/post disk-image hashing
- memory dumps and snapshots
- screenshots and other run artifacts
- isolated network capture when explicitly enabled
- machine-readable JSON/JSONL output for automation

## Security model

AmiSandbox treats every analyzed sample as hostile.

Analysis mode is intended to default to:

- JIT disabled
- external networking disabled
- no writable host filesystem exposure by default
- disposable writable disk overlays
- explicit sample ingress
- explicit artifact egress
- deterministic configuration recorded with each session

These controls are defense-in-depth. Emulator isolation alone must not be treated as a complete security boundary against malicious code.

## Initial analysis profiles

The initial target profiles are:

1. A500 / Kickstart 1.2
2. A500 / Kickstart 1.3
3. A500+ / Kickstart 2.04
4. A1200 / Kickstart 3.0
5. A1200 / Kickstart 3.1

Kickstart ROM images are not distributed with AmiSandbox.

## M1 analysis mode

M1 introduces an opt-in analysis session using environment variables.

```bash
export AMISANDBOX_ANALYSIS_DIR="$PWD/analysis/session-001"
export AMISANDBOX_MACHINE_PROFILE="a500-ks13"
export AMISANDBOX_CONFIG_FINGERPRINT="example"

./amiberry
```

When enabled, AmiSandbox creates analysis artifacts such as:

```text
analysis/session-001/
├── session.json
└── events.jsonl
```

Normal Amiberry operation remains unchanged when `AMISANDBOX_ANALYSIS_DIR` is not set.

## Event model

The JSONL event stream is versioned and designed to remain consumable by external analysis tooling.

Initial event classes include:

- `session.start`
- `session.stop`
- `cpu.snapshot`

Future milestones will add memory, disk, bootblock, process, library, chipset, snapshot, and network events.

## Intended ecosystem

```text
AmiGuard / analyst sample
          |
          v
AmiGuard Signature Workstation (ASW)
          |
          v
      AmiSandbox
          |
   dynamic artifacts
          |
          v
     AmiForensics
          |
          v
signatures / reports / research
```

AmiSandbox is also intended to remain useful as a standalone malware-analysis workstation.

## Building

AmiSandbox currently follows the upstream Amiberry build system.

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j$(nproc)
```

For analysis-oriented builds, JIT should be disabled:

```bash
cmake -B build-analysis \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DUSE_JIT=OFF
cmake --build build-analysis -j$(nproc)
```

Platform-specific build requirements remain largely the same as upstream Amiberry. See the [Amiberry build documentation](https://github.com/BlitterStudio/amiberry/wiki/Compile-from-source).

## Upstream relationship

AmiSandbox is derived from Amiberry, which in turn uses the WinUAE emulation core.

We aim to:

- keep AmiSandbox-specific code isolated where practical
- minimize unnecessary divergence from Amiberry
- periodically integrate appropriate upstream changes
- submit generally useful emulator fixes upstream when practical
- keep malware-analysis-specific behavior in AmiSandbox unless upstream wants it

Upstream project:

- [BlitterStudio/amiberry](https://github.com/BlitterStudio/amiberry)
- [amiberry.com](https://amiberry.com/)

## Contributing

Contributions are welcome, especially around:

- emulator instrumentation
- deterministic execution
- Amiga malware research
- forensic artifact formats
- safe sample handling
- automated qualification
- documentation and test coverage

Please keep generic emulator changes separable from AmiSandbox-specific analysis functionality whenever practical.

## License and attribution

AmiSandbox is derived from Amiberry and is distributed under the **GNU General Public License v3.0**. See [`LICENSE`](LICENSE).

Copyright and attribution notices from Amiberry, WinUAE, and other upstream components remain applicable to their respective code.

AmiSandbox additions are developed by the Ploos-AS project contributors.
