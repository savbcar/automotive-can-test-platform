# Design Decisions

## 1. Reference codec plus cantools

`cantools` is the intended DBC integration dependency, but deterministic core tests should not become un-runnable merely because a package repository or CAN kernel feature is unavailable. The reference codec therefore acts as an executable specification. When `cantools` exists, a parity test prevents the two layouts from silently diverging.

## 2. No false production UDS claim

Using the real service IDs is useful pedagogically. Calling the implementation "UDS compliant" would be misleading because ISO-TP, timing, state transitions and many service rules are absent. The code and docs explicitly label it educational.

## 3. Meaningful C++ boundary

Rather than adding a token C++ file, the repository implements the fault monitor as a standalone library with executable tests. It represents logic that could plausibly migrate closer to an embedded ECU application.

## 4. Counter/checksum simplification

The protection fields demonstrate sequencing/integrity concepts but are not AUTOSAR E2E or an OEM checksum algorithm. A corrupted counter also invalidates the checksum because protected data changed; that correlated detection is expected.

## 5. Recovery policy

A fault becomes inactive after a configurable number of consecutive valid frames. This is a simplified debounce/healing strategy used to demonstrate lifecycle behavior, not an OEM DTC aging specification.

## 6. Stuck signal handling

Stuck values are injected, but the vehicle ECU does not automatically diagnose a constant SOC. A constant value can be valid. A robust stuck-signal diagnostic needs contextual activity, redundancy/model observers and calibration.
