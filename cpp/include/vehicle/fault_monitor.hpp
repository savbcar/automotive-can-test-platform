#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace vehicle {

enum class Fault : std::uint32_t {
    None = 0,
    SocImplausible = 1u << 0,
    VoltageImplausible = 1u << 1,
    OverTemperature = 1u << 2,
    CommunicationTimeout = 1u << 3,
    CounterSequence = 1u << 4,
    ChecksumMismatch = 1u << 5,
};

constexpr std::uint32_t to_mask(Fault fault) {
    return static_cast<std::uint32_t>(fault);
}

struct Limits {
    double soc_min{0.0};
    double soc_max{100.0};
    double voltage_min{250.0};
    double voltage_max{450.0};
    double max_temperature_c{60.0};
    double timeout_s{0.300};
};

struct Sample {
    double soc{0.0};
    double pack_voltage{0.0};
    double max_temperature_c{0.0};
    std::uint8_t counter{0};
    bool checksum_valid{true};
};

class FaultMonitor {
public:
    explicit FaultMonitor(Limits limits = {});

    std::uint32_t evaluate(const Sample& sample, double timestamp_s);
    std::uint32_t supervise(double timestamp_s);
    std::uint32_t active_faults() const noexcept { return active_faults_; }
    std::vector<std::string> fault_names() const;

private:
    Limits limits_;
    bool have_sample_{false};
    std::uint8_t last_counter_{0};
    double last_rx_s_{0.0};
    std::uint32_t active_faults_{0};
};

}  // namespace vehicle
