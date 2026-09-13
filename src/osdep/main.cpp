#include "sysdeps.h"
#include <SDL3/SDL_main.h>

#include <cstdio>
#include <cstdlib>
#include <filesystem>
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

bool env_is_one(const char* name)
{
	const char* value = std::getenv(name);
	return value && std::string(value) == "1";
}

std::string cfgparam_value(int argc, char* argv[], const std::string& key)
{
	const std::string prefix = "-cfgparam=" + key + "=";
	for (int i = 1; i < argc; ++i) {
		const std::string arg = argv[i] ? argv[i] : "";
		if (arg.rfind(prefix, 0) == 0) {
			return arg.substr(prefix.size());
		}
	}
	return {};
}

std::string floppy0_value(int argc, char* argv[])
{
	const std::string cfgparam = cfgparam_value(argc, argv, "floppy0");
	if (!cfgparam.empty()) {
		return cfgparam;
	}

	// Amiberry's native command-line interface mounts DF0 with "-0 <image>".
	// M2.5 accepts that spelling only when it has a non-empty following value;
	// trusted-path validation below remains identical for both syntaxes.
	for (int i = 1; i < argc; ++i) {
		const std::string arg = argv[i] ? argv[i] : "";
		if (arg == "-0") {
			if (i + 1 >= argc || argv[i + 1] == nullptr || *argv[i + 1] == '\0') {
				return {};
			}
			return argv[i + 1];
		}
	}
	return {};
}

bool path_is_within(const std::filesystem::path& child, const std::filesystem::path& parent)
{
	auto child_it = child.begin();
	for (auto parent_it = parent.begin(); parent_it != parent.end(); ++parent_it, ++child_it) {
		if (child_it == child.end() || *child_it != *parent_it) {
			return false;
		}
	}
	return child_it != child.end();
}

bool validated_writable_floppy(int argc, char* argv[], const char* output_dir)
{
	if (!env_is_one("AMISANDBOX_WRITABLE_MEDIA_COPY")) {
		return false;
	}

	const std::string floppy0 = floppy0_value(argc, argv);
	if (floppy0.empty()) {
		return false;
	}

	std::error_code ec;
	const auto media_root = std::filesystem::weakly_canonical(
		std::filesystem::path(output_dir) / "media", ec);
	if (ec) {
		return false;
	}
	const auto requested = std::filesystem::weakly_canonical(floppy0, ec);
	if (ec || !std::filesystem::is_regular_file(requested, ec) || ec) {
		return false;
	}
	return path_is_within(requested, media_root);
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
	std::string floppy_override;

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

		// M2.3 keeps original removable-media evidence immutable. M2.5 permits
		// writable media only when the caller explicitly opts in AND DF0 (whether
		// supplied as -cfgparam=floppy0=... or native -0 <image>) resolves to a
		// regular file below this session's analysis/media tree. Any malformed
		// opt-in fails closed instead of weakening M2.3.
		const bool writable_media_requested = env_is_one("AMISANDBOX_WRITABLE_MEDIA_COPY");
		const bool writable_media_valid = validated_writable_floppy(argc, argv, output_dir);
		if (writable_media_requested && !writable_media_valid) {
			std::fputs("AmiSandbox: writable media opt-in rejected; DF0 must be a session working copy\n", stderr);
			return 78;
		}
		if (writable_media_valid) {
			floppy_override = "-cfgparam=floppy_write_protect=false";
			effective_argv.insert(effective_argv.begin() + 1, floppy_override.data());
			std::fputs("AmiSandbox: allowing writable disposable floppy media in analysis mode\n", stderr);
		} else {
			floppy_override = "-cfgparam=floppy_write_protect=true";
			effective_argv.insert(effective_argv.begin() + 1, floppy_override.data());
			std::fputs("AmiSandbox: forcing floppy_write_protect=true in analysis mode\n", stderr);
		}

		amisandbox::SessionMetadata metadata;
		metadata.amisandbox_version = "m2.5";
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
