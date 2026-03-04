"""
L1 — Hardware Abstraction: J2534Protocol base class.

Defines the abstract interface that all hardware (and simulation) backends
must implement.  Real hardware requires Windows + a VXDIAG DLL; simulation
mode works on any platform.
"""
from __future__ import annotations
import abc
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class J2534Protocol(abc.ABC):
    """Abstract base class for J2534 Pass-Through implementations.

    Platform notes:
        - Real hardware (``WindowsJ2534Interface``) requires Windows 10/11
          and a VXDIAG VCX SE J2534 DLL.
        - ``SimulationInterface`` works on any platform and is safe to use
          in tests and CI environments.
    """

    @abc.abstractmethod
    def open(self) -> bool:
        """Open a connection to the J2534 device."""

    @abc.abstractmethod
    def connect(self, protocol: int = 0x06, baud: int = 500000) -> bool:
        """Establish a channel on the given protocol."""

    @abc.abstractmethod
    def disconnect(self) -> None:
        """Disconnect the channel."""

    @abc.abstractmethod
    def close(self) -> None:
        """Close the device."""

    @abc.abstractmethod
    def write_msg(self, data: bytes, timeout_ms: int = 100) -> bool:
        """Send a raw J2534 message."""

    @abc.abstractmethod
    def read_msg(self, timeout_ms: int = 200) -> Optional[bytes]:
        """Read a raw J2534 message. Returns None on timeout."""

    @property
    @abc.abstractmethod
    def is_connected(self) -> bool:
        """True if the interface is currently connected."""


class SimulationInterface(J2534Protocol):
    """Deterministic simulation backend — works on any platform.

    All reads return ``None`` (or an optional configurable fixture).
    Useful for unit tests and CI environments where no real hardware is
    available.

    Args:
        read_fixture: If provided, :meth:`read_msg` returns this value
            instead of ``None`` on every call.
    """

    def __init__(self, read_fixture: Optional[bytes] = None) -> None:
        self._read_fixture = read_fixture
        self._connected = False
        self.simulation_mode = True  # duck-type compat with J2534Interface

    def open(self) -> bool:
        logger.debug("SimulationInterface.open() called.")
        return True

    def connect(self, protocol: int = 0x06, baud: int = 500000) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def close(self) -> None:
        pass

    def write_msg(self, data: bytes, timeout_ms: int = 100) -> bool:
        return True

    def read_msg(self, timeout_ms: int = 200) -> Optional[bytes]:
        return self._read_fixture

    @property
    def is_connected(self) -> bool:
        return self._connected
