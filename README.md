# VTBAP — Vehicle Telemetry & Behaviour Analysis Platform

VTBAP is a **read-only** diagnostic and telemetry tool for PSA/Stellantis vehicles (Peugeot, Citroën, Vauxhall, etc.).  It connects to the vehicle via a J2534-compatible pass-through interface, captures real-time OBD-II and UDS signals across 8 software layers, and produces structured session recordings plus engineering reports — all without writing a single byte to any ECU.

---

## Hardware Prerequisites

| Requirement | Details |
|---|---|
| Interface | VXDIAG VCX SE (PSA variant) or any J2534-compatible pass-through device |
| Operating System | Windows 10 / 11 (64-bit) — required for real hardware via `ctypes.WinDLL` |
| J2534 DLL | Vendor-supplied DLL (e.g. `VXDIAG_VCX_SE_J2534.dll`) |
| OBD-II connector | Standard 16-pin DLC under the dashboard |

> **Linux / macOS:** The software runs in *simulation mode* on non-Windows platforms.  No real vehicle connection is made, but all layers (recording, analytics, reporting) function normally with synthesised data.

---

## Quick-Start

```bash
# 1. Clone and install in editable mode
git clone https://github.com/sjackson0109/epm2-programmer.git
cd epm2-programmer
pip install -e .

# 2. Run (simulation mode — no DLL needed)
vtbap

# 3. Run against real hardware (Windows only)
vtbap --dll "C:\Program Files\VXDIAG\VCX SE PSA\J2534.dll"
```

---

## Safety Notice

> ⚠️ **VTBAP is a read-only system.**  
> It uses only UDS service `0x22` (ReadDataByIdentifier) and OBD-II mode `0x01`.  
> No write services (`0x2E`, `0x27`, `0x31`, etc.) are available.  
> The `safety.py` module enforces this at import time and will raise `SafetyViolationError` if any write-capable service code is used.

---

## Architecture — 8 Layers

| Layer | Module | Description |
|---|---|---|
| L1 | `l1_hardware` | J2534 DLL abstraction and VCI device manager |
| L2 | `l2_transport` | ISO 15765-4 CAN framing and multi-frame reassembly |
| L3 | `l3_vehicle_comms` | OBD-II and UDS signal readers |
| L4 | `l4_signal_processing` | Frame merging and signal normalisation |
| L5 | `l5_recording` | CSV session recorder with SHA-256 integrity checksum |
| L6 | `l6_analytics` | Gear utilisation, RPM efficiency, torque reserve analysis |
| L7 | `l7_reporting` | Engineering PDF / dealer summary report generation |
| L8 | `l8_ui` | Rich live terminal dashboard and keyboard marker input |

