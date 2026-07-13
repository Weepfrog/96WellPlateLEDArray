---
tags: [96-well-led-array, hardware]
---

# Architecture

```
24V 4-6A brick ─┬─► CONTROL BOARD (170×190mm, 2-layer)
                │     96× PT4115 buck CC channel (256mA, one per well)
                │     6× PCA9685 16-ch I2C PWM → per-well dimming
                │     XL1509-5.0 → 5V rail → ESP32 DevKitC (socketed)
                │     3 buttons + 3 status LEDs + fan switch
                │
                │  4× 50-way IDC ribbon (192 anode/cathode lines)
                │  1× 20-way IDC ribbon (6 analog + 4 addr + 3V3 + GND)
                │
                └─► LED BOARD (140×120mm, 4-layer, flat back → heatsink)
                      96× 660nm 3535 LED at exact 9.0mm SBS pitch
                      96× 10k NTC (one beside each LED)
                      6× CD74HC4067 16:1 mux
```

## Why this shape

- **Per-well dimming at 256 mA** rules out matrix scanning (can't sustain
  power) and display-driver ICs (≤90 mA). One tiny hysteretic buck per LED is
  the cheapest correct answer (~$0.19/channel). See [[Design Decisions]].
- The PT4115 floats its LED between the sense resistor and the inductor, so
  **each well needs its own anode AND cathode line** — hence 192 ribbon lines.
  Each channel's pair sits on adjacent IDC pins to minimize loop area.
- Drivers live on the control board so the LED board's back face is a flat,
  unbroken thermal surface and the NTC analog lines stay away from switching
  noise.
- 96 NTC signals reduce to 10 ribbon lines via the six on-board muxes.

## Channel numbering

`n = (row-1)*12 + col`, rows top→bottom 1-8, cols left→right 1-12, viewed
from the LED side. CH1 = A1 corner well, CH96 = H12. Same numbering on both
boards, in [[../CONNECTIONS|CONNECTIONS]], and in firmware.

## Thermal path

LED thermal pad (tied to its cathode) → 5-via farm → inner + back copper →
insulating thermal pad → heatsink. Per-well NTC lets firmware derate any hot
well; Hongli's limit is 85 °C at the cathode pad ([[Bring-Up Checklist]]).
Heatsink must be electrically isolated because the thermal islands carry
cathode potential.
