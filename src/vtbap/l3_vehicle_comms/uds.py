"""
L3 — PSA/Stellantis UDS extended signal reader.

All operations are READ-ONLY. Signals are best-effort; if unavailable the
system degrades gracefully (returns None).
"""
from __future__ import annotations
import logging
from typing import Optional

from vtbap.l2_transport.can import CANSession
from vtbap.safety import assert_read_only, SafetyViolationError

logger = logging.getLogger(__name__)

# UDS ReadDataByIdentifier (0x22) — read-only service
_SVC_READ_DATA = 0x22
assert_read_only(_SVC_READ_DATA)

# PSA proprietary Data Identifiers (DID) — best-effort
# These are indicative; actual DIDs depend on TCU firmware version.
_DID_GEAR_ACTUAL        = 0x1234
_DID_GEAR_COMMANDED     = 0x1235
_DID_TC_LOCK_STATE      = 0x1236
_DID_DRIVER_TORQUE_REQ  = 0x1237
_DID_ENGINE_TORQUE      = 0x1238
_DID_BOOST_PRESSURE     = 0x1239
_DID_ENGINE_TORQUE_LIMIT= 0x123A
_DID_DRIVE_MODE         = 0x123B
_DID_CLUTCH_SLIP        = 0x123C
_DID_TRANS_INPUT_RPM    = 0x123D
_DID_TRANS_OUTPUT_RPM   = 0x123E


def _uds_read_did(session: CANSession, did: int) -> Optional[bytes]:
    """Send a UDS ReadDataByIdentifier request; returns raw data or None."""
    did_hi = (did >> 8) & 0xFF
    did_lo = did & 0xFF
    payload = bytes([0x03, _SVC_READ_DATA, did_hi, did_lo, 0, 0, 0])
    session.send(0x7DF, payload)
    result = session.receive(timeout_ms=200)
    if result is None:
        return None
    _, resp = result
    # Expected positive response: [len, 0x62, did_hi, did_lo, data…]
    if len(resp) < 4 or resp[1] != 0x62:
        return None
    if resp[2] != did_hi or resp[3] != did_lo:
        return None
    return resp[4:]


class UDSReader:
    """Reads PSA/Stellantis extended transmission signals via UDS."""

    def __init__(self, session: CANSession):
        self._session = session

    def gear_actual(self) -> Optional[int]:
        raw = _uds_read_did(self._session, _DID_GEAR_ACTUAL)
        return int(raw[0]) if raw else None

    def gear_commanded(self) -> Optional[int]:
        raw = _uds_read_did(self._session, _DID_GEAR_COMMANDED)
        return int(raw[0]) if raw else None

    def torque_converter_lock(self) -> Optional[bool]:
        raw = _uds_read_did(self._session, _DID_TC_LOCK_STATE)
        return bool(raw[0]) if raw else None

    def driver_torque_request(self) -> Optional[float]:
        raw = _uds_read_did(self._session, _DID_DRIVER_TORQUE_REQ)
        if raw is None or len(raw) < 2:
            return None
        return int.from_bytes(raw[:2], "big") * 0.5  # Nm, example scaling

    def engine_torque(self) -> Optional[float]:
        raw = _uds_read_did(self._session, _DID_ENGINE_TORQUE)
        if raw is None or len(raw) < 2:
            return None
        return int.from_bytes(raw[:2], "big") * 0.5

    def boost_pressure(self) -> Optional[float]:
        raw = _uds_read_did(self._session, _DID_BOOST_PRESSURE)
        if raw is None or len(raw) < 2:
            return None
        return int.from_bytes(raw[:2], "big") * 0.1  # kPa

    def engine_torque_limit(self) -> Optional[float]:
        raw = _uds_read_did(self._session, _DID_ENGINE_TORQUE_LIMIT)
        if raw is None or len(raw) < 2:
            return None
        return int.from_bytes(raw[:2], "big") * 0.5

    def drive_mode(self) -> Optional[str]:
        raw = _uds_read_did(self._session, _DID_DRIVE_MODE)
        if raw is None:
            return None
        modes = {0: "Eco", 1: "Normal", 2: "Sport", 3: "Manual"}
        return modes.get(raw[0], f"Unknown({raw[0]})")

    def clutch_slip(self) -> Optional[float]:
        raw = _uds_read_did(self._session, _DID_CLUTCH_SLIP)
        if raw is None or len(raw) < 2:
            return None
        return int.from_bytes(raw[:2], "big") * 0.1

    def transmission_input_rpm(self) -> Optional[float]:
        raw = _uds_read_did(self._session, _DID_TRANS_INPUT_RPM)
        if raw is None or len(raw) < 2:
            return None
        return float(int.from_bytes(raw[:2], "big"))

    def transmission_output_rpm(self) -> Optional[float]:
        raw = _uds_read_did(self._session, _DID_TRANS_OUTPUT_RPM)
        if raw is None or len(raw) < 2:
            return None
        return float(int.from_bytes(raw[:2], "big"))

    def read_all(self) -> dict:
        return {
            "gear_actual":            self.gear_actual(),
            "gear_commanded":         self.gear_commanded(),
            "tc_lock":                self.torque_converter_lock(),
            "driver_torque_request":  self.driver_torque_request(),
            "engine_torque":          self.engine_torque(),
            "boost_pressure":         self.boost_pressure(),
            "engine_torque_limit":    self.engine_torque_limit(),
            "drive_mode":             self.drive_mode(),
            "clutch_slip":            self.clutch_slip(),
            "trans_input_rpm":        self.transmission_input_rpm(),
            "trans_output_rpm":       self.transmission_output_rpm(),
        }
