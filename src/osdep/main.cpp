#include "sysdeps.h"
#include <SDL3/SDL_main.h>

#include <cstdlib>
#include <string>

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

	if (output_dir && *output_dir) {
		amisandbox::SessionMetadata metadata;
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

	const int result = amiberry_main(argc, argv);
	if (analysis.active()) {
		analysis.stop(result == 0 ? "emulator-exit" : "emulator-error");
	}
	return result;
}
