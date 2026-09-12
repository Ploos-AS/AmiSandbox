# AmiSandbox M2.2 Qualification — Host Filesystem Isolation

Status: **QUALIFIED — PASS**

## Goal

AmiSandbox analysis mode must not give an untrusted Amiga guest writable access to host-backed directory filesystems or hardfiles by default.

M2.2 uses Amiberry's existing global `harddrive_write_protect` preference. In analysis mode the wrapper injects an authoritative cfgparam:

```text
-cfgparam=harddrive_write_protect=true
```

Amiberry stores this preference as `uae_prefs::harddrive_read_only`. The override is inserted using the same cfgparam-precedence mechanism qualified in M2.1, so a caller-provided `harddrive_write_protect=false` cannot silently win.

## Scope

M2.2 covers host-backed directory filesystems and hardfiles governed by Amiberry's hard-drive write-protect policy. It does not claim immutable host containment by itself; OS-level sandboxing, namespaces, permissions, disposable images and copy-on-write layers remain defense in depth.

Floppy/media-specific write protection and analysis-output directories are separate surfaces and must not be inferred from this milestone unless explicitly qualified.

## Required properties

1. Analysis mode injects `harddrive_write_protect=true` before Amiberry processes effective configuration.
2. A hostile config/CLI request for `harddrive_write_protect=false` is overridden.
3. Session metadata is not emitted as M2.2 until the override has been established.
4. Normal Amiberry mode remains unchanged.
5. M1 through M2.1 contracts remain green.
6. Runtime qualification exercises a writable host-backed directory request and proves the backing host object remains unchanged.

## Static qualification

Run:

```sh
python3 tools/check_amisandbox_m2_2.py
```

Expected:

```text
PASS: AmiSandbox M2.2 host-backed drive read-only contract
```

## Runtime qualification

GitHub Actions workflow:

```text
.github/workflows/amisandbox-m2_2-qual.yml
```

Qualified in:

- Run: `34702386265`
- Job: `103576333288`
- Head: `d7ce25773741ae24ab312371e4bd73501bfb0b4e`
- Evidence artifact: `10300945496`
- Evidence artifact SHA-256: `46bf10f6bfb4bc520ef07e9dc4495e45b6e55ff38cc2cd684950beb21e09a69a`

The successful qualification run proved:

1. M1 through M2.2 static contracts pass.
2. The non-JIT analysis build completes successfully (`499/499`).
3. Analysis mode was deliberately launched with `harddrive_write_protect=false`.
4. A disposable host directory was deliberately requested through `filesystem2=rw,...`.
5. AmiSandbox logged `AmiSandbox: forcing harddrive_write_protect=true in analysis mode`.
6. The configured host-backed path appeared in the emulator log, proving the hostile mount request was processed by the emulator configuration.
7. No `guest-write-marker.txt` persisted in the backing host directory.
8. Pre-recorded SHA-256 hashes for the baseline file and test `S/Startup-Sequence` remained unchanged after the analysis run.
9. Session metadata reported `amisandbox_version=m2.2`, JIT disabled, and external networking disabled.
10. The same binary started normally outside analysis mode without the M2.2 override diagnostic and accepted a clean IPC `QUIT`.
11. Qualification evidence was uploaded successfully.

Representative runtime output:

```text
PASS: AmiSandbox M2.2 host-backed drive read-only contract
AmiSandbox: forcing harddrive_write_protect=true in analysis mode
PASS: hostile rw host mount remained unchanged under M2.2 analysis policy
PASS: M2.2 analysis run left host backing object unchanged
PASS: normal mode remains unaffected by M2.2 analysis-only override
```

## Qualification boundary

This qualification proves the fail-closed host-backed-drive policy and verifies that the backing object remains unchanged despite a hostile writable mount request.

The CI profile does not independently provide a deterministic witness that the guest actually reached and executed the `Echo >DH0:` statement in the disposable `S/Startup-Sequence`. Therefore M2.2 does **not** claim that specific guest instruction execution as independently observed evidence.

A follow-up hardening slice, **M2.2.1**, should add a deterministic guest-side write-attempt witness while retaining the host-side immutability checks.

## Verdict

**PASS — M2.2 host-filesystem isolation is runtime-qualified.**
