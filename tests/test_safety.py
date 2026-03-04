"""Tests for safety constraint enforcement."""
import pytest
from vtbap.safety import assert_read_only, is_read_only_service, SafetyViolationError

def test_blocked_services_raise():
    blocked = [0x27, 0x2E, 0x34, 0x35, 0x36, 0x37, 0x31, 0x85, 0x28]
    for svc in blocked:
        with pytest.raises(SafetyViolationError):
            assert_read_only(svc)

def test_read_services_permitted():
    permitted = [0x01, 0x09, 0x22, 0x19, 0x3E]
    for svc in permitted:
        assert_read_only(svc)  # must not raise

def test_is_read_only_service():
    assert is_read_only_service(0x22) is True
    assert is_read_only_service(0x2E) is False
