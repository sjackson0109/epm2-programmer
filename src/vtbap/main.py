"""
VTBAP — main entry point.

Orchestrates all layers: VCI connection, data acquisition loop,
recording, analytics, and reporting.
"""
from __future__ import annotations
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from vtbap.config import VTBAPConfig, EVENT_MARKERS
from vtbap.l1_hardware.vci_manager import VCIManager
from vtbap.l2_transport.can import CANSession
from vtbap.l3_vehicle_comms.obd2 import OBD2Reader
from vtbap.l3_vehicle_comms.uds import UDSReader
from vtbap.l4_signal_processing.processor import SignalProcessor
from vtbap.l5_recording.recorder import SessionRecorder
from vtbap.l6_analytics.analytics import AnalyticsEngine
from vtbap.l7_reporting.reporter import ReportGenerator
from vtbap.l8_ui.dashboard import LiveDashboard

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def main(config: Optional[VTBAPConfig] = None) -> int:
    cfg = config or VTBAPConfig()
    _shutdown = [False]

    def _handle_signal(sig, frame):
        logger.info("Shutdown signal received.")
        _shutdown[0] = True

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    # L1: VCI
    vci = VCIManager(dll_path=cfg.j2534_dll_path, reconnect_timeout_s=cfg.reconnect_timeout_s)
    if not vci.connect():
        logger.warning("Initial VCI connect failed; will retry during loop.")

    iface = vci.interface
    if iface is None:
        logger.error("No VCI interface available.")
        return 1

    # L2: Transport
    can = CANSession(iface)

    # L3: Vehicle comms
    obd2 = OBD2Reader(can)
    uds = UDSReader(can)

    # L4: Processor
    processor = SignalProcessor()

    # L5: Recorder
    recorder = SessionRecorder(
        output_dir=cfg.output_dir,
        vin=cfg.vin,
        anonymise_vin=cfg.anonymise_vin,
    )
    csv_path = recorder.open()

    # L8: Dashboard
    interval = 1.0 / cfg.sampling_hz
    deadline = time.monotonic() + cfg.session_max_duration_s

    pending_marker: Optional[str] = None
    frames = []

    with LiveDashboard(recording=True) as dash:
        while not _shutdown[0] and time.monotonic() < deadline:
            loop_start = time.monotonic()

            # Ensure connection
            if not vci.ensure_connected():
                logger.warning("VCI not connected; skipping sample.")
                time.sleep(interval)
                continue

            ts = time.time()
            obd2_data = obd2.read_all()
            uds_data = uds.read_all()

            frame = processor.merge(obd2_data, uds_data, ts=ts, marker=pending_marker)
            pending_marker = None

            recorder.write_frame(frame)
            frames.append(frame.to_dict())

            dash.update(frame.to_dict(), recording=True)

            elapsed = time.monotonic() - loop_start
            sleep_time = max(0.0, interval - elapsed)
            time.sleep(sleep_time)

    # Close recording
    checksum = recorder.close()
    logger.info("Session checksum: %s", checksum)

    # L6: Analytics
    df = pd.DataFrame(frames)
    analytics = AnalyticsEngine(df).run_all()

    # L7: Reporting
    reporter = ReportGenerator(
        df=df,
        analytics=analytics,
        output_dir=cfg.output_dir,
        checksum=checksum,
        vin=cfg.vin,
        session_ts=datetime.utcnow().strftime("%Y%m%d_%H%M%S"),
    )
    reporter.generate_graphs()
    reporter.generate_engineering_report()
    reporter.generate_dealer_summary()

    return 0


if __name__ == "__main__":
    sys.exit(main())
