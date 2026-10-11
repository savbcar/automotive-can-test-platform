from automotive_can.protection import expected_next_counter, insert_checksum4, verify_checksum4


def test_checksum_detects_payload_corruption() -> None:
    data = insert_checksum4(bytes.fromhex("A5 A2 0F 59 FE 47 01 00"))
    assert verify_checksum4(data)
    corrupt = bytearray(data)
    corrupt[2] ^= 0x01
    assert not verify_checksum4(bytes(corrupt))


def test_counter_wraps_modulo_16() -> None:
    assert expected_next_counter(14) == 15
    assert expected_next_counter(15) == 0
