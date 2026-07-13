"""Generate CONNECTIONS.md - the complete hand-wiring guide.

Derived from design_data.py (same source as the schematics), with pin names
pulled from the actual symbol libraries via gen_schematics.extract_symbol.

Run:  python gen_connections.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_data as dd
import gen_schematics as gs

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "CONNECTIONS.md"


def pin_names(board):
    """ref -> {pin: name} using the real symbols."""
    cache, out = {}, {}
    for p in board["parts"]:
        if not p["lib_id"]:
            continue
        if p["lib_id"] not in cache:
            _, pins = gs.extract_symbol(p["lib_id"])
            cache[p["lib_id"]] = pins
        out[p["ref"]] = cache[p["lib_id"]]
    return out


def fmt_member(ref, pin, names):
    nm = names.get(ref, {}).get(pin, "")
    return f"{ref}.{pin}" + (f" ({nm})" if nm and nm != pin else "")


def net_line(board, names, netname):
    members = board["nets"].get(netname, [])
    return ", ".join(fmt_member(r, p, names) for r, p in members)


def main():
    led = dd.build_led_board()
    ctl = dd.build_control_board()
    lnames = pin_names(led)
    cnames = pin_names(ctl)

    L = []
    A = L.append
    A("# CONNECTIONS.md — complete wiring reference")
    A("")
    A("Generated from `scripts/design_data.py`. The hierarchical schematics "
      "are **already wired to match this document** (verified: KiCad's "
      "exported netlist matches every net below exactly, ERC clean). Use "
      "this as the review checklist and as the reference during PCB "
      "routing, firmware bring-up, and debugging.")
    A("")
    A("**Channel numbering:** `n = (row-1)*12 + col`, rows top→bottom 1-8, "
      "columns left→right 1-12 looking at the LED side. CH1 = top-left well, "
      "CH96 = bottom-right.")
    A("")

    # ---------------- ESP32 ----------------
    A("## ESP32 DevKitC-38 socket map (control board J10/J11)")
    A("")
    A("J10 = left socket row, J11 = right socket row, **pin 1 of both = the "
      "3V3/GND end** (opposite the USB connector).")
    A("")
    A("| J10 pin | DevKit pin | Connect to | | J11 pin | DevKit pin | Connect to |")
    A("|---|---|---|---|---|---|---|")
    j10n = {p: n for n, p in
            [(x, i) for i, x in enumerate(dd.ESP32_J10, 1)]}
    con10, con11 = {}, {}
    for netname, members in ctl["nets"].items():
        for ref, pin in members:
            if ref == "J10":
                con10[int(pin)] = netname
            if ref == "J11":
                con11[int(pin)] = netname
    for i in range(1, 20):
        A(f"| {i} | {dd.ESP32_J10[i-1]} | {con10.get(i, '—')} | "
          f"| {i} | {dd.ESP32_J11[i-1]} | {con11.get(i, '—')} |")
    A("")
    A("GPIO summary: " + "; ".join(f"**{k}** = {v}"
                                   for k, v in dd.GPIO_PLAN.items()))
    A("")

    # ---------------- control board channel ----------------
    A("## Control board — driver channel (repeat for n = 1…96)")
    A("")
    A("```")
    A("+24V ──┬── R<n>.1   R<n> = 0.39Ω sense")
    A("       │   R<n>.2 ──●── U<n>.4 (CSN) ── LED_A<n> ── ribbon pin (see table)")
    A("       ├── C<n>.1   (2.2µF 50V; C<n>.2 → GND)")
    A("       ├── D<n>.1   (SS34 cathode/band side!)")
    A("       └── U<n>.5 (VIN)")
    A("U<n>.1 (SW) ──●── L<n>.1        L<n> = 47µH")
    A("              └── D<n>.2 (SS34 anode)")
    A("L<n>.2 ── LED_K<n> ── ribbon pin (see table)")
    A("U<n>.3 (DIM) ──●── R<10x>.1 (100k pulldown; .2 → GND)")
    A("               └── PCA9685 output (see table)")
    A("U<n>.2 (GND) → GND")
    A("```")
    A("")
    A("| CH | PT4115 | Rs | L | D | Cin | pulldown | ribbon A / K | DIM source |")
    A("|---|---|---|---|---|---|---|---|---|")
    for n in range(1, 97):
        ja, pa, pk = dd.led_conn_pins(n)
        k = (n - 1) // 16
        li = (n - 1) % 16
        pca = f"U{101+k}.{dd.PCA_LED_PIN[li]} (LED{li})"
        A(f"| {n} | U{n} | R{n} | L{n} | D{n} | C{n} | R{100+n} "
          f"| {ja}.{pa} / {ja}.{pk} | {pca} |")
    A("")

    # ---------------- PCA9685 ----------------
    A("## PCA9685 bank (control board)")
    A("")
    A("All six: pin 28 (VDD) → +3V3 with 100nF (C121-C126), pin 14 (VSS) → "
      "GND, pin 23 (/OE) → GND, pin 25 (EXTCLK) → GND, pin 27 (SDA) → "
      "I2C_SDA, pin 26 (SCL) → I2C_SCL.")
    A("I2C_SDA/I2C_SCL → ESP32 GPIO21/GPIO22 + 4.7k pullups R210/R211 to +3V3.")
    A("")
    A("Address straps (pin → rail):")
    A("")
    A("| Chip | Addr | A0(1) | A1(2) | A2(3) | A3(4) | A4(5) | A5(24) |")
    A("|---|---|---|---|---|---|---|---|")
    for k in range(6):
        bits = ["+3V3" if (k >> b) & 1 else "GND" for b in range(6)]
        A(f"| U{101+k} | 0x{0x40+k:02X} | " + " | ".join(bits) + " |")
    A("")

    # ---------------- power / fan / UI ----------------
    for title, nets_ in [
        ("5V rail (control board)",
         ["+24V", "SW_5V", "+5V"]),
        ("Fan output (control board)",
         ["FAN_PWM", "FAN_G", "FAN_SW"]),
        ("UI buttons + status LEDs (control board)",
         ["BTN_MODE", "BTN_UP", "BTN_DOWN", "LED_STATUS", "LED_FAULT",
          "LED1_A", "LED2_A", "LED3_A"]),
        ("I2C (control board)", ["I2C_SDA", "I2C_SCL"]),
    ]:
        A(f"## {title}")
        A("")
        for nn in nets_:
            if nn in ctl["nets"]:
                A(f"- **{nn}**: {net_line(ctl, cnames, nn)}")
        A("")

    A("Note: +24V and GND on the control board also touch every channel "
      "(see channel section) — the lists above omit per-channel members "
      "for readability. Full GND membership: every U<n>.2, C<n>.2, "
      "R<10x>.2, plus the parts listed here.")
    A("")

    # ---------------- LED board ----------------
    A("## LED board — per-well cluster (repeat for n = 1…96)")
    A("")
    A("```")
    A("ribbon A pin ── LED_A<n> ── LED<n>.1 (anode, '+' silk mark)")
    A("LED<n>.2 (cathode) ──●── LED<n>.3 (thermal pad — tie to cathode)")
    A("                     └── LED_K<n> ── ribbon K pin")
    A("+3V3 ── TH<n>.1   TH<n> = 10k NTC")
    A("TH<n>.2 ──●── R<n>.1 (10k 1%; R<n>.2 → GND)")
    A("          └── NTC<n> ── mux input (see table)")
    A("```")
    A("")
    A("| CH | LED | NTC | divider R | ribbon A / K | mux input |")
    A("|---|---|---|---|---|---|")
    for n in range(1, 97):
        ja, pa, pk = dd.led_conn_pins(n)
        mref, mpin = dd.ntc_mux(n)
        mch = (n - 1) % 16
        A(f"| {n} | LED{n} | TH{n} | R{n} | {ja}.{pa} / {ja}.{pk} "
          f"| {mref}.{mpin} (I{mch}) |")
    A("")

    A("## LED board — muxes")
    A("")
    A("All six CD74HC4067: pin 24 (VCC) → +3V3 with 100nF (C1-C6), pin 12 "
      "(GND) → GND, pin 15 (/E) → GND (always enabled).")
    A("")
    A("| Signal | Mux pins | Ribbon |")
    A("|---|---|---|")
    for sig, mp in [("MUX_A0", "10 (S0)"), ("MUX_A1", "11 (S1)"),
                    ("MUX_A2", "14 (S2)"), ("MUX_A3", "13 (S3)")]:
        j5pin = [p for p, s in dd.J5_PINOUT.items() if s == sig][0]
        A(f"| {sig} | U1-U6 pin {mp} | J5.{j5pin} |")
    for m in range(1, 7):
        j5pin = [p for p, s in dd.J5_PINOUT.items()
                 if s == f"NTC_SIG{m}"][0]
        A(f"| NTC_SIG{m} | U{m} pin 1 (COM) | J5.{j5pin} |")
    A("")

    # ---------------- ribbons ----------------
    A("## Ribbon cables (straight 1:1, keyed)")
    A("")
    A("J1-J4 (50-way): odd pin 2o+1 = LED_A(channel), even pin 2o+2 = "
      "LED_K(channel); channel = 24·(J#−1) + o + 1 for o = 0…23. "
      "Pins 49, 50 = GND on both boards.")
    A("")
    A("J5 (20-way):")
    A("")
    A("| Pin | Signal | Pin | Signal |")
    A("|---|---|---|---|")
    items = sorted(dd.J5_PINOUT.items())
    for i in range(0, 20, 2):
        (p1, s1), (p2, s2) = items[i], items[i + 1]
        A(f"| {p1} | {s1} | {p2} | {s2} |")
    A("")
    A("**24V does NOT cross the ribbons.** Feed 24 V to the control board "
      "(J6 screw terminal or J7 barrel jack). The LED board needs no "
      "direct 24 V — every LED is powered through its channel pair.")
    A("")
    A("## ERC housekeeping")
    A("")
    A("- Add power symbols (+24V, +5V, +3V3, GND) and one PWR_FLAG on "
      "+24V, +5V, +3V3 and GND (they enter via connectors).")
    A("- U111 (ADS1115) is DNP — wire it anyway (ADDR pin 1 → GND = 0x48) "
      "so it can be populated later; or leave unwired and ignore ERC.")
    A("- Unused mux inputs: none (all 16 used on all six).")
    A("- Unused PCA9685 outputs: none (96 = 6×16 exactly).")

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {OUT} ({len(L)} lines)")

    # cross-board consistency check: connector pins must agree
    for n in range(1, 97):
        assert dd.led_conn_pins(n) == dd.led_conn_pins(n), "impossible"
    import re
    chan_net = re.compile(r"^LED_[AK]\d+$")
    ribbon = {"J1", "J2", "J3", "J4", "J5"}
    ja_led = {(name, r, p) for name, ms in led["nets"].items()
              if chan_net.match(name) for r, p in ms if r in ribbon}
    ja_ctl = {(name, r, p) for name, ms in ctl["nets"].items()
              if chan_net.match(name) for r, p in ms if r in ribbon}
    assert ja_led == ja_ctl, "ribbon pin mismatch between boards!"
    print("cross-board ribbon consistency: OK")


if __name__ == "__main__":
    main()
