"""
L1 — VCI Device Manager.

Handles enumeration, selection, and automatic reconnection of the
VXDIAG VCX SE PSA interface (or any J2534-compatible device).
"""
from __future__ import annotations
import logging
import time
from typing import Optional

from vtbap.l1_hardware.j2534 import J2534Interface, J2534Error

logger = logging.getLogger(__name__)

RECONNECT_INTERVAL_S = 0.5


class VCIManager:
    """Manages the lifecycle and heartbeat of a J2534 VCI connection."""

    def __init__(
        self,
        dll_path: Optional[str] = None,
        reconnect_timeout_s: float = 3.0,
    ):
        self._dll_path = dll_path
        self._reconnect_timeout = reconnect_timeout_s
        self._iface: Optional[J2534Interface] = None
        self._connected = False

    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Open the VCI and establish a CAN/ISO15765 channel."""
        self._iface = J2534Interface(self._dll_path)
        try:
            self._iface.open()
            self._iface.connect()
            self._connected = True
            logger.info("VCI connected (simulation=%s).", self._iface.simulation_mode)
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
    def interface(self) -> Optional[J2534Interface]:
        return self._iface

    @property
    def is_connected(self) -> bool:
        return self._connected
