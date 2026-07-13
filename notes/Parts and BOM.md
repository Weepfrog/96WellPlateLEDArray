---
tags: [96-well-led-array, bom]
---

# Parts and BOM

All parts from the JLCPCB/LCSC library, stock checked and **re-verified**
2026-07-13 (see `reference/datasheets/PART_VERIFICATION.json`). Datasheets in
`reference/datasheets/` (named `PART_usage_MFR_C#.pdf`).

Verification notes: C25804 (10k Basic) had zero stock on 2026-07-13 —
fallback C98220 (Yageo, Extended). C9144 is the **right-angle** 2×10 IDC
variant (footprint set accordingly); straight alternatives are low-stock.

## LED board

| Part | Qty | LCSC | Role |
|---|---|---|---|
| Hongli HL-C3535F15R3GA-ZW | 96 (order 110) | C5445086 | 660 nm well emitter |
| Murata NCP18XH103F03RB 0603 | 96 | C13564 | per-well NTC |
| 10k 1% 0603 | 96 | C25804 | NTC divider lower leg |
| CD74HC4067M96 | 6 | C496123 | 16:1 NTC mux (backup: Nexperia C117943) |
| 100nF 0603 | 6 | C14663 | mux decoupling |
| IDC 2×25 box header | 4 | C9044 | channel ribbons (hand-solder) |
| IDC 2×10 box header | 1 | C9144 | logic ribbon (hand-solder) |

## Control board

| Part                    | Qty     | LCSC                 | Role                                  |
| ----------------------- | ------- | -------------------- | ------------------------------------- |
| PT4115 (UMW) SOT-89-5   | 96      | C347356              | per-well buck CC driver               |
| 0.39 Ω 1% 0805          | 96      | C2930218             | sense → 256 mA                        |
| SWPA4030S470MT 47 µH    | 96      | C54731               | channel inductor                      |
| SS34 SMA                | 98      | C8678                | freewheel ×96 + 5V buck + fan flyback |
| 2.2 µF 50 V 0805        | 96      | C125847              | channel VIN cap (Yageo X7R)           |
| 100k 0603               | 97      | C25803               | DIM pulldowns + fan gate pulldown     |
| PCA9685PW               | 6       | C2678753             | 16-ch PWM (addr 0x40-0x45)            |
| 100nF 0603              | 6       | C14663               | PCA decoupling                        |
| XL1509-5.0E1            | 1       | C61063               | 24→5 V logic rail (Basic ✓)           |
| SWPA6045S470MT 47 µH    | 1       | C36414               | 5V buck inductor                      |
| 100 µF 50 V elec        | 1       | C134514              | 5V buck input (Lelon 8×10)            |
| 220 µF 16 V elec        | 1       | C286136              | 5V rail output (Lelon 6.3mm)          |
| 220 µF 35 V elec        | 4       | C134820              | 24 V bulk (Lelon 8×10)                |
| KF301-5.0-2P            | 1       | C474881              | 24 V screw terminal                   |
| DC-005-5A-2.5           | 1       | C381115              | 24 V barrel jack (5 A)                |
| AO3400A                 | 1       | C20917               | fan low-side switch (Basic ✓)         |
| 100R 0603               | 1       | C22775               | fan gate series                       |
| TS-1187A-B-A-B          | 3       | C318884              | MODE/UP/DOWN buttons                  |
| LED 0805 green/blue/red | 1+1+1   | C2297/C2293/C84256   | PWR/STATUS/FAULT (green/red Basic)    |
| 2.2k + 1k 0603          | 1+2     | C4190/C21190         | indicator series R (Basic)            |
| 4.7k 0603               | 2       | C23162               | I2C pullups                           |
| ADS1115IDGSR            | 1 (DNP) | C37593               | optional precision ADC                |
| Pin socket 1×19         | 2       | C319202              | ESP32 DevKitC socket (hand-solder)    |
| Pin header 1×02         | 1       | C2337                | fan connector (1×40 breakaway, snap 2)|
| IDC 2×25 / 2×10         | 4 / 1   | C9044/C9144          | ribbons (hand-solder)                 |

## Off-BOM purchases

- 24 V ≥4 A power brick (5.5×2.5 mm plug or bare leads to screw terminal)
- Finned heatsink ≥ 110×70 mm + **insulating** thermal pad + M3 hardware
- 4× 50-way + 1× 20-way 1.27 mm IDC ribbon cables
- Optional 24 V fan
- ESP32 DevKitC-38 (already owned)

## Cost ballpark

Parts ≈ $75/set · PCBs+assembly ≈ $120-180 (2 assembled sets, SMD single
side, THT self-soldered) · brick/heatsink/ribbons ≈ $50 → **$300-400 total**.

Related: [[Design Decisions]] · [[../CONNECTIONS|CONNECTIONS]]
