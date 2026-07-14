# CONNECTIONS.md — complete wiring reference

Generated from `scripts/design_data.py`. The hierarchical schematics are **already wired to match this document** (verified: KiCad's exported netlist matches every net below exactly, ERC clean). Use this as the review checklist and as the reference during PCB routing, firmware bring-up, and debugging.

**Channel numbering:** `n = (row-1)*12 + col`, rows top→bottom 1-8, columns left→right 1-12 looking at the LED side. CH1 = top-left well, CH96 = bottom-right.

## ESP32 DevKitC-38 socket map (control board J10/J11)

J10 = left socket row, J11 = right socket row, **pin 1 of both = the 3V3/GND end** (opposite the USB connector).

| J10 pin | DevKit pin | Connect to | | J11 pin | DevKit pin | Connect to |
|---|---|---|---|---|---|---|
| 1 | 3V3 | +3.3V | | 1 | GND | GND |
| 2 | EN | — | | 2 | GPIO23 | — |
| 3 | GPIO36/VP | NTC_SIG5 | | 3 | GPIO22 | I2C_SCL |
| 4 | GPIO39/VN | NTC_SIG6 | | 4 | GPIO1/TX0 | — |
| 5 | GPIO34 | NTC_SIG3 | | 5 | GPIO3/RX0 | — |
| 6 | GPIO35 | NTC_SIG4 | | 6 | GPIO21 | I2C_SDA |
| 7 | GPIO32 | NTC_SIG1 | | 7 | GND | GND |
| 8 | GPIO33 | NTC_SIG2 | | 8 | GPIO19 | MUX_A3 |
| 9 | GPIO25 | FAN_PWM | | 9 | GPIO18 | MUX_A2 |
| 10 | GPIO26 | BTN_DOWN | | 10 | GPIO5 | — |
| 11 | GPIO27 | BTN_UP | | 11 | GPIO17 | MUX_A1 |
| 12 | GPIO14 | BTN_MODE | | 12 | GPIO16 | MUX_A0 |
| 13 | GPIO12 | — | | 13 | GPIO4 | LED_STATUS |
| 14 | GND | GND | | 14 | GPIO0 | — |
| 15 | GPIO13 | LED_FAULT | | 15 | GPIO2 | — |
| 16 | GPIO9/D2 | — | | 16 | GPIO15 | — |
| 17 | GPIO10/D3 | — | | 17 | GPIO8/D1 | — |
| 18 | GPIO11/CMD | — | | 18 | GPIO7/D0 | — |
| 19 | 5V | +5V | | 19 | GPIO6/CLK | — |

GPIO summary: **GPIO21** = I2C SDA (PCA9685 x6, ADS1115 opt.); **GPIO22** = I2C SCL; **GPIO16** = MUX_A0; **GPIO17** = MUX_A1; **GPIO18** = MUX_A2; **GPIO19** = MUX_A3; **GPIO32** = NTC_SIG1 (ADC1_CH4); **GPIO33** = NTC_SIG2 (ADC1_CH5); **GPIO34** = NTC_SIG3 (ADC1_CH6); **GPIO35** = NTC_SIG4 (ADC1_CH7); **GPIO36/VP** = NTC_SIG5 (ADC1_CH0); **GPIO39/VN** = NTC_SIG6 (ADC1_CH3); **GPIO25** = FAN_PWM (Q1 gate via R201); **GPIO4** = STATUS LED2 (blue); **GPIO13** = FAULT LED3 (red); **GPIO14** = SW1 MODE (to GND, internal pull-up); **GPIO27** = SW2 UP (to GND, internal pull-up); **GPIO26** = SW3 DOWN (to GND, internal pull-up)

## Control board — driver channel (repeat for n = 1…96)

```
+24V ──┬── R<n>.1   R<n> = 0.39Ω sense
       │   R<n>.2 ──●── U<n>.4 (CSN) ── LED_A<n> ── ribbon pin (see table)
       ├── C<n>.1   (2.2µF 50V; C<n>.2 → GND)
       ├── D<n>.1   (SS34 cathode/band side!)
       └── U<n>.5 (VIN)
U<n>.1 (SW) ──●── L<n>.1        L<n> = 47µH
              └── D<n>.2 (SS34 anode)
L<n>.2 ── LED_K<n> ── ribbon pin (see table)
U<n>.3 (DIM) ──●── R<10x>.1 (100k pulldown; .2 → GND)
               └── PCA9685 output (see table)
U<n>.2 (GND) → GND
```

| CH | PT4115 | Rs | L | D | Cin | pulldown | ribbon A / K | DIM source |
|---|---|---|---|---|---|---|---|---|
| 1 | U1 | R1 | L1 | D1 | C1 | R101 | J1.1 / J1.2 | U101.6 (LED0) |
| 2 | U2 | R2 | L2 | D2 | C2 | R102 | J1.3 / J1.4 | U101.7 (LED1) |
| 3 | U3 | R3 | L3 | D3 | C3 | R103 | J1.5 / J1.6 | U101.8 (LED2) |
| 4 | U4 | R4 | L4 | D4 | C4 | R104 | J1.7 / J1.8 | U101.9 (LED3) |
| 5 | U5 | R5 | L5 | D5 | C5 | R105 | J1.9 / J1.10 | U101.10 (LED4) |
| 6 | U6 | R6 | L6 | D6 | C6 | R106 | J1.13 / J1.14 | U101.11 (LED5) |
| 7 | U7 | R7 | L7 | D7 | C7 | R107 | J1.15 / J1.16 | U101.12 (LED6) |
| 8 | U8 | R8 | L8 | D8 | C8 | R108 | J1.21 / J1.22 | U101.13 (LED7) |
| 9 | U9 | R9 | L9 | D9 | C9 | R109 | J1.25 / J1.26 | U101.15 (LED8) |
| 10 | U10 | R10 | L10 | D10 | C10 | R110 | J1.27 / J1.28 | U101.16 (LED9) |
| 11 | U11 | R11 | L11 | D11 | C11 | R111 | J1.31 / J1.32 | U101.17 (LED10) |
| 12 | U12 | R12 | L12 | D12 | C12 | R112 | J1.33 / J1.34 | U101.18 (LED11) |
| 13 | U13 | R13 | L13 | D13 | C13 | R113 | J1.11 / J1.12 | U101.19 (LED12) |
| 14 | U14 | R14 | L14 | D14 | C14 | R114 | J1.17 / J1.18 | U101.20 (LED13) |
| 15 | U15 | R15 | L15 | D15 | C15 | R115 | J1.23 / J1.24 | U101.21 (LED14) |
| 16 | U16 | R16 | L16 | D16 | C16 | R116 | J1.29 / J1.30 | U101.22 (LED15) |
| 17 | U17 | R17 | L17 | D17 | C17 | R117 | J2.33 / J2.34 | U102.6 (LED0) |
| 18 | U18 | R18 | L18 | D18 | C18 | R118 | J2.31 / J2.32 | U102.7 (LED1) |
| 19 | U19 | R19 | L19 | D19 | C19 | R119 | J2.29 / J2.30 | U102.8 (LED2) |
| 20 | U20 | R20 | L20 | D20 | C20 | R120 | J2.27 / J2.28 | U102.9 (LED3) |
| 21 | U21 | R21 | L21 | D21 | C21 | R121 | J2.25 / J2.26 | U102.10 (LED4) |
| 22 | U22 | R22 | L22 | D22 | C22 | R122 | J2.23 / J2.24 | U102.11 (LED5) |
| 23 | U23 | R23 | L23 | D23 | C23 | R123 | J2.21 / J2.22 | U102.12 (LED6) |
| 24 | U24 | R24 | L24 | D24 | C24 | R124 | J2.17 / J2.18 | U102.13 (LED7) |
| 25 | U25 | R25 | L25 | D25 | C25 | R125 | J2.15 / J2.16 | U102.15 (LED8) |
| 26 | U26 | R26 | L26 | D26 | C26 | R126 | J2.13 / J2.14 | U102.16 (LED9) |
| 27 | U27 | R27 | L27 | D27 | C27 | R127 | J2.11 / J2.12 | U102.17 (LED10) |
| 28 | U28 | R28 | L28 | D28 | C28 | R128 | J2.9 / J2.10 | U102.18 (LED11) |
| 29 | U29 | R29 | L29 | D29 | C29 | R129 | J2.7 / J2.8 | U102.19 (LED12) |
| 30 | U30 | R30 | L30 | D30 | C30 | R130 | J2.5 / J2.6 | U102.20 (LED13) |
| 31 | U31 | R31 | L31 | D31 | C31 | R131 | J2.3 / J2.4 | U102.21 (LED14) |
| 32 | U32 | R32 | L32 | D32 | C32 | R132 | J2.1 / J2.2 | U102.22 (LED15) |
| 33 | U33 | R33 | L33 | D33 | C33 | R133 | J3.33 / J3.34 | U103.6 (LED0) |
| 34 | U34 | R34 | L34 | D34 | C34 | R134 | J3.31 / J3.32 | U103.7 (LED1) |
| 35 | U35 | R35 | L35 | D35 | C35 | R135 | J3.29 / J3.30 | U103.8 (LED2) |
| 36 | U36 | R36 | L36 | D36 | C36 | R136 | J3.27 / J3.28 | U103.9 (LED3) |
| 37 | U37 | R37 | L37 | D37 | C37 | R137 | J3.25 / J3.26 | U103.10 (LED4) |
| 38 | U38 | R38 | L38 | D38 | C38 | R138 | J3.23 / J3.24 | U103.11 (LED5) |
| 39 | U39 | R39 | L39 | D39 | C39 | R139 | J3.21 / J3.22 | U103.12 (LED6) |
| 40 | U40 | R40 | L40 | D40 | C40 | R140 | J3.17 / J3.18 | U103.13 (LED7) |
| 41 | U41 | R41 | L41 | D41 | C41 | R141 | J3.15 / J3.16 | U103.15 (LED8) |
| 42 | U42 | R42 | L42 | D42 | C42 | R142 | J3.13 / J3.14 | U103.16 (LED9) |
| 43 | U43 | R43 | L43 | D43 | C43 | R143 | J3.11 / J3.12 | U103.17 (LED10) |
| 44 | U44 | R44 | L44 | D44 | C44 | R144 | J3.9 / J3.10 | U103.18 (LED11) |
| 45 | U45 | R45 | L45 | D45 | C45 | R145 | J3.7 / J3.8 | U103.19 (LED12) |
| 46 | U46 | R46 | L46 | D46 | C46 | R146 | J3.5 / J3.6 | U103.20 (LED13) |
| 47 | U47 | R47 | L47 | D47 | C47 | R147 | J3.3 / J3.4 | U103.21 (LED14) |
| 48 | U48 | R48 | L48 | D48 | C48 | R148 | J3.1 / J3.2 | U103.22 (LED15) |
| 49 | U49 | R49 | L49 | D49 | C49 | R149 | J4.1 / J4.2 | U104.6 (LED0) |
| 50 | U50 | R50 | L50 | D50 | C50 | R150 | J4.3 / J4.4 | U104.7 (LED1) |
| 51 | U51 | R51 | L51 | D51 | C51 | R151 | J4.5 / J4.6 | U104.8 (LED2) |
| 52 | U52 | R52 | L52 | D52 | C52 | R152 | J4.7 / J4.8 | U104.9 (LED3) |
| 53 | U53 | R53 | L53 | D53 | C53 | R153 | J4.9 / J4.10 | U104.10 (LED4) |
| 54 | U54 | R54 | L54 | D54 | C54 | R154 | J4.13 / J4.14 | U104.11 (LED5) |
| 55 | U55 | R55 | L55 | D55 | C55 | R155 | J4.15 / J4.16 | U104.12 (LED6) |
| 56 | U56 | R56 | L56 | D56 | C56 | R156 | J4.21 / J4.22 | U104.13 (LED7) |
| 57 | U57 | R57 | L57 | D57 | C57 | R157 | J4.25 / J4.26 | U104.15 (LED8) |
| 58 | U58 | R58 | L58 | D58 | C58 | R158 | J4.27 / J4.28 | U104.16 (LED9) |
| 59 | U59 | R59 | L59 | D59 | C59 | R159 | J4.31 / J4.32 | U104.17 (LED10) |
| 60 | U60 | R60 | L60 | D60 | C60 | R160 | J4.33 / J4.34 | U104.18 (LED11) |
| 61 | U61 | R61 | L61 | D61 | C61 | R161 | J4.11 / J4.12 | U104.19 (LED12) |
| 62 | U62 | R62 | L62 | D62 | C62 | R162 | J4.17 / J4.18 | U104.20 (LED13) |
| 63 | U63 | R63 | L63 | D63 | C63 | R163 | J4.23 / J4.24 | U104.21 (LED14) |
| 64 | U64 | R64 | L64 | D64 | C64 | R164 | J4.29 / J4.30 | U104.22 (LED15) |
| 65 | U65 | R65 | L65 | D65 | C65 | R165 | J5.33 / J5.34 | U105.6 (LED0) |
| 66 | U66 | R66 | L66 | D66 | C66 | R166 | J5.31 / J5.32 | U105.7 (LED1) |
| 67 | U67 | R67 | L67 | D67 | C67 | R167 | J5.29 / J5.30 | U105.8 (LED2) |
| 68 | U68 | R68 | L68 | D68 | C68 | R168 | J5.27 / J5.28 | U105.9 (LED3) |
| 69 | U69 | R69 | L69 | D69 | C69 | R169 | J5.25 / J5.26 | U105.10 (LED4) |
| 70 | U70 | R70 | L70 | D70 | C70 | R170 | J5.23 / J5.24 | U105.11 (LED5) |
| 71 | U71 | R71 | L71 | D71 | C71 | R171 | J5.21 / J5.22 | U105.12 (LED6) |
| 72 | U72 | R72 | L72 | D72 | C72 | R172 | J5.17 / J5.18 | U105.13 (LED7) |
| 73 | U73 | R73 | L73 | D73 | C73 | R173 | J5.15 / J5.16 | U105.15 (LED8) |
| 74 | U74 | R74 | L74 | D74 | C74 | R174 | J5.13 / J5.14 | U105.16 (LED9) |
| 75 | U75 | R75 | L75 | D75 | C75 | R175 | J5.11 / J5.12 | U105.17 (LED10) |
| 76 | U76 | R76 | L76 | D76 | C76 | R176 | J5.9 / J5.10 | U105.18 (LED11) |
| 77 | U77 | R77 | L77 | D77 | C77 | R177 | J5.7 / J5.8 | U105.19 (LED12) |
| 78 | U78 | R78 | L78 | D78 | C78 | R178 | J5.5 / J5.6 | U105.20 (LED13) |
| 79 | U79 | R79 | L79 | D79 | C79 | R179 | J5.3 / J5.4 | U105.21 (LED14) |
| 80 | U80 | R80 | L80 | D80 | C80 | R180 | J5.1 / J5.2 | U105.22 (LED15) |
| 81 | U81 | R81 | L81 | D81 | C81 | R181 | J6.33 / J6.34 | U106.6 (LED0) |
| 82 | U82 | R82 | L82 | D82 | C82 | R182 | J6.31 / J6.32 | U106.7 (LED1) |
| 83 | U83 | R83 | L83 | D83 | C83 | R183 | J6.29 / J6.30 | U106.8 (LED2) |
| 84 | U84 | R84 | L84 | D84 | C84 | R184 | J6.27 / J6.28 | U106.9 (LED3) |
| 85 | U85 | R85 | L85 | D85 | C85 | R185 | J6.25 / J6.26 | U106.10 (LED4) |
| 86 | U86 | R86 | L86 | D86 | C86 | R186 | J6.23 / J6.24 | U106.11 (LED5) |
| 87 | U87 | R87 | L87 | D87 | C87 | R187 | J6.21 / J6.22 | U106.12 (LED6) |
| 88 | U88 | R88 | L88 | D88 | C88 | R188 | J6.17 / J6.18 | U106.13 (LED7) |
| 89 | U89 | R89 | L89 | D89 | C89 | R189 | J6.15 / J6.16 | U106.15 (LED8) |
| 90 | U90 | R90 | L90 | D90 | C90 | R190 | J6.13 / J6.14 | U106.16 (LED9) |
| 91 | U91 | R91 | L91 | D91 | C91 | R191 | J6.11 / J6.12 | U106.17 (LED10) |
| 92 | U92 | R92 | L92 | D92 | C92 | R192 | J6.9 / J6.10 | U106.18 (LED11) |
| 93 | U93 | R93 | L93 | D93 | C93 | R193 | J6.7 / J6.8 | U106.19 (LED12) |
| 94 | U94 | R94 | L94 | D94 | C94 | R194 | J6.5 / J6.6 | U106.20 (LED13) |
| 95 | U95 | R95 | L95 | D95 | C95 | R195 | J6.3 / J6.4 | U106.21 (LED14) |
| 96 | U96 | R96 | L96 | D96 | C96 | R196 | J6.1 / J6.2 | U106.22 (LED15) |

## PCA9685 bank (control board)

All six: pin 28 (VDD) → +3.3V with 100nF (C121-C126), pin 14 (VSS) → GND, pin 23 (/OE) → GND, pin 25 (EXTCLK) → GND, pin 27 (SDA) → I2C_SDA, pin 26 (SCL) → I2C_SCL.
I2C_SDA/I2C_SCL → ESP32 GPIO21/GPIO22 + 4.7k pullups R210/R211 to +3.3V.

Address straps (pin → rail):

| Chip | Addr | A0(1) | A1(2) | A2(3) | A3(4) | A4(5) | A5(24) |
|---|---|---|---|---|---|---|---|
| U101 | 0x40 | GND | GND | GND | GND | GND | GND |
| U102 | 0x41 | +3.3V | GND | GND | GND | GND | GND |
| U103 | 0x42 | GND | +3.3V | GND | GND | GND | GND |
| U104 | 0x43 | +3.3V | +3.3V | GND | GND | GND | GND |
| U105 | 0x44 | GND | GND | +3.3V | GND | GND | GND |
| U106 | 0x45 | +3.3V | GND | +3.3V | GND | GND | GND |

## 5V rail (control board)

- **+24V**: R1.1, C1.1, D1.1 (K), U1.5 (VIN), R2.1, C2.1, D2.1 (K), U2.5 (VIN), R3.1, C3.1, D3.1 (K), U3.5 (VIN), R4.1, C4.1, D4.1 (K), U4.5 (VIN), R5.1, C5.1, D5.1 (K), U5.5 (VIN), R6.1, C6.1, D6.1 (K), U6.5 (VIN), R7.1, C7.1, D7.1 (K), U7.5 (VIN), R8.1, C8.1, D8.1 (K), U8.5 (VIN), R9.1, C9.1, D9.1 (K), U9.5 (VIN), R10.1, C10.1, D10.1 (K), U10.5 (VIN), R11.1, C11.1, D11.1 (K), U11.5 (VIN), R12.1, C12.1, D12.1 (K), U12.5 (VIN), R13.1, C13.1, D13.1 (K), U13.5 (VIN), R14.1, C14.1, D14.1 (K), U14.5 (VIN), R15.1, C15.1, D15.1 (K), U15.5 (VIN), R16.1, C16.1, D16.1 (K), U16.5 (VIN), R17.1, C17.1, D17.1 (K), U17.5 (VIN), R18.1, C18.1, D18.1 (K), U18.5 (VIN), R19.1, C19.1, D19.1 (K), U19.5 (VIN), R20.1, C20.1, D20.1 (K), U20.5 (VIN), R21.1, C21.1, D21.1 (K), U21.5 (VIN), R22.1, C22.1, D22.1 (K), U22.5 (VIN), R23.1, C23.1, D23.1 (K), U23.5 (VIN), R24.1, C24.1, D24.1 (K), U24.5 (VIN), R25.1, C25.1, D25.1 (K), U25.5 (VIN), R26.1, C26.1, D26.1 (K), U26.5 (VIN), R27.1, C27.1, D27.1 (K), U27.5 (VIN), R28.1, C28.1, D28.1 (K), U28.5 (VIN), R29.1, C29.1, D29.1 (K), U29.5 (VIN), R30.1, C30.1, D30.1 (K), U30.5 (VIN), R31.1, C31.1, D31.1 (K), U31.5 (VIN), R32.1, C32.1, D32.1 (K), U32.5 (VIN), R33.1, C33.1, D33.1 (K), U33.5 (VIN), R34.1, C34.1, D34.1 (K), U34.5 (VIN), R35.1, C35.1, D35.1 (K), U35.5 (VIN), R36.1, C36.1, D36.1 (K), U36.5 (VIN), R37.1, C37.1, D37.1 (K), U37.5 (VIN), R38.1, C38.1, D38.1 (K), U38.5 (VIN), R39.1, C39.1, D39.1 (K), U39.5 (VIN), R40.1, C40.1, D40.1 (K), U40.5 (VIN), R41.1, C41.1, D41.1 (K), U41.5 (VIN), R42.1, C42.1, D42.1 (K), U42.5 (VIN), R43.1, C43.1, D43.1 (K), U43.5 (VIN), R44.1, C44.1, D44.1 (K), U44.5 (VIN), R45.1, C45.1, D45.1 (K), U45.5 (VIN), R46.1, C46.1, D46.1 (K), U46.5 (VIN), R47.1, C47.1, D47.1 (K), U47.5 (VIN), R48.1, C48.1, D48.1 (K), U48.5 (VIN), R49.1, C49.1, D49.1 (K), U49.5 (VIN), R50.1, C50.1, D50.1 (K), U50.5 (VIN), R51.1, C51.1, D51.1 (K), U51.5 (VIN), R52.1, C52.1, D52.1 (K), U52.5 (VIN), R53.1, C53.1, D53.1 (K), U53.5 (VIN), R54.1, C54.1, D54.1 (K), U54.5 (VIN), R55.1, C55.1, D55.1 (K), U55.5 (VIN), R56.1, C56.1, D56.1 (K), U56.5 (VIN), R57.1, C57.1, D57.1 (K), U57.5 (VIN), R58.1, C58.1, D58.1 (K), U58.5 (VIN), R59.1, C59.1, D59.1 (K), U59.5 (VIN), R60.1, C60.1, D60.1 (K), U60.5 (VIN), R61.1, C61.1, D61.1 (K), U61.5 (VIN), R62.1, C62.1, D62.1 (K), U62.5 (VIN), R63.1, C63.1, D63.1 (K), U63.5 (VIN), R64.1, C64.1, D64.1 (K), U64.5 (VIN), R65.1, C65.1, D65.1 (K), U65.5 (VIN), R66.1, C66.1, D66.1 (K), U66.5 (VIN), R67.1, C67.1, D67.1 (K), U67.5 (VIN), R68.1, C68.1, D68.1 (K), U68.5 (VIN), R69.1, C69.1, D69.1 (K), U69.5 (VIN), R70.1, C70.1, D70.1 (K), U70.5 (VIN), R71.1, C71.1, D71.1 (K), U71.5 (VIN), R72.1, C72.1, D72.1 (K), U72.5 (VIN), R73.1, C73.1, D73.1 (K), U73.5 (VIN), R74.1, C74.1, D74.1 (K), U74.5 (VIN), R75.1, C75.1, D75.1 (K), U75.5 (VIN), R76.1, C76.1, D76.1 (K), U76.5 (VIN), R77.1, C77.1, D77.1 (K), U77.5 (VIN), R78.1, C78.1, D78.1 (K), U78.5 (VIN), R79.1, C79.1, D79.1 (K), U79.5 (VIN), R80.1, C80.1, D80.1 (K), U80.5 (VIN), R81.1, C81.1, D81.1 (K), U81.5 (VIN), R82.1, C82.1, D82.1 (K), U82.5 (VIN), R83.1, C83.1, D83.1 (K), U83.5 (VIN), R84.1, C84.1, D84.1 (K), U84.5 (VIN), R85.1, C85.1, D85.1 (K), U85.5 (VIN), R86.1, C86.1, D86.1 (K), U86.5 (VIN), R87.1, C87.1, D87.1 (K), U87.5 (VIN), R88.1, C88.1, D88.1 (K), U88.5 (VIN), R89.1, C89.1, D89.1 (K), U89.5 (VIN), R90.1, C90.1, D90.1 (K), U90.5 (VIN), R91.1, C91.1, D91.1 (K), U91.5 (VIN), R92.1, C92.1, D92.1 (K), U92.5 (VIN), R93.1, C93.1, D93.1 (K), U93.5 (VIN), R94.1, C94.1, D94.1 (K), U94.5 (VIN), R95.1, C95.1, D95.1 (K), U95.5 (VIN), R96.1, C96.1, D96.1 (K), U96.5 (VIN), U110.1 (VIN), C110.1, C101.1, C102.1, C103.1, C104.1, J12.1 (Pin_1), J7.1, J8.1 (Pin_1), D102.1 (K), TP1.1
- **SW_5V**: U110.2 (OUT), L101.1, D101.1 (K), TP6.1
- **+5V**: L101.2, C111.1, U110.3 (FB), J10.19 (Pin_19), R203.1, TP2.1

## Fan output (control board)

- **FAN_PWM**: R201.1, J10.9 (Pin_9)
- **FAN_G**: Q1.1 (G), R201.2, R202.1
- **FAN_SW**: J8.2 (Pin_2), Q1.3 (D), D102.2 (A), TP9.1

## UI buttons + status LEDs (control board)

- **BTN_MODE**: J10.12 (Pin_12), SW1.1 (A), SW1.2 (B)
- **BTN_UP**: J10.11 (Pin_11), SW2.1 (A), SW2.2 (B)
- **BTN_DOWN**: J10.10 (Pin_10), SW3.1 (A), SW3.2 (B)
- **LED_STATUS**: J11.13 (Pin_13), R204.1
- **LED_FAULT**: J10.15 (Pin_15), R205.1
- **LED1_A**: R203.2, LED1.2 (A)
- **LED2_A**: R204.2, LED2.2 (A)
- **LED3_A**: R205.2, LED3.2 (A)

## I2C (control board)

- **I2C_SDA**: U101.27 (SDA), U102.27 (SDA), U103.27 (SDA), U104.27 (SDA), U105.27 (SDA), U106.27 (SDA), J11.6 (Pin_6), R210.1, U111.10 (SCL), TP7.1
- **I2C_SCL**: U101.26 (SCL), U102.26 (SCL), U103.26 (SCL), U104.26 (SCL), U105.26 (SCL), U106.26 (SCL), J11.3 (Pin_3), R211.1, U111.9 (SDA), TP8.1

Note: +24V and GND on the control board also touch every channel (see channel section) — the lists above omit per-channel members for readability. Full GND membership: every U<n>.2, C<n>.2, R<10x>.2, plus the parts listed here.

## LED board — per-well cluster (repeat for n = 1…96)

```
ribbon A pin ── LED_A<n> ── LED<n>.1 (anode, '+' silk mark)
LED<n>.2 (cathode) ──●── LED<n>.3 (thermal pad — tie to cathode)
                     └── LED_K<n> ── ribbon K pin
+3.3V ── TH<n>.1   TH<n> = 10k NTC
TH<n>.2 ──●── R<n>.1 (10k 1%; R<n>.2 → GND)
          └── NTC<n> ── mux input (see table)
```

| CH | LED | NTC | divider R | ribbon A / K | mux input |
|---|---|---|---|---|---|
| 1 | LED1 | TH1 | R1 | J1.1 / J1.2 | U1.23 (I8) |
| 2 | LED2 | TH2 | R2 | J1.3 / J1.4 | U1.2 (I7) |
| 3 | LED3 | TH3 | R3 | J1.5 / J1.6 | U2.23 (I8) |
| 4 | LED4 | TH4 | R4 | J1.7 / J1.8 | U2.2 (I7) |
| 5 | LED5 | TH5 | R5 | J1.9 / J1.10 | U3.23 (I8) |
| 6 | LED6 | TH6 | R6 | J1.13 / J1.14 | U3.2 (I7) |
| 7 | LED7 | TH7 | R7 | J1.15 / J1.16 | U4.9 (I0) |
| 8 | LED8 | TH8 | R8 | J1.21 / J1.22 | U4.16 (I15) |
| 9 | LED9 | TH9 | R9 | J1.25 / J1.26 | U5.16 (I15) |
| 10 | LED10 | TH10 | R10 | J1.27 / J1.28 | U5.9 (I0) |
| 11 | LED11 | TH11 | R11 | J1.31 / J1.32 | U6.16 (I15) |
| 12 | LED12 | TH12 | R12 | J1.33 / J1.34 | U6.9 (I0) |
| 13 | LED13 | TH13 | R13 | J1.11 / J1.12 | U1.22 (I9) |
| 14 | LED14 | TH14 | R14 | J1.17 / J1.18 | U1.3 (I6) |
| 15 | LED15 | TH15 | R15 | J1.23 / J1.24 | U2.22 (I9) |
| 16 | LED16 | TH16 | R16 | J1.29 / J1.30 | U2.3 (I6) |
| 17 | LED17 | TH17 | R17 | J2.33 / J2.34 | U3.22 (I9) |
| 18 | LED18 | TH18 | R18 | J2.31 / J2.32 | U3.3 (I6) |
| 19 | LED19 | TH19 | R19 | J2.29 / J2.30 | U4.8 (I1) |
| 20 | LED20 | TH20 | R20 | J2.27 / J2.28 | U4.17 (I14) |
| 21 | LED21 | TH21 | R21 | J2.25 / J2.26 | U5.17 (I14) |
| 22 | LED22 | TH22 | R22 | J2.23 / J2.24 | U5.8 (I1) |
| 23 | LED23 | TH23 | R23 | J2.21 / J2.22 | U6.17 (I14) |
| 24 | LED24 | TH24 | R24 | J2.17 / J2.18 | U6.8 (I1) |
| 25 | LED25 | TH25 | R25 | J2.15 / J2.16 | U1.21 (I10) |
| 26 | LED26 | TH26 | R26 | J2.13 / J2.14 | U1.4 (I5) |
| 27 | LED27 | TH27 | R27 | J2.11 / J2.12 | U2.21 (I10) |
| 28 | LED28 | TH28 | R28 | J2.9 / J2.10 | U2.4 (I5) |
| 29 | LED29 | TH29 | R29 | J2.7 / J2.8 | U3.21 (I10) |
| 30 | LED30 | TH30 | R30 | J2.5 / J2.6 | U3.4 (I5) |
| 31 | LED31 | TH31 | R31 | J2.3 / J2.4 | U4.7 (I2) |
| 32 | LED32 | TH32 | R32 | J2.1 / J2.2 | U4.18 (I13) |
| 33 | LED33 | TH33 | R33 | J3.33 / J3.34 | U5.18 (I13) |
| 34 | LED34 | TH34 | R34 | J3.31 / J3.32 | U5.7 (I2) |
| 35 | LED35 | TH35 | R35 | J3.29 / J3.30 | U6.18 (I13) |
| 36 | LED36 | TH36 | R36 | J3.27 / J3.28 | U6.7 (I2) |
| 37 | LED37 | TH37 | R37 | J3.25 / J3.26 | U1.20 (I11) |
| 38 | LED38 | TH38 | R38 | J3.23 / J3.24 | U1.5 (I4) |
| 39 | LED39 | TH39 | R39 | J3.21 / J3.22 | U2.20 (I11) |
| 40 | LED40 | TH40 | R40 | J3.17 / J3.18 | U2.5 (I4) |
| 41 | LED41 | TH41 | R41 | J3.15 / J3.16 | U3.20 (I11) |
| 42 | LED42 | TH42 | R42 | J3.13 / J3.14 | U3.5 (I4) |
| 43 | LED43 | TH43 | R43 | J3.11 / J3.12 | U4.6 (I3) |
| 44 | LED44 | TH44 | R44 | J3.9 / J3.10 | U4.19 (I12) |
| 45 | LED45 | TH45 | R45 | J3.7 / J3.8 | U5.19 (I12) |
| 46 | LED46 | TH46 | R46 | J3.5 / J3.6 | U5.6 (I3) |
| 47 | LED47 | TH47 | R47 | J3.3 / J3.4 | U6.19 (I12) |
| 48 | LED48 | TH48 | R48 | J3.1 / J3.2 | U6.6 (I3) |
| 49 | LED49 | TH49 | R49 | J4.1 / J4.2 | U1.19 (I12) |
| 50 | LED50 | TH50 | R50 | J4.3 / J4.4 | U1.6 (I3) |
| 51 | LED51 | TH51 | R51 | J4.5 / J4.6 | U2.19 (I12) |
| 52 | LED52 | TH52 | R52 | J4.7 / J4.8 | U2.6 (I3) |
| 53 | LED53 | TH53 | R53 | J4.9 / J4.10 | U3.19 (I12) |
| 54 | LED54 | TH54 | R54 | J4.13 / J4.14 | U3.6 (I3) |
| 55 | LED55 | TH55 | R55 | J4.15 / J4.16 | U4.5 (I4) |
| 56 | LED56 | TH56 | R56 | J4.21 / J4.22 | U4.20 (I11) |
| 57 | LED57 | TH57 | R57 | J4.25 / J4.26 | U5.20 (I11) |
| 58 | LED58 | TH58 | R58 | J4.27 / J4.28 | U5.5 (I4) |
| 59 | LED59 | TH59 | R59 | J4.31 / J4.32 | U6.20 (I11) |
| 60 | LED60 | TH60 | R60 | J4.33 / J4.34 | U6.5 (I4) |
| 61 | LED61 | TH61 | R61 | J4.11 / J4.12 | U1.18 (I13) |
| 62 | LED62 | TH62 | R62 | J4.17 / J4.18 | U1.7 (I2) |
| 63 | LED63 | TH63 | R63 | J4.23 / J4.24 | U2.18 (I13) |
| 64 | LED64 | TH64 | R64 | J4.29 / J4.30 | U2.7 (I2) |
| 65 | LED65 | TH65 | R65 | J5.33 / J5.34 | U3.18 (I13) |
| 66 | LED66 | TH66 | R66 | J5.31 / J5.32 | U3.7 (I2) |
| 67 | LED67 | TH67 | R67 | J5.29 / J5.30 | U4.4 (I5) |
| 68 | LED68 | TH68 | R68 | J5.27 / J5.28 | U4.21 (I10) |
| 69 | LED69 | TH69 | R69 | J5.25 / J5.26 | U5.21 (I10) |
| 70 | LED70 | TH70 | R70 | J5.23 / J5.24 | U5.4 (I5) |
| 71 | LED71 | TH71 | R71 | J5.21 / J5.22 | U6.21 (I10) |
| 72 | LED72 | TH72 | R72 | J5.17 / J5.18 | U6.4 (I5) |
| 73 | LED73 | TH73 | R73 | J5.15 / J5.16 | U1.17 (I14) |
| 74 | LED74 | TH74 | R74 | J5.13 / J5.14 | U1.8 (I1) |
| 75 | LED75 | TH75 | R75 | J5.11 / J5.12 | U2.17 (I14) |
| 76 | LED76 | TH76 | R76 | J5.9 / J5.10 | U2.8 (I1) |
| 77 | LED77 | TH77 | R77 | J5.7 / J5.8 | U3.17 (I14) |
| 78 | LED78 | TH78 | R78 | J5.5 / J5.6 | U3.8 (I1) |
| 79 | LED79 | TH79 | R79 | J5.3 / J5.4 | U4.3 (I6) |
| 80 | LED80 | TH80 | R80 | J5.1 / J5.2 | U4.22 (I9) |
| 81 | LED81 | TH81 | R81 | J6.33 / J6.34 | U5.22 (I9) |
| 82 | LED82 | TH82 | R82 | J6.31 / J6.32 | U5.3 (I6) |
| 83 | LED83 | TH83 | R83 | J6.29 / J6.30 | U6.22 (I9) |
| 84 | LED84 | TH84 | R84 | J6.27 / J6.28 | U6.3 (I6) |
| 85 | LED85 | TH85 | R85 | J6.25 / J6.26 | U1.16 (I15) |
| 86 | LED86 | TH86 | R86 | J6.23 / J6.24 | U1.9 (I0) |
| 87 | LED87 | TH87 | R87 | J6.21 / J6.22 | U2.16 (I15) |
| 88 | LED88 | TH88 | R88 | J6.17 / J6.18 | U2.9 (I0) |
| 89 | LED89 | TH89 | R89 | J6.15 / J6.16 | U3.16 (I15) |
| 90 | LED90 | TH90 | R90 | J6.13 / J6.14 | U3.9 (I0) |
| 91 | LED91 | TH91 | R91 | J6.11 / J6.12 | U4.2 (I7) |
| 92 | LED92 | TH92 | R92 | J6.9 / J6.10 | U4.23 (I8) |
| 93 | LED93 | TH93 | R93 | J6.7 / J6.8 | U5.23 (I8) |
| 94 | LED94 | TH94 | R94 | J6.5 / J6.6 | U5.2 (I7) |
| 95 | LED95 | TH95 | R95 | J6.3 / J6.4 | U6.23 (I8) |
| 96 | LED96 | TH96 | R96 | J6.1 / J6.2 | U6.2 (I7) |

## LED board — muxes

All six CD74HC4067: pin 24 (VCC) → +3.3V with 100nF (C1-C6), pin 12 (GND) → GND, pin 15 (/E) → GND (always enabled).

| Signal | Mux pins | Ribbon |
|---|---|---|
| MUX_A0 | U1-U6 pin 10 (S0) | J9.15 |
| MUX_A1 | U1-U6 pin 11 (S1) | J9.16 |
| MUX_A2 | U1-U6 pin 14 (S2) | J9.17 |
| MUX_A3 | U1-U6 pin 13 (S3) | J9.18 |
| NTC_SIG1 | U1 pin 1 (COM) | J9.3 |
| NTC_SIG2 | U2 pin 1 (COM) | J9.5 |
| NTC_SIG3 | U3 pin 1 (COM) | J9.7 |
| NTC_SIG4 | U4 pin 1 (COM) | J9.9 |
| NTC_SIG5 | U5 pin 1 (COM) | J9.11 |
| NTC_SIG6 | U6 pin 1 (COM) | J9.13 |

## Ribbon cables (straight 1:1, keyed)

J1-J6 (40-way, one PCA9685 bank per ribbon): channel = 16*(J#-1) + i for pair i = 1..16. Pairs 1-9 on pins 1-18, pairs 10-16 on pins 21-34; pin 20 UNUSED (IDE-cable key), pins 19 and 35-40 = GND. A = odd pin, K = even pin of each pair.

J9 (20-way):

| Pin | Signal | Pin | Signal |
|---|---|---|---|
| 1 | +3.3V | 2 | GND |
| 3 | NTC_SIG1 | 4 | GND |
| 5 | NTC_SIG2 | 6 | GND |
| 7 | NTC_SIG3 | 8 | GND |
| 9 | NTC_SIG4 | 10 | GND |
| 11 | NTC_SIG5 | 12 | GND |
| 13 | NTC_SIG6 | 14 | GND |
| 15 | MUX_A0 | 16 | MUX_A1 |
| 17 | MUX_A2 | 18 | MUX_A3 |
| 19 | GND | 20 | GND |

**24V does NOT cross the ribbons.** Feed 24 V to the control board (J6 screw terminal or J7 barrel jack). The LED board needs no direct 24 V — every LED is powered through its channel pair.

## Test points

**LED board:** TP1 = +3.3V, TP2 = GND, TP3 = GND

**Control board:** TP1 = +24V, TP2 = +5V, TP3 = +3.3V, TP4 = GND, TP5 = GND, TP6 = SW_5V, TP7 = I2C_SDA, TP8 = I2C_SCL, TP9 = FAN_SW, TP10 = DIM1, TP11 = LED_A1, TP12 = LED_K1

## ERC housekeeping

- Add power symbols (+24V, +5V, +3.3V, GND) and one PWR_FLAG on +24V, +5V, +3.3V and GND (they enter via connectors).
- U111 (ADS1115) is DNP — wire it anyway (ADDR pin 1 → GND = 0x48) so it can be populated later; or leave unwired and ignore ERC.
- Unused mux inputs: none (all 16 used on all six).
- Unused PCA9685 outputs: none (96 = 6×16 exactly).
