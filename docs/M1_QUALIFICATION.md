# AmiSandbox M1 Qualification

Status: **IMPLEMENTED — runtime qualification pending**

M1 establishes the first end-to-end AmiSandbox analysis boundary without changing normal Amiberry behavior when analysis mode is not requested.

## Implemented

- `src/amisandbox/analysis_session.h` defines the versioned analysis-session API.
- `src/amisandbox/analysis_session.cpp` writes `session.json` and `events.jsonl`.
- JSONL schema version starts at `1`.
- Session lifecycle events: `session.start` and `session.stop`.
- CPU/register snapshot event model: `cpu.snapshot`, with D0-D7, A0-A7, PC, SR and emulated-cycle counter.
- Runtime opt-in boundary: `AMISANDBOX_ANALYSIS_DIR`.
- Optional deterministic metadata inputs: `AMISANDBOX_MACHINE_PROFILE` and `AMISANDBOX_CONFIG_FINGERPRINT`.
- Analysis output setup failure terminates before the guest starts.
- With `AMISANDBOX_ANALYSIS_DIR` unset, the entry point calls upstream `amiberry_main()` without starting an analysis session.
- `tools/check_amisandbox_m1.py` pins the static M1 contract.

## Runtime usage

Example:

```sh
AMISANDBOX_ANALYSIS_DIR=/tmp/amisandbox-session \
AMISANDBOX_MACHINE_PROFILE=a500-ks13 \
AMISANDBOX_CONFIG_FINGERPRINT=test-m1 \
./amiberry
```

Expected artifacts:

```text
/tmp/amisandbox-session/
  session.json
  events.jsonl
```

`events.jsonl` must begin with a `session.start` event and end with `session.stop` after a normal emulator exit.

## Important M1 limitation

M1 defines and implements the CPU snapshot event representation, but does **not yet hook it into the 68k execution loop**. That hook is intentionally deferred to M1.1 so the first core modification can be reviewed and qualified separately. M1 therefore proves the session, metadata, event-stream, and opt-in runtime boundary first.

M1 also records the intended safe defaults (`jit_enabled=false`, `external_networking_enabled=false`) as analysis metadata. Enforcement of those emulator preferences belongs to the next isolation milestone and must not be inferred solely from the metadata fields.

## Static qualification

Run:

```sh
python3 tools/check_amisandbox_m1.py
```

Expected:

```text
PASS: AmiSandbox M1 analysis-session contract
```

## Build/runtime qualification still required

Before marking M1 fully qualified:

1. Configure and build the normal Amiberry target.
2. Run `tools/check_amisandbox_m1.py`.
3. Launch once with `AMISANDBOX_ANALYSIS_DIR` unset and verify normal behavior.
4. Launch once with the environment variables above.
5. Verify valid JSON in `session.json` and every line of `events.jsonl`.
6. Verify session start/stop ordering and monotonically increasing sequence values.

No proprietary Kickstart ROM is required for the static contract check. Guest runtime qualification may use a legally supplied ROM or an appropriate open replacement.

## Next: M1.1

M1.1 should add the first narrow emulator-core hook: capture an explicit CPU/register snapshot at a deterministic lifecycle point, then qualify that hook on a 68000 profile with JIT disabled.
