from __future__ import annotations


def checksum4(payload_without_checksum: bytes) -> int:
    """Educational 4-bit application checksum.

    This is deliberately simple and is NOT an OEM E2E profile. It sums every
    nibble and returns the one's-complement modulo 16.
    """
    total = 0
    for byte in payload_without_checksum:
        total += byte & 0x0F
        total += (byte >> 4) & 0x0F
    return (~total) & 0x0F


def insert_checksum4(data: bytes) -> bytes:
    if len(data) != 8:
        raise ValueError("BMS_Status must be exactly 8 bytes")
    mutable = bytearray(data)
    mutable[7] &= 0x0F
    csum = checksum4(bytes(mutable))
    mutable[7] |= csum << 4
    return bytes(mutable)


def verify_checksum4(data: bytes) -> bool:
    if len(data) != 8:
        return False
    expected = (data[7] >> 4) & 0x0F
    mutable = bytearray(data)
    mutable[7] &= 0x0F
    return checksum4(bytes(mutable)) == expected


def expected_next_counter(previous: int) -> int:
    return (previous + 1) & 0x0F
