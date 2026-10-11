from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any


class BatteryState(IntEnum):
    OFF = 0
    READY = 1
    CHARGING = 2
    FAULT = 3


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class CanFrame:
    arbitration_id: int
    data: bytes
    timestamp_s: float = 0.0
    is_extended_id: bool = False

    def __post_init__(self) -> None:
        if not 0 <= self.arbitration_id <= 0x1FFFFFFF:
            raise ValueError("arbitration_id outside CAN range")
        if len(self.data) > 64:
            raise ValueError("CAN/CAN-FD payload cannot exceed 64 bytes")
        if not self.is_extended_id and self.arbitration_id > 0x7FF:
            raise ValueError("standard CAN identifier must be <= 0x7FF")

    @property
    def dlc(self) -> int:
        return len(self.data)


@dataclass
class Dtc:
    code: int
    name: str
    description: str
    active: bool = True
    occurrence_count: int = 1
    first_seen_s: float = 0.0
    last_seen_s: float = 0.0


@dataclass(frozen=True)
class MonitorEvent:
    timestamp_s: float
    code: str
    severity: Severity
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class VehicleHealth:
    healthy: bool
    warnings: tuple[str, ...] = ()
    dtcs: tuple[int, ...] = ()
