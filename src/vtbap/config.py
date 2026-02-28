"""VTBAP system configuration."""
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

@dataclass
class VTBAPConfig:
    sampling_hz: int = SAMPLING_FREQ_DEFAULT
    j2534_dll_path: Optional[str] = None
    output_dir: str = "."
    vin: Optional[str] = None
    anonymise_vin: bool = False
    reconnect_timeout_s: float = 3.0
    session_max_duration_s: float = 7200  # 2 hours
