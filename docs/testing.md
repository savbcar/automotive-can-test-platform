# Test Strategy

## Unit tests

Exercise each deterministic unit: binary encoding, checksum, counter wrap, ECU monitors, DTC lifecycle, fault rules, in-memory broadcast behavior and UDS responses.

## Integration tests

Prove components work together: BMS -> virtual CAN -> Vehicle ECU and Python -> compiled C++ CLI. An opt-in `vcan0` test exercises `python-can` on Linux SocketCAN.

## Regression tests

`configs/regression.yaml` is test data. Each scenario injects a fault during a bounded window and leaves sufficient post-fault time for recovery. The runner records every time step and checks expected warnings plus final recovery state.

## Evidence

`automotive_can.reporting` emits JSON, CSV, Markdown and plots. This makes regression output suitable for CI artifacts and portfolio review rather than only console logs.

## Why deterministic injection

Random fault injection can be useful for robustness campaigns but complicates debugging. The core suite uses deterministic time windows and sinusoidal noise so failures reproduce exactly.
