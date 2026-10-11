# Educational UDS Layer

The diagnostic implementation teaches service semantics rather than claiming conformance.

Implemented services:

- `0x10` DiagnosticSessionControl
- `0x22` ReadDataByIdentifier
- `0x19` ReadDTCInformation (simplified `0x02` behavior)
- `0x3E` TesterPresent
- `0x14` ClearDiagnosticInformation

Positive responses use `request SID + 0x40`. Negative responses use `0x7F`, original SID and an NRC.

The CAN transport is deliberately a single 8-byte frame with a one-byte payload length. It is **not ISO-TP (ISO 15765-2)**. Therefore multi-frame diagnostics, flow control, segmentation/reassembly and standard transport timing are outside scope.

A production extension should use a standards-compliant ISO-TP layer and a tested UDS implementation, then add OEM-specific DID/DTC/security/session data.
