# AmiSandbox M1.1 Qualification

## Scope

M1.1 adds live 68k CPU/register sampling to the M1 analysis-session foundation without patching Amiberry's generated CPU execution loops.

The sampler uses Amiberry's existing Unix-domain IPC command `GET_CPU_REGS` and writes normalized AmiSandbox `cpu.snapshot` events to a separate JSONL stream.

## Implementation

- `tools/amisandbox_cpu_sampler.py`
- `tools/check_amisandbox_m1_1.py`
- output: `cpu-snapshots.jsonl`
- source marker: `amiberry-ipc`
- schema version: `1`

Each snapshot records:

- D0-D7
- A0-A7
- PC
- SR
- USP/ISP when supplied by Amiberry
- decoded T/S/X/N/Z/V/C flags when supplied
- host monotonic timestamp

M1.1 deliberately does not append to the emulator-owned `events.jsonl`. Keeping the sampler stream separate avoids concurrent writers and lets later milestones merge streams deterministically.

The sampler also performs an IPC readiness probe before the first CPU request. This avoids treating socket creation alone as proof that Amiberry's event loop is ready to service IPC commands.

## Build

For the first qualification, use a non-JIT build with IPC enabled:

```bash
cmake -B build-m1_1 \
  -DCMAKE_BUILD_TYPE=Release \
  -DUSE_JIT=OFF \
  -DUSE_IPC_SOCKET=ON
cmake --build build-m1_1 -j"$(nproc)"
```

Run the static contract check:

```bash
python3 tools/check_amisandbox_m1.py
python3 tools/check_amisandbox_m1_1.py
```

Both must report `PASS`.

## Runtime usage

Create a disposable output directory and launch AmiSandbox with a known analysis profile:

```bash
rm -rf /tmp/amisandbox-m1_1
mkdir -p /tmp/amisandbox-m1_1

export AMISANDBOX_ANALYSIS_DIR=/tmp/amisandbox-m1_1
export AMISANDBOX_MACHINE_PROFILE=a500-ks13
export AMISANDBOX_CONFIG_FINGERPRINT=m1_1-local

./build-m1_1/amiberry <normal Amiberry arguments>
```

Amiberry chooses its IPC socket as follows:

- `$XDG_RUNTIME_DIR/amiberry.sock` when `XDG_RUNTIME_DIR` exists;
- otherwise `/tmp/amiberry.sock`;
- additional instances use `_1` through `_9` before `.sock`.

In another terminal, collect ten samples at 100 ms intervals:

```bash
export AMISANDBOX_ANALYSIS_DIR=/tmp/amisandbox-m1_1
python3 tools/amisandbox_cpu_sampler.py --count 10 --interval-ms 100
```

## Required evidence

Qualification passes when all of the following are true:

1. AmiSandbox/Amiberry starts normally with `USE_JIT=OFF` and `USE_IPC_SOCKET=ON`.
2. `session.json` is created by the M1 runtime boundary.
3. `events.jsonl` contains `session.start` and later `session.stop`.
4. `cpu-snapshots.jsonl` is created by the M1.1 sampler.
5. At least 10 valid `cpu.snapshot` records are present.
6. Every snapshot contains exactly 8 D registers and 8 A registers plus PC and SR.
7. At least one register or PC value changes while the guest executes.
8. Stopping the sampler does not stop or destabilize emulation.
9. Running without `AMISANDBOX_ANALYSIS_DIR` leaves normal Amiberry behavior unchanged.

## Qualification evidence

GitHub Actions runtime qualification passed on the `master` branch:

- workflow: `AmiSandbox Runtime Qualification`
- run: `34658255305`
- qualified commit: `61b75ba1d87831691c5ce5e32b8e9744959af475`
- job: `runtime-qual-m1-m1_1`
- conclusion: `success`

The workflow verified all nine criteria above, including live CPU-state changes and a separate no-analysis normal-mode smoke test. Qualification evidence was uploaded as `amisandbox-m1-m1_1-runtime-evidence`.

## Security and determinism notes

- M1.1 only observes CPU state; it does not yet instrument memory writes or disk I/O.
- `USE_JIT=OFF` is required for the initial qualification profile even though IPC register reads can technically work with other builds.
- External networking remains disabled by policy for malware-analysis runs.
- Samples should run on disposable disk images or overlays.
- The Unix socket is a host control surface and must not be exposed outside the analysis host.

## Status

**PASS — M1.1 is runtime-qualified.**

A later milestone may add an inline interpreter hook if IPC sampling proves too coarse for a particular malware-analysis workload. That decision should be evidence-driven because directly patching hot CPU execution paths increases upstream divergence and performance risk.
