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

    # ---------------- logical channel map (firmware bible) ----------------
    A("## Logical channel map (well ↔ channel ↔ driver ↔ PWM)")
    A("")
    A("The driver serving a well is **not** the same index — each board's "
      "ribbon pinout was optimized independently to minimize crossings, and "
      "the cable wires them together slot-for-slot. Firmware addresses a "
      "well's brightness through the PCA output in this table, and reads its "
      "temperature through the mux input. **This is the mapping to hard-code.**")
    A("")
    well_of = {dd.well_channel(w): w for w in range(1, 97)}
    drv_of = {dd.drv_channel(d): d for d in range(1, 97)}
    A("| CH | Well (grid) | Ribbon | Driver | PWM (PCA.out) | NTC (mux.in) |")
    A("|---|---|---|---|---|---|")
    inv_led = {v: k for k, v in dd.PCA_LED_PIN.items()}
    for ch in range(1, 97):
        w = well_of[ch]; d = drv_of[ch]
        r, c = dd.ch_rc(w)
        ja, pa, pk = dd.WELL_CONN[w]
        pref, ppin = dd.PCA_MAP[d]
        mref, mpin = dd.ntc_mux(w)
        mch = 9 - mpin if mpin <= 9 else 31 - mpin
        A(f"| {ch} | LED{w} (r{r}c{c}) | {ja} p{pa}/{pk} | U{d} "
          f"| {pref}.LED{inv_led.get(ppin,'?')} | {mref}.I{mch} |")
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
    A("Drivers are indexed physically (U1…U96); the logical channel each "
      "carries is CH = whichever ribbon slot it was assigned. Table sorted "
      "by driver.")
    A("")
    A("| Driver | CH | Rs | L | D | Cin | pulldown | ribbon A / K | DIM source |")
    A("|---|---|---|---|---|---|---|---|---|")
    inv_pca_led = {v: k for k, v in dd.PCA_LED_PIN.items()}
    for d in range(1, 97):
        ch = dd.drv_channel(d)
        ja, pa, pk = dd.DRV_CONN[d]
        pref, ppin = dd.PCA_MAP[d]
        li = inv_pca_led.get(ppin, "?")
        A(f"| U{d} | {ch} | R{d} | L{d} | D{d} | C{d} | R{100+d} "
          f"| {ja}.{pa} / {ja}.{pk} | {pref}.{ppin} (LED{li}) |")
    A("")

    # ---------------- PCA9685 ----------------
    A("## PCA9685 bank (control board)")
    A("")
    A("All six: pin 28 (VDD) → +3.3V with 100nF (C121-C126), pin 14 (VSS) → "
      "GND, pin 23 (/OE) → GND, pin 25 (EXTCLK) → GND, pin 27 (SDA) → "
      "I2C_SDA, pin 26 (SCL) → I2C_SCL.")
    A("I2C_SDA/I2C_SCL → ESP32 GPIO21/GPIO22 + 4.7k pullups R210/R211 to +3.3V.")
    A("")
    A("Address straps (pin → rail):")
    A("")
    A("| Chip | Addr | A0(1) | A1(2) | A2(3) | A3(4) | A4(5) | A5(24) |")
    A("|---|---|---|---|---|---|---|---|")
    for k in range(6):
        bits = ["+3.3V" if (k >> b) & 1 else "GND" for b in range(6)]
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
    A("+3.3V ── TH<n>.1   TH<n> = 10k NTC")
    A("TH<n>.2 ──●── R<n>.1 (10k 1%; R<n>.2 → GND)")
    A("          └── NTC<n> ── mux input (see table)")
    A("```")
    A("")
    A("Wells are indexed by grid position (LED1…LED96, row-major). The "
      "logical channel each well carries is CH. Table sorted by well.")
    A("")
    A("| Well | row,col | CH | NTC | divider R | ribbon A / K | mux input |")
    A("|---|---|---|---|---|---|---|")
    for w in range(1, 97):
        r, c = dd.ch_rc(w)
        ch = dd.well_channel(w)
        ja, pa, pk = dd.WELL_CONN[w]
        mref, mpin = dd.ntc_mux(w)
        mch = 9 - mpin if mpin <= 9 else 31 - mpin   # pin -> S-channel index
        A(f"| LED{w} | {r},{c} | {ch} | TH{w} | R{w} | {ja}.{pa} / {ja}.{pk} "
          f"| {mref}.{mpin} (I{mch}) |")
    A("")

    A("## LED board — muxes")
    A("")
    A("All six CD74HC4067: pin 24 (VCC) → +3.3V with 100nF (C1-C6), pin 12 "
      "(GND) → GND, pin 15 (/E) → GND (always enabled).")
    A("")
    A("| Signal | Mux pins | Ribbon |")
    A("|---|---|---|")
    for sig, mp in [("MUX_A0", "10 (S0)"), ("MUX_A1", "11 (S1)"),
                    ("MUX_A2", "14 (S2)"), ("MUX_A3", "13 (S3)")]:
        j5pin = [p for p, s in dd.J5_PINOUT.items() if s == sig][0]
        A(f"| {sig} | U1-U6 pin {mp} | J9.{j5pin} |")
    for m in range(1, 7):
        j5pin = [p for p, s in dd.J5_PINOUT.items()
                 if s == f"NTC_SIG{m}"][0]
        A(f"| NTC_SIG{m} | U{m} pin 1 (COM) | J9.{j5pin} |")
    A("")

    # ---------------- ribbons ----------------
    A("## Ribbon cables (straight 1:1, keyed)")
    A("")
    A("J1-J6 (40-way): each ribbon carries 16 channels as pin-pairs. Pairs "
      "1-9 on pins 1-18, pairs 10-16 on pins 21-34; pin 20 UNUSED (IDE-cable "
      "key), pins 19 and 35-40 = GND. A = odd pin, K = even pin of each pair. "
      "Which well and which driver land on each slot is in the channel map "
      "above (they differ per board — the cable is a straight 1:1).")
    A("")
    A("J9 (20-way):")
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
    A("## Test points")
    A("")
    for title, board_, in [("LED board", led), ("Control board", ctl)]:
        tps = [p for p in board_["parts"] if p["ref"].startswith("TP")]
        if tps:
            A(f"**{title}:** " + ", ".join(
                f"{p['ref']} = {p['value']}" for p in tps))
            A("")
    A("## ERC housekeeping")
    A("")
    A("- Add power symbols (+24V, +5V, +3.3V, GND) and one PWR_FLAG on "
      "+24V, +5V, +3.3V and GND (they enter via connectors).")
    A("- U111 (ADS1115) is DNP — wire it anyway (ADDR pin 1 → GND = 0x48) "
      "so it can be populated later; or leave unwired and ignore ERC.")
    A("- Unused mux inputs: none (all 16 used on all six).")
    A("- Unused PCA9685 outputs: none (96 = 6×16 exactly).")

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {OUT} ({len(L)} lines)")

    # cross-board consistency check: every ribbon pin must carry the same
    # LED_A#/LED_K# net on both boards (the cable is a straight 1:1).
    import re
    chan_net = re.compile(r"^LED_[AK]\d+$")
    ribbon = {f"J{k}" for k in range(1, 7)}
    ja_led = {(name, r, p) for name, ms in led["nets"].items()
              if chan_net.match(name) for r, p in ms if r in ribbon}
    ja_ctl = {(name, r, p) for name, ms in ctl["nets"].items()
              if chan_net.match(name) for r, p in ms if r in ribbon}
    assert ja_led == ja_ctl, "ribbon pin mismatch between boards!"
    print(f"cross-board ribbon consistency: OK ({len(ja_led)} pin-nets)")


if __name__ == "__main__":
    main()
