# Interview Defence Guide

## Explain CAN arbitration

CAN is multi-master. While transmitting the identifier, each node monitors the bus. Dominant zero overwrites recessive one. If a transmitter sends recessive but reads dominant, it loses arbitration and stops. The winning frame is not corrupted; numerically lower identifiers have higher priority.

## What is a DBC?

A database mapping frame payload bits to engineering signals: message ID/name/DLC, signal start bit and length, byte order, signedness, scale, offset, range, unit, transmitting/receiving nodes and optional metadata such as cycle time.

## Why CAN instead of Ethernet?

The answer is not "CAN is better." CAN is simple, robust and priority-arbitrated for relatively low-bandwidth control/status traffic. Automotive Ethernet offers much higher bandwidth and supports data-intensive domains, but has different topology, stack, cost and real-time design considerations. Modern vehicles use both.

## What did your project actually do?

It creates BMS/thermal CAN messages from physical signals, serializes them according to a DBC-compatible layout, transports them through deterministic SIL or SocketCAN, decodes them in a Vehicle ECU model, applies plausibility/communication monitors, stores DTCs and validates behavior with fault-injected regression tests.

## How are physical values encoded?

Use the DBC transformation `physical = raw * factor + offset`. For example SOC 82.5% with factor 0.5 becomes raw 165. Multi-byte values additionally require signedness and endianness.

## SIL vs MIL vs HIL

- MIL: algorithm/model tested against model-level plant before production software implementation.
- SIL: compiled/interpreted software tested against simulated environment without target ECU hardware.
- HIL: real target/controller hardware connects to real-time simulated plant and physical/electrical I/O.

This repository is SIL-style, not HIL.

## What is UDS?

ISO 14229 application-layer diagnostics: sessions, DIDs, DTC operations, tester present, security/programming and other services. This project implements a small educational subset and explicitly does not implement ISO-TP or full conformance.

## What is a DTC?

A code representing a diagnosed fault/condition, generally with status/lifecycle semantics. The project keeps simplified 24-bit codes and active/inactive lifecycle to demonstrate the concept.

## How did automated tests work?

The runner uses fixed-step simulation. At each configured BMS cycle, it generates physical values, applies signal-level faults, encodes a frame, applies frame-level faults and feeds the receiver. Timeout supervision runs every simulation step. Tests assert the expected warning appears and that the ECU recovers after the fault window.

## Why do dropout tests also show counter errors?

The BMS counter continues incrementing while frames are dropped. When communication resumes, the receiver sees a counter jump. That is realistic correlation, not a test bug.

## Why does counter corruption also trigger checksum mismatch?

The checksum protects the payload including the counter nibble. Mutating the counter after checksum generation invalidates both sequence and integrity checks.

## How is this different from CANoe/HIL?

The project does not reproduce real-time hardware I/O, transceiver physics, ECU power states, commercial rest-bus tooling or target hardware. It tests application/network logic in software. A real setup would replace `vcan0` with hardware, adopt production diagnostics/E2E and add HIL or CANoe as appropriate.

## How would you extend it to real ECUs?

Use a SocketCAN-compatible CAN adapter, retain DBC/test intent, add bench power/wakeup control, real timestamped logging, production ISO-TP/UDS, OEM E2E protection, ECU-specific DIDs/DTCs and then execute against rest-bus or HIL infrastructure.
