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

    return pd.DataFrame({
        "Timestamp":       np.linspace(0, 600, n),
        "Speed":           speeds_kmh,
        "RPM":             rpms,
        "PedalPosition":   rng.uniform(0, 100, n),
        "ThrottlePosition": rng.uniform(0, 100, n),
        "GearActual":      gears_actual.astype(float),
        "GearCommanded":   gears_commanded.astype(float),
        "EngineLoad":      rng.uniform(10, 80, n),
        "TorqueRequest":   rng.uniform(50, 200, n),
        "TorqueActual":    rng.uniform(60, 220, n),
        "Boost":           rng.uniform(100, 200, n),
        "DriveMode":       rng.choice(["Eco", "Normal", "Sport"], n).tolist(),
        "Marker":          [None] * n,
    })
