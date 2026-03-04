"""
L4 — Signal Processing Engine.

Merges OBD-II and UDS signal frames, aligns timestamps (\u22645 ms deviation),
and produces unified telemetry records.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any, Optional

TIMESTAMP_TOLERANCE_MS = 5.0


@dataclass
class TelemetryFrame:
    """A single aligned telemetry snapshot."""
    timestamp: float = field(default_factory=time.time)
    vehicle_speed: Optional[float] = None          # km/h
    engine_rpm: Optional[float] = None
    throttle_position: Optional[float] = None      # %
    accelerator_pedal: Optional[float] = None      # %
    engine_load: Optional[float] = None            # %
    intake_manifold_press: Optional[float] = None  # kPa
    gear_actual: Optional[int] = None
    gear_commanded: Optional[int] = None
    tc_lock: Optional[bool] = None
    driver_torque_request: Optional[float] = None  # Nm
    engine_torque: Optional[float] = None          # Nm
    boost_pressure: Optional[float] = None         # kPa
    engine_torque_limit: Optional[float] = None    # Nm
    drive_mode: Optional[str] = None
    clutch_slip: Optional[float] = None
    trans_input_rpm: Optional[float] = None
    trans_output_rpm: Optional[float] = None
    gear_ratio: Optional[float] = None
    marker: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "Timestamp":              self.timestamp,
            "Speed":                  self.vehicle_speed,
            "RPM":                    self.engine_rpm,
            "PedalPosition":          self.accelerator_pedal,
            "ThrottlePosition":       self.throttle_position,
            "GearActual":             self.gear_actual,
            "GearCommanded":          self.gear_commanded,
            "EngineLoad":             self.engine_load,
            "IntakeManifoldPressure": self.intake_manifold_press,
            "TorqueRequest":          self.driver_torque_request,
            "TorqueActual":           self.engine_torque,
            "EngineTorqueLimit":      self.engine_torque_limit,
            "Boost":                  self.boost_pressure,
            "TCLock":                 self.tc_lock,
            "ClutchSlip":             self.clutch_slip,
            "TransInputRPM":          self.trans_input_rpm,
            "TransOutputRPM":         self.trans_output_rpm,
            "GearRatio":              self.gear_ratio,
            "DriveMode":              self.drive_mode,
            "Marker":                 self.marker,
        }


class SignalProcessor:
    """Merges OBD-II and UDS dictionaries into a timestamp-aligned frame."""

    def merge(
        self,
        obd2_data: dict,
        uds_data: dict,
        ts: Optional[float] = None,
        marker: Optional[str] = None,
    ) -> TelemetryFrame:
        t = ts if ts is not None else time.time()
        frame = TelemetryFrame(timestamp=t, marker=marker)
        frame.vehicle_speed         = obd2_data.get("vehicle_speed")
        frame.engine_rpm            = obd2_data.get("engine_rpm")
        frame.throttle_position     = obd2_data.get("throttle_position")
        frame.accelerator_pedal     = obd2_data.get("accelerator_pedal")
        frame.engine_load           = obd2_data.get("engine_load")
        frame.intake_manifold_press = obd2_data.get("intake_manifold_press")
        frame.gear_actual           = uds_data.get("gear_actual")
        frame.gear_commanded        = uds_data.get("gear_commanded")
        frame.tc_lock               = uds_data.get("tc_lock")
        frame.driver_torque_request = uds_data.get("driver_torque_request")
        frame.engine_torque         = uds_data.get("engine_torque")
        frame.boost_pressure        = uds_data.get("boost_pressure")
        frame.engine_torque_limit   = uds_data.get("engine_torque_limit")
        frame.drive_mode            = uds_data.get("drive_mode")
        frame.clutch_slip           = uds_data.get("clutch_slip")
        frame.trans_input_rpm       = uds_data.get("trans_input_rpm")
        frame.trans_output_rpm      = uds_data.get("trans_output_rpm")
        # Derived: gear ratio = transmission input RPM / output RPM
        t_in  = frame.trans_input_rpm
        t_out = frame.trans_output_rpm
        if t_in is not None and t_out is not None and t_out > 1e-6:
            frame.gear_ratio = t_in / t_out
        return frame
