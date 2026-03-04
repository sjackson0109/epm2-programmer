"""
L3 — OBD-II standard PID reader (Mode 01).

All operations are READ-ONLY.
"""
from __future__ import annotations
import logging
import struct
from typing import Optional

from vtbap.l2_transport.can import CANSession
from vtbap.safety import assert_read_only

logger = logging.getLogger(__name__)

# UDS service for OBD-II mode 01 = 0x01 (ShowCurrentData)
_SERVICE_SHOW_CURRENT = 0x01
# Safety check: mode 01 reads are permitted
assert_read_only(_SERVICE_SHOW_CURRENT)


def _obd2_request(session: CANSession, pid: int) -> Optional[bytes]:
    """Send a Mode 01 PID request and return the raw response bytes."""
    payload = bytes([0x02, _SERVICE_SHOW_CURRENT, pid, 0, 0, 0, 0])
    session.send(0x7DF, payload)
    result = session.receive(timeout_ms=200)
    if result is None:
        return None
    _, resp = result
    # Expected: [len, 0x41, pid, data…]
    if len(resp) < 3 or resp[1] != 0x41 or resp[2] != pid:
        return None
    return resp[3:]


class OBD2Reader:
    """Reads mandatory OBD-II signals."""

    def __init__(self, session: CANSession):
        self._session = session

    # ------------------------------------------------------------------

    def vehicle_speed(self) -> Optional[float]:
        """PID 0x0D — Vehicle Speed (km/h)."""
        raw = _obd2_request(self._session, 0x0D)
        if raw is None:
            return None
        return float(raw[0])  # 1 km/h per bit

    def engine_rpm(self) -> Optional[float]:
        """PID 0x0C — Engine RPM."""
        raw = _obd2_request(self._session, 0x0C)
        if raw is None or len(raw) < 2:
            return None
        return ((raw[0] * 256) + raw[1]) / 4.0

    def throttle_position(self) -> Optional[float]:
        """PID 0x11 — Throttle Position (%)."""
        raw = _obd2_request(self._session, 0x11)
        if raw is None:
            return None
        return raw[0] * 100.0 / 255.0

    def accelerator_pedal_position(self) -> Optional[float]:
        """PID 0x49 — Accelerator Pedal Position (%)."""
        raw = _obd2_request(self._session, 0x49)
        if raw is None:
            return None
        return raw[0] * 100.0 / 255.0

    def engine_load(self) -> Optional[float]:
        """PID 0x04 — Calculated Engine Load (%)."""
        raw = _obd2_request(self._session, 0x04)
        if raw is None:
            return None
        return raw[0] * 100.0 / 255.0

    def intake_manifold_pressure(self) -> Optional[float]:
        """PID 0x0B — Intake Manifold Absolute Pressure (kPa)."""
        raw = _obd2_request(self._session, 0x0B)
        if raw is None:
            return None
        return float(raw[0])

    def read_all(self) -> dict:
        return {
            "vehicle_speed":          self.vehicle_speed(),
            "engine_rpm":             self.engine_rpm(),
            "throttle_position":      self.throttle_position(),
            "accelerator_pedal":      self.accelerator_pedal_position(),
            "engine_load":            self.engine_load(),
            "intake_manifold_press":  self.intake_manifold_pressure(),
        }
