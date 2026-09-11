#include "analysis_session.h"

#include <chrono>
#include <iomanip>
#include <sstream>

namespace amisandbox {
namespace {

std::string hex32(const std::uint32_t value)
{
    std::ostringstream out;
    out << "0x" << std::hex << std::setw(8) << std::setfill('0') << value;
    return out.str();
}

std::string hex16(const std::uint16_t value)
{
    std::ostringstream out;
    out << "0x" << std::hex << std::setw(4) << std::setfill('0') << value;
    return out.str();
}

std::string iso8601_utc_now()
{
    const auto now = std::chrono::system_clock::now();
    const auto time = std::chrono::system_clock::to_time_t(now);
    std::tm utc{};
#if defined(_WIN32)
    gmtime_s(&utc, &time);
#else
    gmtime_r(&time, &utc);
#endif
    std::ostringstream out;
    out << std::put_time(&utc, "%Y-%m-%dT%H:%M:%SZ");
    return out.str();
}

} // namespace

std::string json_escape(const std::string& value)
{
    std::ostringstream out;
    for (const unsigned char ch : value) {
        switch (ch) {
        case '"': out << "\\\""; break;
        case '\\': out << "\\\\"; break;
        case '\b': out << "\\b"; break;
        case '\f': out << "\\f"; break;
        case '\n': out << "\\n"; break;
        case '\r': out << "\\r"; break;
        case '\t': out << "\\t"; break;
        default:
            if (ch < 0x20) {
                out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << static_cast<unsigned>(ch);
            } else {
                out << ch;
            }
        }
    }
    return out.str();
}

AnalysisSession::~AnalysisSession()
{
    stop("destructor");
}

bool AnalysisSession::start(const std::filesystem::path& output_directory,
                            const SessionMetadata& metadata,
                            std::string* error)
{
    if (active_) {
        if (error) *error = "analysis session already active";
        return false;
    }

    std::error_code ec;
    std::filesystem::create_directories(output_directory, ec);
    if (ec) {
        if (error) *error = "cannot create analysis output directory: " + ec.message();
        return false;
    }

    output_directory_ = output_directory;
    events_.open(output_directory_ / "events.jsonl", std::ios::out | std::ios::trunc);
    if (!events_) {
        if (error) *error = "cannot open events.jsonl";
        return false;
    }

    std::ofstream metadata_file(output_directory_ / "session.json", std::ios::out | std::ios::trunc);
    if (!metadata_file) {
        events_.close();
        if (error) *error = "cannot open session.json";
        return false;
    }

    metadata_file
        << "{\n"
        << "  \"schema_version\": " << kEventSchemaVersion << ",\n"
        << "  \"amisandbox_version\": \"" << json_escape(metadata.amisandbox_version) << "\",\n"
        << "  \"emulator_version\": \"" << json_escape(metadata.emulator_version) << "\",\n"
        << "  \"machine_profile\": \"" << json_escape(metadata.machine_profile) << "\",\n"
        << "  \"configuration_fingerprint\": \"" << json_escape(metadata.configuration_fingerprint) << "\",\n"
        << "  \"jit_enabled\": " << (metadata.jit_enabled ? "true" : "false") << ",\n"
        << "  \"external_networking_enabled\": " << (metadata.external_networking_enabled ? "true" : "false") << "\n"
        << "}\n";

    active_ = true;
    sequence_ = 0;
    emit_event("session.start", "{\"wallclock_utc\":\"" + iso8601_utc_now() + "\"}");
    return true;
}

void AnalysisSession::emit_event(const std::string& type, const std::string& payload)
{
    if (!active_ || !events_) return;
    events_ << "{\"schema_version\":" << kEventSchemaVersion
            << ",\"sequence\":" << sequence_++
            << ",\"type\":\"" << json_escape(type) << "\",\"data\":" << payload << "}\n";
    events_.flush();
}

void AnalysisSession::emit_cpu_snapshot(const CpuSnapshot& snapshot, const std::uint64_t emulated_cycles)
{
    if (!active_) return;

    std::ostringstream payload;
    payload << "{\"emulated_cycles\":" << emulated_cycles << ",\"pc\":\"" << hex32(snapshot.pc)
            << "\",\"sr\":\"" << hex16(snapshot.sr) << "\",\"d\":[";
    for (std::size_t i = 0; i < snapshot.d.size(); ++i) {
        if (i) payload << ',';
        payload << '"' << hex32(snapshot.d[i]) << '"';
    }
    payload << "],\"a\":[";
    for (std::size_t i = 0; i < snapshot.a.size(); ++i) {
        if (i) payload << ',';
        payload << '"' << hex32(snapshot.a[i]) << '"';
    }
    payload << "]}";
    emit_event("cpu.snapshot", payload.str());
}

void AnalysisSession::stop(const std::string& reason)
{
    if (!active_) return;
    emit_event("session.stop", "{\"reason\":\"" + json_escape(reason) + "\"}");
    active_ = false;
    events_.close();
}

} // namespace amisandbox
