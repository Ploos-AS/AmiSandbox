# AmiSandbox M2.6 qualification — guest-side removable-media mutation

Status: **IMPLEMENTED — guest runtime qualification pending**

## Goal

M2.6 strengthens M2.5 by proving that a write initiated by code running inside
the emulated Amiga can mutate only the disposable working image while the
original evidence image remains immutable.

M2.5 already qualifies launch integration, path isolation, fail-closed policy,
and mutation accounting. M2.6 adds the missing provenance guarantee: the disk
mutation must originate from the guest.

## Qualification boundary

A host-side mutation does not qualify for M2.6, even if all hashes and manifest
fields are otherwise correct.

The runtime qualification must execute a controlled guest-side disk write using
one explicitly identified mechanism, initially one of:

- direct `trackdisk.device` guest I/O,
- a guest filesystem write to DF0:, or
- a purpose-built guest program that writes a deterministic marker.

The selected mechanism must produce a machine-readable witness identifying:

- `schema_version=1`,
- `amisandbox_milestone=m2.6`,
- `mutation_origin=guest`,
- the guest write mechanism,
- the byte offset of the deterministic marker, and
- the marker bytes as hexadecimal.

The witness must be generated as part of the guest execution path. CI or host
helpers must not manufacture a guest witness after performing a host-side write.

## Evidence requirements

Qualification must prove all of the following:

1. An immutable source ADF is prepared through the M2.4/M2.5 full-copy flow.
2. AmiSandbox launches only the working copy with the M2.5 writable-media
   policy enabled.
3. A controlled guest-side disk write occurs.
4. The working image SHA-256 changes.
5. The source image SHA-256 remains identical to its initial value.
6. The deterministic marker is present at the expected location in the working
   image and absent at that location in the immutable source.
7. `media-manifest.json` finalizes with `working.mutated=true`.
8. `tools/amisandbox_guest_media_verify.py` accepts the manifest, witness,
   offset, and marker and reports PASS.
9. The default no-opt-in path remains M2.3 read-only.
10. Qualification evidence is uploaded.

## Verifier

`tools/amisandbox_guest_media_verify.py` is the M2.6 evidence verifier. It does
not write media. It fails closed unless the source stayed immutable, the working
copy changed, the deterministic marker is present only in the working copy, and
the supplied witness explicitly records a supported guest mutation mechanism.

This separation is intentional: the verifier can validate evidence, but the
runtime qualification must independently demonstrate that the witness came from
an actual guest-side disk write.

## Initial implementation status

The evidence verifier and static contract are implemented. The remaining M2.6
work is the guest execution harness and dedicated GitHub Actions runtime
qualification. M2.6 must remain pending until that workflow demonstrates a real
guest-originated write.
