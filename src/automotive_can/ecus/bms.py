from __future__ import annotations

from dataclasses import dataclass

from ..dbc_codec import Codec
from ..model import BatteryState, CanFrame


@dataclass
class BatteryPlantState:
    soc: float = 82.5
    pack_voltage: float = 400.2
    pack_current: float = -42.3
    max_cell_temp: float = 31.0
    battery_state: int = int(BatteryState.READY)
    fault_flags: int = 0


class BmsEcu:
    def __init__(self, codec: Codec) -> None:
        self.codec = codec
        self.counter = 0
        self.state = BatteryPlantState()

    def signals(self) -> dict[str, float | int]:
        return {
            "SOC": self.state.soc,
            "PackVoltage": self.state.pack_voltage,
            "PackCurrent": self.state.pack_current,
            "MaxCellTemp": self.state.max_cell_temp,
            "BatteryState": self.state.battery_state,
            "FaultFlags": self.state.fault_flags,
            "Counter": self.counter,
        }

    def build_status_frame(self) -> CanFrame:
        frame = self.codec.encode_bms_status(self.signals())
        self.counter = (self.counter + 1) & 0x0F
        return frame

    def update_synthetic_plant(self, timestamp_s: float) -> None:
        # Deterministic, physically plausible trace used only as test stimulus.
        self.state.soc = max(0.0, 82.5 - 0.08 * timestamp_s)
        self.state.pack_voltage = 400.2 - 0.12 * timestamp_s
        self.state.pack_current = -42.3 + 3.0 * timestamp_s
        self.state.max_cell_temp = 31.0 + 0.35 * timestamp_s
