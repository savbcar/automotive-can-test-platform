from __future__ import annotations

from ..dbc_codec import DIAG_REQUEST_ID, DIAG_RESPONSE_ID
from ..model import CanFrame
from .uds import EducationalUdsServer


def pack_single_frame(arbitration_id: int, payload: bytes) -> CanFrame:
    """Pack a deliberately simplified ISO-TP-like single frame.

    Byte 0 carries payload length (0..7), bytes 1..7 carry data/padding. This is
    educational only and must not be described as an ISO 15765-2 implementation.
    """
    if len(payload) > 7:
        raise ValueError("educational diagnostic transport supports <= 7 payload bytes")
    data = bytes([len(payload)]) + payload + bytes(7 - len(payload))
    return CanFrame(arbitration_id, data)


def unpack_single_frame(frame: CanFrame) -> bytes:
    if len(frame.data) != 8:
        raise ValueError("diagnostic CAN frame must contain 8 bytes")
    length = frame.data[0]
    if length > 7:
        raise ValueError("invalid educational diagnostic length")
    return frame.data[1 : 1 + length]


class DiagnosticCanServer:
    def __init__(self, uds: EducationalUdsServer) -> None:
        self.uds = uds

    def handle_frame(self, frame: CanFrame) -> CanFrame | None:
        if frame.arbitration_id != DIAG_REQUEST_ID:
            return None
        request = unpack_single_frame(frame)
        response = self.uds.handle(request)
        return pack_single_frame(DIAG_RESPONSE_ID, response.payload)
