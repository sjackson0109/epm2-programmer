"""Tests for ISO 15765 framing."""
from vtbap.l2_transport.iso15765 import build_single_frame, parse_response
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
