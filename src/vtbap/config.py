"""VTBAP system configuration."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

SAMPLING_FREQ_MIN = 5   # Hz
SAMPLING_FREQ_MAX = 20  # Hz
SAMPLING_FREQ_DEFAULT = 10  # Hz

OBD2_PIDS = {
    "vehicle_speed":       0x0D,
    "engine_rpm":          0x0C,
    "throttle_position":   0x11,
    "accelerator_pedal":   0x49,
    "engine_load":         0x04,
    "intake_manifold_press": 0x0B,
}

EVENT_MARKERS = {
    "M1": "Eco Mode Start",
    "M2": "Normal Mode Start",
    "M3": "Sport Mode Start",
    "M4": "Manual Upshift",
    "M5": "Manual Downshift",
    "M6": "Cruise Stable",
    "M7": "Flat Road Confirmation",
}

SPEED_BANDS_MPH = [30, 40, 50, 60, 70]

# PSA/Stellantis proprietary UDS Data Identifiers (DIDs).
# WARNING: These are indicative placeholder values only.  They must be
# verified against the actual TCU firmware revision before use on a real
# vehicle.  Override them at runtime via VTBAPConfig.did_map or the
# UDSReader(did_map=…) constructor argument.
PSA_DIDS: dict[str, int] = {
    "gear_actual":          0x1234,
    "gear_commanded":       0x1235,
    "tc_lock_state":        0x1236,
    "driver_torque_req":    0x1237,
    "engine_torque":        0x1238,
    "boost_pressure":       0x1239,
    "engine_torque_limit":  0x123A,
    "drive_mode":           0x123B,
    "clutch_slip":          0x123C,
    "trans_input_rpm":      0x123D,
    "trans_output_rpm":     0x123E,
}


@dataclass
class VTBAPConfig:
    sampling_hz: int = SAMPLING_FREQ_DEFAULT
    j2534_dll_path: Optional[str] = None
    output_dir: str = "."
    vin: Optional[str] = None
    anonymise_vin: bool = False
    reconnect_timeout_s: float = 3.0
    session_max_duration_s: float = 7200  # 2 hours
    # Override PSA_DIDS at runtime (None = use built-in placeholders).
    did_map: Optional[dict] = None
