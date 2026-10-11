import os

import pytest

from automotive_can.can.socketcan import SocketCanEndpoint
from automotive_can.model import CanFrame

pytestmark = pytest.mark.requires_socketcan


@pytest.mark.skipif(os.getenv("CAN_SOCKETCAN_TEST") != "1", reason="set CAN_SOCKETCAN_TEST=1 with vcan0 available")
def test_python_can_socketcan_round_trip() -> None:
    pytest.importorskip("can")
    tx = SocketCanEndpoint("vcan0")
    rx = SocketCanEndpoint("vcan0")
    try:
        tx.send(CanFrame(0x321, bytes.fromhex("DE AD BE EF")))
        frame = rx.recv(timeout_s=0.5)
        assert frame is not None
        assert frame.arbitration_id == 0x321
        assert frame.data == bytes.fromhex("DE AD BE EF")
    finally:
        tx.close()
        rx.close()
