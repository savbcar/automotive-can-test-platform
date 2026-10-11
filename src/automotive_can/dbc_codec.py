from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .model import BatteryState, CanFrame
from .protection import insert_checksum4, verify_checksum4

BMS_STATUS_ID = 0x180
THERMAL_STATUS_ID = 0x280
DIAG_REQUEST_ID = 0x700
DIAG_RESPONSE_ID = 0x708


class Codec(Protocol):
    def encode_bms_status(self, signals: dict[str, float | int]) -> CanFrame: ...
    def decode_bms_status(self, frame: CanFrame) -> dict[str, float | int]: ...


@dataclass
class ReferenceDbcCodec:
    """Dependency-free reference codec matching ``dbc/vehicle_can.dbc``.

    It exists so deterministic SIL tests can run in restricted CI environments.
    Production/SocketCAN demonstrations use :class:`CantoolsDbcCodec` when the
    external dependency is available.
    """

    def encode_bms_status(self, signals: dict[str, float | int]) -> CanFrame:
        soc = int(round(float(signals["SOC"]) / 0.5))
        voltage = int(round(float(signals["PackVoltage"]) / 0.1))
        current = int(round(float(signals["PackCurrent"]) / 0.1))
        temp = int(round(float(signals["MaxCellTemp"]) + 40.0))
        state = int(signals.get("BatteryState", BatteryState.READY))
        flags = int(signals.get("FaultFlags", 0))
        counter = int(signals.get("Counter", 0)) & 0x0F

        for name, value, lo, hi in (
            ("SOC raw", soc, 0, 255),
            ("PackVoltage raw", voltage, 0, 65535),
            ("PackCurrent raw", current, -32768, 32767),
            ("MaxCellTemp raw", temp, 0, 255),
            ("BatteryState", state, 0, 7),
            ("FaultFlags", flags, 0, 31),
        ):
            if not lo <= value <= hi:
                raise ValueError(f"{name} outside representable range: {value}")

        data = bytearray(8)
        data[0] = soc
        data[1:3] = voltage.to_bytes(2, "little", signed=False)
        data[3:5] = current.to_bytes(2, "little", signed=True)
        data[5] = temp
        data[6] = (state & 0x07) | ((flags & 0x1F) << 3)
        data[7] = counter
        protected = insert_checksum4(bytes(data))
        return CanFrame(BMS_STATUS_ID, protected)

    def decode_bms_status(self, frame: CanFrame) -> dict[str, float | int]:
        if frame.arbitration_id != BMS_STATUS_ID:
            raise ValueError(f"expected 0x{BMS_STATUS_ID:X}, got 0x{frame.arbitration_id:X}")
        if len(frame.data) != 8:
            raise ValueError("BMS_Status requires 8 data bytes")
        data = frame.data
        current_raw = int.from_bytes(data[3:5], "little", signed=True)
        return {
            "SOC": data[0] * 0.5,
            "PackVoltage": int.from_bytes(data[1:3], "little") * 0.1,
            "PackCurrent": current_raw * 0.1,
            "MaxCellTemp": data[5] - 40.0,
            "BatteryState": data[6] & 0x07,
            "FaultFlags": (data[6] >> 3) & 0x1F,
            "Counter": data[7] & 0x0F,
            "AppChecksum": (data[7] >> 4) & 0x0F,
            "ChecksumValid": int(verify_checksum4(data)),
        }

    def encode_thermal_status(self, signals: dict[str, float | int]) -> CanFrame:
        coolant = int(round(float(signals["CoolantTemp"]) + 40))
        pump = int(round(float(signals["PumpDuty"])))
        fan = int(round(float(signals["FanDuty"])))
        state = int(signals.get("ThermalState", 0))
        counter = int(signals.get("Counter", 0)) & 0x0F
        if not all(0 <= x <= 255 for x in (coolant, pump, fan)):
            raise ValueError("thermal signal outside representable range")
        data = bytearray(8)
        data[0] = coolant
        data[1] = pump
        data[2] = fan
        data[3] = state & 0x0F
        data[7] = counter
        data = bytearray(insert_checksum4(bytes(data)))
        return CanFrame(THERMAL_STATUS_ID, bytes(data))

    def decode_thermal_status(self, frame: CanFrame) -> dict[str, float | int]:
        if frame.arbitration_id != THERMAL_STATUS_ID or len(frame.data) != 8:
            raise ValueError("invalid Thermal_Status frame")
        return {
            "CoolantTemp": frame.data[0] - 40.0,
            "PumpDuty": frame.data[1],
            "FanDuty": frame.data[2],
            "ThermalState": frame.data[3] & 0x0F,
            "Counter": frame.data[7] & 0x0F,
            "ChecksumValid": int(verify_checksum4(frame.data)),
        }


class CantoolsDbcCodec:
    """DBC codec backed by cantools.

    The application checksum is written after cantools encodes the signals and
    verified before/after decoding. This keeps the DBC as the signal-layout
    source of truth while making the simplified E2E behavior explicit.
    """

    def __init__(self, dbc_path: str | Path) -> None:
        import cantools  # type: ignore

        self.db = cantools.database.load_file(str(dbc_path))
        self._bms = self.db.get_message_by_name("BMS_Status")
        self._thermal = self.db.get_message_by_name("Thermal_Status")

    def encode_bms_status(self, signals: dict[str, float | int]) -> CanFrame:
        values = dict(signals)
        values.setdefault("AppChecksum", 0)
        data = self._bms.encode(values, strict=True)
        return CanFrame(BMS_STATUS_ID, insert_checksum4(data))

    def decode_bms_status(self, frame: CanFrame) -> dict[str, Any]:
        decoded = self._bms.decode(frame.data, decode_choices=False)
        decoded["ChecksumValid"] = int(verify_checksum4(frame.data))
        return decoded

    def encode_thermal_status(self, signals: dict[str, float | int]) -> CanFrame:
        values = dict(signals)
        values.setdefault("AppChecksum", 0)
        data = self._thermal.encode(values, strict=True)
        return CanFrame(THERMAL_STATUS_ID, insert_checksum4(data))

    def decode_thermal_status(self, frame: CanFrame) -> dict[str, Any]:
        decoded = self._thermal.decode(frame.data, decode_choices=False)
        decoded["ChecksumValid"] = int(verify_checksum4(frame.data))
        return decoded
