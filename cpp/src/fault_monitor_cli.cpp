#include "vehicle/fault_monitor.hpp"

#include <cstdlib>
#include <iostream>

int main(int argc, char** argv) {
    if (argc != 7) {
        std::cerr << "usage: fault_monitor_cli <soc> <voltage> <temp> <counter> <checksum_valid> <timestamp_s>\n";
        return 2;
    }

    vehicle::FaultMonitor monitor;
    vehicle::Sample sample{
        std::strtod(argv[1], nullptr),
        std::strtod(argv[2], nullptr),
        std::strtod(argv[3], nullptr),
        static_cast<std::uint8_t>(std::strtoul(argv[4], nullptr, 10)),
        std::strtoul(argv[5], nullptr, 10) != 0,
    };
    const auto faults = monitor.evaluate(sample, std::strtod(argv[6], nullptr));
    std::cout << faults << '\n';
    return 0;
}
