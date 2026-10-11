from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class VehicleLimits:
    soc_min: float = 0.0
    soc_max: float = 100.0
    voltage_min: float = 250.0
    voltage_max: float = 450.0
    max_temp_warning_c: float = 60.0
    bms_timeout_ms: int = 300
    recovery_frames: int = 3


@dataclass(frozen=True)
class SimulationConfig:
    duration_s: float = 4.0
    step_ms: int = 10
    bms_cycle_ms: int = 100
    thermal_cycle_ms: int = 200
    limits: VehicleLimits = VehicleLimits()


def _limits_from(data: dict[str, Any]) -> VehicleLimits:
    return VehicleLimits(
        soc_min=float(data.get("soc_min", 0.0)),
        soc_max=float(data.get("soc_max", 100.0)),
        voltage_min=float(data.get("voltage_min", 250.0)),
        voltage_max=float(data.get("voltage_max", 450.0)),
        max_temp_warning_c=float(data.get("max_temp_warning_c", 60.0)),
        bms_timeout_ms=int(data.get("bms_timeout_ms", 300)),
        recovery_frames=int(data.get("recovery_frames", 3)),
    )


def load_simulation_config(path: str | Path) -> SimulationConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return SimulationConfig(
        duration_s=float(raw.get("duration_s", 4.0)),
        step_ms=int(raw.get("step_ms", 10)),
        bms_cycle_ms=int(raw.get("bms_cycle_ms", 100)),
        thermal_cycle_ms=int(raw.get("thermal_cycle_ms", 200)),
        limits=_limits_from(raw.get("limits", {})),
    )
