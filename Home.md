---
tags: [96-well-led-array, dashboard]
---

# 96-Well Plate LED Array — Home

660 nm illuminator for a standard **96-well microplate**: 12×8 LEDs at 9 mm
(SBS well pitch), one LED per well, **per-well dimming + per-well temperature
sensing**, ESP32-controlled, JLCPCB-fabricated.

## Start here

- [[notes/Architecture|Architecture]] — how the two boards work
- [[CONNECTIONS|Wiring guide (CONNECTIONS.md)]] — every net, pin by pin ← *wire the schematics from this*
- [[notes/Design Decisions|Design Decisions]] — why each part/topology was chosen
- [[notes/Parts and BOM|Parts and BOM]] — every component with LCSC numbers
- [[notes/Bring-Up Checklist|Bring-Up Checklist]] — first power-on procedure
- [[notes/Firmware Plan|Firmware Plan]] — ESP32 pin map + software sketch
- [[README|README]] — GitHub-facing overview

## Files

- KiCad LED board: `12x8 Led Array 9mm pitch/`
- KiCad control board: `control-board/`
- Schematic PDFs: [[docs/led-board-schematic.pdf|LED board PDF]] · [[docs/control-board-schematic.pdf|control board PDF]]
- Datasheets: `reference/datasheets/` (named by part + usage)
- Generators: `scripts/` (`design_data.py` = single source of truth)

## Status

| Stage | State |
|---|---|
| Parts selection (JLCPCB-stocked) | ✅ done |
| Schematics (parts placed, verified pinouts) | ✅ done — **awaiting your review** |
| Wiring | ⬜ you, per [[CONNECTIONS]] |
| PCB placement | ⏸ drafts exist, on hold until schematics verified |
| JLCPCB BOM/CPL | ⬜ after LCSC verification agent returns |
| Order + bring-up | ⬜ |

## Quick facts

- 96 × Hongli 3535 660 nm LED (3 W-rated) run at **256 mA ≈ 0.5 W** → ~50 W panel
- One **PT4115** buck constant-current channel per LED; PWM via 6 × PCA9685
- 96 × 10k NTC → six 16:1 muxes → 6 ESP32 ADC pins
- LEDs are **wavelength-swappable** (any 3535 3-pad part, ~1.5–3.4 V Vf) — see [[notes/Design Decisions#LED swapability]]
