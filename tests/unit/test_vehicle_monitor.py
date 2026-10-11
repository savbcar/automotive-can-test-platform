import pytest

from automotive_can.config import VehicleLimits
from automotive_can.dbc_codec import ReferenceDbcCodec
from automotive_can.ecus.vehicle import (
    DTC_CHECKSUM,
    DTC_COMM_TIMEOUT,
    DTC_COUNTER,
    DTC_OVERTEMP,
    DTC_SOC_IMPLAUSIBLE,
    DTC_VOLTAGE_IMPLAUSIBLE,
    VehicleControlEcu,
)


def base(counter: int = 0) -> dict[str, float | int]:
    return {
        "SOC": 80.0,
        "PackVoltage": 400.0,
        "PackCurrent": -20.0,
        "MaxCellTemp": 35.0,
        "BatteryState": 1,
        "FaultFlags": 0,
        "Counter": counter,
    }


def test_healthy_frame_is_accepted() -> None:
    codec = ReferenceDbcCodec()
    ecu = VehicleControlEcu(codec)
    health = ecu.process_frame(codec.encode_bms_status(base()), 0.0)
    assert health.healthy
    assert health.warnings == ()

@pytest.mark.parametrize(
    ("signal", "value", "warning", "dtc"),
    [
        ("SOC", 110.0, "BMS_SOC_IMPLAUSIBLE", DTC_SOC_IMPLAUSIBLE),
        ("PackVoltage", 220.0, "BMS_PACK_VOLTAGE_IMPLAUSIBLE", DTC_VOLTAGE_IMPLAUSIBLE),
        ("MaxCellTemp", 75.0, "BMS_OVER_TEMPERATURE", DTC_OVERTEMP),
    ],
)
def test_plausibility_monitors(signal: str, value: float, warning: str, dtc: int) -> None:
    codec = ReferenceDbcCodec()
    ecu = VehicleControlEcu(codec)
    values = base()
    values[signal] = value
    health = ecu.process_frame(codec.encode_bms_status(values), 0.0)
    assert warning in health.warnings
    assert dtc in health.dtcs


def test_timeout_dtc_after_configured_age() -> None:
    codec = ReferenceDbcCodec()
    ecu = VehicleControlEcu(codec, VehicleLimits(bms_timeout_ms=300))
    ecu.process_frame(codec.encode_bms_status(base()), 0.0)
    assert ecu.supervise_timeouts(0.300).healthy
    health = ecu.supervise_timeouts(0.301)
    assert "BMS_COMMUNICATION_TIMEOUT" in health.warnings
    assert DTC_COMM_TIMEOUT in health.dtcs


def test_wrong_counter_is_detected() -> None:
    codec = ReferenceDbcCodec()
    ecu = VehicleControlEcu(codec)
    ecu.process_frame(codec.encode_bms_status(base(0)), 0.0)
    health = ecu.process_frame(codec.encode_bms_status(base(3)), 0.1)
    assert "BMS_COUNTER_SEQUENCE" in health.warnings
    assert DTC_COUNTER in health.dtcs


def test_checksum_mismatch_is_detected() -> None:
    codec = ReferenceDbcCodec()
    ecu = VehicleControlEcu(codec)
    frame = codec.encode_bms_status(base())
    corrupt = bytearray(frame.data)
    corrupt[7] ^= 0x10
    health = ecu.process_frame(type(frame)(frame.arbitration_id, bytes(corrupt)), 0.0)
    assert "BMS_CHECKSUM_MISMATCH" in health.warnings
    assert DTC_CHECKSUM in health.dtcs


def test_dtc_recovers_after_configured_good_frames() -> None:
    codec = ReferenceDbcCodec()
    ecu = VehicleControlEcu(codec, VehicleLimits(recovery_frames=3))
    bad = base(0)
    bad["SOC"] = 110.0
    ecu.process_frame(codec.encode_bms_status(bad), 0.0)
    assert not ecu.health().healthy
    for idx in range(1, 4):
        ecu.process_frame(codec.encode_bms_status(base(idx)), idx * 0.1)
    assert ecu.health().healthy
