# epm2-programmer — VTBAP

**PSA Vehicle Transmission Behaviour Analysis Platform**

A read-only diagnostic tool for analysing Stellantis/PSA automatic gearbox behaviour via an OBD-II / J2534 pass-through interface (e.g. VXDIAG VCX SE PSA).  
The primary goal is to capture live ECU/TCU telemetry, measure actual gear ratios, and compare them against EAT8 nominal values — helping to diagnose gearbox calibration issues (shift-point RPM, torque converter lock-up, clutch-slip, etc.) without writing to or reprogramming the ECU.

---

## Architecture — 8-layer stack

| Layer | Package | Responsibility |
|-------|---------|---------------|
| L1 | `l1_hardware` | J2534 DLL abstraction; simulation mode on non-Windows |
| L2 | `l2_transport` | CAN session, ISO 15765-4 framing |
| L3 | `l3_vehicle_comms` | OBD-II Mode 01 PIDs + UDS ReadDataByIdentifier (0x22) |
| L4 | `l4_signal_processing` | Merge & timestamp-align OBD-II / UDS frames; compute derived `GearRatio` |
| L5 | `l5_recording` | Write telemetry to timestamped CSV + SHA-256 sidecar |
| L6 | `l6_analytics` | Gear utilisation map, RPM efficiency profile, upshift thresholds, torque reserve, manual override stability, **gear ratio analysis** |
| L7 | `l7_reporting` | PDF engineering report + dealer summary + PNG graph pack |
| L8 | `l8_ui` | Rich live terminal dashboard |

---

## Safety

The system is **strictly read-only**.  All write/programming UDS services are blocked at the safety layer (`safety.py`) and will raise `SafetyViolationError` if attempted:

- `0x27` SecurityAccess  
- `0x2E` WriteDataByIdentifier  
- `0x34–0x37` Download/Upload/Transfer  
- `0x31` RoutineControl (ECU coding/flash)  
- `0x85` ControlDTCSetting  
- `0x28` CommunicationControl  

---

## Signals collected

### OBD-II (Mode 01)
| Signal | PID |
|--------|-----|
| Vehicle speed | `0x0D` |
| Engine RPM | `0x0C` |
| Throttle position | `0x11` |
| Accelerator pedal position | `0x49` |
| Calculated engine load | `0x04` |
| Intake manifold pressure | `0x0B` |

### UDS ReadDataByIdentifier (PSA/Stellantis proprietary DIDs)
| Signal | DID |
|--------|-----|
| Gear actual / commanded | `0x1234` / `0x1235` |
| Torque converter lock state | `0x1236` |
| Driver torque request / engine torque / limit | `0x1237–0x123A` |
| Drive mode (Eco/Normal/Sport/Manual) | `0x123B` |
| Clutch slip | `0x123C` |
| Transmission input / output RPM | `0x123D` / `0x123E` |

`GearRatio` is computed in real time as `TransInputRPM / TransOutputRPM`.

---

## Analytics

| Module | Method | Description |
|--------|--------|-------------|
| 8.1 | `gear_utilisation_map()` | Speed-vs-gear heat map |
| 8.2 | `rpm_efficiency_profile()` | Average RPM per speed band (30–70 mph) |
| 8.3 | `upshift_thresholds()` | Conditions at each upshift event |
| 8.4 | `torque_reserve()` | Available minus requested torque |
| 8.5 | `manual_override_stability()` | Periods where commanded gear > automatic gear |
| 8.6 | `gear_ratio_analysis()` | **Measured ratio vs EAT8 nominal per gear — flags calibration deviations** |

EAT8 nominal ratios used for comparison (AL8 / EF8):

| Gear | Nominal ratio |
|------|--------------|
| 1 | 4.714 |
| 2 | 3.143 |
| 3 | 2.106 |
| 4 | 1.667 |
| 5 | 1.285 |
| 6 | 1.000 |
| 7 | 0.839 |
| 8 | 0.667 |

---

## Outputs

- `YYYYMMDD_HHMMSS_<VIN>_SESSION.csv` — raw telemetry (all signals + computed GearRatio)
- `*.sha256` — SHA-256 checksum sidecar for data integrity
- `*_engineering_report.pdf` — full analytical report including gear ratio deviation table
- `*_dealer_summary.pdf` — 1-page summary
- `*_speed_vs_gear.png`, `*_rpm_vs_speed.png`, `*_pedal_vs_torque.png`, `*_mode_comparison.png`, `*_gear_delta.png`, `*_gear_ratio.png`

---

## Installation

```bash
pip install -e .
```

## Usage

```bash
vtbap                          # simulation mode (no hardware)
vtbap --dll-path C:\path\to\j2534.dll --vin VF3XXXXXX
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```
