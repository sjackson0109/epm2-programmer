"""Tests for J2534 interface (simulation mode)."""
from vtbap.l1_hardware.j2534 import J2534Interface, WindowsJ2534Interface
from vtbap.l1_hardware.protocol import SimulationInterface
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

# ------------------------------------------------------------------
# Concern 5: SimulationInterface and dependency injection tests
# ------------------------------------------------------------------

def test_simulation_interface_open_connect():
    iface = SimulationInterface()
    assert iface.open() is True
    assert iface.connect() is True
    assert iface.is_connected is True

def test_simulation_interface_read_returns_none():
    iface = SimulationInterface()
    iface.open()
    iface.connect()
    assert iface.read_msg() is None

def test_simulation_interface_read_fixture():
    fixture = bytes([0x03, 0x62, 0x12, 0x34, 0x05])
    iface = SimulationInterface(read_fixture=fixture)
    iface.open()
    iface.connect()
    assert iface.read_msg() == fixture

def test_simulation_interface_write_returns_true():
    iface = SimulationInterface()
    iface.open()
    iface.connect()
    assert iface.write_msg(b"\x01\x02") is True

def test_vci_manager_accepts_injected_interface():
    """VCIManager should use an injected J2534Protocol without creating its own."""
    sim = SimulationInterface()
    mgr = VCIManager(interface=sim)
    assert mgr.connect() is True
    assert mgr.is_connected is True
    assert mgr.interface is sim

def test_windows_j2534_alias():
    """J2534Interface backward-compat alias must point to WindowsJ2534Interface."""
    assert J2534Interface is WindowsJ2534Interface

