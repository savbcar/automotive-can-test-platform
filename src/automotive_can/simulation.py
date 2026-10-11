from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from .config import SimulationConfig
from .dbc_codec import ReferenceDbcCodec
from .ecus.bms import BmsEcu
from .ecus.thermal import ThermalControlEcu
from .ecus.vehicle import VehicleControlEcu
from .fault_injection.injector import FaultInjector, FaultKind, FaultRule


@dataclass(frozen=True)
class TraceRow:
    time_s: float
    tx_soc: float
    rx_soc: float | None
    tx_temp_c: float
    rx_temp_c: float | None
    frame_received: bool
    healthy: bool
    warnings: str
    active_dtcs: str


@dataclass
class ScenarioResult:
    name: str
    expected_warning: str | None
    rows: list[TraceRow]
    observed_warnings: set[str]
    recovered: bool

    @property
    def passed(self) -> bool:
        if self.expected_warning and self.expected_warning not in self.observed_warnings:
            return False
        if self.expected_warning is None and self.observed_warnings:
            return False
        return self.recovered

    def summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "expected_warning": self.expected_warning,
            "observed_warnings": sorted(self.observed_warnings),
            "recovered": self.recovered,
            "passed": self.passed,
            "samples": len(self.rows),
        }


def _rules(raw: list[dict[str, Any]]) -> list[FaultRule]:
    return [
        FaultRule(
            kind=FaultKind(item["kind"]),
            start_s=float(item["start_s"]),
            end_s=float(item["end_s"]),
            signal=item.get("signal"),
            value=float(item["value"]) if "value" in item else None,
            amplitude=float(item.get("amplitude", 0.0)),
            delay_ms=int(item.get("delay_ms", 0)),
        )
        for item in raw
    ]


def load_scenarios(path: str | Path) -> list[dict[str, Any]]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return list(data.get("scenarios", []))


def run_scenario(spec: dict[str, Any], config: SimulationConfig) -> ScenarioResult:
    codec = ReferenceDbcCodec()
    bms = BmsEcu(codec)
    thermal = ThermalControlEcu(codec)
    vehicle = VehicleControlEcu(codec, config.limits)
    injector = FaultInjector(_rules(spec.get("faults", [])))

    rows: list[TraceRow] = []
    observed: set[str] = set()
    bms_period_steps = max(1, config.bms_cycle_ms // config.step_ms)
    thermal_period_steps = max(1, config.thermal_cycle_ms // config.step_ms)
    total_steps = int(round(config.duration_s * 1000 / config.step_ms))

    for step in range(total_steps + 1):
        t = step * config.step_ms / 1000.0
        bms.update_synthetic_plant(t)
        received_this_step = False

        # Thermal ECU exists on the virtual architecture even though BMS safety
        # assertions are the principal regression target in this project.
        if step % thermal_period_steps == 0:
            _ = thermal.build_status_frame(t)

        for delayed in injector.release_due(t):
            health = vehicle.process_frame(delayed, t)
            observed.update(health.warnings)
            received_this_step = True

        if step % bms_period_steps == 0:
            source = bms.signals()
            mutated = injector.mutate_signals(source, t)
            frame = codec.encode_bms_status(mutated)
            bms.counter = (bms.counter + 1) & 0x0F
            for delivered in injector.mutate_frame(frame, t):
                health = vehicle.process_frame(delivered, t)
                observed.update(health.warnings)
                received_this_step = True

        health = vehicle.supervise_timeouts(t)
        observed.update(health.warnings)
        rows.append(
            TraceRow(
                time_s=t,
                tx_soc=float(bms.state.soc),
                rx_soc=vehicle.snapshot.soc,
                tx_temp_c=float(bms.state.max_cell_temp),
                rx_temp_c=vehicle.snapshot.max_cell_temp,
                frame_received=received_this_step,
                healthy=health.healthy,
                warnings=";".join(health.warnings),
                active_dtcs=";".join(f"0x{x:06X}" for x in health.dtcs),
            )
        )

    # Recovery is assessed at the end of each scenario. Faults intentionally end
    # before the simulation does, giving several healthy frames to recover.
    recovered = vehicle.health().healthy
    return ScenarioResult(
        name=str(spec["name"]),
        expected_warning=spec.get("expected_warning"),
        rows=rows,
        observed_warnings=observed,
        recovered=recovered,
    )


def row_to_dict(row: TraceRow) -> dict[str, Any]:
    return asdict(row)
