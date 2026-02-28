"""CAN session helpers."""
from __future__ import annotations
import logging
from typing import Optional

from vtbap.l1_hardware.j2534 import J2534Interface

logger = logging.getLogger(__name__)

# Standard 11-bit CAN arbitration ID for OBD-II functional request
OBD2_REQUEST_ID  = 0x7DF
OBD2_RESPONSE_ID = 0x7E8   # ECM response


class CANSession:
    """Thin wrapper providing raw CAN send/receive helpers."""

    def __init__(self, iface: J2534Interface):
        self._iface = iface

    def send(self, arb_id: int, data: bytes) -> bool:
        frame = arb_id.to_bytes(4, "big") + data
        return self._iface.write_msg(frame)

    def receive(self, timeout_ms: int = 200) -> Optional[tuple[int, bytes]]:
        raw = self._iface.read_msg(timeout_ms)
        if raw is None or len(raw) < 4:
            return None
        arb_id = int.from_bytes(raw[:4], "big")
        return arb_id, raw[4:]
