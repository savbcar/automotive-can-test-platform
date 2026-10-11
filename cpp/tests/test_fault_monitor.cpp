#include "vehicle/fault_monitor.hpp"

#include <cassert>
#include <cstdint>

using vehicle::Fault;
using vehicle::FaultMonitor;
using vehicle::Sample;
using vehicle::to_mask;

int main() {
    {
        FaultMonitor monitor;
        const auto faults = monitor.evaluate(Sample{80.0, 400.0, 35.0, 0, true}, 0.0);
        assert(faults == 0u);
    }
    {
        FaultMonitor monitor;
        const auto faults = monitor.evaluate(Sample{110.0, 400.0, 35.0, 0, true}, 0.0);
        assert((faults & to_mask(Fault::SocImplausible)) != 0u);
    }
    {
        FaultMonitor monitor;
        const auto faults = monitor.evaluate(Sample{80.0, 220.0, 35.0, 0, true}, 0.0);
        assert((faults & to_mask(Fault::VoltageImplausible)) != 0u);
    }
    {
        FaultMonitor monitor;
        const auto faults = monitor.evaluate(Sample{80.0, 400.0, 75.0, 0, true}, 0.0);
        assert((faults & to_mask(Fault::OverTemperature)) != 0u);
    }
    {
        FaultMonitor monitor;
        monitor.evaluate(Sample{80.0, 400.0, 35.0, 0, true}, 0.0);
        const auto faults = monitor.evaluate(Sample{80.0, 400.0, 35.0, 3, true}, 0.1);
        assert((faults & to_mask(Fault::CounterSequence)) != 0u);
    }
    {
        FaultMonitor monitor;
        const auto faults = monitor.evaluate(Sample{80.0, 400.0, 35.0, 0, false}, 0.0);
        assert((faults & to_mask(Fault::ChecksumMismatch)) != 0u);
    }
    {
        FaultMonitor monitor;
        monitor.evaluate(Sample{80.0, 400.0, 35.0, 0, true}, 0.0);
        const auto faults = monitor.supervise(0.301);
        assert((faults & to_mask(Fault::CommunicationTimeout)) != 0u);
    }
    return 0;
}
