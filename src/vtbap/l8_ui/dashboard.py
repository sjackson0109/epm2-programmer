"""
L8 — UI Layer: Live terminal dashboard using Rich.

Displays: Speed, RPM, Current Gear, Requested Gear, Pedal %, Engine Load,
Drive Mode, Recording Status. Latency < 200 ms.
"""
from __future__ import annotations
import time
from typing import Callable, Optional

from rich.columns import Columns
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def _make_table(frame: dict) -> Table:
    t = Table.grid(padding=(0, 2))
    t.add_column(style="bold cyan", no_wrap=True)
    t.add_column(style="white")

    def _val(v, unit="", fmt=".1f"):
        if v is None:
            return Text("---", style="dim")
        return Text(f"{v:{fmt}} {unit}".strip())

    t.add_row("Speed",          _val(frame.get("Speed"),          "km/h"))
    t.add_row("RPM",            _val(frame.get("RPM"),            "",    ".0f"))
    t.add_row("Gear (Actual)",  _val(frame.get("GearActual"),     "",    "d") if frame.get("GearActual") is not None else Text("---", style="dim"))
    t.add_row("Gear (Request)", _val(frame.get("GearCommanded"),  "",    "d") if frame.get("GearCommanded") is not None else Text("---", style="dim"))
    t.add_row("Pedal",          _val(frame.get("PedalPosition"),  "%"))
    t.add_row("Engine Load",    _val(frame.get("EngineLoad"),     "%"))
    t.add_row("Drive Mode",     Text(str(frame.get("DriveMode") or "---")))
    t.add_row("Keys 1-7",       Text("markers", style="dim"))
    return t


class LiveDashboard:
    """
    Live-updating terminal dashboard.

    Usage:
        dash = LiveDashboard(recording=True)
        with dash:
            while running:
                dash.update(frame_dict)
                time.sleep(0.1)
    """

    def __init__(self, recording: bool = False):
        self._recording = recording
        self._live: Optional[Live] = None
        self._last_frame: dict = {}

    def _render(self) -> Panel:
        rec_label = Text("\u25cf RECORDING", style="bold red") if self._recording else Text("\u25cb IDLE", style="dim")
        table = _make_table(self._last_frame)
        return Panel(table, title="[bold]VTBAP Dashboard[/bold]", subtitle=rec_label)

    def update(self, frame: dict, recording: Optional[bool] = None) -> None:
        self._last_frame = frame
        if recording is not None:
            self._recording = recording
        if self._live:
            self._live.update(self._render())

    def __enter__(self):
        self._live = Live(self._render(), console=console, refresh_per_second=10)
        self._live.__enter__()
        return self

    def __exit__(self, *args):
        if self._live:
            self._live.__exit__(*args)
