# Requirements Traceability

| Requirement | Implementation | Verification |
|---|---|---|
| BMS transmits SOC/voltage/current/temp/state/faults | `ecus/bms.py`, DBC | codec + integration tests |
| Vehicle decodes and checks plausibility | `ecus/vehicle.py` | `test_vehicle_monitor.py` |
| timeout detection | `VehicleControlEcu.supervise_timeouts` | unit + dropout regression |
| DBC encode/decode | `vehicle_can.dbc`, codecs | reference round-trip + cantools parity |
| python-can / SocketCAN | `can/socketcan.py` | opt-in `vcan0` integration CI |
| fault injection | `fault_injection/injector.py` | unit + regression scenarios |
| counter/checksum | `protection.py`, vehicle monitor | unit + regressions |
| DTCs | `diagnostics/dtc.py` | vehicle + UDS tests |
| UDS fundamentals | `diagnostics/uds.py` | UDS unit tests |
| simplified diagnostic CAN transport | `diagnostics/transport.py` | transport round-trip test |
| meaningful C++ | `cpp/vehicle_fault_monitor` | CTest + Python CLI integration |
| reports | `reporting.py` | generated example artifacts |
| CI | `.github/workflows/ci.yml` | GitHub Actions definition |
| Docker | `Dockerfile`, `compose.yaml` | build recipe supplied; not locally run if Docker unavailable |
