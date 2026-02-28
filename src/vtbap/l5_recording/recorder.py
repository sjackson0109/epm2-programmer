"""
L5 — Data Recording Engine.

Writes telemetry frames to a timestamped CSV file and computes a SHA-256
checksum of the data. Logs are immutable after session close.
"""
from __future__ import annotations
import csv
import hashlib
import io
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from vtbap.l4_signal_processing.processor import TelemetryFrame

logger = logging.getLogger(__name__)

CSV_COLUMNS = [
    "Timestamp", "Speed", "RPM", "PedalPosition", "ThrottlePosition",
    "GearActual", "GearCommanded", "EngineLoad", "TorqueRequest",
    "TorqueActual", "Boost", "DriveMode", "Marker",
]


class SessionRecorder:
    """
    Records telemetry frames to a CSV file.

    File naming: YYYYMMDD_HHMMSS_<VIN>_SESSION.csv
    Computes SHA-256 of the CSV content on close.
    """

    def __init__(
        self,
        output_dir: str = ".",
        vin: Optional[str] = None,
        anonymise_vin: bool = False,
    ):
        self._output_dir = Path(output_dir)
        self._vin = "ANONYMISED" if anonymise_vin else (vin or "UNKNOWN")
        self._file: Optional[io.TextIOWrapper] = None
        self._writer: Optional[csv.DictWriter] = None
        self._path: Optional[Path] = None
        self._closed = False
        self._frame_count = 0
        self._checksum: Optional[str] = None
        self._start_time: Optional[datetime] = None

    # ------------------------------------------------------------------

    def open(self) -> Path:
        """Create the CSV file and write the header."""
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._start_time = datetime.utcnow()
        ts = self._start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"{ts}_{self._vin}_SESSION.csv"
        self._path = self._output_dir / filename
        self._file = open(self._path, "w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        self._writer.writeheader()
        self._closed = False
        logger.info("Recording session opened: %s", self._path)
        return self._path

    def write_frame(self, frame: TelemetryFrame) -> None:
        """Write a single telemetry frame to CSV."""
        if self._closed or self._writer is None:
            raise RuntimeError("Session is not open.")
        self._writer.writerow(frame.to_dict())
        self._frame_count += 1

    def close(self) -> str:
        """Close the file, compute SHA-256 checksum, and make the log immutable."""
        if self._closed:
            return self._checksum or ""
        if self._file:
            self._file.flush()
            self._file.close()
        self._closed = True
        if self._path and self._path.exists():
            self._checksum = _sha256_file(self._path)
            # Write checksum sidecar
            sidecar = self._path.with_suffix(".sha256")
            sidecar.write_text(f"{self._checksum}  {self._path.name}\n", encoding="utf-8")
            logger.info(
                "Session closed: %d frames, SHA-256=%s", self._frame_count, self._checksum
            )
        return self._checksum or ""

    @property
    def path(self) -> Optional[Path]:
        return self._path

    @property
    def frame_count(self) -> int:
        return self._frame_count

    @property
    def checksum(self) -> Optional[str]:
        return self._checksum


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
