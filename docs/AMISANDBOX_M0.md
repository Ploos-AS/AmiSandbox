# AmiSandbox M0

**AmiSandbox — Amiberry Malware Analysis Edition**

AmiSandbox is a malware-analysis-focused fork of Amiberry. The project keeps the upstream emulator as intact as practical while adding deterministic execution, instrumentation, event capture, artifact collection, and automation for Amiga malware and virus research.

## M0 goals

M0 establishes the project identity, security model, architecture, supported baseline machines, and the first implementation path. M0 intentionally avoids invasive emulator-core changes until the analysis interfaces are defined and testable.

## Design principles

- Preserve upstream Amiberry compatibility wherever practical.
- Keep AmiSandbox-specific code isolated behind explicit analysis-mode boundaries.
- Prefer deterministic and observable execution over maximum emulation speed.
- Disable JIT by default in analysis mode.
- Treat every sample as hostile.
- No writable host filesystem exposure by default.
- No external networking by default.
- Make analysis runs reproducible and machine-readable.
- Never require proprietary Kickstart ROMs to be committed to the repository.

## Initial machine profiles

The first supported analysis profiles are:

1. A500 / Kickstart 1.2
2. A500 / Kickstart 1.3
3. A500+ / Kickstart 2.04
4. A1200 / Kickstart 3.0
5. A1200 / Kickstart 3.1

Additional machines may be added after the instrumentation path is stable.

## Analysis session model

Each run should eventually produce a self-contained session directory containing, where applicable:

- session metadata
- emulator and AmiSandbox version
- machine profile and effective emulator configuration
- sample hashes and provenance metadata
- timestamped JSONL event stream
- CPU/register snapshots
- memory dumps
- disk/block-write events
- pre/post disk-image hashes
- screenshots
- network captures when explicitly enabled
- analyst notes and verdict metadata

## Planned event classes

The analysis layer is expected to grow support for events including:

- session start/stop
- CPU state and selected instruction tracing
- memory writes and watchpoints
- exception/vector-table changes
- Exec task/process/library/device activity
- LoadSeg/CreateProc and related executable-loading activity
- floppy and hard-disk I/O
- bootblock reads and writes
- custom-chip activity relevant to direct-hardware malware
- snapshots and artifact creation
- network activity when an isolated network backend is enabled

The emulator-level view is important because Amiga malware may bypass AmigaOS APIs and interact directly with memory, vectors, disks, or custom hardware.

## Isolation defaults

Analysis mode should default to:

- JIT disabled
- external networking disabled
- host directory mounts disabled or read-only unless explicitly requested
- disposable writable disk overlays
- explicit sample ingress path
- explicit artifact egress path
- no host clipboard integration where avoidable
- deterministic configuration recorded with the session

These controls are defense-in-depth. AmiSandbox must not claim that emulator sandboxing alone provides a complete security boundary against a malicious sample.

## Architecture direction

AmiSandbox should be divided conceptually into four layers:

1. **Amiberry core** — upstream emulation functionality.
2. **Instrumentation layer** — stable hooks for CPU, memory, disk, chipset and emulator state.
3. **Analysis session layer** — event normalization, metadata, snapshots and artifact collection.
4. **Controller/API layer** — automation for AmiGuard, AmiGuard Signature Workstation (ASW), AmiForensics and standalone analyst workflows.

AmiSandbox-specific implementation should be kept in clearly named modules/directories where possible instead of scattering unrelated changes throughout the emulator.

## Integration direction

Intended ecosystem flow:

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

AmiSandbox must also remain useful as a standalone dynamic-analysis workstation.

## Upstream policy

Amiberry remains the upstream emulator project. AmiSandbox should periodically merge or rebase appropriate upstream changes while minimizing divergence in generic emulation code.

Changes that are generally useful to Amiberry should be suitable for upstream submission when practical. Malware-analysis-specific behavior should remain AmiSandbox-specific unless upstream maintainers want the functionality.

## Licensing

AmiSandbox is derived from Amiberry and remains subject to the GNU General Public License v3.0 and all applicable upstream copyright notices.

## M0 completion criteria

M0 is complete when:

- the AmiSandbox project identity and purpose are documented;
- the initial machine profiles are defined;
- isolation defaults are documented;
- the event/session model is defined;
- the upstream maintenance policy is documented; and
- M1 has a concrete implementation target.

## M1 — first instrumentation slice

M1 will implement the smallest useful end-to-end analysis path:

- add a build/runtime boundary for AmiSandbox analysis support;
- introduce an analysis-session abstraction;
- write session metadata to an output directory;
- emit a versioned JSONL event stream;
- record deterministic machine/configuration metadata;
- expose initial CPU/register snapshot events;
- provide a minimal command-line or configuration switch to enable analysis mode;
- add tests/checks that keep normal Amiberry behavior unchanged when analysis mode is disabled.

The objective of M1 is not complete malware tracing. It is to prove that AmiSandbox can run Amiberry normally, enter an explicit analysis mode, and generate stable machine-readable evidence suitable for later instrumentation.
