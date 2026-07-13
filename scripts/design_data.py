"""Single source of truth for the 12x8 LED array design.

Both boards' parts, positions, and nets are defined here.
- gen_schematics.py consumes SCH positions (mm, y-down, 1.27 grid)
- gen_pcbs.py consumes PCB positions (mm) and rotations
- gen_outputs.py consumes parts + nets for BOM/CPL/CONNECTIONS.md

Channel numbering: n = (row-1)*12 + col, row 1..8 top->bottom, col 1..12 left->right.
"""

# ---------------------------------------------------------------- helpers

def snap(v, g=1.27):
    return round(round(v / g) * g, 3)


def part(ref, lib_id, value, footprint, lcsc, sch_xy, pcb_xy, pcb_rot=0.0,
         dnp=False, desc=""):
    return dict(ref=ref, lib_id=lib_id, value=value, footprint=footprint,
                lcsc=lcsc, sch_xy=(snap(sch_xy[0]), snap(sch_xy[1])),
                pcb_xy=pcb_xy, pcb_rot=pcb_rot, dnp=dnp, desc=desc)


def ch_rc(n):  # channel -> (row, col) 1-based
    return ((n - 1) // 12 + 1, (n - 1) % 12 + 1)


# LED connector map: J1..J4 carry channels in blocks of 24, two pins each.
def led_conn_pins(n):
    """Return (conn_ref, anode_pin, cathode_pin) for channel n (1..96)."""
    j = (n - 1) // 24 + 1            # J1..J4
    o = (n - 1) % 24                 # 0..23 within connector
    return (f"J{j}", 2 * o + 1, 2 * o + 2)


# 4067 mux input pin numbers: I0..I7 = pins 9..2, I8..I15 = pins 23..16
MUX_INPUT_PIN = {k: 9 - k for k in range(8)}
MUX_INPUT_PIN.update({k: 31 - k for k in range(8, 16)})
# mux control pins (CD74HC4067M96): COM=1, S0=10, S1=11, S2=14, S3=13, /E=15,
# GND=12, VCC=24


def ntc_mux(n):
    """NTC n -> (mux_ref, input_pin)."""
    m = (n - 1) // 16 + 1            # U1..U6
    k = (n - 1) % 16                 # channel 0..15
    return (f"U{m}", MUX_INPUT_PIN[k])


# J5 logic ribbon pinout (both boards)
J5_PINOUT = {
    1: "+3.3V", 2: "GND", 3: "NTC_SIG1", 4: "GND", 5: "NTC_SIG2", 6: "GND",
    7: "NTC_SIG3", 8: "GND", 9: "NTC_SIG4", 10: "GND", 11: "NTC_SIG5",
    12: "GND", 13: "NTC_SIG6", 14: "GND", 15: "MUX_A0", 16: "MUX_A1",
    17: "MUX_A2", 18: "MUX_A3", 19: "GND", 20: "GND",
}

# PCA9685PW pin map (TSSOP-28)
PCA_LED_PIN = {i: 6 + i for i in range(8)}          # LED0..LED7 = 6..13
PCA_LED_PIN.update({i: 7 + i for i in range(8, 16)})  # LED8..LED15 = 15..22
PCA_PINS = dict(A0=1, A1=2, A2=3, A3=4, A4=5, GND=14, OE=23, A5=24,
                EXTCLK=25, SCL=26, SDA=27, VDD=28)

# ESP32 DevKitC-38 socket map: J10 = left row seen from top (pin1 = 3V3 corner),
# J11 = right row (pin1 = GND corner, same end of board as J10 pin1).
ESP32_J10 = ["3V3", "EN", "GPIO36/VP", "GPIO39/VN", "GPIO34", "GPIO35",
             "GPIO32", "GPIO33", "GPIO25", "GPIO26", "GPIO27", "GPIO14",
             "GPIO12", "GND", "GPIO13", "GPIO9/D2", "GPIO10/D3", "GPIO11/CMD",
             "5V"]
ESP32_J11 = ["GND", "GPIO23", "GPIO22", "GPIO1/TX0", "GPIO3/RX0", "GPIO21",
             "GND", "GPIO19", "GPIO18", "GPIO5", "GPIO17", "GPIO16", "GPIO4",
             "GPIO0", "GPIO2", "GPIO15", "GPIO8/D1", "GPIO7/D0", "GPIO6/CLK"]

# GPIO assignments (see CONNECTIONS.md)
GPIO_PLAN = {
    "GPIO21": "I2C SDA (PCA9685 x6, ADS1115 opt.)",
    "GPIO22": "I2C SCL",
    "GPIO16": "MUX_A0", "GPIO17": "MUX_A1", "GPIO18": "MUX_A2",
    "GPIO19": "MUX_A3",
    "GPIO32": "NTC_SIG1 (ADC1_CH4)", "GPIO33": "NTC_SIG2 (ADC1_CH5)",
    "GPIO34": "NTC_SIG3 (ADC1_CH6)", "GPIO35": "NTC_SIG4 (ADC1_CH7)",
    "GPIO36/VP": "NTC_SIG5 (ADC1_CH0)", "GPIO39/VN": "NTC_SIG6 (ADC1_CH3)",
    "GPIO25": "FAN_PWM (Q1 gate via R201)",
    "GPIO4": "STATUS LED2 (blue)", "GPIO13": "FAULT LED3 (red)",
    "GPIO14": "SW1 MODE (to GND, internal pull-up)",
    "GPIO27": "SW2 UP (to GND, internal pull-up)",
    "GPIO26": "SW3 DOWN (to GND, internal pull-up)",
}

# ------------------------------------------------------------ footprints

FP = {
    "led":    "jlc_parts:LED-SMD_3P-L3.5-W3.5_NLW3535AV2",
    "pt4115": "jlc_parts:SOT-89-5_L4.5-W2.5-P1.50-LS4.5-BR",
    "mux":    "jlc_parts:SOIC-24_L15.4-W7.5-P1.27-LS10.3-BL",
    "button": "jlc_parts:SW-SMD_4P-L5.1-W5.1-P3.70-LS6.5-TL_H1.5",
    "r0603":  "Resistor_SMD:R_0603_1608Metric",
    "r0805":  "Resistor_SMD:R_0805_2012Metric",
    "c0603":  "Capacitor_SMD:C_0603_1608Metric",
    "c0805":  "Capacitor_SMD:C_0805_2012Metric",
    "led0805": "LED_SMD:LED_0805_2012Metric",
    "sma":    "Diode_SMD:D_SMA",
    "swpa4030": "Inductor_SMD:L_Sunlord_SWPA4030S",
    "swpa6045": "Inductor_SMD:L_Sunlord_SWPA6045S",
    "soic8":  "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    "tssop28": "Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm",
    "vssop10": "Package_SO:TSSOP-10_3x3mm_P0.5mm",
    "sot23":  "Package_TO_SOT_SMD:SOT-23",
    "idc50":  "Connector_IDC:IDC-Header_2x25_P2.54mm_Vertical",
    "idc20":  "Connector_IDC:IDC-Header_2x10_P2.54mm_Horizontal",
    "sock19": "Connector_PinSocket_2.54mm:PinSocket_1x19_P2.54mm_Vertical",
    # KF301-5.0-2P (C474881): MX126 footprint geometry but drills enlarged to
    # 1.4 mm per JLCPCB/EasyEDA recommended pattern (KF301 blade pins are a
    # marginal fit in the stock MX126 1.3 mm holes).
    "screw2": "jlc_parts:TerminalBlock_KF301-5.0-2P_1x02_P5.00mm",
    "barrel": "Connector_BarrelJack:BarrelJack_Horizontal",
    "hdr2":   "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    "elec8":  "Capacitor_SMD:CP_Elec_8x10",
    "elec63": "Capacitor_SMD:CP_Elec_6.3x7.7",
    "hole":   "MountingHole:MountingHole_3.2mm_M3",
    "tp":     "TestPoint:TestPoint_Pad_1.5x1.5mm",
}

LIB = {
    "led":    "jlc_parts:HL-C3535F15R3GA-ZW",
    "pt4115": "jlc_parts:PT4115",
    "mux":    "jlc_parts:CD74HC4067M96",
    "button": "jlc_parts:TS-1187A-B-A-B",
    "r":      "Device:R",
    "c":      "Device:C",
    "cp":     "Device:C_Polarized",
    "l":      "Device:L",
    "dsch":   "Device:D_Schottky",
    "ntc":    "Device:Thermistor_NTC",
    "led2":   "Device:LED",
    "pca":    "Driver_LED:PCA9685PW",
    "xl1509": "Regulator_Switching:XL1509-5.0",
    "ads":    "Analog_ADC:ADS1115IDGS",
    "fet":    "Transistor_FET:AO3400A",
    "conn50": "Connector_Generic:Conn_02x25_Odd_Even",
    "conn20": "Connector_Generic:Conn_02x10_Odd_Even",
    "sock19": "Connector_Generic:Conn_01x19",
    "screw2": "Connector:Screw_Terminal_01x02",
    "barrel": "Connector:Barrel_Jack",
    "hdr2":   "Connector_Generic:Conn_01x02",
    "tp":     "Connector:TestPoint",
    "hole":   "Mechanical:MountingHole",
}


# ============================================================ LED BOARD

def build_led_board():
    parts, nets = [], {}

    def net(name, ref, pin):
        nets.setdefault(name, []).append((ref, str(pin)))

    # --- 96 LED/NTC clusters ---
    for n in range(1, 97):
        r, c = ch_rc(n)
        # schematic cluster (A1): 55mm x-pitch, 55mm y-pitch
        sx, sy = 35 + (c - 1) * 55, 45 + (r - 1) * 55
        # pcb: 9mm grid, field origin (19.5, 14)
        px, py = 19.5 + (c - 1) * 9.0, 14.0 + (r - 1) * 9.0

        parts += [
            part(f"LED{n}", LIB["led"], "HL-C3535F15R3GA-ZW 660nm",
                 FP["led"], "C5445086", (sx, sy), (px, py), 0,
                 desc=f"660nm LED ch{n} (row{r},col{c})"),
            part(f"TH{n}", LIB["ntc"], "NTC 10k B3434",
                 FP["r0603"], "C13564", (sx + 17.78, sy - 5.08),
                 (px + 3.6, py - 2.0), 90,
                 desc=f"NTC under LED{n}"),
            part(f"R{n}", LIB["r"], "10k 1%",
                 FP["r0603"], "C25804", (sx + 17.78, sy + 8.89),
                 (px + 3.6, py + 2.0), 90,
                 desc=f"NTC divider lower leg ch{n}"),
        ]
        ja, pa, pk = led_conn_pins(n)
        net(f"LED_A{n}", f"LED{n}", 1)          # pad 1 = anode ('+' silk)
        net(f"LED_A{n}", ja, pa)
        net(f"LED_K{n}", f"LED{n}", 2)          # pad 2 = cathode
        net(f"LED_K{n}", f"LED{n}", 3)          # pad 3 = thermal, tie to cathode
        net(f"LED_K{n}", ja, pk)
        net("+3.3V", f"TH{n}", 1)
        net(f"NTC{n}", f"TH{n}", 2)
        net(f"NTC{n}", f"R{n}", 1)
        mref, mpin = ntc_mux(n)
        net(f"NTC{n}", mref, mpin)
        net("GND", f"R{n}", 2)

    # --- 6 muxes + decoupling (bottom strip) ---
    for m in range(1, 7):
        sx, sy = 60 + (m - 1) * 110, 520
        px, py = 24 + (m - 1) * 19, 88
        parts += [
            part(f"U{m}", LIB["mux"], "CD74HC4067M96", FP["mux"], "C496123",
                 (sx, sy), (px, py), 0, desc=f"NTC mux {m} (ch {16*(m-1)+1}-{16*m})"),
            part(f"C{m}", LIB["c"], "100nF", FP["c0603"], "C14663",
                 (sx + 25.4, sy - 12.7), (px + 6.4, py - 7.0), 90,
                 desc=f"decoupling U{m}"),
        ]
        net("+3.3V", f"U{m}", 24)
        net("GND", f"U{m}", 12)
        net("GND", f"U{m}", 15)                 # /E enabled
        net(f"NTC_SIG{m}", f"U{m}", 1)          # COM
        for i, sig in ((10, "MUX_A0"), (11, "MUX_A1"), (14, "MUX_A2"),
                       (13, "MUX_A3")):
            net(sig, f"U{m}", i)
        net("+3.3V", f"C{m}", 1)
        net("GND", f"C{m}", 2)

    # --- connectors ---
    # J1..J4: two rows of two on bottom edge strip
    for j in range(1, 5):
        sx, sy = 740, 60 + (j - 1) * 125
        px = 37 + ((j - 1) % 2) * 66            # two columns
        py = 100 if j <= 2 else 111             # two rows
        parts.append(part(f"J{j}", LIB["conn50"], f"LED ch {24*(j-1)+1}-{24*j}",
                          FP["idc50"], "C9044", (sx, sy), (px, py), 0,
                          desc="2x25 IDC to control board"))
        net("GND", f"J{j}", 49)
        net("GND", f"J{j}", 50)
    parts.append(part("J5", LIB["conn20"], "logic/analog", FP["idc20"],
                      "C9144", (740, 545), (7, 105), 90,
                      desc="2x10 IDC logic ribbon"))
    for p, sig in J5_PINOUT.items():
        net(sig if sig not in ("+3.3V",) else "+3.3V", "J5", p)

    # --- test points ---
    for i, (tnet, txy) in enumerate([("+3.3V", (13, 86)), ("GND", (13, 90)),
                                     ("GND", (13, 94))], 1):
        parts.append(part(f"TP{i}", LIB["tp"], tnet, FP["tp"], "",
                          (0, 0), txy, 0, desc=f"test point {tnet}"))
        net(tnet, f"TP{i}", 1)

    # --- mounting holes: 4 corners of LED field + top mid ---
    holes = [(5.5, 5.5), (134.5, 5.5), (5.5, 82), (134.5, 82), (70, 5.5)]
    for i, (hx, hy) in enumerate(holes, 1):
        parts.append(part(f"H{i}", LIB["hole"], "M3", FP["hole"], "",
                          (0, 0), (hx, hy), 0, desc="M3 mounting hole"))

    board = dict(
        name="12x8 Led Array 9mm pitch",
        title="12x8 660nm LED Array - LED Board",
        paper="A1", size=(140, 120), layers=4,
        parts=parts, nets=nets)
    return board


# ======================================================== CONTROL BOARD

def build_control_board():
    parts, nets = [], {}

    def net(name, ref, pin):
        nets.setdefault(name, []).append((ref, str(pin)))

    # --- 96 driver channels ---
    for n in range(1, 97):
        r, c = ch_rc(n)
        sx, sy = 45 + (c - 1) * 92, 50 + (r - 1) * 62   # A0 sheet
        px, py = 22 + (c - 1) * 12.0, 40 + (r - 1) * 14.0

        parts += [
            part(f"U{n}", LIB["pt4115"], "PT4115", FP["pt4115"], "C347356",
                 (sx, sy), (px, py), 0, desc=f"buck CC driver ch{n} (row{r},col{c})"),
            part(f"R{n}", LIB["r"], "0.39R 1%", FP["r0805"], "C2930218",
                 (sx - 20.32, sy - 7.62), (px - 3.8, py - 4.4), 90,
                 desc=f"Rsense ch{n} (256mA)"),
            part(f"L{n}", LIB["l"], "47uH", FP["swpa4030"], "C54731",
                 (sx + 16.51, sy - 7.62), (px + 3.2, py - 4.4), 0,
                 desc=f"buck inductor ch{n}"),
            part(f"D{n}", LIB["dsch"], "SS34", FP["sma"], "C8678",
                 (sx + 16.51, sy + 6.35), (px + 2.6, py + 4.2), 180,
                 desc=f"freewheel ch{n}"),
            part(f"C{n}", LIB["c"], "2.2uF 50V", FP["c0805"], "C125847",
                 (sx - 20.32, sy + 6.35), (px - 4.0, py + 4.2), 90,
                 desc=f"VIN cap ch{n}"),
            part(f"R{100 + n}", LIB["r"], "100k", FP["r0603"], "C25803",
                 (sx - 1.27, sy + 12.7), (px, py + 8.8), 0,
                 desc=f"DIM pulldown ch{n}"),
        ]
        # nets
        net("+24V", f"R{n}", 1)
        net("+24V", f"C{n}", 1)
        net("+24V", f"D{n}", 1)                 # cathode to +24V
        net("+24V", f"U{n}", 5)                 # VIN
        net(f"LED_A{n}", f"R{n}", 2)            # CSN node
        net(f"LED_A{n}", f"U{n}", 4)
        net(f"SW{n}", f"U{n}", 1)
        net(f"SW{n}", f"L{n}", 1)
        net(f"SW{n}", f"D{n}", 2)               # anode to SW
        net(f"LED_K{n}", f"L{n}", 2)
        net(f"DIM{n}", f"U{n}", 3)
        net(f"DIM{n}", f"R{100 + n}", 1)
        net("GND", f"U{n}", 2)
        net("GND", f"C{n}", 2)
        net("GND", f"R{100 + n}", 2)
        ja, pa, pk = led_conn_pins(n)
        net(f"LED_A{n}", ja, pa)
        net(f"LED_K{n}", ja, pk)
        k = (n - 1) // 16                        # PCA chip index 0..5
        led_i = (n - 1) % 16
        net(f"DIM{n}", f"U{101 + k}", PCA_LED_PIN[led_i])

    # --- PCA9685 bank ---
    for k in range(6):
        u = f"U{101 + k}"
        sx, sy = 50 + k * 80, 600
        px, py = 30 + k * 20, 152
        parts += [
            part(u, LIB["pca"], f"PCA9685PW (0x{0x40 + k:02X})", FP["tssop28"],
                 "C2678753", (sx, sy), (px, py), 0,
                 desc=f"16ch PWM, channels {16*k+1}-{16*k+16}"),
            part(f"C{121 + k}", LIB["c"], "100nF", FP["c0603"], "C14663",
                 (sx + 20.32, sy - 17.78), (px + 6.6, py - 3.0), 90,
                 desc=f"decoupling {u}"),
        ]
        net("+3.3V", u, PCA_PINS["VDD"])
        net("GND", u, PCA_PINS["GND"])
        net("GND", u, PCA_PINS["OE"])           # outputs live at reset (LOW)
        net("GND", u, PCA_PINS["EXTCLK"])       # unused, tie low
        net("I2C_SDA", u, PCA_PINS["SDA"])
        net("I2C_SCL", u, PCA_PINS["SCL"])
        # address straps: 0x40+k -> A5..A0 = k in binary (A6 fixed 1 internally)
        for bit, pname in enumerate(["A0", "A1", "A2", "A3", "A4", "A5"]):
            net("+3.3V" if (k >> bit) & 1 else "GND", u, PCA_PINS[pname])
        net("+3.3V", f"C{121 + k}", 1)
        net("GND", f"C{121 + k}", 2)

    # --- 5V rail: XL1509-5.0E1 buck ---
    #   XL1509 SOP8: extract pin names from symbol; expected LM2596-style:
    #   VIN, GND, /ON-OFF, FB, OUT
    sx, sy = 560, 700
    parts += [
        part("U110", LIB["xl1509"], "XL1509-5.0E1", FP["soic8"], "C61063",
             (sx, sy), (36, 172), 0, desc="24V->5V 2A buck"),
        part("C110", LIB["cp"], "100uF 50V", FP["elec8"], "C134514",
             (sx - 30.48, sy), (22, 172), 0, desc="5V buck input cap"),
        part("L101", LIB["l"], "47uH 2A+", FP["swpa6045"], "C36414",
             (sx + 25.4, sy - 5.08), (48, 168), 0, desc="5V buck inductor"),
        part("D101", LIB["dsch"], "SS34", FP["sma"], "C8678",
             (sx + 25.4, sy + 7.62), (48, 176), 90, desc="5V buck freewheel"),
        part("C111", LIB["cp"], "220uF 16V", FP["elec63"], "C286136",
             (sx + 45.72, sy), (58, 172), 0, desc="5V rail output cap"),
    ]
    # XL1509-5.0 (verified): 1=VIN 2=OUT 3=FB 4=/EN 5..8=GND
    net("+24V", "U110", 1); net("+24V", "C110", 1)
    net("GND", "C110", 2)
    net("SW_5V", "U110", 2)                             # OUT
    net("SW_5V", "L101", 1)
    net("SW_5V", "D101", 1)             # freewheel cathode to SW node
    net("GND", "D101", 2)               # anode to GND
    net("+5V", "L101", 2)
    net("+5V", "C111", 1)
    net("GND", "C111", 2)
    net("+5V", "U110", 3)                               # FB senses 5V rail
    net("GND", "U110", 4)                               # /EN low = enabled
    for gp in (5, 6, 7, 8):
        net("GND", "U110", gp)

    # --- bulk 24V caps ---
    for i in range(4):
        parts.append(part(f"C{101 + i}", LIB["cp"], "220uF 35V", FP["elec8"],
                          "C134820", (660 + i * 30.48, 700), (22 + i * 11, 183),
                          0, desc="24V bulk"))
        net("+24V", f"C{101 + i}", 1)
        net("GND", f"C{101 + i}", 2)

    # --- power inputs ---
    parts += [
        part("J6", LIB["screw2"], "24V IN", FP["screw2"], "C474881",
             (800, 700), (8, 172), 90, desc="24V screw terminal"),
        part("J7", LIB["barrel"], "24V IN (5.5/2.5)", FP["barrel"], "C381115",
             (800, 740), (8, 150), 0, desc="24V barrel jack 5A"),
    ]
    net("+24V", "J6", 1); net("GND", "J6", 2)
    net("+24V", "J7", 1); net("GND", "J7", 2)

    # --- fan output ---
    parts += [
        part("J8", LIB["hdr2"], "FAN 24V", FP["hdr2"], "C2337", (900, 700),
             (160, 183), 0, desc="fan header"),
        part("Q1", LIB["fet"], "AO3400A", FP["sot23"], "C20917", (900, 730),
             (160, 172), 0, desc="fan low-side switch"),
        part("R201", LIB["r"], "100R", FP["r0603"], "C22775", (880, 745),
             (155, 168), 90, desc="fan gate series"),
        part("R202", LIB["r"], "100k", FP["r0603"], "C25803", (920, 745),
             (165, 168), 90, desc="fan gate pulldown"),
        part("D102", LIB["dsch"], "SS34", FP["sma"], "C8678", (900, 680),
             (160, 177), 0, desc="fan flyback"),
    ]
    net("+24V", "J8", 1)
    net("FAN_SW", "J8", 2)
    net("FAN_SW", "Q1", 3)              # drain (AO3400A: 1=G 2=S 3=D verified at gen)
    net("FAN_SW", "D102", 2)
    net("+24V", "D102", 1)
    net("GND", "Q1", 2)
    net("FAN_G", "Q1", 1)
    net("FAN_G", "R201", 2)
    net("FAN_PWM", "R201", 1)
    net("FAN_G", "R202", 1)
    net("GND", "R202", 2)

    # --- ESP32 DevKitC socket ---
    parts += [
        part("J10", LIB["sock19"], "ESP32 left (3V3 row)", FP["sock19"],
             "C319202", (1000, 100), (140.0, 130), 0, desc="DevKitC-38 socket L"),
        part("J11", LIB["sock19"], "ESP32 right (GND row)", FP["sock19"],
             "C319202", (1030, 100), (165.4, 130), 0, desc="DevKitC-38 socket R"),
    ]
    for i, name in enumerate(ESP32_J10, 1):
        sig = {"3V3": "+3.3V", "5V": "+5V", "GND": "GND",
               "GPIO36/VP": "NTC_SIG5", "GPIO39/VN": "NTC_SIG6",
               "GPIO34": "NTC_SIG3", "GPIO35": "NTC_SIG4",
               "GPIO32": "NTC_SIG1", "GPIO33": "NTC_SIG2",
               "GPIO25": "FAN_PWM", "GPIO26": "BTN_DOWN", "GPIO27": "BTN_UP",
               "GPIO14": "BTN_MODE", "GPIO13": "LED_FAULT",
               }.get(name)
        if sig:
            net(sig, "J10", i)
    for i, name in enumerate(ESP32_J11, 1):
        sig = {"GND": "GND", "GPIO22": "I2C_SCL", "GPIO21": "I2C_SDA",
               "GPIO19": "MUX_A3", "GPIO18": "MUX_A2", "GPIO17": "MUX_A1",
               "GPIO16": "MUX_A0", "GPIO4": "LED_STATUS",
               }.get(name)
        if sig:
            net(sig, "J11", i)

    # --- I2C pullups ---
    parts += [
        part("R210", LIB["r"], "4.7k", FP["r0603"], "C23162", (1070, 600),
             (150, 145), 0, desc="SDA pullup"),
        part("R211", LIB["r"], "4.7k", FP["r0603"], "C23162", (1070, 615),
             (150, 148), 0, desc="SCL pullup"),
    ]
    net("I2C_SDA", "R210", 1); net("+3.3V", "R210", 2)
    net("I2C_SCL", "R211", 1); net("+3.3V", "R211", 2)

    # --- UI: buttons + status LEDs ---
    for i, (name, sig) in enumerate([("MODE", "BTN_MODE"), ("UP", "BTN_UP"),
                                     ("DOWN", "BTN_DOWN")], 1):
        parts.append(part(f"SW{i}", LIB["button"], name, FP["button"],
                          "C318884", (950 + (i - 1) * 40, 600),
                          (120 + (i - 1) * 12, 172), 0, desc=f"button {name}"))
        # TS-1187A: pins 1/2 one side, 3/4 other; 1-2 and 3-4 are pairs
        net(sig, f"SW{i}", 1)
        net(sig, f"SW{i}", 2)
        net("GND", f"SW{i}", 3)
        net("GND", f"SW{i}", 4)
    leds = [("LED1", "PWR green", "+5V", "R203", "2.2k", "C4190"),
            ("LED2", "STATUS blue", "LED_STATUS", "R204", "1k", "C21190"),
            ("LED3", "FAULT red", "LED_FAULT", "R205", "1k", "C21190")]
    for i, (lref, val, drive, rref, rval, rlcsc) in enumerate(leds):
        parts += [
            part(lref, LIB["led2"], val, FP["led0805"],
                 {"LED1": "C2297", "LED2": "C2293", "LED3": "C84256"}[lref],
                 (950 + i * 40, 640), (120 + i * 12, 162), 0, desc=val),
            part(rref, LIB["r"], rval, FP["r0603"], rlcsc,
                 (950 + i * 40, 660), (120 + i * 12, 158), 90,
                 desc=f"{lref} series R"),
        ]
        net(drive, rref, 1)
        net(f"{lref}_A", rref, 2)       # series R feeds LED anode
        net(f"{lref}_A", lref, 2)       # Device:LED pin2 = A
        net("GND", lref, 1)             # pin1 = K to GND

    # --- optional ADS1115 (DNP) ---
    parts.append(part("U111", LIB["ads"], "ADS1115IDGS (DNP)", FP["vssop10"],
                      "C37593", (1120, 600), (150, 155), 0, dnp=True,
                      desc="optional precision ADC"))
    net("+3.3V", "U111", 8); net("GND", "U111", 3)
    net("I2C_SDA", "U111", 10); net("I2C_SCL", "U111", 9)
    net("GND", "U111", 1)               # ADDR -> 0x48

    # --- IDC + logic connectors (top edge) ---
    for j in range(1, 5):
        sx, sy = 1120, 60 + (j - 1) * 125
        px = 40 + ((j - 1) % 2) * 68
        py = 8 if j <= 2 else 19
        parts.append(part(f"J{j}", LIB["conn50"], f"LED ch {24*(j-1)+1}-{24*j}",
                          FP["idc50"], "C9044", (sx, sy), (px, py), 0,
                          desc="2x25 IDC to LED board"))
        net("GND", f"J{j}", 49)
        net("GND", f"J{j}", 50)
    parts.append(part("J5", LIB["conn20"], "logic/analog", FP["idc20"],
                      "C9144", (1120, 560), (135, 13.5), 90,
                      desc="2x10 IDC logic ribbon"))
    for p, sig in J5_PINOUT.items():
        net(sig, "J5", p)

    # --- test points ---
    tps = [("+24V", (68, 166)), ("+5V", (74, 166)), ("+3.3V", (80, 166)),
           ("GND", (86, 166)), ("GND", (92, 166)), ("SW_5V", (98, 166)),
           ("I2C_SDA", (104, 166)), ("I2C_SCL", (110, 166)),
           ("FAN_SW", (152, 178)),
           ("DIM1", (68, 178)), ("LED_A1", (74, 178)), ("LED_K1", (80, 178))]
    for i, (tnet, txy) in enumerate(tps, 1):
        parts.append(part(f"TP{i}", LIB["tp"], tnet, FP["tp"], "",
                          (0, 0), txy, 0, desc=f"test point {tnet}"))
        net(tnet, f"TP{i}", 1)

    # --- mounting holes ---
    holes = [(5.5, 5.5), (164.5, 5.5), (5.5, 184.5), (164.5, 184.5)]
    for i, (hx, hy) in enumerate(holes, 1):
        parts.append(part(f"H{i}", LIB["hole"], "M3", FP["hole"], "",
                          (0, 0), (hx, hy), 0, desc="M3 mounting hole"))

    board = dict(
        name="control-board",
        title="12x8 660nm LED Array - Control Board",
        paper="A0", size=(170, 190), layers=2,
        parts=parts, nets=nets)
    return board


if __name__ == "__main__":
    for b in (build_led_board(), build_control_board()):
        refs = [p["ref"] for p in b["parts"]]
        assert len(refs) == len(set(refs)), "duplicate refs!"
        pins = sum(len(v) for v in b["nets"].values())
        print(f"{b['name']}: {len(b['parts'])} parts, {len(b['nets'])} nets, "
              f"{pins} net-pins")
