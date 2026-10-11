#include "vehicle/fault_monitor.hpp"

namespace vehicle {

FaultMonitor::FaultMonitor(Limits limits) : limits_(limits) {}

std::uint32_t FaultMonitor::evaluate(const Sample& sample, double timestamp_s) {
    std::uint32_t faults = 0;

    if (sample.soc < limits_.soc_min || sample.soc > limits_.soc_max) {
        faults |= to_mask(Fault::SocImplausible);
    }
    if (sample.pack_voltage < limits_.voltage_min || sample.pack_voltage > limits_.voltage_max) {
        faults |= to_mask(Fault::VoltageImplausible);
    }
    if (sample.max_temperature_c > limits_.max_temperature_c) {
        faults |= to_mask(Fault::OverTemperature);
    }
    if (!sample.checksum_valid) {
        faults |= to_mask(Fault::ChecksumMismatch);
    }
    if (have_sample_) {
        const auto expected = static_cast<std::uint8_t>((last_counter_ + 1u) & 0x0Fu);
        if ((sample.counter & 0x0Fu) != expected) {
            faults |= to_mask(Fault::CounterSequence);
        }
    }

    have_sample_ = true;
    last_counter_ = static_cast<std::uint8_t>(sample.counter & 0x0Fu);
    last_rx_s_ = timestamp_s;
    active_faults_ = faults;
    return active_faults_;
}

std::uint32_t FaultMonitor::supervise(double timestamp_s) {
    if (have_sample_ && (timestamp_s - last_rx_s_) > limits_.timeout_s) {
        active_faults_ |= to_mask(Fault::CommunicationTimeout);
    }
    return active_faults_;
}

std::vector<std::string> FaultMonitor::fault_names() const {
    std::vector<std::string> names;
    const auto add_if = [&](Fault fault, const char* name) {
        if ((active_faults_ & to_mask(fault)) != 0u) {
            names.emplace_back(name);
        }
    };
    add_if(Fault::SocImplausible, "SOC_IMPLAUSIBLE");
    add_if(Fault::VoltageImplausible, "VOLTAGE_IMPLAUSIBLE");
    add_if(Fault::OverTemperature, "OVER_TEMPERATURE");
    add_if(Fault::CommunicationTimeout, "COMMUNICATION_TIMEOUT");
    add_if(Fault::CounterSequence, "COUNTER_SEQUENCE");
    add_if(Fault::ChecksumMismatch, "CHECKSUM_MISMATCH");
    return names;
}

}  // namespace vehicle
