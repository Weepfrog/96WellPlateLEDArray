---
tags: [96-well-led-array, reference]
---

# What Every Part Does

Plain-language tour of every component, grouped by job. Quantities are per
board set.

## The light itself (LED board)

- **LED1–LED96 — 660nm LEDs (3535 package).** One per well of the 96-well
  plate. 3W-rated but run at 256mA (~0.5W) for lifetime and thermal headroom.
  Pad 1 = anode, pad 2 = cathode, center pad = heat outlet (tied to cathode).
- **TH1–TH96 — 10k NTC thermistors.** One beside each LED; resistance drops
  as temperature rises. This is the per-well thermometer.
- **R1–R96 (LED board) — 10k 1% resistors.** The bottom half of each NTC's
  voltage divider: 3.3V → NTC → *measure here* → 10k → GND. The midpoint
  voltage encodes the well temperature.
- **U1–U6 — CD74HC4067 analog multiplexers (16:1).** Each connects 16 NTC
  divider midpoints, one at a time, onto a single output wire. Six of them
  turn 96 analog signals into 6 wires + 4 shared address lines.
- **C1–C6 — 100nF decoupling capacitors.** Local energy reservoirs that keep
  each mux's supply steady when it switches.

## Making constant current (control board, ×96 each)

- **U1–U96 — PT4115 buck LED drivers.** The heart of each channel: a tiny
  switching regulator that chops 24V down to whatever its LED needs while
  holding current constant. Has a DIM input for brightness control.
- **R1–R96 — 0.39Ω 1% sense resistors.** The PT4115 measures the voltage
  across this to know the current: 0.1V ÷ 0.39Ω = 256mA. Change this value
  to change LED current.
- **L1–L96 — 47µH inductors.** The energy-storage element of each buck
  converter; smooths the chopped 24V into steady LED current.
- **D1–D96 — SS34 Schottky diodes.** The "freewheel" path: when the PT4115's
  switch opens, inductor current keeps flowing through this diode. Band
  faces +24V.
- **C1–C96 — 2.2µF 50V capacitors.** Per-channel input reservoir so each
  converter's current pulses don't disturb its neighbors.
- **R101–R196 — 100k pulldowns.** Safety: a floating PT4115 DIM pin means
  FULL brightness, so these hold every channel OFF until the ESP32 says
  otherwise. The panel cannot boot bright.

## Brightness control

- **U101–U106 — PCA9685 16-channel PWM chips.** The ESP32 tells them over
  I2C what brightness each channel should be; they generate 96 independent
  PWM signals (~244Hz, ~10-11 usable bits) into the PT4115 DIM pins.
  One chip = one 16-channel bank = one ribbon cable.
- **C121–C126 — 100nF decoupling** for each PCA9685.
- **R210, R211 — 4.7k I2C pullups.** I2C lines idle high; these provide the
  pull. One pair serves the whole bus.

## Power conversion

- **J12 (screw terminal) / J7 (barrel jack) — 24V input.** Two options for
  the same input; use either.
- **C101–C104 — 220µF bulk electrolytics.** Big reservoirs on the 24V rail:
  two at the input, two near the fan/load side.
- **U110 — XL1509-5.0 buck regulator.** Makes the 5V logic rail from 24V.
- **L101 (47µH), D101 (SS34), C110 (100µF in), C111 (220µF out)** — the
  XL1509's supporting cast: same buck-converter roles as in the LED channels.
- The ESP32 dev board's own regulator then makes 3.3V from the 5V rail for
  all logic.

## Brains and interface

- **J10, J11 — 1×19 socket headers.** The ESP32 DevKitC-38 plugs in here;
  socketed so you can pull it for programming or replacement.
- **U111 — ADS1115 16-bit ADC (not fitted by default).** Insurance: if the
  ESP32's built-in ADC proves too noisy for the NTC readings, solder this in
  and read temperatures over I2C instead.
- **SW1–SW3 — tactile buttons (MODE / UP / DOWN).** Front-panel control
  without a computer.
- **LED1–LED3 (control board) — indicator LEDs.** Green = 5V power present
  (hardwired), blue = status heartbeat, red = fault latch. **R203–R205** set
  their brightness.
- **Q1 — AO3400 MOSFET.** Low-side switch so the ESP32 can PWM a 24V fan.
  **R201** (100Ω) tames its gate; **R202** (100k) keeps it off at boot;
  **D102** (SS34) absorbs the fan motor's inductive kick. **J8** is the fan
  plug.

## Connecting the two boards

- **J1–J6 (both boards) — 40-pin IDC ribbon headers.** Each carries one
  PCA9685 bank: 16 channels × (anode + cathode) on pins 1-18 and 21-34.
  Pin 20 is deliberately unused so keyed IDE cables work; pin 19 and 35-40
  are grounds. Cheap 40-pin ribbon cables connect them 1:1.
- **J9 (both boards) — 20-pin IDC logic ribbon.** Carries 3.3V, the six mux
  outputs, the four mux address lines, and grounds between boards.
- **TP1–TP12 — test points.** Bare pads for probing rails and one full
  debug channel (DIM1/LED_A1/LED_K1) during bring-up.
- **H1–H5 — M3 mounting holes.** Standoffs; the two boards share the same
  hole spacing so the sandwich bolts together.

## Copper that acts like a component

- **Thermal via farms (5 per LED)** — copper tubes carrying heat from each
  LED's pad through the board to the back face.
- **Cathode islands (96, back of LED board)** — heat-spreading pads under
  each LED, pressed against the heatsink through an insulating pad.
- **Inner planes** — solid GND and +24V sheets inside both boards: quiet
  return paths for 96 switching converters and effortless power delivery.

Related: [[Parts and BOM]] (part numbers & prices) · [[Architecture]] ·
[[../CONNECTIONS|CONNECTIONS]]
