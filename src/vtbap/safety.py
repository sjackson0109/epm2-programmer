"""
Safety constraint enforcement.

ABSOLUTE REQUIREMENTS (Section 11):
- System SHALL operate read-only by default.
- Disable write services.
- Block ECU coding.
- Block telecoding.
- Block firmware flashing.
- No Seed-Key Algorithms permitted.
- No SecurityAccess UDS routines permitted.
"""

# Blocked UDS service IDs
_BLOCKED_SERVICES = frozenset([
    0x27,  # SecurityAccess
    0x2E,  # WriteDataByIdentifier
    0x34,  # RequestDownload
    0x35,  # RequestUpload
    0x36,  # TransferData
    0x37,  # RequestTransferExit
    0x31,  # RoutineControl (ECU coding/flash)
    0x85,  # ControlDTCSetting
    0x28,  # CommunicationControl
])

class SafetyViolationError(Exception):
    """Raised when a prohibited operation is attempted."""

def assert_read_only(service_id: int) -> None:
    """Raise SafetyViolationError if service_id is a write/programming service."""
    if service_id in _BLOCKED_SERVICES:
        raise SafetyViolationError(
            f"UDS service 0x{service_id:02X} is blocked: system is read-only."
        )

def is_read_only_service(service_id: int) -> bool:
    """Return True if the service is permitted (read-only)."""
    return service_id not in _BLOCKED_SERVICES
