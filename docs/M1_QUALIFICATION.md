# AmiSandbox M1 Qualification

Status: **QUALIFIED — PASS**

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

## Qualification evidence

GitHub Actions runtime qualification passed on the `master` branch:

- workflow: `AmiSandbox Runtime Qualification`
- run: `34658255305`
- qualified commit: `61b75ba1d87831691c5ce5e32b8e9744959af475`
- job: `runtime-qual-m1-m1_1`
- conclusion: `success`

The run verified:

1. analysis build with `USE_JIT=OFF` and `USE_IPC_SOCKET=ON`;
2. M1 and M1.1 static contract checks;
3. runtime startup with the built-in AROS fallback ROM;
4. creation and validation of `session.json`;
5. `session.start` / `session.stop` lifecycle ordering;
6. clean emulator shutdown through IPC; and
7. a separate no-analysis smoke test with AmiSandbox analysis environment variables unset, proving that the opt-in boundary preserves normal Amiberry behavior.

Qualification evidence was uploaded by the workflow as `amisandbox-m1-m1_1-runtime-evidence`.

## Static qualification

Run:

```sh
python3 tools/check_amisandbox_m1.py
```

Expected:

```text
PASS: AmiSandbox M1 analysis-session contract
```

## Scope boundary

M1 proves the session, metadata, event-stream, opt-in runtime boundary and stable artifact generation. Live CPU sampling is qualified separately as M1.1.

M1 records the intended safe defaults (`jit_enabled=false`, `external_networking_enabled=false`) as analysis metadata. Enforcement of emulator preferences belongs to later isolation milestones and must not be inferred solely from metadata fields.

No proprietary Kickstart ROM is required for the automated qualification path; the GitHub Actions runtime qualification uses Amiberry's built-in AROS fallback ROM.

## Result

**PASS — M1 is runtime-qualified.**
