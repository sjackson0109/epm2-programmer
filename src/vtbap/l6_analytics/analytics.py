"""
L6 — Analytics Engine.

Computes:
  8.1 Gear Utilisation Map (speed vs gear heat distribution)
  8.2 RPM Efficiency Profile (average RPM per speed band)
  8.3 Upshift Threshold Detection
  8.4 Torque Reserve Estimation
  8.5 Manual Override Stability
"""
from __future__ import annotations
from collections import defaultdict
from typing import Any, Optional

import numpy as np
import pandas as pd

from vtbap.config import SPEED_BANDS_MPH, EAT8_GEAR_RATIOS

KMH_TO_MPH = 0.621371


class AnalyticsEngine:
    """Runs analytics over a completed session DataFrame."""

    def __init__(self, df: pd.DataFrame):
        self._df = df.copy()
        # Ensure numeric columns
        for col in ["Speed", "RPM", "GearActual", "GearCommanded",
                    "TorqueRequest", "TorqueActual", "PedalPosition"]:
            if col in self._df.columns:
                self._df[col] = pd.to_numeric(self._df[col], errors="coerce")

    # ------------------------------------------------------------------
    # 8.1

    def gear_utilisation_map(self) -> pd.DataFrame:
        """
        Returns a DataFrame with speed (km/h, rounded to 5) as index,
        gear as columns, and count as values.
        """
        df = self._df.dropna(subset=["Speed", "GearActual"])
        df = df.copy()
        df["SpeedBin"] = (df["Speed"] / 5).round() * 5
        pivot = (
            df.groupby(["SpeedBin", "GearActual"])
            .size()
            .unstack(fill_value=0)
        )
        return pivot

    # ------------------------------------------------------------------
    # 8.2

    def rpm_efficiency_profile(self) -> dict[int, float]:
        """
        Returns average RPM per speed band (mph).
        Speed bands: 30/40/50/60/70 mph.
        """
        df = self._df.dropna(subset=["Speed", "RPM"])
        df = df.copy()
        df["SpeedMPH"] = df["Speed"] * KMH_TO_MPH
        result: dict[int, float] = {}
        band_width = 5  # ±5 mph around each band centre
        for band in SPEED_BANDS_MPH:
            mask = (df["SpeedMPH"] >= band - band_width) & (df["SpeedMPH"] < band + band_width)
            subset = df.loc[mask, "RPM"]
            result[band] = float(subset.mean()) if not subset.empty else float("nan")
        return result

    # ------------------------------------------------------------------
    # 8.3

    def upshift_thresholds(self) -> list[dict]:
        """
        Detect upshift events and return conditions at the moment of shift.
        An upshift is: GearActual increases by 1 between consecutive rows.
        """
        df = self._df.dropna(subset=["GearActual"]).copy()
        df["PrevGear"] = df["GearActual"].shift(1)
        upshifts = df[df["GearActual"] == df["PrevGear"] + 1].copy()
        records = []
        for _, row in upshifts.iterrows():
            records.append({
                "Timestamp":    row.get("Timestamp"),
                "FromGear":     int(row["PrevGear"]),
                "ToGear":       int(row["GearActual"]),
                "Speed":        row.get("Speed"),
                "RPM":          row.get("RPM"),
                "PedalPosition": row.get("PedalPosition"),
                "DriveMode":    row.get("DriveMode"),
            })
        return records

    # ------------------------------------------------------------------
    # 8.4

    def torque_reserve(self) -> pd.Series:
        """
        Returns a Series of: AvailableTorque - RequiredTorque.
        Uses TorqueActual as a proxy for AvailableTorque when limit is absent.
        """
        df = self._df.dropna(subset=["TorqueRequest", "TorqueActual"])
        reserve = df["TorqueActual"] - df["TorqueRequest"]
        reserve.name = "TorqueReserve"
        return reserve

    # ------------------------------------------------------------------
    # 8.5

    def manual_override_stability(self) -> pd.DataFrame:
        """
        Identifies periods where ManualGear > AutomaticGear AND no downshift occurred.
        Returns the filtered DataFrame slice.
        """
        df = self._df.dropna(subset=["GearActual", "GearCommanded"]).copy()
        # Manual > Auto: commanded gear (driver selection) > auto gear
        override = df[df["GearCommanded"] > df["GearActual"]].copy()
        # Exclude rows where a downshift occurred (GearActual drops)
        override["PrevGearActual"] = override["GearActual"].shift(1)
        stable = override[
            override["PrevGearActual"].isna()
            | (override["GearActual"] >= override["PrevGearActual"])
        ]
        return stable.drop(columns=["PrevGearActual"])

    # ------------------------------------------------------------------
    # 8.6

    def gear_ratio_analysis(self) -> dict[int, dict]:
        """
        Compares measured gear ratios (TransInputRPM / TransOutputRPM) against
        EAT8 nominal values for each gear engaged.

        Returns a dict keyed by gear number with:
          - ``nominal``: published EAT8 ratio
          - ``measured_mean``: average measured ratio (None if no data)
          - ``deviation``: measured_mean − nominal (None if no data)
          - ``n``: sample count
        """
        results: dict[int, dict] = {}
        if "GearRatio" not in self._df.columns or "GearActual" not in self._df.columns:
            for gear, nominal in EAT8_GEAR_RATIOS.items():
                results[gear] = {"nominal": nominal, "measured_mean": None, "deviation": None, "n": 0}
            return results

        df = self._df.dropna(subset=["GearActual", "GearRatio"]).copy()
        df = df[df["GearRatio"] > 0]

        for gear, nominal in EAT8_GEAR_RATIOS.items():
            subset = df[df["GearActual"] == gear]["GearRatio"]
            if subset.empty:
                results[gear] = {"nominal": nominal, "measured_mean": None, "deviation": None, "n": 0}
            else:
                mean = float(subset.mean())
                results[gear] = {
                    "nominal": nominal,
                    "measured_mean": mean,
                    "deviation": mean - nominal,
                    "n": len(subset),
                }
        return results

    def run_all(self) -> dict[str, Any]:
        return {
            "gear_utilisation_map":     self.gear_utilisation_map(),
            "rpm_efficiency_profile":   self.rpm_efficiency_profile(),
            "upshift_thresholds":       self.upshift_thresholds(),
            "torque_reserve":           self.torque_reserve(),
            "manual_override_stability": self.manual_override_stability(),
            "gear_ratio_analysis":      self.gear_ratio_analysis(),
        }
