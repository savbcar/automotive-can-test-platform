import pytest

from automotive_can.dbc_codec import ReferenceDbcCodec
from automotive_can.fault_injection.injector import FaultInjector, FaultKind, FaultRule


def signals() -> dict[str, float | int]:
    return {
        "SOC": 80.0,
        "PackVoltage": 400.0,
        "PackCurrent": -20.0,
        "MaxCellTemp": 35.0,
        "BatteryState": 1,
        "FaultFlags": 0,
        "Counter": 0,
    }


def test_drop_fault_removes_frame_in_window() -> None:
    codec = ReferenceDbcCodec()
    injector = FaultInjector([FaultRule(FaultKind.DROP, 1.0, 2.0)])
    frame = codec.encode_bms_status(signals())
    assert injector.mutate_frame(frame, 0.5)
    assert injector.mutate_frame(frame, 1.5) == []


def test_delay_fault_releases_later() -> None:
    codec = ReferenceDbcCodec()
    injector = FaultInjector([FaultRule(FaultKind.DELAY, 1.0, 2.0, delay_ms=400)])
    frame = codec.encode_bms_status(signals())
    assert injector.mutate_frame(frame, 1.0) == []
    assert injector.release_due(1.39) == []
    assert len(injector.release_due(1.40)) == 1


def test_override_and_stuck_signal_faults() -> None:
    override = FaultInjector(
        [FaultRule(FaultKind.OVERRIDE_SIGNAL, 0.0, 1.0, signal="SOC", value=110.0)]
    )
    assert override.mutate_signals(signals(), 0.5)["SOC"] == 110.0

    stuck = FaultInjector([FaultRule(FaultKind.STUCK_SIGNAL, 0.0, 2.0, signal="SOC")])
    first = signals()
    first["SOC"] = 80.0
    second = signals()
    second["SOC"] = 75.0
    assert stuck.mutate_signals(first, 0.1)["SOC"] == 80.0
    assert stuck.mutate_signals(second, 0.2)["SOC"] == 80.0


def test_noisy_signal_is_deterministic() -> None:
    injector = FaultInjector(
        [FaultRule(FaultKind.NOISY_SIGNAL, 0.0, 2.0, signal="MaxCellTemp", amplitude=2.0)]
    )
    a = injector.mutate_signals(signals(), 0.25)["MaxCellTemp"]
    b = injector.mutate_signals(signals(), 0.25)["MaxCellTemp"]
    assert a == pytest.approx(b)
    assert a != 35.0
