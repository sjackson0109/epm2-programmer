"""Tests for UDS extended signal reader in simulation mode."""
from unittest.mock import MagicMock
from vtbap.l3_vehicle_comms.uds import UDSReader, _DID_GEAR_ACTUAL


def make_uds_response(did: int, payload: bytes):
    """Build a mock UDS ReadDataByIdentifier positive response."""
    did_hi = (did >> 8) & 0xFF
    did_lo = did & 0xFF
    data = bytes([len(payload) + 3, 0x62, did_hi, did_lo]) + payload
    session = MagicMock()
    session.receive.return_value = (0x7DF, data)
    return session


def test_gear_actual():
    session = make_uds_response(_DID_GEAR_ACTUAL, bytes([3]))
    reader = UDSReader(session)
    assert reader.gear_actual() == 3


def test_none_on_nrc():
    session = MagicMock()
    session.receive.return_value = (0x7DF, bytes([3, 0x7F, 0x22, 0x31, 0, 0, 0, 0]))
    reader = UDSReader(session)
    assert reader.gear_actual() is None


def test_read_all_graceful():
    session = MagicMock()
    session.receive.return_value = None
    reader = UDSReader(session)
    result = reader.read_all()
    assert isinstance(result, dict)
    for v in result.values():
        assert v is None
