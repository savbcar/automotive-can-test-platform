from automotive_can.diagnostics.dtc import DtcStore
from automotive_can.diagnostics.transport import DiagnosticCanServer, pack_single_frame, unpack_single_frame
from automotive_can.diagnostics.uds import EducationalUdsServer


def make_server() -> EducationalUdsServer:
    dtcs = DtcStore()
    dtcs.set(0xA00101, "SOC_RANGE", "SOC invalid", 1.0)
    return EducationalUdsServer(dtcs, {0xF190: lambda: bytes.fromhex("03 39")})


def test_session_control_positive_response() -> None:
    uds = make_server()
    resp = uds.handle(bytes([0x10, 0x03]))
    assert resp.positive
    assert resp.payload == bytes([0x50, 0x03])


def test_read_did_positive_response() -> None:
    resp = make_server().handle(bytes([0x22, 0xF1, 0x90]))
    assert resp.positive
    assert resp.payload == bytes.fromhex("62 F1 90 03 39")


def test_unknown_did_negative_response() -> None:
    resp = make_server().handle(bytes([0x22, 0x12, 0x34]))
    assert not resp.positive
    assert resp.payload == bytes.fromhex("7F 22 31")


def test_read_dtc_information() -> None:
    resp = make_server().handle(bytes([0x19, 0x02]))
    assert resp.positive
    assert bytes.fromhex("A0 01 01") in resp.payload


def test_tester_present() -> None:
    uds = make_server()
    assert uds.handle(bytes([0x3E, 0x00])).payload == bytes([0x7E, 0x00])
    assert uds.tester_present_count == 1


def test_clear_dtc_information() -> None:
    uds = make_server()
    assert uds.handle(bytes.fromhex("14 FF FF FF")).payload == bytes([0x54])
    assert uds.dtcs.codes() == ()


def test_diagnostic_can_transport_round_trip() -> None:
    server = DiagnosticCanServer(make_server())
    req = pack_single_frame(0x700, bytes([0x10, 0x03]))
    resp = server.handle_frame(req)
    assert resp is not None
    assert resp.arbitration_id == 0x708
    assert unpack_single_frame(resp) == bytes([0x50, 0x03])
