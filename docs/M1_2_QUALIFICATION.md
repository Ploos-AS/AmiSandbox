# AmiSandbox M1.2 Qualification

Status: **QUALIFIED — PASS**

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

## Runtime qualification

M1.2 passed on GitHub Actions:

- workflow run: `34664928273`
- job: `103474806893`
- qualified commit: `e024542961d75fd58e69d38d7803d723559243c1`
- result: **SUCCESS**

The qualification demonstrated:

1. M1 and M1.1 remained green.
2. AmiSandbox built with `USE_JIT=OFF` and `USE_IPC_SOCKET=ON`.
3. The watcher reached IPC readiness and established its baseline.
4. A controlled write to one watched address produced exactly one corresponding `memory.change` event.
5. The event contained the expected address, width, old value, and new value.
6. A second unchanged watched address produced no event.
7. Two watched addresses were observed in the same run.
8. The controlled mutation was restored and verified.
9. The guest resumed and exited cleanly.
10. The no-analysis normal-mode smoke test remained green.

The qualification uses writable Slow RAM near `0x00c7fff0`. Earlier attempts at low Chip RAM were affected by the AROS fallback ROM overlay: reads succeeded while writes were effectively blocked by the overlay. The qualification therefore intentionally uses a writable RAM bank rather than treating an IPC `OK` response alone as proof of mutation.

A qualification test may use Amiberry's existing `WRITE_MEM` IPC command solely to inject a deterministic test mutation. Production analysis remains observational unless the analyst explicitly requests mutation through the emulator control interface.

## Security and fidelity notes

- M1.2 is read-only during normal observation.
- Polling can miss a write that is changed back before the next read; later milestones may add inline write hooks or debugger watchpoints where higher fidelity is required.
- The default addresses are architectural 68000 autovectors, not AmigaOS API hooks.
- The IPC socket is a host-side control interface and must not be exposed to an untrusted network.
- External networking remains disabled by policy for malware-analysis runs.

## Next direction

M2 begins **analysis isolation enforcement**. The first slice is fail-closed JIT enforcement: an analysis session must not start in a binary compiled with JIT support enabled. Later M2 slices will enforce network and host-filesystem isolation rather than merely documenting those policies.
