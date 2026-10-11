# CAN Primer

## Why an automotive network exists

Point-to-point wiring scales poorly as the number of ECUs and shared signals grows. CAN lets multiple nodes share a differential physical bus and exchange prioritized frames.

## Identifier and arbitration

A CAN identifier expresses message priority and is commonly associated with message meaning; it is not simply a destination address. During arbitration, dominant (`0`) overrides recessive (`1`). A transmitter that sends recessive but observes dominant stops, so the lowest numerical identifier wins without destroying the winning frame.

## Frame vs signal

A CAN frame contains an identifier, protocol/control fields and a payload. A signal is an engineering value packed into a bit range within the payload. Several signals can share one frame.

## DLC

Classical CAN data frames carry up to 8 payload bytes. CAN FD permits larger payloads (up to 64 bytes) and optionally a faster data phase. This project uses classical 8-byte messages.

## Scaling

A common DBC relationship is:

`physical = raw * factor + offset`

For SOC with factor `0.5`, 82.5% becomes raw 165 (`0xA5`).

## Endianness and signedness

Multi-byte values require a defined byte/bit order. `PackVoltage` and `PackCurrent` here are little-endian. Current is signed because it can represent charging/discharging direction.

## Cycle time and timeout

The BMS publishes every 100 ms. The receiver treats more than 300 ms without a BMS frame as a communication fault. Cycle time is an application scheduling requirement; CAN itself does not schedule application messages.

## Counter and checksum

The 4-bit rolling counter increments modulo 16. The 4-bit application checksum is a deliberately simple teaching mechanism. CAN already includes frame-level error detection; application-layer protection addresses different failure models and OEM/AUTOSAR implementations are much more sophisticated.
