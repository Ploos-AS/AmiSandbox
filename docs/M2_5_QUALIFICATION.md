# AmiSandbox M2.5 qualification — disposable media launch integration

Status: **IMPLEMENTED — runtime qualification pending**

## Goal

M2.5 integrates M2.4 full-copy disposable media with the AmiSandbox runtime.
Writable removable media in analysis mode is allowed only when the mounted
`floppy0` image resolves to a regular file below the active session's
`<analysis-dir>/media/` tree.

The immutable source evidence image is never passed to Amiberry by the M2.5
launcher. The launcher prepares a working copy, mounts that copy, enables the
explicit writable-media policy, waits for emulator exit, and finalizes hashes
and mutation state in `media/media-manifest.json`.

## Fail-closed policy

Analysis mode keeps the M2.3 read-only default unless all of these are true:

1. `AMISANDBOX_WRITABLE_MEDIA_COPY=1` is explicitly set.
2. `floppy0` is supplied.
3. The supplied path resolves to an existing regular file.
4. The canonical path is strictly below `<analysis-dir>/media/`.

An explicit writable opt-in that fails validation exits with configuration
status 78 rather than falling back to writable media.

## Qualification criteria

The dedicated GitHub Actions qualification must prove:

- M1 through M2.5 static contract checks pass.
- A non-JIT AmiSandbox binary builds with IPC enabled.
- `tools/amisandbox_launch.py` creates a session working copy from an original
  ADF and starts analysis mode using only that working-copy path.
- Runtime logs contain the M2.5 writable-disposable-media diagnostic.
- `session.json` reports `amisandbox_version=m2.5`, JIT disabled, and external
  networking disabled.
- The working copy may change during the session while the source SHA-256 stays
  identical.
- Finalization records `mutated=true` for the changed working copy.
- A hostile direct opt-in that points `floppy0` outside `<analysis-dir>/media/`
  is rejected with exit code 78.
- Normal M2.3 behavior remains fail-closed read-only when no writable-copy
  opt-in is present.
- Qualification evidence is uploaded.

## Scope note

M2.5 is runtime integration of a **full-copy disposable image**, not block-level
copy-on-write. The initial CI qualification may mutate the working copy from the
host side while Amiberry is running to prove lifecycle, path isolation, source
immutability, and final mutation accounting. That does **not** by itself prove a
guest-side disk write path. A later qualification may add a controlled Amiga
guest write operation.
