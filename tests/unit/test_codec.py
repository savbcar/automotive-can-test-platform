from pathlib import Path

import pytest

from automotive_can.dbc_codec import BMS_STATUS_ID, CantoolsDbcCodec, ReferenceDbcCodec


@pytest.fixture
def signals() -> dict[str, float | int]:
    return {
        "SOC": 82.5,
        "PackVoltage": 400.2,
        "PackCurrent": -42.3,
        "MaxCellTemp": 31.0,
        "BatteryState": 1,
        "FaultFlags": 2,
        "Counter": 7,
    }


def test_reference_codec_exact_payload(signals: dict[str, float | int]) -> None:
    frame = ReferenceDbcCodec().encode_bms_status(signals)
    assert frame.arbitration_id == BMS_STATUS_ID
    # Byte 7 high nibble is the computed educational checksum.
    assert frame.data[:7] == bytes.fromhex("A5 A2 0F 59 FE 47 11")
    assert frame.data[7] & 0x0F == 7


def test_reference_codec_round_trip(signals: dict[str, float | int]) -> None:
    codec = ReferenceDbcCodec()
    decoded = codec.decode_bms_status(codec.encode_bms_status(signals))
    assert decoded["SOC"] == pytest.approx(82.5)
    assert decoded["PackVoltage"] == pytest.approx(400.2)
    assert decoded["PackCurrent"] == pytest.approx(-42.3)
    assert decoded["MaxCellTemp"] == pytest.approx(31.0)
    assert decoded["BatteryState"] == 1
    assert decoded["FaultFlags"] == 2
    assert decoded["Counter"] == 7
    assert decoded["ChecksumValid"] == 1


def test_reference_codec_allows_test_range_above_100_soc(signals: dict[str, float | int]) -> None:
    signals["SOC"] = 110.0
    codec = ReferenceDbcCodec()
    assert codec.decode_bms_status(codec.encode_bms_status(signals))["SOC"] == 110.0


def test_reference_codec_rejects_unrepresentable_soc(signals: dict[str, float | int]) -> None:
    signals["SOC"] = 200.0
    with pytest.raises(ValueError):
        ReferenceDbcCodec().encode_bms_status(signals)


def test_thermal_round_trip() -> None:
    codec = ReferenceDbcCodec()
    frame = codec.encode_thermal_status(
        {"CoolantTemp": 33, "PumpDuty": 45, "FanDuty": 20, "ThermalState": 1, "Counter": 4}
    )
    decoded = codec.decode_thermal_status(frame)
    assert decoded["CoolantTemp"] == 33
    assert decoded["PumpDuty"] == 45
    assert decoded["FanDuty"] == 20
    assert decoded["Counter"] == 4
    assert decoded["ChecksumValid"] == 1


def test_cantools_and_reference_codec_have_same_layout(signals: dict[str, float | int]) -> None:
    pytest.importorskip("cantools")
    root = Path(__file__).resolve().parents[2]
    reference = ReferenceDbcCodec().encode_bms_status(signals)
    cantools_frame = CantoolsDbcCodec(root / "dbc" / "vehicle_can.dbc").encode_bms_status(signals)
    assert cantools_frame.data == reference.data
