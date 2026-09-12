# AmiSandbox M2.0 Qualification

Status: **IMPLEMENTED — runtime qualification pending**

## Scope

M2.0 is the first enforced isolation control for AmiSandbox analysis mode.

When `AMISANDBOX_ANALYSIS_DIR` enables an analysis session, a binary compiled with JIT support must fail closed before creating analysis artifacts or entering the emulator. Normal Amiberry operation without analysis mode remains unchanged.

This converts the earlier `jit_enabled=false` metadata assumption into an enforceable launch invariant.

## Implementation

`src/osdep/main.cpp` now checks the compile-time `JIT` configuration before starting an analysis session:

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

## Runtime qualification criteria

M2.0 is qualified when CI demonstrates all of the following:

1. Existing M1/M1.1/M1.2 qualification remains green in a `USE_JIT=OFF` analysis build.
2. The non-JIT build creates a normal analysis session and records `jit_enabled=false`.
3. A JIT-enabled build started with `AMISANDBOX_ANALYSIS_DIR` exits with code `78` before emulator execution.
4. The rejected JIT analysis launch does not create `session.json` or `events.jsonl`.
5. Normal Amiberry mode remains launchable independently of the analysis-mode guard.

## Security note

M2.0 only enforces the JIT invariant. It does not yet prove network or host-filesystem isolation. Those controls are separate M2 slices and must be enforced and qualified independently before AmiSandbox is treated as ready for hostile malware samples.

## Next M2 slices

- **M2.1:** external networking fail-closed by default, explicit opt-in only through an analysis policy.
- **M2.2:** writable host-filesystem integration blocked by default; use disposable guest media/overlays instead.
- **M2.3:** disable or constrain other host integrations such as clipboard/shared paths where applicable.
- **M2.4:** record the effective enforced isolation policy in session metadata and qualify the combined profile.
