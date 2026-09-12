# AmiSandbox M2.0 Qualification

Status: **QUALIFIED — PASS**

## Scope

M2.0 is the first enforced isolation control for AmiSandbox analysis mode.

When `AMISANDBOX_ANALYSIS_DIR` enables an analysis session, a binary compiled with JIT support must fail closed before creating analysis artifacts or entering the emulator. Normal Amiberry operation without analysis mode remains unchanged.

This converts the earlier `jit_enabled=false` metadata assumption into an enforceable launch invariant.

## Implementation

`src/osdep/main.cpp` checks the compile-time `JIT` configuration before starting an analysis session:

- analysis mode + JIT build: exit code `78`
- analysis mode + non-JIT build: allowed to continue
- normal mode: unaffected by this AmiSandbox guard

The session metadata identifies this implementation as `m2.0` and records `jit_enabled=false` only after the fail-closed guard has passed.

## Static qualification

Run:

```bash
python3 tools/check_amisandbox_m2_0.py
```

Expected:

```text
PASS: AmiSandbox M2.0 fail-closed JIT isolation contract
```

## Runtime qualification

GitHub Actions qualification passed:

- workflow: `AmiSandbox M2 Isolation Qualification`
- run: `34671936080`
- job: `103494800457`
- qualified head: `fb0248dcd041d503e2dc2343e1baec9608860f27`
- conclusion: **SUCCESS**

The run demonstrated:

1. Static M2.0 contract check PASS.
2. A `USE_JIT=ON` qualification binary built successfully.
3. Analysis mode rejected the JIT-enabled binary with exit code `78`.
4. Rejected analysis startup created neither `session.json` nor `events.jsonl`.
5. The same JIT-enabled binary remained launchable in normal Amiberry mode.
6. Normal-mode IPC readiness was proven with `GET_VERSION` before a clean `QUIT`, avoiding the socket-created-before-event-loop-ready race.
7. Qualification evidence upload PASS.

## Security note

M2.0 only enforces the JIT invariant. It does not yet prove network or host-filesystem isolation. Those controls are separate M2 slices and must be enforced and qualified independently before AmiSandbox is treated as ready for hostile malware samples.

## Next M2 slices

- **M2.1:** external networking fail-closed by default, explicit opt-in only through an analysis policy.
- **M2.2:** writable host-filesystem integration blocked by default; use disposable guest media/overlays instead.
- **M2.3:** disable or constrain other host integrations such as clipboard/shared paths where applicable.
- **M2.4:** record the effective enforced isolation policy in session metadata and qualify the combined profile.
