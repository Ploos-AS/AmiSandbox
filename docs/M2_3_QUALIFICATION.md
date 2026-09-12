# AmiSandbox M2.3 qualification — removable media isolation

Status: **IMPLEMENTED — runtime qualification pending**

M2.3 protects original floppy/removable disk images from guest writes during malware analysis.

## Policy

When `AMISANDBOX_ANALYSIS_DIR` is non-empty, AmiSandbox injects an authoritative
`-cfgparam=floppy_write_protect=true` before Amiberry startup. Because cfgparams are
prepended and applied after loaded configuration, this final override wins even if a
configuration or caller explicitly requests `floppy_write_protect=false`.

This complements M2.2 (`harddrive_write_protect=true`) for host-backed directories and
hardfiles. Normal Amiberry mode remains unchanged.

## Qualification criteria

1. M1 through M2.2 static contracts remain green.
2. `tools/check_amisandbox_m2_3.py` passes.
3. A non-JIT analysis build starts with an explicit hostile `floppy_write_protect=false` request.
4. Analysis startup logs the M2.3 forced write-protect policy.
5. Session metadata reports `amisandbox_version=m2.3` and retains JIT/network isolation metadata.
6. A supplied disposable test disk image has the same SHA-256 before and after the analysis run.
7. Normal Amiberry mode does not receive the analysis-only override.
8. Evidence is uploaded from the qualification workflow.

A future milestone may add copy-on-write working media for workflows that intentionally need to observe disk mutations while preserving the original evidence image.
