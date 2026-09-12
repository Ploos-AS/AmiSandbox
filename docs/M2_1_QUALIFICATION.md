# AmiSandbox M2.1 Qualification

Status: **PLANNED — implementation pending**

## Scope

M2.1 makes the `external_networking_enabled=false` analysis-session claim enforceable rather than metadata-only.

Analysis mode must default to no guest-to-external-network path. A sample must not gain external connectivity merely because an Amiberry configuration, command-line option, or inherited user preference enables a networking backend.

Any future network-enabled malware-analysis mode must require an explicit AmiSandbox analysis policy and must be isolated/captured separately; it is not part of M2.1.

## Design requirements

1. Analysis mode is fail-closed for external networking.
2. Network-related emulator configuration is inspected after configuration parsing but before guest execution.
3. If an external networking path is enabled, analysis startup must either force it off safely or reject startup before guest execution. Prefer rejection where silently rewriting configuration could be ambiguous.
4. Normal Amiberry mode remains unchanged.
5. `session.json` records `external_networking_enabled=false` only after enforcement has succeeded.
6. IPC used for AmiSandbox control is a local Unix-domain control channel and is not itself treated as guest external networking.
7. M2.1 must not claim host-level sandboxing; host namespace/firewall containment remains defense-in-depth outside this emulator-level invariant.

## Implementation discovery

Before changing emulator code, identify every Amiberry guest-network path and its effective preference fields/backends. Qualification must cover all paths compiled into the CI build rather than checking only one UI option.

Candidate areas include emulated BSD socket/network integrations and emulated Ethernet backends. Exact fields and enforcement point must be derived from the current Amiberry source before implementation.

## Static qualification

Add `tools/check_amisandbox_m2_1.py` once the enforcement fields and code path are known. The checker should verify the fail-closed network invariant and ensure metadata is not set to `false` before enforcement.

## Runtime qualification criteria

M2.1 is qualified when CI demonstrates all of the following:

1. Existing M1 through M2.0 qualification remains green.
2. Default analysis mode starts with all supported guest external-network paths disabled.
3. At least one deliberately network-enabled Amiberry configuration is rejected or neutralized before guest execution, with the expected deterministic result.
4. No analysis artifacts falsely claim networking is disabled when enforcement failed.
5. Normal Amiberry mode with the same network-capable build remains unaffected by the AmiSandbox analysis guard.
6. The effective network-isolation state is captured as qualification evidence.

## Security note

M2.1 is emulator-level network isolation. Running hostile samples should additionally use host/container/VM network controls so an emulator defect or future backend cannot silently become the only security boundary.

## Next

After M2.1 is qualified, proceed to **M2.2 — writable host-filesystem isolation**.
