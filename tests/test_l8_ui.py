"""Tests for L8 UI components."""
import queue
import pytest

from vtbap.l8_ui.marker_input import MarkerInput, _KEY_MAP
from vtbap.config import EVENT_MARKERS


def test_key_map_covers_m1_to_m7():
    for i in range(1, 8):
        assert str(i) in _KEY_MAP
        assert _KEY_MAP[str(i)] == EVENT_MARKERS[f"M{i}"]


def test_get_pending_returns_none_when_empty():
    mi = MarkerInput()
    assert mi.get_pending() is None


def test_get_pending_returns_marker_from_queue():
    """Inject a pre-populated queue to verify get_pending()."""
    q: queue.Queue = queue.Queue()
    q.put(EVENT_MARKERS["M1"])
    mi = MarkerInput(_queue=q)
    assert mi.get_pending() == EVENT_MARKERS["M1"]
    assert mi.get_pending() is None  # consumed


def test_get_pending_clears_after_read():
    q: queue.Queue = queue.Queue()
    q.put(EVENT_MARKERS["M3"])
    mi = MarkerInput(_queue=q)
    first = mi.get_pending()
    second = mi.get_pending()
    assert first == EVENT_MARKERS["M3"]
    assert second is None


def test_marker_input_context_manager_does_not_raise():
    """Entering/exiting the context manager must not raise."""
    with MarkerInput() as mi:
        assert mi.get_pending() is None
