# Architecture

## Responsibilities

- **BMS ECU** owns synthetic battery state, packs `BMS_Status`, increments the rolling counter and transmits cyclically.
- **Thermal ECU** emits a second cyclic message to make the network multi-node.
- **Vehicle ECU** decodes BMS status, applies plausibility/protection checks, supervises reception age and stores DTCs.
- **Fault Injector** can mutate engineering values before encoding or raw frames after encoding.
- **Diagnostic Server** exposes selected vehicle information and DTCs through a minimal UDS-like API.
- **Regression Runner** advances deterministic simulation time, schedules cyclic traffic, applies faults and records traces.

## Execution modes

### Deterministic in-memory SIL

The simulation clock is advanced in fixed steps. There are no background threads or wall-clock sleeps, so failures reproduce identically and can run quickly in CI.

### SocketCAN

`SocketCanEndpoint` wraps `python-can`. `vcan0` provides a Linux virtual CAN interface; a real SocketCAN hardware interface can replace it without changing the application frame model.

## Separation of concerns

Signal encoding is isolated behind a codec interface. `ReferenceDbcCodec` is a dependency-free executable specification used by deterministic tests; `CantoolsDbcCodec` loads the real DBC for external integration. Tests compare the two when `cantools` is installed.
