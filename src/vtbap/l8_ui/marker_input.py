"""
L8 — UI Layer: Non-blocking keyboard marker input.

Reads single-keypress input from the terminal in a background thread and
maps keys ``1``–``7`` to the corresponding ``EVENT_MARKERS`` labels.
"""
from __future__ import annotations
import platform
import queue
import sys
import threading
from typing import Optional

from vtbap.config import EVENT_MARKERS

# Key-to-marker mapping (keys '1'–'7' → M1–M7 labels)
_KEY_MAP: dict[str, str] = {
    str(i): EVENT_MARKERS[f"M{i}"] for i in range(1, 8)
}


def _read_key_posix() -> Optional[str]:
    """Read a single character from stdin without echo (POSIX)."""
    import tty
    import termios

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch


def _read_key_windows() -> Optional[str]:
    """Read a single character from the console (Windows)."""
    import msvcrt  # type: ignore[import]

    return msvcrt.getwch()


class MarkerInput:
    """Non-blocking keyboard marker input using a background thread.

    Maps key presses ``1``–``7`` to the corresponding ``EVENT_MARKERS``
    description strings.  Uses ``msvcrt.getwch()`` on Windows and
    ``tty``/``termios`` on POSIX platforms.

    Usage::

        with MarkerInput() as mi:
            while running:
                pending = mi.get_pending()   # returns str or None

    Thread-safety: :meth:`get_pending` is safe to call from any thread.
    """

    def __init__(self, _queue: Optional[queue.Queue] = None) -> None:
        # Allow injection of a pre-populated queue for unit testing.
        self._q: queue.Queue[str] = _queue if _queue is not None else queue.Queue()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._read_key = (
            _read_key_windows if platform.system() == "Windows" else _read_key_posix
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_pending(self) -> Optional[str]:
        """Return and clear the latest pending marker, or ``None``."""
        try:
            return self._q.get_nowait()
        except queue.Empty:
            return None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "MarkerInput":
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *args: object) -> None:
        self._stop_event.set()
        # The background thread is a daemon and will not block interpreter
        # shutdown, but we join briefly to allow clean teardown.
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _run(self) -> None:
        """Background thread: read keys and enqueue matching markers.

        Both ``_read_key_posix`` and ``_read_key_windows`` block until a
        character is available, so this thread does not spin the CPU.
        """
        while not self._stop_event.is_set():
            try:
                ch = self._read_key()
            except Exception:
                # stdin not a tty (e.g. redirected in CI) — stop silently.
                break
            if ch is None:
                # Shouldn't normally occur with blocking reads; yield anyway.
                import time as _time
                _time.sleep(0.05)
                continue
            marker = _KEY_MAP.get(ch)
            if marker:
                # Keep only the latest unread marker.
                while not self._q.empty():
                    try:
                        self._q.get_nowait()
                    except queue.Empty:
                        break
                self._q.put(marker)
