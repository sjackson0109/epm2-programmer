"""Tests for Analytics Engine."""
import pandas as pd
import numpy as np
import pytest
from vtbap.l6_analytics.analytics import AnalyticsEngine


def test_gear_utilisation_map(sample_df):
    engine = AnalyticsEngine(sample_df)
    gum = engine.gear_utilisation_map()
    assert isinstance(gum, pd.DataFrame)
    assert not gum.empty


def test_rpm_efficiency_profile(sample_df):
    engine = AnalyticsEngine(sample_df)
    profile = engine.rpm_efficiency_profile()
    assert isinstance(profile, dict)
    assert 30 in profile
    assert 70 in profile
    for band, rpm in profile.items():
        assert isinstance(rpm, float)


def test_upshift_thresholds(sample_df):
    engine = AnalyticsEngine(sample_df)
    thresholds = engine.upshift_thresholds()
    assert isinstance(thresholds, list)
    for ev in thresholds:
        assert ev["ToGear"] == ev["FromGear"] + 1


def test_torque_reserve(sample_df):
    engine = AnalyticsEngine(sample_df)
    reserve = engine.torque_reserve()
    assert isinstance(reserve, pd.Series)
    assert len(reserve) > 0


def test_manual_override_stability(sample_df):
    engine = AnalyticsEngine(sample_df)
    stability = engine.manual_override_stability()
    assert isinstance(stability, pd.DataFrame)


def test_empty_dataframe():
    empty_df = pd.DataFrame(columns=["Speed", "RPM", "GearActual", "GearCommanded",
                                     "TorqueRequest", "TorqueActual", "PedalPosition",
                                     "DriveMode", "Timestamp"])
    engine = AnalyticsEngine(empty_df)
    assert engine.gear_utilisation_map().empty
    assert engine.upshift_thresholds() == []


def test_gear_ratio_analysis_with_data(sample_df):
    engine = AnalyticsEngine(sample_df)
    result = engine.gear_ratio_analysis()
    assert isinstance(result, dict)
    # All 8 EAT8 gears should be represented
    assert set(result.keys()) == {1, 2, 3, 4, 5, 6, 7, 8}
    for gear, entry in result.items():
        assert "nominal" in entry
        assert "measured_mean" in entry
        assert "deviation" in entry
        assert "n" in entry
        if entry["measured_mean"] is not None:
            assert entry["n"] > 0
            # deviation = measured - nominal
            assert entry["deviation"] == pytest.approx(
                entry["measured_mean"] - entry["nominal"], abs=1e-6
            )


def test_gear_ratio_analysis_no_data():
    """When GearRatio column is absent, all entries should have n=0."""
    df = pd.DataFrame({"GearActual": [1, 2, 3]})
    engine = AnalyticsEngine(df)
    result = engine.gear_ratio_analysis()
    for entry in result.values():
        assert entry["n"] == 0
        assert entry["measured_mean"] is None


def test_run_all_includes_gear_ratio(sample_df):
    engine = AnalyticsEngine(sample_df)
    result = engine.run_all()
    assert "gear_ratio_analysis" in result
