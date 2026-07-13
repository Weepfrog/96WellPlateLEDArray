---
tags: [96-well-led-array, bring-up]
---

# Bring-Up Checklist

## Before ordering

- [ ] Wire both schematics per [[../CONNECTIONS|CONNECTIONS]]; ERC clean
  (power symbols + PWR_FLAG as noted there)
- [ ] F8 sync both PCBs, route, DRC clean
- [ ] JLCPCB DFM upload; **check LED polarity in the assembly preview** — a
  rotated/mirrored LED footprint is the classic whole-board failure
- [ ] Confirm every Extended part is still in stock at order time

## Control board alone (no ribbons, no LED board)

- [ ] Visual: no solder bridges on PT4115 rows
- [ ] 24 V in via J6, current-limited bench supply if available (set 200 mA
  limit first)
- [ ] +5 V rail = 4.9-5.2 V; +3V3 present after socketing ESP32
- [ ] ESP32 I2C scan finds 0x40-0x45 (and 0x48 if ADS1115 fitted)
- [ ] All DIM lines read ~0 V (pulldowns working, panel would boot dark)
- [ ] Clip a test LED (any color, any Vf) across one channel's A/K pins;
  command 5 % duty → dim glow; 100 % → bright, current ≈ 256 mA in series
  meter

## Boards mated

- [ ] Ribbons keyed, 1:1, seated; 24 V only at control board
- [ ] All 96 wells at 5 % duty — walk a "chaser" pattern to map channel ↔ well
  and catch any swapped ribbon
- [ ] NTC scan: all 96 read ~ambient ±3 °C; heat one well with a fingertip
  and watch it move
- [ ] Mount heatsink (insulating pad!) before any run >20 % duty

## Full power soak

- [ ] 100 % duty, log max/min/spread of all 96 NTCs every 10 s
- [ ] Cathode-pad temps must stay < 85 °C (Hongli limit; 75 °C is the
  comfortable target) — set firmware derate threshold from this run
- [ ] Input current at 24 V ≈ 2.4-2.6 A
- [ ] ⚠ **Never look at the array at power** — 50 W of 660 nm at 10 cm² is an
  eye hazard. Use indirect viewing / camera.

Related: [[Firmware Plan]] · [[Architecture]]
