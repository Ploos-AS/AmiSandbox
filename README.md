# AmiSandbox

**Amiberry Malware Analysis Edition**

AmiSandbox is a malware-analysis-focused fork of [Amiberry](https://github.com/BlitterStudio/amiberry), designed for controlled dynamic analysis of Amiga malware, viruses, suspicious executables, bootblocks, disk images, and related artifacts.

The project keeps the upstream emulator as intact as practical while adding deterministic execution, instrumentation, event capture, artifact collection, and automation for malware research.

> AmiSandbox is an independent fork. Amiberry remains the upstream emulator project.

## Project status

AmiSandbox is under active early development.

Current milestone state:

- **M0 — complete:** project identity, security model, architecture, machine profiles, event/session model, upstream policy.
- **M1 — qualified:** opt-in analysis sessions, `session.json`, versioned JSONL event stream, lifecycle events, and preserved normal Amiberry behavior when analysis mode is disabled.
- **M1.1 — qualified:** live 68k D0-D7/A0-A7/PC/SR sampling through Amiberry IPC into `cpu-snapshots.jsonl`, including IPC readiness handling.
- **M1.2 — qualified:** first memory-observation slice using read-only IPC polling and versioned `memory.change` JSONL events.
- **M2.0 — qualified:** analysis mode fails closed for JIT-enabled builds while normal Amiberry mode remains unaffected.
- **M2.1 — qualified:** guest Ethernet backends are blocked in analysis mode and direct `bsdsocket.library` emulation is authoritatively forced off, while normal Amiberry mode remains unaffected.
- **M2.2 — next:** enforce no writable host-filesystem exposure by default in analysis mode.

M1/M1.1 runtime qualification passed in GitHub Actions run `34658255305` at commit `61b75ba1d87831691c5ce5e32b8e9744959af475`.

M1.2 runtime qualification passed in GitHub Actions run `34664928273` at commit `e024542961d75fd58e69d38d7803d723559243c1`.

M2.0 JIT-isolation qualification passed in GitHub Actions run `34671936080` (job `103494800457`) at commit `fb0248dcd041d503e2dc2343e1baec9608860f27`.

M2.1 network-isolation qualification passed in GitHub Actions run `34700520843` (job `103571342139`) at commit `7f92ef2ed711f2fe0a62d866db598926c4c4a0fc`.

See:

- [`docs/AMISANDBOX_M0.md`](docs/AMISANDBOX_M0.md)
- [`docs/M1_QUALIFICATION.md`](docs/M1_QUALIFICATION.md)
- [`docs/M1_1_QUALIFICATION.md`](docs/M1_1_QUALIFICATION.md)
- [`docs/M1_2_QUALIFICATION.md`](docs/M1_2_QUALIFICATION.md)
- [`docs/M2_0_QUALIFICATION.md`](docs/M2_0_QUALIFICATION.md)
- [`docs/M2_1_QUALIFICATION.md`](docs/M2_1_QUALIFICATION.md)

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
├── events.jsonl
├── cpu-snapshots.jsonl
└── memory-changes.jsonl
```

Normal Amiberry operation remains unchanged when `AMISANDBOX_ANALYSIS_DIR` is not set.

### Live CPU sampling (M1.1)

With IPC enabled, collect live 68k register snapshots from another terminal:

```bash
export AMISANDBOX_ANALYSIS_DIR="$PWD/analysis/session-001"
python3 tools/amisandbox_cpu_sampler.py --interval-ms 100
```

The sampler uses Amiberry's existing `GET_CPU_REGS` Unix-socket command. It waits for IPC readiness before starting sampling, which avoids a startup race where the Unix socket exists before the emulator event loop can service commands.

### Memory observation (M1.2)

The M1.2 watcher polls selected guest-memory locations through Amiberry's existing read-only `READ_MEM` IPC command and writes `memory.change` events when values change:

```bash
export AMISANDBOX_ANALYSIS_DIR="$PWD/analysis/session-001"
python3 tools/amisandbox_memory_watch.py --address 0x64 --address 0x68 --interval-ms 100
```

The default watch set covers the 68000 autovectors at `0x64` through `0x7c`. The watcher establishes a baseline first and emits events only when a watched value changes. This polling implementation is intentionally the first low-divergence memory-observation slice; it can miss transient writes that change and revert between polls.

## Upstream relationship

AmiSandbox follows Amiberry upstream and should minimize invasive divergence where practical. Analysis-specific code should remain clearly separated and reviewable so upstream updates can be incorporated without turning the fork into an unrelated emulator.

## License

AmiSandbox inherits Amiberry's GNU GPLv3 licensing. See [`LICENSE`](LICENSE).
