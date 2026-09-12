#include "sysdeps.h"
#include <SDL3/SDL_main.h>

#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

// M1 deliberately keeps the analysis implementation isolated from the
// upstream source list. A later milestone can promote it to its own target.
#include "../amisandbox/analysis_session.cpp"

int amiberry_main(int argc, char* argv[]);

namespace {

const char* env_or_empty(const char* name)
{
	const char* value = std::getenv(name);
	return value ? value : "";
}

} // namespace

int main(int argc, char* argv[])
{
	amisandbox::AnalysisSession analysis;
	const char* output_dir = std::getenv("AMISANDBOX_ANALYSIS_DIR");
	const bool analysis_mode = output_dir && *output_dir;
	std::vector<char*> effective_argv(argv, argv + argc);
	std::string bsdsocket_override;
	std::string storage_override;

	if (analysis_mode) {
#ifdef JIT
		// M2.0 isolation rule: malware-analysis sessions must never run in a
		// JIT-enabled binary. Fail closed before creating session artifacts or
		// entering the emulator. Normal Amiberry operation remains unaffected.
		std::fputs("AmiSandbox: analysis mode requires a non-JIT build\n", stderr);
		return 78;
#endif

		// M2.1b isolation rule: direct bsdsocket.library emulation is an
		// independent guest-to-host network path. cfgfile parameters are applied
		// after the loaded configuration. cfgfile_addcfgparam() prepends entries,
		// so inserting this argument first makes it the last cfgparam applied and
		// therefore authoritative even if the caller requested bsdsocket_emu=true.
		// M2.1a separately blocks Ethernet backends at ethernet_open().
		bsdsocket_override = "-cfgparam=bsdsocket_emu=false";
		effective_argv.insert(effective_argv.begin() + 1, bsdsocket_override.data());
		std::fputs("AmiSandbox: forcing bsdsocket_emu=false in analysis mode\n", stderr);

		// M2.2 isolation rule: host-backed directory filesystems and hardfiles
		// must not be writable by malware-analysis guests. Amiberry exposes the
		// global harddrive_write_protect preference as harddrive_read_only in
		// uae_prefs. Use the same authoritative cfgparam precedence rule as M2.1b
		// so a hostile config/CLI request cannot silently re-enable writes.
		storage_override = "-cfgparam=harddrive_write_protect=true";
		effective_argv.insert(effective_argv.begin() + 1, storage_override.data());
		std::fputs("AmiSandbox: forcing harddrive_write_protect=true in analysis mode\n", stderr);

		amisandbox::SessionMetadata metadata;
		metadata.amisandbox_version = "m2.2";
#ifdef AMIBERRY_VERSION
		metadata.emulator_version = AMIBERRY_VERSION;
#else
		metadata.emulator_version = "unknown";
#endif
		metadata.machine_profile = env_or_empty("AMISANDBOX_MACHINE_PROFILE");
		metadata.configuration_fingerprint = env_or_empty("AMISANDBOX_CONFIG_FINGERPRINT");
		metadata.jit_enabled = false;
		metadata.external_networking_enabled = false;

		std::string error;
		if (!analysis.start(output_dir, metadata, &error)) {
			return 78; // configuration / analysis-output failure
		}
	}

	const int result = amiberry_main(static_cast<int>(effective_argv.size()), effective_argv.data());
	if (analysis.active()) {
		analysis.stop(result == 0 ? "emulator-exit" : "emulator-error");
	}
	return result;
}
