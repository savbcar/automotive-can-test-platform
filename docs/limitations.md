# Honest Limitations

This project does **not** model or validate:

- CAN transceiver analog behavior, termination, common-mode voltage, EMC or wiring faults;
- exact controller bit timing, sample points, oscillator tolerance or bus-load timing guarantees;
- CAN error frames, TEC/REC error states, bus-off recovery or arbitration timing at bit level;
- real-time scheduling determinism;
- production ISO-TP or full ISO 14229 UDS behavior;
- AUTOSAR E2E profiles or OEM proprietary counters/checksums;
- real ECU boot/wakeup/ignition/power behavior;
- flash programming, security access or authenticated diagnostics;
- Vector CANoe/CANalyzer test modules, CAPL or proprietary rest-bus simulation;
- HIL I/O, plant real-time execution, sensor/actuator electrical faults or target hardware timing;
- ASIL evidence, ISO 26262 work products, cybersecurity compliance or production release qualification.

The value of the project is foundational communication/test engineering: message design, signal encoding, ECU monitoring, diagnostics concepts, repeatable fault injection and automation.
