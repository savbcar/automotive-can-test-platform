from automotive_can.can.inmemory import InMemoryCanHub
from automotive_can.model import CanFrame


def test_hub_broadcasts_to_other_nodes_only() -> None:
    hub = InMemoryCanHub()
    a = hub.endpoint("a")
    b = hub.endpoint("b")
    c = hub.endpoint("c")
    frame = CanFrame(0x123, b"\x01\x02")
    a.send(frame, timestamp_s=1.25)
    assert a.recv() is None
    assert b.recv() == CanFrame(0x123, b"\x01\x02", timestamp_s=1.25)
    assert c.recv() == CanFrame(0x123, b"\x01\x02", timestamp_s=1.25)
