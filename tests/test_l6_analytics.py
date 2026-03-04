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
