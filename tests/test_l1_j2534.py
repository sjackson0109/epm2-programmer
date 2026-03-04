"""Tests for J2534 interface (simulation mode)."""
from vtbap.l1_hardware.j2534 import J2534Interface
from vtbap.l1_hardware.vci_manager import VCIManager

def test_simulation_mode_no_dll():
    iface = J2534Interface(dll_path=None)
    assert iface.simulation_mode is True

def test_simulation_open_connect():
    iface = J2534Interface(dll_path=None)
    assert iface.open() is True
    assert iface.connect() is True
    assert iface.is_connected is True

def test_simulation_read_msg_returns_none():
    iface = J2534Interface(dll_path=None)
    iface.open()
    result = iface.read_msg()
    assert result is None

def test_vci_manager_connect_simulation():
    mgr = VCIManager(dll_path=None)
    assert mgr.connect() is True
    assert mgr.is_connected is True

def test_vci_manager_ensure_connected():
    mgr = VCIManager(dll_path=None)
    assert mgr.ensure_connected() is True
