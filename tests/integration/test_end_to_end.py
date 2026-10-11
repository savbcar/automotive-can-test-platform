import pytest

from automotive_can.can.inmemory import InMemoryCanHub
from automotive_can.dbc_codec import ReferenceDbcCodec
from automotive_can.ecus.bms import BmsEcu
from automotive_can.ecus.vehicle import VehicleControlEcu


def test_bms_to_vehicle_over_virtual_hub() -> None:
    codec = ReferenceDbcCodec()
    bms = BmsEcu(codec)
    vehicle = VehicleControlEcu(codec)
    hub = InMemoryCanHub()
    bms_bus = hub.endpoint("bms")
    vehicle_bus = hub.endpoint("vehicle")

    bms_bus.send(bms.build_status_frame(), timestamp_s=0.0)
    frame = vehicle_bus.recv()
    assert frame is not None
    health = vehicle.process_frame(frame, 0.0)
    assert health.healthy
    assert vehicle.snapshot.soc == 82.5
    assert vehicle.snapshot.pack_voltage == pytest.approx(400.2)
