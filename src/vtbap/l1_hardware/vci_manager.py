"""
L1 — VCI Device Manager.

Handles enumeration, selection, and automatic reconnection of the
VXDIAG VCX SE PSA interface (or any J2534-compatible device).
"""
from __future__ import annotations
import logging
import time
from typing import Optional

from vtbap.l1_hardware.j2534 import WindowsJ2534Interface, J2534Error
from vtbap.l1_hardware.protocol import J2534Protocol

logger = logging.getLogger(__name__)

RECONNECT_INTERVAL_S = 0.5


class VCIManager:
    """Manages the lifecycle and heartbeat of a J2534 VCI connection.

    Accepts either a pre-built ``J2534Protocol`` instance (dependency
    injection, preferred for testing) or a ``dll_path`` string which
    constructs a ``WindowsJ2534Interface`` internally.

    Args:
        dll_path: Path to the J2534 DLL (Windows only).  Ignored when
            *interface* is provided.
        reconnect_timeout_s: How long to wait during auto-reconnect.
        interface: Pre-built ``J2534Protocol`` instance to use directly.
            When provided, *dll_path* is ignored.
    """

    def __init__(
        self,
        dll_path: Optional[str] = None,
        reconnect_timeout_s: float = 3.0,
        interface: Optional[J2534Protocol] = None,
    ):
        self._dll_path = dll_path
        self._reconnect_timeout = reconnect_timeout_s
        self._injected_iface: Optional[J2534Protocol] = interface
        self._iface: Optional[J2534Protocol] = interface
        self._connected = False

    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Open the VCI and establish a CAN/ISO15765 channel."""
        if self._injected_iface is not None:
            self._iface = self._injected_iface
        else:
            self._iface = WindowsJ2534Interface(self._dll_path)
        try:
            self._iface.open()
            self._iface.connect()
            self._connected = True
            sim = getattr(self._iface, "simulation_mode", False)
            logger.info("VCI connected (simulation=%s).", sim)
            return True
        except J2534Error as exc:
            logger.error("VCI connect failed: %s", exc)
            self._connected = False
            return False

    def ensure_connected(self) -> bool:
        """Auto-reconnect within reconnect_timeout_s if disconnected."""
        if self._connected and self._iface and self._iface.is_connected:
            return True
        deadline = time.monotonic() + self._reconnect_timeout
        while time.monotonic() < deadline:
            logger.info("Attempting VCI reconnect …")
            if self.connect():
                return True
            time.sleep(RECONNECT_INTERVAL_S)
        logger.error("VCI reconnect timed out after %.1fs.", self._reconnect_timeout)
        return False

    def disconnect(self) -> None:
        if self._iface:
            self._iface.disconnect()
            self._iface.close()
        self._connected = False

    @property
    def interface(self) -> Optional[J2534Protocol]:
        return self._iface

    @property
    def is_connected(self) -> bool:
        return self._connected

