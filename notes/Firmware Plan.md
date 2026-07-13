---
tags: [96-well-led-array, firmware]
---

# Firmware Plan (ESP32 DevKitC-38)

## Pin map

| GPIO | Function |
|---|---|
| 21 / 22 | I2C SDA/SCL @ 400 kHz → 6× PCA9685 (0x40-0x45), opt. ADS1115 (0x48) |
| 16 / 17 / 18 / 19 | Mux address S0-S3 (shared across all six muxes) |
| 32 / 33 / 34 / 35 / 36 / 39 | ADC1 ← NTC_SIG1-6 (muxes U1-U6) |
| 25 | Fan PWM (25 kHz LEDC, low-side AO3400A) |
| 4 / 13 | STATUS (blue) / FAULT (red) LEDs |
| 14 / 27 / 26 | Buttons MODE/UP/DOWN (to GND, `INPUT_PULLUP`) |

Note: GPIO34/35/36/39 are input-only — fine, they're ADC inputs here.

## Core loops

- **PWM**: PCA9685 prescale ≈ 244 Hz (see [[Design Decisions#Dimming]]).
  Well n → chip `(n-1)//16` (0x40+k), output `LED[(n-1)%16]`. Full-frame
  update ≈ 90 Hz max — plenty.
- **Thermal scan**: set S0-S3, wait ≥200 µs, read 6 ADCs (one per mux) →
  6 wells per address step, 96 wells in 16 steps, full sweep well under
  100 ms. Convert ratiometrically (B=3434, 10k/10k divider); calibrate ADC
  with `esp_adc_cal`.
- **Derating**: per-well PI or simple threshold — above 75 °C scale that
  well's duty down; above 85 °C zero it and set FAULT. Log over serial/WiFi.
- **Boot**: all duties 0, ramp to setpoint over ~1 s ([[Design
  Decisions#Boot safety]]).

## UI sketch

MODE cycles presets (off / 10 % / 50 % / 100 % / chaser test), UP/DOWN trim,
STATUS blinks heartbeat, FAULT latches on any thermal event until MODE held.

## Libraries

Arduino-ESP32 or ESP-IDF; Adafruit PWM Servo Driver library works for
PCA9685 (it's the same chip as their servo board), or ~50 lines of raw I2C.

Related: [[Bring-Up Checklist]] · [[../CONNECTIONS|CONNECTIONS]]
