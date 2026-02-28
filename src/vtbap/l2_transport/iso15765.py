"""ISO 15765-4 frame construction/parsing helpers."""
from __future__ import annotations


def build_single_frame(pci_data: bytes) -> bytes:
    """Build an ISO 15765 Single Frame (SF) for up to 7 bytes of data."""
    if len(pci_data) > 7:
        raise ValueError("Single frame supports \u22647 data bytes.")
    length = len(pci_data)
    return bytes([length]) + pci_data + bytes(7 - length)


def parse_response(data: bytes) -> bytes:
    """Extract payload from an ISO 15765 Single Frame response."""
    if not data:
        return b""
    frame_type = (data[0] & 0xF0) >> 4
    if frame_type == 0:  # Single Frame
        length = data[0] & 0x0F
        return data[1 : 1 + length]
    return data  # Return raw for multi-frame (not implemented here)
