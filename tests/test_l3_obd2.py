"""Tests for OBD-II PID reader in simulation mode."""
from unittest.mock import MagicMock, patch
from vtbap.l3_vehicle_comms.obd2 import OBD2Reader


def make_session(response_bytes):
    session = MagicMock()
    session.receive.return_value = (0x7E8, response_bytes)
    return session


def test_vehicle_speed():
    # PID 0x0D response: [len=3, 0x41, 0x0D, value=80]
    session = make_session(bytes([3, 0x41, 0x0D, 80, 0, 0, 0, 0]))
    reader = OBD2Reader(session)
    assert reader.vehicle_speed() == 80.0


def test_engine_rpm():
    # PID 0x0C: (A*256+B)/4
    session = make_session(bytes([4, 0x41, 0x0C, 0x19, 0x00, 0, 0, 0]))
    reader = OBD2Reader(session)
    assert reader.engine_rpm() == (0x19 * 256 + 0x00) / 4.0


def test_none_on_no_response():
    session = MagicMock()
    session.receive.return_value = None
    reader = OBD2Reader(session)
    assert reader.vehicle_speed() is None
    assert reader.engine_rpm() is None


def test_read_all_returns_dict():
    session = MagicMock()
    session.receive.return_value = None
    reader = OBD2Reader(session)
    result = reader.read_all()
    assert isinstance(result, dict)
    assert "vehicle_speed" in result
