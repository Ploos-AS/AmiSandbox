# AmiSandbox M1.2 Qualification

Status: **IMPLEMENTED — runtime qualification pending**

## Scope

M1.2 adds the first memory-observation capability without patching Amiberry's hot memory-write paths.

It uses the existing read-only IPC command `READ_MEM` to establish a baseline for selected addresses and emits a `memory.change` event whenever a watched value changes.

The default watch set is the 68000 autovector area for vectors 25-31 (`0x64` through `0x7c`, four-byte aligned). Analysts can override or extend this with repeated `--address` arguments.

This is intentionally a first slice. It is not yet complete write tracing and it does not claim to observe every transient write between polling intervals.

## Implementation

- `tools/amisandbox_memory_watch.py`
- `tools/check_amisandbox_m1_2.py`
- output: `memory-changes.jsonl`
- event type: `memory.change`
- source: `amiberry-ipc`
- schema version: `1`

Each change event contains:

- address
- width
- old value
- new value
- host monotonic timestamp
- monotonically increasing event sequence

## Usage

With AmiSandbox running in analysis mode:

```bash
export AMISANDBOX_ANALYSIS_DIR=/tmp/amisandbox-m1_2
python3 tools/amisandbox_memory_watch.py
```

Watch explicit locations:

```bash
python3 tools/amisandbox_memory_watch.py \
  --address 0x64 \
  --address 0x68 \
  --address 0x6c \
  --interval-ms 50
```

The watcher waits for real IPC readiness using `GET_VERSION` before establishing its baseline, avoiding the socket-created-before-event-loop-ready race found during M1.1 qualification.

## Static qualification

Run:

```bash
python3 tools/check_amisandbox_m1.py
python3 tools/check_amisandbox_m1_1.py
python3 tools/check_amisandbox_m1_2.py
```

Expected M1.2 result:

```text
PASS: AmiSandbox M1.2 memory observation contract
```

## Runtime qualification criteria

M1.2 passes when all of the following are demonstrated on the GitHub runner or equivalent disposable runtime:

1. M1 and M1.1 remain green.
2. AmiSandbox starts with `USE_JIT=OFF` and `USE_IPC_SOCKET=ON`.
3. The watcher reaches IPC readiness and records its baseline without errors.
4. A controlled write to one watched address causes exactly one corresponding `memory.change` event.
5. The event contains the expected address, width, old value, and new value.
6. An unchanged watched value produces no event.
7. At least two watched addresses can be observed in the same run.
8. Stopping the watcher does not destabilize or stop emulation.
9. The no-analysis normal-mode smoke test continues to pass.

A qualification test may use Amiberry's existing `WRITE_MEM` IPC command solely to inject a deterministic test mutation. Production analysis remains observational unless the analyst explicitly requests mutation through the emulator control interface.

## Security and fidelity notes

- M1.2 is read-only during normal observation.
- Polling can miss a write that is changed back before the next read; later milestones may add inline write hooks or debugger watchpoints where higher fidelity is required.
- The default addresses are architectural 68000 autovectors, not AmigaOS API hooks.
- The IPC socket is a host-side control interface and must not be exposed to an untrusted network.
- External networking remains disabled by policy for malware-analysis runs.

## Next direction

After M1.2 qualification, the next instrumentation decision should be evidence-driven: either expand selected memory/vector monitoring, add higher-fidelity memory-write hooks, or begin disk/bootblock observation depending on which capability produces the most useful malware evidence with the least upstream divergence.
