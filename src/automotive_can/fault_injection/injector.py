from __future__ import annotations

import math
from dataclasses import dataclass, replace
from enum import Enum

from ..dbc_codec import BMS_STATUS_ID, ReferenceDbcCodec
from ..model import CanFrame


class FaultKind(str, Enum):
    DROP = "drop"
    DELAY = "delay"
    OVERRIDE_SIGNAL = "override_signal"
    STUCK_SIGNAL = "stuck_signal"
    NOISY_SIGNAL = "noisy_signal"
    WRONG_COUNTER = "wrong_counter"
    CHECKSUM_MISMATCH = "checksum_mismatch"


@dataclass(frozen=True)
class FaultRule:
    kind: FaultKind
    start_s: float
    end_s: float
    signal: str | None = None
    value: float | None = None
    amplitude: float = 0.0
    delay_ms: int = 0

    def active(self, timestamp_s: float) -> bool:
        return self.start_s <= timestamp_s < self.end_s


@dataclass
class _DelayedFrame:
    release_s: float
    frame: CanFrame


class FaultInjector:
    """Two-stage fault injector for signal-level and frame-level faults."""

    def __init__(self, rules: list[FaultRule] | None = None) -> None:
        self.rules = rules or []
        self._stuck_values: dict[str, float] = {}
        self._delayed: list[_DelayedFrame] = []

    def mutate_signals(self, signals: dict[str, float | int], timestamp_s: float) -> dict[str, float | int]:
        out = dict(signals)
        for rule in self.rules:
            if not rule.active(timestamp_s) or rule.signal is None:
                continue
            if rule.kind == FaultKind.OVERRIDE_SIGNAL:
                if rule.value is None:
                    raise ValueError("override_signal requires value")
                out[rule.signal] = rule.value
            elif rule.kind == FaultKind.STUCK_SIGNAL:
                if rule.signal not in self._stuck_values:
                    self._stuck_values[rule.signal] = float(out[rule.signal])
                out[rule.signal] = self._stuck_values[rule.signal]
            elif rule.kind == FaultKind.NOISY_SIGNAL:
                # Deterministic sinusoidal noise keeps regression runs repeatable.
                out[rule.signal] = float(out[rule.signal]) + rule.amplitude * math.sin(31.0 * timestamp_s)
        return out

    def mutate_frame(self, frame: CanFrame, timestamp_s: float) -> list[CanFrame]:
        if frame.arbitration_id != BMS_STATUS_ID:
            return [replace(frame, timestamp_s=timestamp_s)]

        current = replace(frame, timestamp_s=timestamp_s)
        for rule in self.rules:
            if not rule.active(timestamp_s):
                continue
            if rule.kind == FaultKind.DROP:
                return []
            if rule.kind == FaultKind.WRONG_COUNTER:
                data = bytearray(current.data)
                data[7] = (data[7] & 0xF0) | (((data[7] & 0x0F) + 3) & 0x0F)
                current = replace(current, data=bytes(data))
            elif rule.kind == FaultKind.CHECKSUM_MISMATCH:
                data = bytearray(current.data)
                data[7] ^= 0x10
                current = replace(current, data=bytes(data))
            elif rule.kind == FaultKind.DELAY:
                self._delayed.append(_DelayedFrame(timestamp_s + rule.delay_ms / 1000.0, current))
                return []
        return [current]

    def release_due(self, timestamp_s: float) -> list[CanFrame]:
        ready = [item for item in self._delayed if item.release_s <= timestamp_s]
        self._delayed = [item for item in self._delayed if item.release_s > timestamp_s]
        return [replace(item.frame, timestamp_s=item.release_s) for item in sorted(ready, key=lambda x: x.release_s)]


def corrupt_raw_signal(frame: CanFrame, signal: str, value: float) -> CanFrame:
    """Convenience helper: decode, override a BMS signal and re-encode correctly."""
    codec = ReferenceDbcCodec()
    decoded = codec.decode_bms_status(frame)
    decoded[signal] = value
    required = {
        key: decoded[key]
        for key in ("SOC", "PackVoltage", "PackCurrent", "MaxCellTemp", "BatteryState", "FaultFlags", "Counter")
    }
    new = codec.encode_bms_status(required)
    return replace(new, timestamp_s=frame.timestamp_s)
