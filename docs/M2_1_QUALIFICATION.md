# AmiSandbox M2.1 Qualification

Status: **QUALIFIED — PASS**

## Scope

M2.1 makes the `external_networking_enabled=false` analysis-session claim enforceable rather than metadata-only.

Analysis mode defaults to no guest-to-external-network path. A sample cannot gain external connectivity merely because an Amiberry configuration, command-line option, or inherited user preference enables a supported networking backend.

Any future network-enabled malware-analysis mode must require an explicit AmiSandbox analysis policy and must be isolated/captured separately; it is not part of M2.1.

## Implemented isolation

M2.1 covers the two guest-network paths identified in the current Amiberry source.

### M2.1a — emulated Ethernet

`src/ethernet.cpp` blocks `ethernet_open()` whenever `AMISANDBOX_ANALYSIS_DIR` is non-empty. This common activation point covers the compiled SLIRP, TAP and PCAP guest Ethernet backends before they open a host networking backend.

Implementation commit: `30db098698120d917ef82bc351a59bb4c2c3cdcd`.

### M2.1b — direct bsdsocket.library emulation

Amiberry maps configuration key `bsdsocket_emu` to `uae_prefs::socket_emu`, and `bsdsocket.library` startup depends on that preference.

For analysis launches, `src/osdep/main.cpp` injects an authoritative `-cfgparam=bsdsocket_emu=false` before entering Amiberry. `cfgfile_addcfgparam()` prepends entries internally, so inserting the AmiSandbox override as the first command-line cfgparam causes it to be applied last after the loaded configuration and caller-provided cfgparams. A caller requesting `bsdsocket_emu=true` therefore cannot override the analysis invariant.

The override is added only when `AMISANDBOX_ANALYSIS_DIR` is non-empty; normal Amiberry mode is unchanged.

Implementation commits:

- `5debf42a011f871523a440746bd06f48ed4e3100` — initial M2.1b wrapper enforcement.
- `e5a5865a15e60c730bde5588169f42dcc6449381` — authoritative cfgparam ordering fix.

Analysis-session metadata is now versioned as `m2.1`, and `external_networking_enabled=false` is emitted only for launches where both M2.1 controls are active.

## Static qualification

`tools/check_amisandbox_m2_1.py` verifies:

1. the analysis guard runs before the Ethernet backend switch/open;
2. SLIRP, TAP and PCAP coverage remains present;
3. `socket_emu` and `sana2` remain recognized network preferences;
4. Amiberry still maps `bsdsocket_emu` to `socket_emu`;
5. cfgparam list semantics still prepend entries;
6. the authoritative `bsdsocket_emu=false` override is installed before analysis-session/emulator startup;
7. M2.1 metadata records external networking disabled only after the enforcement setup is established.

Static checker commits:

- `1f1309dae61000664795c1b9eb5b68749d553e42`
- `6572b203a3f26e3febe2cbdc1ef13b00f5504d97`

The M2.0 regression checker was also made milestone-version-independent while continuing to require its JIT fail-closed invariant: `17232aecf6868b285694b9497e3361a78c366c08`.

## Runtime qualification

Dedicated workflow: `.github/workflows/amisandbox-m2_1-qual.yml`.

Qualified GitHub Actions run:

- Run: `34700520843`
- Job: `103571342139`
- Qualified head: `7f92ef2ed711f2fe0a62d866db598926c4c4a0fc`
- Result: **SUCCESS**

The successful run demonstrated:

1. M1, M1.1, M1.2, M2.0 and M2.1 static contracts all PASS.
2. A full non-JIT, IPC-enabled Amiberry qualification build PASS.
3. Analysis mode was deliberately launched with caller-supplied `-cfgparam=bsdsocket_emu=true`.
4. AmiSandbox installed its mandatory `bsdsocket_emu=false` override and the analysis launch completed without `bsdsocket.library installed` appearing in the evidence log.
5. `session.json` reported `amisandbox_version=m2.1` and `external_networking_enabled=false`.
6. The emulator became IPC-ready and accepted a clean `QUIT`.
7. A normal-mode launch using the same network-capable binary and caller-supplied `bsdsocket_emu=true` did not receive the AmiSandbox analysis override and remained operational.
8. Qualification evidence upload PASS.

The first dedicated run, `34700415750`, failed only because the older M2.0 static checker required the literal milestone string `m2.0`; no build or runtime network test had run. The regression checker was corrected to test the M2.0 JIT invariant rather than freeze the metadata milestone string, after which run `34700520843` passed.

## Security boundary

M2.1 is emulator-level network isolation. The local Unix-domain IPC socket is AmiSandbox's host control channel and is not guest external networking.

Host/container/VM namespace and firewall controls remain recommended defense-in-depth. M2.1 does not claim that emulator-level enforcement replaces host isolation.

## Next

M2.1 is closed. Proceed to **M2.2 — writable host-filesystem isolation**.
