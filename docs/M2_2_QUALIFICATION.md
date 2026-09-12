# AmiSandbox M2.2 Qualification — Host Filesystem Isolation

Status: **IMPLEMENTED — runtime qualification pending**

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
6. Runtime qualification must exercise at least one writable host-backed directory or hardfile request and prove the guest cannot persist a write to the backing host object.

## Static qualification

Run:

```sh
python3 tools/check_amisandbox_m2_2.py
```

Expected:

```text
PASS: AmiSandbox M2.2 host-backed drive read-only contract
```

## Runtime qualification target

The dedicated M2.2 workflow must:

1. build a non-JIT analysis binary;
2. launch analysis mode with a deliberately hostile `harddrive_write_protect=false` request;
3. confirm the M2.2 override is active before guest execution;
4. mount a disposable host-backed test object requested as writable;
5. attempt a deterministic guest-side write;
6. prove the backing host object is unchanged;
7. launch the same build outside analysis mode and prove the analysis-only override is absent;
8. upload logs and test artifacts.

Until the guest-side persistence test passes, M2.2 remains **implemented, not qualified**.
