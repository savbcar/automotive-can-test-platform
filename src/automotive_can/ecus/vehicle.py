from __future__ import annotations

from dataclasses import dataclass

from ..config import VehicleLimits
from ..dbc_codec import BMS_STATUS_ID, Codec
from ..diagnostics.dtc import DtcStore
from ..model import CanFrame, MonitorEvent, Severity, VehicleHealth
from ..protection import expected_next_counter

DTC_SOC_IMPLAUSIBLE = 0xA00101
DTC_VOLTAGE_IMPLAUSIBLE = 0xA00102
DTC_OVERTEMP = 0xA00103
DTC_COMM_TIMEOUT = 0xA00104
DTC_COUNTER = 0xA00105
DTC_CHECKSUM = 0xA00106


@dataclass
class VehicleSnapshot:
    soc: float | None = None
    pack_voltage: float | None = None
    pack_current: float | None = None
    max_cell_temp: float | None = None
    battery_state: int | None = None


class VehicleControlEcu:
    def __init__(self, codec: Codec, limits: VehicleLimits | None = None) -> None:
        self.codec = codec
        self.limits = limits or VehicleLimits()
        self.dtcs = DtcStore()
        self.snapshot = VehicleSnapshot()
        self.events: list[MonitorEvent] = []
        self.last_bms_rx_s: float | None = None
        self.last_counter: int | None = None
        self._valid_recovery_frames = 0
        self._last_warnings: tuple[str, ...] = ()

    def _event(self, ts: float, code: str, message: str, **details: object) -> None:
        self.events.append(MonitorEvent(ts, code, Severity.WARNING, message, dict(details)))

    def _set_dtc(self, code: int, name: str, description: str, ts: float) -> None:
        self.dtcs.set(code, name, description, ts)

    def process_frame(self, frame: CanFrame, now_s: float) -> VehicleHealth:
        if frame.arbitration_id != BMS_STATUS_ID:
            return self.health()

        values = self.codec.decode_bms_status(frame)
        warnings: list[str] = []

        checksum_valid = bool(values.get("ChecksumValid", 1))
        if not checksum_valid:
            warnings.append("BMS_CHECKSUM_MISMATCH")
            self._set_dtc(DTC_CHECKSUM, "BMS_CHECKSUM", "BMS application checksum invalid", now_s)
            self._event(now_s, "BMS_CHECKSUM_MISMATCH", "Application checksum invalid")

        counter = int(values["Counter"])
        if self.last_counter is not None and counter != expected_next_counter(self.last_counter):
            warnings.append("BMS_COUNTER_SEQUENCE")
            self._set_dtc(DTC_COUNTER, "BMS_COUNTER", "BMS rolling counter sequence invalid", now_s)
            self._event(
                now_s,
                "BMS_COUNTER_SEQUENCE",
                "Unexpected rolling counter",
                previous=self.last_counter,
                received=counter,
            )
        self.last_counter = counter
        self.last_bms_rx_s = now_s

        soc = float(values["SOC"])
        voltage = float(values["PackVoltage"])
        current = float(values["PackCurrent"])
        temp = float(values["MaxCellTemp"])
        state = int(values["BatteryState"])
        self.snapshot = VehicleSnapshot(soc, voltage, current, temp, state)

        if not self.limits.soc_min <= soc <= self.limits.soc_max:
            warnings.append("BMS_SOC_IMPLAUSIBLE")
            self._set_dtc(DTC_SOC_IMPLAUSIBLE, "SOC_RANGE", "SOC outside configured range", now_s)
            self._event(now_s, "BMS_SOC_IMPLAUSIBLE", "SOC outside range", soc=soc)

        if not self.limits.voltage_min <= voltage <= self.limits.voltage_max:
            warnings.append("BMS_PACK_VOLTAGE_IMPLAUSIBLE")
            self._set_dtc(
                DTC_VOLTAGE_IMPLAUSIBLE,
                "PACK_VOLTAGE_RANGE",
                "Pack voltage outside configured range",
                now_s,
            )
            self._event(now_s, "BMS_PACK_VOLTAGE_IMPLAUSIBLE", "Pack voltage outside range", voltage=voltage)

        if temp > self.limits.max_temp_warning_c:
            warnings.append("BMS_OVER_TEMPERATURE")
            self._set_dtc(DTC_OVERTEMP, "OVER_TEMP", "Battery temperature above warning threshold", now_s)
            self._event(now_s, "BMS_OVER_TEMPERATURE", "Battery over-temperature", temperature=temp)

        if warnings:
            self._valid_recovery_frames = 0
        else:
            self._valid_recovery_frames += 1
            if self._valid_recovery_frames >= self.limits.recovery_frames:
                for code in (
                    DTC_SOC_IMPLAUSIBLE,
                    DTC_VOLTAGE_IMPLAUSIBLE,
                    DTC_OVERTEMP,
                    DTC_COUNTER,
                    DTC_CHECKSUM,
                    DTC_COMM_TIMEOUT,
                ):
                    self.dtcs.clear_active(code)

        self._last_warnings = tuple(warnings)
        return self.health()

    def supervise_timeouts(self, now_s: float) -> VehicleHealth:
        if self.last_bms_rx_s is None:
            return self.health()
        age_ms = (now_s - self.last_bms_rx_s) * 1000.0
        if age_ms > self.limits.bms_timeout_ms:
            if "BMS_COMMUNICATION_TIMEOUT" not in self._last_warnings:
                self._event(now_s, "BMS_COMMUNICATION_TIMEOUT", "BMS_Status reception timeout", age_ms=age_ms)
            self._set_dtc(DTC_COMM_TIMEOUT, "BMS_TIMEOUT", "BMS_Status not received in time", now_s)
            self._last_warnings = tuple(sorted(set(self._last_warnings + ("BMS_COMMUNICATION_TIMEOUT",))))
            self._valid_recovery_frames = 0
        return self.health()

    def health(self) -> VehicleHealth:
        active_dtcs = self.dtcs.codes(active_only=True)
        return VehicleHealth(not active_dtcs, self._last_warnings, active_dtcs)
