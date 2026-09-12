# AmiSandbox M2.4 — Disposable working media

Status: **IMPLEMENTED — qualification pending**

M2.4 adds an explicit per-session working-media path for malware analysis where the original evidence image remains immutable while a disposable copy may be modified.

## Security model

- The supplied source image is evidence and must never be mounted writable by the M2.4 helper.
- `tools/amisandbox_media_prepare.py prepare` hashes the source and creates a full copy under `<analysis-dir>/media/`.
- This milestone implements **full-copy disposable media**, not block-level copy-on-write.
- The working copy is the only image intended for writable analysis.
- `finalize` re-hashes both source and working image.
- Finalization fails closed if the source evidence hash changed.
- The media manifest records initial/final working SHA-256 and a `mutated` verdict.

## Artifacts

`<analysis-dir>/media/media-manifest.json` records:

- schema version
- milestone `m2.4`
- copy strategy `full-copy`
- source path, size, initial SHA-256 and final SHA-256
- working path, initial/final size and SHA-256
- whether the working copy mutated
- the expectation that the source remains immutable

## Qualification criteria

The dedicated GitHub Actions qualification must prove:

1. M1 through M2.4 static contracts pass.
2. A disposable ADF-sized evidence image is prepared.
3. The working copy initially has the same SHA-256 as the original.
4. A controlled write changes only the working copy.
5. `finalize` reports `mutated=true`.
6. The original image SHA-256 is unchanged.
7. The manifest records identical source initial/final hashes and different working initial/final hashes.
8. A second no-mutation case reports `mutated=false`.
9. Qualification evidence is uploaded.

This milestone qualifies the media preparation/evidence boundary. Guest-side automatic mounting of the writable working copy is a later integration step and must not be implied by this qualification.
