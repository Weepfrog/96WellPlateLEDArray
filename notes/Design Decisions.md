---
tags: [96-well-led-array, decisions]
---

# Design Decisions

Decisions confirmed 2026-07-13 (planning session): **~50 W** total power ·
**24 V** brick · **per-LED control** · **two boards**.

## Topology: one buck per LED

Considered and rejected:
- **Matrix scanning** — 1/8 duty needs 8× peak current; LEDs can't sustain it,
  and average power collapses.
- **Multichannel display drivers** (TLC59xx, MBI…) — top out at ~60-90 mA/ch;
  we need 256 mA.
- **String + shunt-switch (TPS92662 matrix manager)** — elegant but pricey,
  automotive parts thin at LCSC.
- **Linear per-channel from a low rail** — a 24 V→3 V/34 A converter plus 40 W
  of linear dissipation; awful.

**Chosen:** PT4115 hysteretic buck per channel from 24 V. Confirmed by
datasheet math: single 2.1 V LED from 24 V → ~9 % duty, fsw ≈ 630 kHz with
47 µH — inside the 1 MHz limit, no minimum-on-time problem.

## LED: Hongli HL-C3535F15R3GA-ZW (C5445086)

- No 660 nm LED exists in JLCPCB's *Basic* library; nothing viable ≥0.5 W in
  2835/3030 was in stock → 3535 it is.
- 3 W-rated part run at 0.5 W → big lifetime/thermal margin.
- Pad 1 = anode (`+` silk), pad 2 = cathode, pad 3 = thermal → **tie pad 3 to
  pad 2** per datasheet recommendation (safe whether or not the pad is
  internally bonded to the cathode).
- **One reflow only** — LED board is single-side assembly. Avoid hot-air rework.

## LED swapability

Requirement: swap wavelengths without redesign.
- 3535 3-pad is the industry-standard (XP-style) footprint: 730 nm far-red,
  850/940 nm IR, blue, UV drop in.
- PT4115 buck is Vf-agnostic (~1.5–3.4 V all fine) — zero component changes.
- Current set only by Rs: `I = 0.1 V / 0.39 Ω = 256 mA`; change R1-R96 on the
  control board for lower-rated LEDs.
- Mixed-wavelength (e.g. 660/730 checkerboard) works since channels are
  independent.

## Dimming: PCA9685 at ~244 Hz

PCA9685's 12-bit PWM at max 1526 Hz has 160 ns LSBs — far below the PT4115
DIM response (~tens of µs). At 244 Hz prescale, 1 LSB ≈ 1 µs → **~10-11 usable
bits**, monotonic. Full-panel update over 400 kHz I2C ≈ 90 Hz.
PCA9685 is NXP-only at LCSC (~$2, the priciest BOM line); AW9523B is the
8-bit fallback if it goes out of stock.

## Temperature sensing

10k NTC (B=3434) + 10k 1% divider from 3.3 V, ratiometric into the ESP32 ADC
(nonlinearity mostly cancels; absolute accuracy ±2 °C is plenty for derating).
Six CD74HC4067 on the LED board; ADS1115 footprint on the control board is
DNP insurance if the internal ADC disappoints.

## Boot safety

PT4115 DIM **floating = 100 % on**. Defenses: PCA9685 outputs are LOW at
reset, /OE hard-tied to GND, and a 100k pulldown on every DIM line. The panel
cannot boot bright.

## Interconnect

2.54 mm shrouded IDC (2.5-3 A/pin vs 256 mA needed), keyed against reversal.
24 V never crosses the ribbons — it enters only at the control board screw
terminal/barrel jack. Ribbon spare pins carry GND.

## Related

[[Architecture]] · [[Parts and BOM]] · [[../CONNECTIONS|CONNECTIONS]]
