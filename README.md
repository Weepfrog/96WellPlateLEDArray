# 12×8 High-Power 660nm LED Array

A 96-LED (12 across × 8 down, 9 mm pitch) deep-red 660 nm panel with **per-LED
dimming** and **per-LED temperature sensing**, driven by an ESP32 DevKitC.
Designed for JLCPCB fabrication + assembly; all parts chosen from the
JLCPCB/LCSC library (stock verified 2026-07-13).

## System overview

```
24V 4-6A brick ──► CONTROL BOARD ══ 4× 50-way + 1× 20-way IDC ribbon ══► LED BOARD
                   96× PT4115 buck CC        192 anode/cathode lines        96× 660nm 3535 LED
                   6× PCA9685 PWM (I2C)      + analog/logic lines           96× 10k NTC
                   XL1509 5V rail                                           6× CD74HC4067 mux
                   ESP32 DevKitC socket                                     flat back → heatsink
                   3 buttons + status LEDs
```

- **~50 W** total at full drive (≈0.5 W per LED @ 256 mA, huge margin on 3 W-rated LEDs)
- Per-LED PWM: one PT4115 buck constant-current channel per LED, DIM pins on six
  PCA9685 16-channel I2C PWM expanders (run PWM at ~244 Hz → ~10-11 usable bits)
- Per-LED temperature: one 0603 NTC beside each LED, multiplexed 16:1 onto six
  ESP32 ADC1 inputs
- LED board is 4-layer with thermal-via farms; back face is bare copper for a
  bolt-on heatsink (use an insulating thermal pad)

## Repository layout

| Path | What |
|---|---|
| `12x8 Led Array 9mm pitch/` | **LED board** KiCad project (96 LEDs + NTCs + muxes) |
| `control-board/` | **Control board** KiCad project (drivers, PWM, ESP32, UI) |
| `libraries/` | `jlc_parts` symbol/footprint/3D library (converted from EasyEDA, JLCPCB-exact pads) |
| `scripts/design_data.py` | **Single source of truth**: every part, position, and net |
| `scripts/gen_schematics.py` | Regenerates both `.kicad_sch` (parts placed, you wire per CONNECTIONS.md) |
| `scripts/gen_pcbs.py` | Regenerates both `.kicad_pcb` (footprints pre-placed) |
| `reference/datasheets/` | Datasheets for key parts |
| `production/` | JLCPCB BOM + CPL exports |
| `CONNECTIONS.md` | **Your wiring guide** — every net, pin by pin |

## Workflow

1. **Schematics are hierarchical and fully wired**: each board is a root
   sheet + one sub-sheet (`well.kicad_sch` / `channel.kicad_sch`)
   instantiated 96×, with references matching `CONNECTIONS.md` (LED1-96,
   U1-96, …). Verified automatically: KiCad's exported netlist matches the
   intended netlist in `design_data.py` net-for-net; ERC is clean (3 benign
   library-mismatch warnings on the control board). Review, then move to
   layout.
2. Open the PCB — footprints are pre-placed (LED grid at exact 9.0 mm
   pitch; placement still draft). Run **Tools → Update PCB from Schematic
   (F8)**, then route.
3. Regenerating: `python scripts/gen_schematics_hier.py`, then
   `scripts/gen_pcbs.py` with KiCad's Python (see script headers), then
   `python scripts/gen_connections.py`. Verify with
   `scripts/verify_netlist.py` (see header). **Regeneration overwrites the
   sch/pcb files** — don't rerun after manual edits unless you want a reset.

## Key design rules (don't skip)

- **LED polarity:** pad 1 = anode (marked `+` on silk), pad 2 = cathode,
  pad 3 = center thermal pad — **tie pad 3 to pad 2 (cathode)** per Hongli's
  datasheet. Each LED's thermal island is at its own cathode potential, so the
  heatsink must be electrically isolated (thermal pad, not bare paste).
- **PT4115 DIM floats high** = full brightness. Every DIM has a 100k pulldown
  so the panel boots dark. Keep them.
- **One reflow only** for the LEDs (datasheet) — LED board is single-side
  assembly, which satisfies this. Don't hot-air rework casually.
- 24 V power enters each board via its own screw terminal — **do not route
  LED supply current through the IDC ribbons** (they carry per-channel
  anode/cathode pairs and logic only).
- IDC headers and ESP32 sockets are through-hole: hand-solder them (cheaper
  than JLCPCB THT assembly).

## Swapping LED wavelengths

The design is wavelength-agnostic on purpose:

- The 3535 3-pad footprint is the industry-standard pattern (Cree XP
  compatible). 730 nm far-red, 850/940 nm IR, blue, and UV parts from Hongli,
  Silverlight, JNJ and others drop straight in.
- The PT4115 buck **does not care about forward voltage** — anything from
  ~1.5 V (IR) to ~3.4 V (blue/UV) runs at the same regulated current with zero
  component changes.
- Current is set only by the 0.39 Ω sense resistor (256 mA). For a lower-rated
  LED, change R1–R96 on the control board: `I = 0.1 V / Rs`.
- Checklist when swapping: 3535 package with center pad, anode on pad 1 /
  matching polarity, continuous current rating ≥ 300 mA, note the part's own
  reflow limits.
- Mixed arrays are fine too (e.g. 660 nm + 730 nm checkerboard) since every
  channel is independent.

## Firmware map (ESP32 DevKitC-38)

| GPIO | Function |
|---|---|
| 21 / 22 | I2C SDA / SCL → PCA9685 ×6 (0x40–0x45), optional ADS1115 (0x48) |
| 16 / 17 / 18 / 19 | Mux address S0–S3 (shared, all six muxes) |
| 32, 33, 34, 35, 36, 39 | ADC1 inputs ← NTC_SIG1–6 (mux outputs) |
| 25 | Fan PWM (low-side AO3400A) |
| 4 / 13 | Status LED (blue) / Fault LED (red) |
| 14 / 27 / 26 | Buttons MODE / UP / DOWN (to GND, internal pull-ups) |

NTC conversion: 10k NTC (B=3434 K) high side, 10k 1% low side, ratiometric to
3.3 V. Scan all 96 via mux (settle ≥200 µs after address change). Derate any
channel whose pad temperature approaches 85 °C (Hongli's recommended limit).

## Safety

50 W of 660 nm in a 10 cm square is extremely bright — never look at the
array at power, ramp brightness in firmware, and treat the NTC thermal
shutdown as a backstop, not a substitute for the heatsink.

## Status

- [x] Architecture + parts selection (all JLCPCB-stocked, C-numbers in BOM)
- [x] Schematics generated, parts placed with library-verified pinouts
- [ ] PCBs with pre-placed footprints
- [ ] CONNECTIONS.md wiring guide
- [ ] JLCPCB BOM/CPL exports
- [ ] User wiring + routing
- [ ] Order + bring-up
