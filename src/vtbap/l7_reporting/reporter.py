"""
L7 — Reporting Engine.

Outputs:
  1. Engineering Report (PDF)
  2. Dealer Summary Report (1-page PDF)
  3. Raw CSV Export (already produced by recorder)
  4. Graph Pack (PNG)

All reports embed the SHA-256 source data checksum.
"""
from __future__ import annotations
import io
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import matplotlib
matplotlib.use("Agg")  # non-interactive backend for CI/server environments
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from fpdf import FPDF
from fpdf.enums import XPos, YPos

from vtbap.config import GEAR_RATIO_DEVIATION_THRESHOLD

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates all required report artefacts from a session."""

    def __init__(
        self,
        df: pd.DataFrame,
        analytics: dict[str, Any],
        output_dir: str = ".",
        checksum: str = "",
        vin: Optional[str] = None,
        session_ts: Optional[str] = None,
    ):
        self._df = df
        self._analytics = analytics
        self._out = Path(output_dir)
        self._out.mkdir(parents=True, exist_ok=True)
        self._checksum = checksum
        self._vin = vin or "UNKNOWN"
        self._ts = session_ts or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # ------------------------------------------------------------------
    # Graph Pack

    def generate_graphs(self) -> list[Path]:
        paths: list[Path] = []
        paths.append(self._graph_speed_vs_gear())
        paths.append(self._graph_rpm_vs_speed())
        paths.append(self._graph_pedal_vs_torque())
        paths.append(self._graph_mode_comparison())
        paths.append(self._graph_gear_delta())
        paths.append(self._graph_gear_ratio())
        return [p for p in paths if p is not None]

    def _graph_speed_vs_gear(self) -> Optional[Path]:
        gum = self._analytics.get("gear_utilisation_map")
        if gum is None or (isinstance(gum, pd.DataFrame) and gum.empty):
            return None
        fig, ax = plt.subplots(figsize=(10, 5))
        gum_df = gum if isinstance(gum, pd.DataFrame) else pd.DataFrame()
        if not gum_df.empty:
            im = ax.imshow(gum_df.T, aspect="auto", origin="lower", cmap="hot")
            ax.set_xlabel("Speed Band (km/h)")
            ax.set_ylabel("Gear")
            ax.set_title("Speed vs Gear Utilisation Heat Map")
            plt.colorbar(im, ax=ax, label="Samples")
        path = self._out / f"{self._ts}_speed_vs_gear.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return path

    def _graph_rpm_vs_speed(self) -> Optional[Path]:
        df = self._df.dropna(subset=["Speed", "RPM"])
        if df.empty:
            return None
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.scatter(df["Speed"], df["RPM"], s=2, alpha=0.4, color="steelblue")
        ax.set_xlabel("Speed (km/h)")
        ax.set_ylabel("Engine RPM")
        ax.set_title("RPM vs Speed")
        path = self._out / f"{self._ts}_rpm_vs_speed.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return path

    def _graph_pedal_vs_torque(self) -> Optional[Path]:
        df = self._df.dropna(subset=["PedalPosition", "TorqueRequest"])
        if df.empty:
            return None
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.scatter(df["PedalPosition"], df["TorqueRequest"], s=2, alpha=0.4, color="tomato")
        ax.set_xlabel("Accelerator Pedal Position (%)")
        ax.set_ylabel("Driver Torque Request (Nm)")
        ax.set_title("Pedal Position vs Torque Request")
        path = self._out / f"{self._ts}_pedal_vs_torque.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return path

    def _graph_mode_comparison(self) -> Optional[Path]:
        df = self._df.dropna(subset=["DriveMode", "RPM"])
        if df.empty:
            return None
        modes = df["DriveMode"].unique()
        fig, ax = plt.subplots(figsize=(10, 5))
        for mode in modes:
            subset = df[df["DriveMode"] == mode]["RPM"]
            ax.hist(subset, bins=30, alpha=0.5, label=str(mode))
        ax.set_xlabel("RPM")
        ax.set_ylabel("Count")
        ax.set_title("RPM Distribution by Drive Mode")
        ax.legend()
        path = self._out / f"{self._ts}_mode_comparison.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return path

    def _graph_gear_delta(self) -> Optional[Path]:
        df = self._df.dropna(subset=["GearActual", "GearCommanded"]).copy()
        if df.empty:
            return None
        df["GearDelta"] = df["GearCommanded"] - df["GearActual"]
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df["Timestamp"], df["GearDelta"], lw=0.8, color="purple")
        ax.axhline(0, color="gray", linestyle="--", lw=0.5)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Commanded \u2212 Actual Gear")
        ax.set_title("Automatic vs Manual Gear Delta")
        path = self._out / f"{self._ts}_gear_delta.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return path

    def _graph_gear_ratio(self) -> Optional[Path]:
        """Bar chart: measured mean gear ratio vs EAT8 nominal per gear."""
        gra = self._analytics.get("gear_ratio_analysis")
        if not gra:
            return None
        gears_with_data = {g: v for g, v in gra.items() if v["measured_mean"] is not None}
        if not gears_with_data:
            return None
        gears = sorted(gears_with_data.keys())
        nominal  = [gra[g]["nominal"]       for g in gears]
        measured = [gra[g]["measured_mean"] for g in gears]
        x = np.arange(len(gears))
        width = 0.35
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(x - width / 2, nominal,  width, label="EAT8 Nominal", color="steelblue",  alpha=0.8)
        ax.bar(x + width / 2, measured, width, label="Measured Mean", color="tomato", alpha=0.8)
        ax.set_xlabel("Gear")
        ax.set_ylabel("Ratio")
        ax.set_title("Gear Ratio: Measured vs EAT8 Nominal")
        ax.set_xticks(x)
        ax.set_xticklabels([str(g) for g in gears])
        ax.legend()
        path = self._out / f"{self._ts}_gear_ratio.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return path

    # ------------------------------------------------------------------
    # Engineering Report (PDF)

    def generate_engineering_report(self) -> Path:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "VTBAP Engineering Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"Generated: {datetime.now(timezone.utc).isoformat()}Z", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.cell(0, 6, f"VIN: {self._vin}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.ln(4)

        # Checksum section
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Data Integrity", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Courier", "", 9)
        pdf.cell(0, 6, f"SHA-256: {self._checksum}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(4)

        # Session summary
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Session Summary", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"Total frames: {len(self._df)}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if not self._df.empty and "Timestamp" in self._df.columns:
            duration = self._df["Timestamp"].max() - self._df["Timestamp"].min()
            pdf.cell(0, 6, f"Duration: {duration:.1f} s", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(4)

        # RPM efficiency profile
        rpm_profile = self._analytics.get("rpm_efficiency_profile", {})
        if rpm_profile:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 8, "RPM Efficiency Profile", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 10)
            for band, avg_rpm in rpm_profile.items():
                pdf.cell(0, 6, f"  {band} mph band: avg RPM = {avg_rpm:.0f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(4)

        # Upshift thresholds
        upshifts = self._analytics.get("upshift_thresholds", [])
        if upshifts:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 8, f"Upshift Events ({len(upshifts)} detected)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 9)
            for ev in upshifts[:20]:  # cap at 20 lines
                pdf.cell(
                    0, 5,
                    f"  Gear {ev['FromGear']}->{ev['ToGear']}  "
                    f"Speed={ev['Speed']:.1f} km/h  RPM={ev['RPM']:.0f}  "
                    f"Pedal={ev['PedalPosition']:.1f}%",
                    new_x=XPos.LMARGIN, new_y=YPos.NEXT,
                )
            pdf.ln(4)

        # Gear ratio analysis
        gra = self._analytics.get("gear_ratio_analysis", {})
        if gra:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 8, "Gear Ratio Analysis (vs EAT8 Nominal)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 9)
            for gear in sorted(gra.keys()):
                entry = gra[gear]
                nominal = entry["nominal"]
                if entry["measured_mean"] is None:
                    pdf.cell(
                        0, 5, f"  Gear {gear}: nominal={nominal:.3f}  (no data)",
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
                    )
                else:
                    dev = entry["deviation"]
                    flag = "  *** DEVIATION" if abs(dev) > GEAR_RATIO_DEVIATION_THRESHOLD else ""
                    pdf.cell(
                        0, 5,
                        f"  Gear {gear}: nominal={nominal:.3f}  "
                        f"measured={entry['measured_mean']:.3f}  "
                        f"dev={dev:+.3f}  n={entry['n']}{flag}",
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
                    )
            pdf.ln(4)

        path = self._out / f"{self._ts}_engineering_report.pdf"
        pdf.output(str(path))
        logger.info("Engineering report: %s", path)
        return path

    # ------------------------------------------------------------------
    # Dealer Summary Report (1-page PDF)

    def generate_dealer_summary(self) -> Path:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "VTBAP Dealer Summary", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"VIN: {self._vin}  |  Date: {self._ts[:8]}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.ln(4)

        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Key Findings", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 10)

        rpm_profile = self._analytics.get("rpm_efficiency_profile", {})
        for band, avg_rpm in rpm_profile.items():
            label = "HIGH" if avg_rpm > 3000 else "OK"
            pdf.cell(0, 6, f"  {band} mph: avg {avg_rpm:.0f} RPM  [{label}]", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        upshifts = self._analytics.get("upshift_thresholds", [])
        pdf.cell(0, 6, f"  Upshift events detected: {len(upshifts)}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(4)
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 6, f"Source checksum (SHA-256): {self._checksum}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        path = self._out / f"{self._ts}_dealer_summary.pdf"
        pdf.output(str(path))
        logger.info("Dealer summary: %s", path)
        return path
