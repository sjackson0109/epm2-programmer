"""Tests for Signal Processing Engine."""
import pytest
from vtbap.l4_signal_processing.processor import SignalProcessor, TelemetryFrame


def test_merge_basic():
    proc = SignalProcessor()
    obd2 = {"vehicle_speed": 80.0, "engine_rpm": 2000.0, "throttle_position": 30.0,
            "accelerator_pedal": 25.0, "engine_load": 40.0, "intake_manifold_press": 120.0}
    uds = {"gear_actual": 4, "gear_commanded": 4, "drive_mode": "Normal",
           "engine_torque": 100.0, "driver_torque_request": 80.0}
    frame = proc.merge(obd2, uds, ts=1000.0)
    assert frame.vehicle_speed == 80.0
    assert frame.engine_rpm == 2000.0
    assert frame.gear_actual == 4
    assert frame.drive_mode == "Normal"
    assert frame.timestamp == 1000.0


def test_merge_with_marker():
    proc = SignalProcessor()
    frame = proc.merge({}, {}, ts=0.0, marker="M3")
    assert frame.marker == "M3"


def test_gear_ratio_computed():
    proc = SignalProcessor()
    uds = {"trans_input_rpm": 2000.0, "trans_output_rpm": 500.0}
    frame = proc.merge({}, uds, ts=0.0)
    assert frame.gear_ratio == pytest.approx(4.0)


def test_gear_ratio_none_when_output_zero():
    proc = SignalProcessor()
    uds = {"trans_input_rpm": 1000.0, "trans_output_rpm": 0.0}
    frame = proc.merge({}, uds, ts=0.0)
    assert frame.gear_ratio is None


def test_to_dict_keys():
    proc = SignalProcessor()
    frame = proc.merge({}, {}, ts=0.0)
    d = frame.to_dict()
    expected_keys = {
        "Timestamp", "Speed", "RPM", "PedalPosition", "ThrottlePosition",
        "GearActual", "GearCommanded", "EngineLoad", "IntakeManifoldPressure",
        "TorqueRequest", "TorqueActual", "EngineTorqueLimit", "Boost",
        "TCLock", "ClutchSlip", "TransInputRPM", "TransOutputRPM", "GearRatio",
        "DriveMode", "Marker",
    }
    assert expected_keys == set(d.keys())
