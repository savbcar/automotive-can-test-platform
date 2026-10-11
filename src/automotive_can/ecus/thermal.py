from __future__ import annotations

from ..dbc_codec import ReferenceDbcCodec
from ..model import CanFrame


class ThermalControlEcu:
    def __init__(self, codec: ReferenceDbcCodec) -> None:
        self.codec = codec
        self.counter = 0

    def build_status_frame(self, timestamp_s: float) -> CanFrame:
        coolant = 28.0 + 0.2 * timestamp_s
        pump = min(100.0, 35.0 + 1.5 * timestamp_s)
        fan = 20.0 if coolant < 35.0 else 45.0
        frame = self.codec.encode_thermal_status(
            {
                "CoolantTemp": coolant,
                "PumpDuty": pump,
                "FanDuty": fan,
                "ThermalState": 1,
                "Counter": self.counter,
            }
        )
        self.counter = (self.counter + 1) & 0x0F
        return frame
