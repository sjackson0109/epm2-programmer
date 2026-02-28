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


# ---------------------------------------------------------------------------
# ISO 15765-4 multi-frame helpers
# ---------------------------------------------------------------------------

def parse_first_frame(data: bytes) -> tuple[int, bytes]:
    """Extract total length and initial payload from a First Frame.

    A First Frame has PCI nibble ``0x1`` in the upper nibble of byte 0.
    Bytes 0-1 encode:  ``0x1NNN`` where NNN is the 12-bit total length.
    Bytes 2-7 carry the first 6 bytes of payload.

    Returns:
        (total_length, initial_payload)

    Raises:
        ValueError: if *data* is not a valid First Frame.
    """
    if len(data) < 2:
        raise ValueError("First Frame must be at least 2 bytes.")
    if (data[0] & 0xF0) >> 4 != 0x1:
        raise ValueError(f"Not a First Frame (PCI nibble: {(data[0] & 0xF0) >> 4:#x}).")
    total_length = ((data[0] & 0x0F) << 8) | data[1]
    payload = data[2:]
    return total_length, payload


def parse_consecutive_frame(data: bytes) -> tuple[int, bytes]:
    """Extract sequence number and payload from a Consecutive Frame.

    A Consecutive Frame has PCI nibble ``0x2``.  The lower nibble of
    byte 0 is the sequence number (0–F, wrapping).

    Returns:
        (sequence_number, payload)

    Raises:
        ValueError: if *data* is not a valid Consecutive Frame.
    """
    if not data:
        raise ValueError("Consecutive Frame must not be empty.")
    if (data[0] & 0xF0) >> 4 != 0x2:
        raise ValueError(f"Not a Consecutive Frame (PCI nibble: {(data[0] & 0xF0) >> 4:#x}).")
    seq = data[0] & 0x0F
    return seq, data[1:]


class FrameReassembler:
    """Stateful ISO 15765-4 multi-frame reassembler.

    Feed raw CAN frames one at a time via :meth:`feed`.  Returns the
    complete reassembled payload once all frames have been received, or
    ``None`` while assembly is still in progress.

    Handles Single Frame, First Frame, and Consecutive Frame types.

    Example::

        r = FrameReassembler()
        result = r.feed(single_frame_bytes)   # → bytes immediately
        r2 = FrameReassembler()
        assert r2.feed(first_frame_bytes) is None
        result = r2.feed(consecutive_frame_bytes)  # → bytes when done

    Raises:
        ValueError: on unexpected frame type or sequence number mismatch.
    """

    def __init__(self) -> None:
        self._total_length: int = 0
        self._buf: bytearray = bytearray()
        self._next_seq: int = 1
        self._in_progress: bool = False

    def feed(self, frame: bytes) -> bytes | None:
        """Accept one raw CAN frame.

        Returns the reassembled payload when complete, otherwise ``None``.

        Raises:
            ValueError: on unexpected frame type or out-of-order sequence.
        """
        if not frame:
            return None

        frame_type = (frame[0] & 0xF0) >> 4

        if frame_type == 0x0:  # Single Frame
            length = frame[0] & 0x0F
            return bytes(frame[1 : 1 + length])

        if frame_type == 0x1:  # First Frame
            self._total_length, initial = parse_first_frame(frame)
            self._buf = bytearray(initial)
            self._next_seq = 1
            self._in_progress = True
            return None

        if frame_type == 0x2:  # Consecutive Frame
            if not self._in_progress:
                raise ValueError("Received Consecutive Frame before First Frame.")
            seq, payload = parse_consecutive_frame(frame)
            if seq != self._next_seq:
                raise ValueError(
                    f"Sequence mismatch: expected {self._next_seq}, got {seq}."
                )
            self._buf.extend(payload)
            self._next_seq = (self._next_seq + 1) & 0x0F
            if len(self._buf) >= self._total_length:
                result = bytes(self._buf[: self._total_length])
                self._in_progress = False
                return result
            return None

        raise ValueError(f"Unexpected frame type: {frame_type:#x}.")

