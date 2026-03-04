"""
L3 — PSA/Stellantis UDS extended signal reader.

All operations are READ-ONLY. Signals are best-effort; if unavailable the
system degrades gracefully (returns None).
"""
from __future__ import annotations
import logging
from typing import Optional

from vtbap.l2_transport.can import CANSession
from vtbap.l2_transport.iso15765 import FrameReassembler
from vtbap.config import PSA_DIDS
from vtbap.safety import assert_read_only, SafetyViolationError

logger = logging.getLogger(__name__)

# UDS ReadDataByIdentifier (0x22) — read-only service
_SVC_READ_DATA = 0x22
assert_read_only(_SVC_READ_DATA)

# Default PSA DID constants — kept for backward compatibility.
# WARNING: indicative placeholders only; verify against actual TCU firmware.
_DID_GEAR_ACTUAL        = PSA_DIDS["gear_actual"]
_DID_GEAR_COMMANDED     = PSA_DIDS["gear_commanded"]
_DID_TC_LOCK_STATE      = PSA_DIDS["tc_lock_state"]
_DID_DRIVER_TORQUE_REQ  = PSA_DIDS["driver_torque_req"]
_DID_ENGINE_TORQUE      = PSA_DIDS["engine_torque"]
_DID_BOOST_PRESSURE     = PSA_DIDS["boost_pressure"]
_DID_ENGINE_TORQUE_LIMIT= PSA_DIDS["engine_torque_limit"]
_DID_DRIVE_MODE         = PSA_DIDS["drive_mode"]
_DID_CLUTCH_SLIP        = PSA_DIDS["clutch_slip"]
_DID_TRANS_INPUT_RPM    = PSA_DIDS["trans_input_rpm"]
_DID_TRANS_OUTPUT_RPM   = PSA_DIDS["trans_output_rpm"]


def _uds_read_did(session: CANSession, did: int) -> Optional[bytes]:
    """Send a UDS ReadDataByIdentifier request; returns raw data or None."""
    did_hi = (did >> 8) & 0xFF
    did_lo = did & 0xFF
    payload = bytes([0x03, _SVC_READ_DATA, did_hi, did_lo, 0, 0, 0])
    session.send(0x7DF, payload)

    reassembler = FrameReassembler()
    while True:
        result = session.receive(timeout_ms=200)
        if result is None:
            return None
        _, frame = result
        try:
            resp = reassembler.feed(frame)
        except ValueError:
            return None
        if resp is None:
            # Still assembling consecutive frames
            continue
        # Expected positive response: [0x62, did_hi, did_lo, data…]
        if len(resp) < 3 or resp[0] != 0x62:
            return None
        if resp[1] != did_hi or resp[2] != did_lo:
            return None
        return resp[3:]


class UDSReader:
    """Reads PSA/Stellantis extended transmission signals via UDS."""

    def __init__(self, session: CANSession, did_map: Optional[dict] = None):
        self._session = session
        # Merge provided map over the built-in defaults.
        self._dids: dict[str, int] = {**PSA_DIDS, **(did_map or {})}

    def gear_actual(self) -> Optional[int]:
        raw = _uds_read_did(self._session, self._dids["gear_actual"])
        return int(raw[0]) if raw else None

    def gear_commanded(self) -> Optional[int]:
        raw = _uds_read_did(self._session, self._dids["gear_commanded"])
        return int(raw[0]) if raw else None

    def torque_converter_lock(self) -> Optional[bool]:
        raw = _uds_read_did(self._session, self._dids["tc_lock_state"])
        return bool(raw[0]) if raw else None

    def driver_torque_request(self) -> Optional[float]:
        raw = _uds_read_did(self._session, self._dids["driver_torque_req"])
        if raw is None or len(raw) < 2:
            return None
        return int.from_bytes(raw[:2], "big") * 0.5  # Nm, example scaling

    def engine_torque(self) -> Optional[float]:
        raw = _uds_read_did(self._session, self._dids["engine_torque"])
        if raw is None or len(raw) < 2:
            return None
        return int.from_bytes(raw[:2], "big") * 0.5

    def boost_pressure(self) -> Optional[float]:
        raw = _uds_read_did(self._session, self._dids["boost_pressure"])
        if raw is None or len(raw) < 2:
            return None
        return int.from_bytes(raw[:2], "big") * 0.1  # kPa

    def engine_torque_limit(self) -> Optional[float]:
        raw = _uds_read_did(self._session, self._dids["engine_torque_limit"])
        if raw is None or len(raw) < 2:
            return None
        return int.from_bytes(raw[:2], "big") * 0.5

    def drive_mode(self) -> Optional[str]:
        raw = _uds_read_did(self._session, self._dids["drive_mode"])
        if raw is None:
            return None
        modes = {0: "Eco", 1: "Normal", 2: "Sport", 3: "Manual"}
        return modes.get(raw[0], f"Unknown({raw[0]})")

    def clutch_slip(self) -> Optional[float]:
        raw = _uds_read_did(self._session, self._dids["clutch_slip"])
        if raw is None or len(raw) < 2:
            return None
        return int.from_bytes(raw[:2], "big") * 0.1

    def transmission_input_rpm(self) -> Optional[float]:
        raw = _uds_read_did(self._session, self._dids["trans_input_rpm"])
        if raw is None or len(raw) < 2:
            return None
        return float(int.from_bytes(raw[:2], "big"))

    def transmission_output_rpm(self) -> Optional[float]:
        raw = _uds_read_did(self._session, self._dids["trans_output_rpm"])
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
