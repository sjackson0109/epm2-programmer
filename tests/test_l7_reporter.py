"""Tests for Reporting Engine."""
import tempfile
import os
from pathlib import Path
import pandas as pd
import numpy as np
import pytest
from vtbap.l6_analytics.analytics import AnalyticsEngine
from vtbap.l7_reporting.reporter import ReportGenerator


@pytest.fixture
def report_inputs(sample_df):
    analytics = AnalyticsEngine(sample_df).run_all()
    return sample_df, analytics


def test_generate_graphs(report_inputs):
    df, analytics = report_inputs
    with tempfile.TemporaryDirectory() as tmp:
        reporter = ReportGenerator(df, analytics, output_dir=tmp, checksum="abc123")
        paths = reporter.generate_graphs()
        # At least some graphs should be generated (non-empty df)
        assert len(paths) > 0
        for p in paths:
            assert p.exists()
            assert p.suffix == ".png"


def test_engineering_report(report_inputs):
    df, analytics = report_inputs
    with tempfile.TemporaryDirectory() as tmp:
        reporter = ReportGenerator(df, analytics, output_dir=tmp,
                                   checksum="deadbeef" * 8, vin="TEST_VIN")
        path = reporter.generate_engineering_report()
        assert path.exists()
        assert path.suffix == ".pdf"
        assert path.stat().st_size > 0


def test_dealer_summary(report_inputs):
    df, analytics = report_inputs
    with tempfile.TemporaryDirectory() as tmp:
        reporter = ReportGenerator(df, analytics, output_dir=tmp,
                                   checksum="deadbeef" * 8, vin="TEST_VIN")
        path = reporter.generate_dealer_summary()
        assert path.exists()
        assert path.suffix == ".pdf"
        assert path.stat().st_size > 0
