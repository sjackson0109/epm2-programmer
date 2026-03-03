"""Tests for Session Recorder."""
import tempfile
import csv
from pathlib import Path
from vtbap.l5_recording.recorder import SessionRecorder
from vtbap.l4_signal_processing.processor import TelemetryFrame


def test_open_creates_file():
    with tempfile.TemporaryDirectory() as tmp:
        rec = SessionRecorder(output_dir=tmp, vin="TEST123")
        path = rec.open()
        assert path.exists()


def test_write_and_close():
    with tempfile.TemporaryDirectory() as tmp:
        rec = SessionRecorder(output_dir=tmp, vin="TEST123")
        rec.open()
        frame = TelemetryFrame(timestamp=1.0, vehicle_speed=80.0, engine_rpm=2000.0)
        rec.write_frame(frame)
        checksum = rec.close()
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA-256 hex
        sidecar = rec.path.with_suffix(".sha256")
        assert sidecar.exists()


def test_csv_has_correct_columns():
    with tempfile.TemporaryDirectory() as tmp:
        rec = SessionRecorder(output_dir=tmp)
        rec.open()
        frame = TelemetryFrame(timestamp=1.0)
        rec.write_frame(frame)
        rec.close()
        with open(rec.path) as f:
            reader = csv.DictReader(f)
            row = next(reader)
            assert "Timestamp" in row
            assert "Speed" in row
            assert "GearActual" in row
            assert "TransInputRPM" in row
            assert "TransOutputRPM" in row
            assert "GearRatio" in row
            assert "IntakeManifoldPressure" in row


def test_vin_anonymisation():
    with tempfile.TemporaryDirectory() as tmp:
        rec = SessionRecorder(output_dir=tmp, vin="VF3ABCDEF", anonymise_vin=True)
        path = rec.open()
        rec.close()
        assert "ANONYMISED" in path.name
