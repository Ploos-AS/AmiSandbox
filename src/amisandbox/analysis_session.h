#pragma once

#include <array>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <string>

namespace amisandbox {

constexpr unsigned kEventSchemaVersion = 1;

struct CpuSnapshot {
    std::array<std::uint32_t, 8> d{};
    std::array<std::uint32_t, 8> a{};
    std::uint32_t pc{};
    std::uint16_t sr{};
};

struct SessionMetadata {
    std::string amisandbox_version{"m1"};
    std::string emulator_version;
    std::string machine_profile;
    std::string configuration_fingerprint;
    bool jit_enabled{false};
    bool external_networking_enabled{false};
};

class AnalysisSession {
public:
    AnalysisSession() = default;
    ~AnalysisSession();

    AnalysisSession(const AnalysisSession&) = delete;
    AnalysisSession& operator=(const AnalysisSession&) = delete;

    bool start(const std::filesystem::path& output_directory,
               const SessionMetadata& metadata,
               std::string* error = nullptr);
    void emit_cpu_snapshot(const CpuSnapshot& snapshot, std::uint64_t emulated_cycles);
    void stop(const std::string& reason = "normal");

    [[nodiscard]] bool active() const noexcept { return active_; }
    [[nodiscard]] const std::filesystem::path& output_directory() const noexcept { return output_directory_; }

private:
    void emit_event(const std::string& type, const std::string& payload);

    std::filesystem::path output_directory_;
    std::ofstream events_;
    bool active_{false};
    std::uint64_t sequence_{0};
};

std::string json_escape(const std::string& value);

} // namespace amisandbox
