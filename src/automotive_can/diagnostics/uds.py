from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Callable

from .dtc import DtcStore


class Sid(IntEnum):
    DIAGNOSTIC_SESSION_CONTROL = 0x10
    READ_DTC_INFORMATION = 0x19
    READ_DATA_BY_IDENTIFIER = 0x22
    TESTER_PRESENT = 0x3E
    CLEAR_DIAGNOSTIC_INFORMATION = 0x14


class Nrc(IntEnum):
    GENERAL_REJECT = 0x10
    SERVICE_NOT_SUPPORTED = 0x11
    SUBFUNCTION_NOT_SUPPORTED = 0x12
    INCORRECT_MESSAGE_LENGTH = 0x13
    REQUEST_OUT_OF_RANGE = 0x31


@dataclass(frozen=True)
class UdsResponse:
    payload: bytes
    positive: bool


class EducationalUdsServer:
    """Minimal single-frame UDS-like server for learning/testing.

    It intentionally does not implement ISO-TP segmentation, timing parameters,
    security access, programming services, authentication, or full ISO 14229
    semantics. Service IDs and positive/negative response conventions follow UDS.
    """

    def __init__(self, dtcs: DtcStore, did_readers: dict[int, Callable[[], bytes]]) -> None:
        self.dtcs = dtcs
        self.did_readers = did_readers
        self.session = 0x01
        self.tester_present_count = 0

    @staticmethod
    def _negative(sid: int, nrc: Nrc) -> UdsResponse:
        return UdsResponse(bytes([0x7F, sid & 0xFF, int(nrc)]), positive=False)

    def handle(self, request: bytes) -> UdsResponse:
        if not request:
            return self._negative(0x00, Nrc.INCORRECT_MESSAGE_LENGTH)
        sid = request[0]
        if sid == Sid.DIAGNOSTIC_SESSION_CONTROL:
            if len(request) != 2:
                return self._negative(sid, Nrc.INCORRECT_MESSAGE_LENGTH)
            if request[1] not in (0x01, 0x03):
                return self._negative(sid, Nrc.SUBFUNCTION_NOT_SUPPORTED)
            self.session = request[1]
            return UdsResponse(bytes([sid + 0x40, self.session]), True)

        if sid == Sid.READ_DATA_BY_IDENTIFIER:
            if len(request) != 3:
                return self._negative(sid, Nrc.INCORRECT_MESSAGE_LENGTH)
            did = (request[1] << 8) | request[2]
            reader = self.did_readers.get(did)
            if reader is None:
                return self._negative(sid, Nrc.REQUEST_OUT_OF_RANGE)
            return UdsResponse(bytes([sid + 0x40, request[1], request[2]]) + reader(), True)

        if sid == Sid.READ_DTC_INFORMATION:
            if len(request) != 2 or request[1] != 0x02:
                return self._negative(sid, Nrc.SUBFUNCTION_NOT_SUPPORTED)
            payload = bytearray([sid + 0x40, 0x02])
            for code in self.dtcs.codes(active_only=True):
                payload.extend(code.to_bytes(3, "big"))
            return UdsResponse(bytes(payload), True)

        if sid == Sid.TESTER_PRESENT:
            if len(request) != 2 or request[1] not in (0x00, 0x80):
                return self._negative(sid, Nrc.SUBFUNCTION_NOT_SUPPORTED)
            self.tester_present_count += 1
            return UdsResponse(bytes([sid + 0x40, request[1] & 0x7F]), True)

        if sid == Sid.CLEAR_DIAGNOSTIC_INFORMATION:
            if request != bytes([Sid.CLEAR_DIAGNOSTIC_INFORMATION, 0xFF, 0xFF, 0xFF]):
                return self._negative(sid, Nrc.REQUEST_OUT_OF_RANGE)
            self.dtcs.clear_all()
            return UdsResponse(bytes([sid + 0x40]), True)

        return self._negative(sid, Nrc.SERVICE_NOT_SUPPORTED)
