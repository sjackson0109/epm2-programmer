"""Shared fixtures for VTBAP tests."""
import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def sample_df():
    """A small synthetic telemetry DataFrame."""
    n = 100
    rng = np.random.default_rng(42)
    speeds_kmh = rng.uniform(30, 130, n)
    rpms = rng.uniform(1000, 4500, n)
    gears_actual = np.clip((speeds_kmh / 20).astype(int), 1, 8)
    gears_commanded = np.clip(gears_actual + rng.integers(-1, 2, n), 1, 8)

    # Simulate plausible EAT8 input/output RPM values so GearRatio is computable.
    # nominal ratios for gears 1-8: 4.714, 3.143, 2.106, 1.667, 1.285, 1.000, 0.839, 0.667
    from vtbap.config import EAT8_GEAR_RATIOS
    nominal_ratio = np.array([EAT8_GEAR_RATIOS.get(int(g), 1.0) for g in gears_actual])
    # Guard against any zero ratio (should not occur with valid EAT8 gears, but be safe)
    nominal_ratio = np.where(nominal_ratio > 0, nominal_ratio, 1.0)
    trans_output_rpm = rpms / nominal_ratio
    gear_ratio = rpms / trans_output_rpm  # == nominal_ratio

    return pd.DataFrame({
        "Timestamp":              np.linspace(0, 600, n),
        "Speed":                  speeds_kmh,
        "RPM":                    rpms,
        "PedalPosition":          rng.uniform(0, 100, n),
        "ThrottlePosition":        rng.uniform(0, 100, n),
        "GearActual":              gears_actual.astype(float),
        "GearCommanded":           gears_commanded.astype(float),
        "EngineLoad":              rng.uniform(10, 80, n),
        "IntakeManifoldPressure":  rng.uniform(90, 200, n),
        "TorqueRequest":           rng.uniform(50, 200, n),
        "TorqueActual":            rng.uniform(60, 220, n),
        "EngineTorqueLimit":       rng.uniform(150, 300, n),
        "Boost":                   rng.uniform(100, 200, n),
        "TCLock":                  rng.choice([True, False], n).tolist(),
        "ClutchSlip":              rng.uniform(0, 50, n),
        "TransInputRPM":           rpms,
        "TransOutputRPM":          trans_output_rpm,
        "GearRatio":               gear_ratio,
        "DriveMode":               rng.choice(["Eco", "Normal", "Sport"], n).tolist(),
        "Marker":                  [None] * n,
    })
