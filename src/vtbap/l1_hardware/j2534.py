"""
L1 — Hardware Interface Layer: J2534 Pass-Through API abstraction.

Wraps the Windows J2534 DLL via ctypes.  On non-Windows platforms or when
the DLL is unavailable, the interface degrades gracefully.

Platform requirement: real hardware requires Windows 10/11 and a VXDIAG
VCX SE (or compatible) J2534 DLL.  For cross-platform use, inject a
``SimulationInterface`` from ``vtbap.l1_hardware.protocol`` instead.
"""
from __future__ import annotations
import ctypes
import logging
import platform
import struct
from typing import Optional

from vtbap.l1_hardware.protocol import J2534Protocol

logger = logging.getLogger(__name__)

# J2534 PassThru protocol IDs
CAN         = 0x05
ISO15765    = 0x06

# J2534 error codes
ERR_SUCCESS = 0x00

class J2534Error(Exception):
    pass

class PASSTHRU_MSG(ctypes.Structure):
    _fields_ = [
        ("ProtocolID",   ctypes.c_ulong),
        ("RxStatus",     ctypes.c_ulong),
        ("TxFlags",      ctypes.c_ulong),
        ("Timestamp",    ctypes.c_ulong),
        ("DataSize",     ctypes.c_ulong),
        ("ExtraDataIndex", ctypes.c_ulong),
        ("Data",         ctypes.c_ubyte * 4128),
    ]


class WindowsJ2534Interface(J2534Protocol):
    """
    Thin wrapper around a J2534 v04.04 DLL.

    Platform requirement: requires Windows 10/11 and a compatible J2534 DLL
    (e.g. VXDIAG VCX SE).  If the DLL is unavailable (non-Windows or missing
    path) the interface runs in *simulation mode* and all reads return None.
    """

    def __init__(self, dll_path: Optional[str] = None):
        self._dll = None
        self._channel_id: Optional[int] = None
        self._device_id: Optional[int] = None
        self.simulation_mode = False

        if platform.system() != "Windows":
            logger.warning("Non-Windows platform: J2534 running in simulation mode.")
            self.simulation_mode = True
            return

        if dll_path is None:
            logger.warning("No J2534 DLL path provided: running in simulation mode.")
            self.simulation_mode = True
            return

        try:
            self._dll = ctypes.WinDLL(dll_path)  # type: ignore[attr-defined]
            logger.info("Loaded J2534 DLL: %s", dll_path)
        except OSError as exc:
            logger.error("Failed to load J2534 DLL %s: %s", dll_path, exc)
            self.simulation_mode = True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def open(self) -> bool:
        """Open a connection to the J2534 device."""
        if self.simulation_mode:
            logger.debug("J2534 open() called in simulation mode.")
            return True
        dev_id = ctypes.c_ulong(0)
        ret = self._dll.PassThruOpen(None, ctypes.byref(dev_id))
        if ret != ERR_SUCCESS:
            raise J2534Error(f"PassThruOpen failed: 0x{ret:08X}")
        self._device_id = dev_id.value
        return True

    def connect(self, protocol: int = ISO15765, baud: int = 500000) -> bool:
        """Establish a channel on the given protocol."""
        if self.simulation_mode:
            return True
        ch_id = ctypes.c_ulong(0)
        ret = self._dll.PassThruConnect(
            self._device_id, protocol, 0, baud, ctypes.byref(ch_id)
        )
        if ret != ERR_SUCCESS:
            raise J2534Error(f"PassThruConnect failed: 0x{ret:08X}")
        self._channel_id = ch_id.value
        return True

    def disconnect(self) -> None:
        """Disconnect the channel."""
        if self.simulation_mode or self._channel_id is None:
            return
        self._dll.PassThruDisconnect(self._channel_id)
        self._channel_id = None

    def close(self) -> None:
        """Close the device."""
        if self.simulation_mode or self._device_id is None:
            return
        self._dll.PassThruClose(self._device_id)
        self._device_id = None

    def write_msg(self, data: bytes, timeout_ms: int = 100) -> bool:
        """Send a raw J2534 message (read-only operations only)."""
        if self.simulation_mode:
            return True
        msg = PASSTHRU_MSG()
        msg.ProtocolID = ISO15765
        msg.DataSize = len(data)
        for i, b in enumerate(data):
            msg.Data[i] = b
        num_msgs = ctypes.c_ulong(1)
        ret = self._dll.PassThruWriteMsgs(
            self._channel_id, ctypes.byref(msg), ctypes.byref(num_msgs), timeout_ms
        )
        return ret == ERR_SUCCESS

    def read_msg(self, timeout_ms: int = 200) -> Optional[bytes]:
        """Read a raw J2534 message. Returns None on timeout/simulation."""
        if self.simulation_mode:
            return None
        msg = PASSTHRU_MSG()
        num_msgs = ctypes.c_ulong(1)
        ret = self._dll.PassThruReadMsgs(
            self._channel_id, ctypes.byref(msg), ctypes.byref(num_msgs), timeout_ms
        )
        if ret != ERR_SUCCESS:
            return None
        return bytes(msg.Data[: msg.DataSize])

    @property
    def is_connected(self) -> bool:
        return self.simulation_mode or self._channel_id is not None


# Backward-compatibility alias — existing code importing J2534Interface
# continues to work without changes.
J2534Interface = WindowsJ2534Interface

