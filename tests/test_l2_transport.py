"""Tests for ISO 15765 framing."""
from vtbap.l2_transport.iso15765 import (
    build_single_frame,
    parse_response,
    parse_first_frame,
    parse_consecutive_frame,
    FrameReassembler,
)
import pytest

def test_single_frame_build():
    frame = build_single_frame(b"\x01\x0D")
    assert len(frame) == 8
    assert frame[0] == 2  # length
    assert frame[1] == 0x01
    assert frame[2] == 0x0D

def test_single_frame_too_long():
    with pytest.raises(ValueError):
        build_single_frame(b"\x00" * 8)

def test_parse_single_frame_response():
    data = bytes([0x03, 0x41, 0x0D, 0x50, 0, 0, 0, 0])
    payload = parse_response(data)
    assert payload == bytes([0x41, 0x0D, 0x50])

def test_parse_empty():
    assert parse_response(b"") == b""

# ------------------------------------------------------------------
# Concern 2: multi-frame helpers
# ------------------------------------------------------------------

def test_parse_first_frame():
    # FF: 0x10 0x0A = total length 10, payload starts at byte 2
    frame = bytes([0x10, 0x0A, 0x62, 0x12, 0x34, 0x01, 0x02, 0x03])
    total, payload = parse_first_frame(frame)
    assert total == 10
    assert payload == bytes([0x62, 0x12, 0x34, 0x01, 0x02, 0x03])

def test_parse_first_frame_invalid():
    with pytest.raises(ValueError):
        parse_first_frame(bytes([0x03, 0x62, 0x12, 0x34]))  # SF, not FF

def test_parse_consecutive_frame():
    frame = bytes([0x21, 0x04, 0x05, 0x06, 0x07, 0x00, 0x00])
    seq, payload = parse_consecutive_frame(frame)
    assert seq == 1
    assert payload == bytes([0x04, 0x05, 0x06, 0x07, 0x00, 0x00])

def test_parse_consecutive_frame_invalid():
    with pytest.raises(ValueError):
        parse_consecutive_frame(bytes([0x10, 0x0A]))  # FF, not CF

# ------------------------------------------------------------------
# FrameReassembler tests
# ------------------------------------------------------------------

def test_reassembler_single_frame():
    r = FrameReassembler()
    sf = bytes([0x04, 0x62, 0x12, 0x34, 0x03, 0x00, 0x00, 0x00])
    result = r.feed(sf)
    assert result == bytes([0x62, 0x12, 0x34, 0x03])

def test_reassembler_multi_frame():
    r = FrameReassembler()
    # Total length = 9 bytes; first frame carries 6, consecutive frame carries 3
    # (remaining 4 bytes in CF are padding and must be trimmed)
    ff = bytes([0x10, 0x09, 0x62, 0x12, 0x34, 0x01, 0x02, 0x03])
    cf = bytes([0x21, 0x04, 0x05, 0x06, 0x00, 0x00, 0x00, 0x00])
    assert r.feed(ff) is None
    result = r.feed(cf)
    # Padding bytes beyond total_length (9) must be stripped
    assert result == bytes([0x62, 0x12, 0x34, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06])
    assert len(result) == 9

def test_reassembler_sequence_error():
    r = FrameReassembler()
    ff = bytes([0x10, 0x0A, 0x62, 0x12, 0x34, 0x01, 0x02, 0x03])
    r.feed(ff)
    # Wrong sequence number (expected 0x21 = seq 1, got 0x22 = seq 2)
    cf_wrong = bytes([0x22, 0x04, 0x05, 0x06, 0x00, 0x00, 0x00, 0x00])
    with pytest.raises(ValueError):
        r.feed(cf_wrong)

def test_reassembler_unexpected_cf_without_ff():
    r = FrameReassembler()
    cf = bytes([0x21, 0x04, 0x05, 0x06])
    with pytest.raises(ValueError):
        r.feed(cf)

