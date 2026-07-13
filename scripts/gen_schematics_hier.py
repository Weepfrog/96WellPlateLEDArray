"""Hierarchical schematic generator.

Each board = root sheet + ONE sub-sheet instantiated 96x:
  LED board:     well.kicad_sch     (LED + NTC + divider R, pre-wired)
  control board: channel.kicad_sch  (PT4115 + Rs + L + D + Cin + pulldown, pre-wired)

Reference designators per instance match design_data (LED1..96, U1..96, ...),
so CONNECTIONS.md, the BOM and the PCB generator stay valid. Root-level
symbols (muxes, PCA9685s, power, ESP32 socket, UI, connectors) carry a net
label on every connected pin and a no-connect marker on unused pins, so the
whole design is electrically complete and verifiable with ERC/netlist.

Run:  python gen_schematics_hier.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_data as dd
import gen_schematics as gs
from gen_schematics import esc, suuid, extract_symbol

ROOT = Path(__file__).resolve().parent.parent
SCH_VERSION, GEN_VERSION = "20260306", "10.0"
FONT = "(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t)"


def pin_geo(lib_id):
    """{number: (x, y, angle)} in symbol coords (y up)."""
    block, _ = extract_symbol(lib_id)
    out = {}
    for m in re.finditer(
            r'\(pin\s+\S+\s+\S+\s*\(at\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\)'
            r'\s*\(length\s+[-\d.]+\)[\s\S]*?\(number\s+"([^"]*)"', block):
        out[m.group(4)] = (float(m.group(1)), float(m.group(2)),
                           float(m.group(3)))
    return out


def pin_abs(origin, geo, rot=0):
    """Absolute sheet coords of a pin (sheet y is down)."""
    x0, y0 = origin
    px, py, pang = geo
    if rot == 0:
        return (round(x0 + px, 4), round(y0 - py, 4), pang)
    if rot == 180:
        return (round(x0 - px, 4), round(y0 + py, 4), (pang + 180) % 360)
    if rot == 90:   # 90 CCW
        return (round(x0 + py, 4), round(y0 + px, 4), (pang + 90) % 360)
    if rot == 270:
        return (round(x0 - py, 4), round(y0 - px, 4), (pang + 270) % 360)
    raise ValueError(rot)


class Emitter:
    def __init__(self, project, fname):
        self.project = project
        self.fname = fname
        self.uuid = suuid(project, fname, "root")
        self.libs = {}          # lib_id -> block
        self.pins = {}          # lib_id -> {num: name}
        self.geo = {}           # lib_id -> {num: (x,y,ang)}
        self.body = []
        self.k = 0

    def key(self):
        self.k += 1
        return suuid(self.project, self.fname, self.k)

    def use(self, lib_id):
        if lib_id not in self.libs:
            block, pins = extract_symbol(lib_id)
            self.libs[lib_id] = block
            self.pins[lib_id] = pins
            self.geo[lib_id] = pin_geo(lib_id)

    def wire(self, a, b):
        self.body.append(
            f"\t(wire\n\t\t(pts\n\t\t\t(xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})"
            f"\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n"
            f"\t\t)\n\t\t(uuid \"{self.key()}\")\n\t)")

    def junction(self, p):
        self.body.append(
            f"\t(junction\n\t\t(at {p[0]} {p[1]})\n\t\t(diameter 0)\n"
            f"\t\t(color 0 0 0 0)\n\t\t(uuid \"{self.key()}\")\n\t)")

    def label(self, name, p, rot=0):
        self.body.append(
            f"\t(label \"{esc(name)}\"\n\t\t(at {p[0]} {p[1]} {rot})\n"
            f"\t\t{FONT}\n\t\t(uuid \"{self.key()}\")\n\t)")

    def hlabel(self, name, p, rot=0):
        self.body.append(
            f"\t(hierarchical_label \"{esc(name)}\"\n\t\t(shape passive)\n"
            f"\t\t(at {p[0]} {p[1]} {rot})\n\t\t{FONT}\n"
            f"\t\t(uuid \"{self.key()}\")\n\t)")

    def no_connect(self, p):
        self.body.append(
            f"\t(no_connect\n\t\t(at {p[0]} {p[1]})\n"
            f"\t\t(uuid \"{self.key()}\")\n\t)")

    def text(self, s, x, y, size=2.0):
        self.body.append(
            f"\t(text \"{esc(s)}\"\n\t\t(exclude_from_sim no)\n"
            f"\t\t(at {x} {y} 0)\n\t\t(effects\n\t\t\t(font\n"
            f"\t\t\t\t(size {size} {size})\n\t\t\t)\n"
            f"\t\t\t(justify left bottom)\n\t\t)\n"
            f"\t\t(uuid \"{self.key()}\")\n\t)")

    def symbol(self, p, instances, rot=0, uid=None):
        """instances = [(path, reference)]"""
        self.use(p["lib_id"])
        x, y = p["sch_xy"]
        su = uid or suuid(self.project, self.fname, "sym", p["ref"])
        lines = [
            "\t(symbol",
            f'\t\t(lib_id "{p["lib_id"]}")',
            f"\t\t(at {x} {y} {rot})",
            "\t\t(unit 1)",
            "\t\t(exclude_from_sim no)",
            "\t\t(in_bom yes)",
            "\t\t(on_board yes)",
            f'\t\t(dnp {"yes" if p.get("dnp") else "no"})',
            f'\t\t(uuid "{su}")',
        ]

        def prop(name, val, dy, hide):
            lines.append(f'\t\t(property "{esc(name)}" "{esc(val)}"')
            lines.append(f"\t\t\t(at {round(x + 2.54, 3)} {round(y + dy, 3)} 0)")
            lines.append("\t\t\t(effects")
            lines.append("\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)")
            lines.append("\t\t\t\t(justify left)")
            if hide:
                lines.append("\t\t\t\t(hide yes)")
            lines.append("\t\t\t)")
            lines.append("\t\t)")

        prop("Reference", instances[0][1], -5.08, False)
        prop("Value", p["value"], -2.54, False)
        prop("Footprint", p.get("footprint") or "", 0, True)
        prop("Datasheet", "~", 2.54, True)
        if p.get("lcsc"):
            prop("LCSC", p["lcsc"], 5.08, True)
        for num in self.pins[p["lib_id"]]:
            lines.append(f'\t\t(pin "{esc(num)}"')
            lines.append(f'\t\t\t(uuid "{self.key()}")')
            lines.append("\t\t)")
        lines.append("\t\t(instances")
        lines.append(f'\t\t\t(project "{esc(self.project)}"')
        for path, ref in instances:
            lines.append(f'\t\t\t\t(path "{path}"')
            lines.append(f'\t\t\t\t\t(reference "{esc(ref)}")')
            lines.append("\t\t\t\t\t(unit 1)")
            lines.append("\t\t\t\t)")
        lines.append("\t\t\t)")
        lines.append("\t\t)")
        lines.append("\t)")
        self.body.append("\n".join(lines))
        return su

    def sheet(self, name, file, x, y, w, h, pins, page, root_uuid, uid):
        lines = [
            "\t(sheet",
            f"\t\t(at {x} {y})",
            f"\t\t(size {w} {h})",
            "\t\t(exclude_from_sim no)",
            "\t\t(in_bom yes)",
            "\t\t(on_board yes)",
            "\t\t(dnp no)",
            "\t\t(stroke\n\t\t\t(width 0.1524)\n\t\t\t(type solid)\n\t\t)",
            "\t\t(fill\n\t\t\t(color 0 0 0 0.0000)\n\t\t)",
            f'\t\t(uuid "{uid}")',
            f'\t\t(property "Sheetname" "{esc(name)}"',
            f"\t\t\t(at {x} {round(y - 0.8, 3)} 0)",
            "\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n"
            "\t\t\t\t)\n\t\t\t\t(justify left bottom)\n\t\t\t)",
            "\t\t)",
            f'\t\t(property "Sheetfile" "{esc(file)}"',
            f"\t\t\t(at {x} {round(y + h + 0.8, 3)} 0)",
            "\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n"
            "\t\t\t\t)\n\t\t\t\t(justify left top)\n\t\t\t\t(hide yes)\n"
            "\t\t\t)",
            "\t\t)",
        ]
        for pname, px, py in pins:
            lines.append(f'\t\t(pin "{esc(pname)}" passive')
            lines.append(f"\t\t\t(at {px} {py} 0)")
            lines.append("\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t"
                         "(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t"
                         "(justify right)\n\t\t\t)")
            lines.append(f'\t\t\t(uuid "{self.key()}")')
            lines.append("\t\t)")
        lines.append("\t\t(instances")
        lines.append(f'\t\t\t(project "{esc(self.project)}"')
        lines.append(f'\t\t\t\t(path "/{root_uuid}"')
        lines.append(f'\t\t\t\t\t(page "{page}")')
        lines.append("\t\t\t\t)")
        lines.append("\t\t\t)")
        lines.append("\t\t)")
        lines.append("\t)")
        self.body.append("\n".join(lines))

    def write(self, path, paper, title):
        chunks = [
            "(kicad_sch",
            f"\t(version {SCH_VERSION})",
            '\t(generator "eeschema")',
            f'\t(generator_version "{GEN_VERSION}")',
            f'\t(uuid "{self.uuid}")',
            f'\t(paper "{paper}")',
            "\t(title_block",
            f'\t\t(title "{esc(title)}")',
            '\t\t(date "2026-07-13")',
            "\t)",
            "\t(lib_symbols",
        ]
        for block in self.libs.values():
            chunks.append("\t\t" + block.replace("\n", "\n\t\t"))
        chunks.append("\t)")
        chunks += self.body
        chunks += [
            "\t(sheet_instances",
            '\t\t(path "/"',
            '\t\t\t(page "1")',
            "\t\t)",
            "\t)",
            "\t(embedded_fonts no)",
            ")",
            "",
        ]
        path.write_text("\n".join(chunks), encoding="utf-8")
        print(f"wrote {path}")


def P(lib, value, ref, fp="", lcsc="", xy=(0, 0), dnp=False):
    return dict(lib_id=lib, value=value, ref=ref, footprint=fp, lcsc=lcsc,
                sch_xy=xy, dnp=dnp)


# =============================================================== WELL SHEET

def build_well_sheet(project, root_uuid, sheet_uuids, parts_by_ref):
    e = Emitter(project, "well")
    inst = lambda base: [(f"/{root_uuid}/{sheet_uuids[n]}", f"{base}{n}")
                         for n in range(1, 97)]

    led = dict(parts_by_ref["LED1"]);  led["sch_xy"] = (76.2, 63.5)
    th = dict(parts_by_ref["TH1"]);    th["sch_xy"] = (114.3, 55.88)
    r = dict(parts_by_ref["R1"]);      r["sch_xy"] = (114.3, 71.12)
    e.symbol(led, inst("LED"))
    e.symbol(th, inst("TH"))
    e.symbol(r, inst("R"))

    # LED pins: 1 (81.28,64.77) 2 (71.12,64.77) 3 (76.2,62.23)
    e.wire((81.28, 64.77), (86.36, 64.77))
    e.hlabel("LED_A", (86.36, 64.77), 0)
    e.wire((71.12, 64.77), (66.04, 64.77))
    e.hlabel("LED_K", (66.04, 64.77), 180)
    e.wire((76.2, 62.23), (76.2, 58.42))
    e.wire((76.2, 58.42), (66.04, 58.42))
    e.wire((66.04, 58.42), (66.04, 64.77))
    e.junction((66.04, 64.77))
    # NTC divider
    pwr3 = P("power:+3V3", "+3V3", "#PWR?", xy=(114.3, 49.53))
    gnd = P("power:GND", "GND", "#PWR?", xy=(114.3, 77.47))
    e.symbol(pwr3, inst("#PWR01"), uid=suuid(project, "well", "pwr3v3"))
    e.symbol(gnd, inst("#PWR02"), uid=suuid(project, "well", "pwrgnd"))
    e.wire((114.3, 52.07), (114.3, 49.53))
    e.wire((114.3, 59.69), (114.3, 63.5))
    e.wire((114.3, 63.5), (114.3, 67.31))
    e.wire((114.3, 63.5), (121.92, 63.5))
    e.junction((114.3, 63.5))
    e.hlabel("NTC_OUT", (121.92, 63.5), 0)
    e.wire((114.3, 74.93), (114.3, 77.47))
    e.text("One well: 660nm LED (pad3 thermal tied to cathode) + "
           "10k NTC / 10k 1% divider from 3V3.", 25.4, 25.4, 2.0)
    e.text("Instantiated 96x from the root sheet (CH01..CH96).",
           25.4, 30.48, 2.0)
    return e


# ============================================================ CHANNEL SHEET

def build_channel_sheet(project, root_uuid, sheet_uuids, parts_by_ref):
    e = Emitter(project, "channel")
    inst = lambda base, off=0: [
        (f"/{root_uuid}/{sheet_uuids[n]}", f"{base}{n + off}")
        for n in range(1, 97)]

    u = dict(parts_by_ref["U1"]);    u["sch_xy"] = (127, 76.2)
    rs = dict(parts_by_ref["R1"]);   rs["sch_xy"] = (147.32, 60.96)
    ln = dict(parts_by_ref["L1"]);   ln["sch_xy"] = (104.14, 82.55)
    dio = dict(parts_by_ref["D1"]);  dio["sch_xy"] = (127, 90.17)
    cin = dict(parts_by_ref["C1"]);  cin["sch_xy"] = (162.56, 66.04)
    rpd = dict(parts_by_ref["R101"]); rpd["sch_xy"] = (114.3, 102.87)

    e.symbol(u, inst("U"))
    e.symbol(rs, inst("R"))
    e.symbol(ln, inst("L"))
    e.symbol(dio, inst("D"), rot=180)
    e.symbol(cin, inst("C"))
    e.symbol(rpd, inst("R", 100))

    for i, xy in enumerate([(147.32, 54.61), (139.7, 66.04), (162.56, 59.69),
                            (135.89, 90.17)]):
        e.symbol(P("power:+24V", "+24V", "#PWR?", xy=xy),
                 [(f"/{root_uuid}/{sheet_uuids[n]}", f"#PWRA{i}{n:03d}")
                  for n in range(1, 97)],
                 uid=suuid(e.project, "channel", "pwr24", i))
    for i, xy in enumerate([(162.56, 72.39), (114.3, 109.22),
                            (111.76, 101.6)]):
        e.symbol(P("power:GND", "GND", "#PWR?", xy=xy),
                 [(f"/{root_uuid}/{sheet_uuids[n]}", f"#PWRG{i}{n:03d}")
                  for n in range(1, 97)],
                 uid=suuid(e.project, "channel", "pwrgnd", i))

    # Rs: +24V -> Rs -> CSN node (= LED_A)
    e.wire((147.32, 57.15), (147.32, 54.61))
    e.wire((147.32, 64.77), (147.32, 78.74))
    e.wire((147.32, 78.74), (137.16, 78.74))       # to CSN (U pin 4)
    e.wire((147.32, 78.74), (154.94, 78.74))
    e.junction((147.32, 78.74))
    e.hlabel("LED_A", (154.94, 78.74), 0)
    # VIN
    e.wire((137.16, 73.66), (139.7, 73.66))
    e.wire((139.7, 73.66), (139.7, 66.04))
    # input cap
    e.wire((162.56, 62.23), (162.56, 59.69))
    e.wire((162.56, 69.85), (162.56, 72.39))
    # SW node: U.1 -> L.1, D anode riser joins mid-wire
    e.wire((116.84, 73.66), (104.14, 73.66))
    e.wire((104.14, 73.66), (104.14, 78.74))
    e.wire((123.19, 90.17), (106.68, 90.17))       # D anode (rot180 -> pin2 left)
    e.wire((106.68, 90.17), (106.68, 73.66))
    e.junction((106.68, 73.66))
    e.wire((130.81, 90.17), (135.89, 90.17))       # D cathode -> +24V
    # LED_K from L.2
    e.wire((104.14, 86.36), (104.14, 93.98))
    e.hlabel("LED_K", (104.14, 93.98), 270)
    # DIM: U.3 -> label + pulldown
    e.wire((116.84, 78.74), (114.3, 78.74))
    e.wire((114.3, 78.74), (114.3, 93.98))
    e.wire((114.3, 93.98), (121.92, 93.98))
    e.hlabel("DIM", (121.92, 93.98), 0)
    e.wire((114.3, 93.98), (114.3, 99.06))
    e.junction((114.3, 93.98))
    e.wire((114.3, 106.68), (114.3, 109.22))
    # U GND
    e.wire((116.84, 76.2), (111.76, 76.2))
    e.wire((111.76, 76.2), (111.76, 101.6))

    e.text("One channel: PT4115 buck CC @ 256mA (Rs=0.39R). "
           "SS34 band to +24V. DIM: 100k pulldown = dark boot.",
           25.4, 25.4, 2.0)
    e.text("LED_A/LED_K go to the ribbon; wire crossings without "
           "junction dots are NOT connected.", 25.4, 30.48, 2.0)
    return e


# ================================================================== ROOTS

def netmap(board):
    m = {}
    for name, members in board["nets"].items():
        for ref, pin in members:
            m[(ref, pin)] = name
    return m


def place_root(e, board, root_uuid, sub_file, sub_pins, chan_refs,
               root_pos, texts):
    nm = netmap(board)
    # 96 sheet boxes
    sheet_uuids = {}
    for n in range(1, 97):
        r, c = dd.ch_rc(n)
        x = dd.snap(25.4 + (c - 1) * 35.56)
        y = dd.snap(25.4 + (r - 1) * 27.94)
        w, h = 17.78, 12.7
        uid = suuid(e.project, "sheetinst", n)
        sheet_uuids[n] = uid
        pins = []
        for i, pname in enumerate(sub_pins):
            py = dd.snap(y + 3.81 + i * 2.54)
            pins.append((pname, dd.snap(x + w), py))
        e.sheet(f"CH{n:02d}", sub_file, x, y, w, h, pins, page=n + 1,
                root_uuid=root_uuid, uid=uid)
        for i, pname in enumerate(sub_pins):
            py = dd.snap(y + 3.81 + i * 2.54)
            px = dd.snap(x + w)
            e.wire((px, py), (dd.snap(px + 3.81), py))
            e.label(chan_refs(n)[i], (dd.snap(px + 3.81), py), 0)
    # root singletons with labels / no-connects on every pin
    for p in board["parts"]:
        ref = p["ref"]
        if ref not in root_pos or not p["lib_id"]:
            continue
        q = dict(p)
        q["sch_xy"] = root_pos[ref]
        e.symbol(q, [(f"/{root_uuid}", ref)])
        geo = e.geo[p["lib_id"]]
        for num, g in geo.items():
            pt = pin_abs(root_pos[ref], g, 0)
            net = nm.get((ref, num))
            if net:
                rot = int((pt[2] + 180) % 360)
                e.label(net, (pt[0], pt[1]), rot)
            else:
                e.no_connect((pt[0], pt[1]))
    for t in texts:
        e.text(*t)
    return sheet_uuids


def power_corner(e, project, root_uuid, rails, x0, y0):
    for i, rail in enumerate(rails):
        x = dd.snap(x0 + i * 20.32)
        lib = f"power:{rail}" if rail != "GND" else "power:GND"
        e.symbol(P(lib, rail, f"#PWR_{rail}", xy=(x, y0)),
                 [(f"/{root_uuid}", f"#PWR1{i:02d}")])
        e.symbol(P("power:PWR_FLAG", "PWR_FLAG", f"#FLG{i}", xy=(x, y0)),
                 [(f"/{root_uuid}", f"#FLG1{i:02d}")])


def main():
    led = dd.build_led_board()
    ctl = dd.build_control_board()

    # ---------------- LED board ----------------
    proj = led["name"]
    led_dir = ROOT / "12x8 Led Array 9mm pitch"
    root = Emitter(proj, "root")
    root_uuid = root.uuid
    led_parts = {p["ref"]: p for p in led["parts"]}

    led_pos = {}
    for m in range(1, 7):
        led_pos[f"U{m}"] = (dd.snap(38.1 + (m - 1) * 76.2), 304.8)
        led_pos[f"C{m}"] = (dd.snap(63.5 + (m - 1) * 76.2), 287.02)
    for j in range(1, 5):
        led_pos[f"J{j}"] = (dd.snap(495.3 + (j - 1) * 25.4), 266.7)
    led_pos["J5"] = (571.5, 355.6)

    sheet_uuids = place_root(
        root, led, root_uuid, "well.kicad_sch",
        ["LED_A", "LED_K", "NTC_OUT"],
        lambda n: [f"LED_A{n}", f"LED_K{n}", f"NTC{n}"],
        led_pos,
        texts=[("96 WELLS (CH01..CH96) - see well.kicad_sch", 25.4, 22.86, 2.5),
               ("NTC MUXES U1-U6 (ch 1-16 / 17-32 / 33-48 / 49-64 / 65-80 / 81-96)",
                25.4, 273.05, 2.5),
               ("RIBBONS TO CONTROL BOARD", 490.22, 227.33, 2.5)])
    power_corner(root, proj, root_uuid, ["+3V3", "GND"], 30.48, 388.62)
    root.write(led_dir / "12x8 Led Array 9mm pitch.kicad_sch", "A2",
               led["title"])

    well = build_well_sheet(proj, root_uuid, sheet_uuids, led_parts)
    well.write(led_dir / "well.kicad_sch", "A4", "Well: LED + NTC")

    meta = {}
    for n in range(1, 97):
        for base in ("LED", "TH", "R"):
            meta[f"{base}{n}"] = {
                "path": f"/{root_uuid}/{sheet_uuids[n]}/"
                        + suuid(proj, "well", "sym", f"{base}1")}
    for ref in led_pos:
        meta[ref] = {"path": f"/{root_uuid}/"
                     + suuid(proj, "root", "sym", ref)}
    meta["__root__"] = root_uuid
    (led_dir / "sch_meta.json").write_text(json.dumps(meta, indent=1),
                                           encoding="utf-8")

    # ---------------- control board ----------------
    proj = ctl["name"]
    ctl_dir = ROOT / "control-board"
    root = Emitter(proj, "root")
    root_uuid = root.uuid
    ctl_parts = {p["ref"]: p for p in ctl["parts"]}

    pos = {}
    for k in range(6):
        pos[f"U{101 + k}"] = (dd.snap(38.1 + k * 76.2), 330.2)
        pos[f"C{121 + k}"] = (dd.snap(68.58 + k * 76.2), 306.07)
    pos.update({
        "C110": (25.4, 448.31), "U110": (76.2, 447.04),
        "L101": (127, 448.31), "D101": (127, 471.17),
        "C111": (154.94, 448.31),
        "C101": (190.5, 448.31), "C102": (210.82, 448.31),
        "C103": (231.14, 448.31), "C104": (251.46, 448.31),
        "J6": (281.94, 448.31), "J7": (317.5, 448.31),
        "R201": (508, 477.52), "Q1": (533.4, 477.52),
        "R202": (558.8, 477.52), "D102": (584.2, 477.52),
        "J8": (609.6, 477.52),
        "SW1": (508, 431.8), "SW2": (546.1, 431.8), "SW3": (584.2, 431.8),
        "LED1": (508, 406.4), "LED2": (546.1, 406.4), "LED3": (584.2, 406.4),
        "R203": (508, 383.54), "R204": (546.1, 383.54), "R205": (584.2, 383.54),
        "R210": (698.5, 431.8), "R211": (723.9, 431.8),
        "U111": (698.5, 477.52),
        "J10": (749.3, 330.2), "J11": (800.1, 330.2),
        "J1": (711.2, 63.5), "J2": (736.6, 63.5), "J3": (762, 63.5),
        "J4": (787.4, 63.5), "J5": (812.8, 152.4),
    })

    sheet_uuids = place_root(
        root, ctl, root_uuid, "channel.kicad_sch",
        ["LED_A", "LED_K", "DIM"],
        lambda n: [f"LED_A{n}", f"LED_K{n}", f"DIM{n}"],
        pos,
        texts=[("96 DRIVER CHANNELS (CH01..CH96) - see channel.kicad_sch",
                25.4, 22.86, 2.5),
               ("PCA9685 PWM BANK 0x40-0x45", 25.4, 298.45, 2.5),
               ("5V RAIL + 24V INPUT", 25.4, 421.64, 2.5),
               ("UI", 508, 375.92, 2.5),
               ("FAN", 508, 469.9, 2.5),
               ("ESP32 DEVKITC-38 SOCKET (J10 left / J11 right, "
                "pin1 = 3V3/GND end)", 693.42, 298.45, 2.5),
               ("RIBBONS TO LED BOARD", 706.12, 22.86, 2.5)])
    power_corner(root, proj, root_uuid, ["+24V", "+5V", "+3V3", "GND"],
                 30.48, 552.45)
    root.write(ctl_dir / "control-board.kicad_sch", "A1", ctl["title"])

    chan = build_channel_sheet(proj, root_uuid, sheet_uuids, ctl_parts)
    chan.write(ctl_dir / "channel.kicad_sch", "A4",
               "Channel: PT4115 buck 256mA")

    meta = {}
    for n in range(1, 97):
        for base, off in (("U", 0), ("R", 0), ("L", 0), ("D", 0), ("C", 0),
                          ("R", 100)):
            ref = f"{base}{n + off}"
            tmpl = f"{base}{1 + off}"
            meta[ref] = {"path": f"/{root_uuid}/{sheet_uuids[n]}/"
                         + suuid(proj, "channel", "sym", tmpl)}
    for ref in pos:
        meta[ref] = {"path": f"/{root_uuid}/"
                     + suuid(proj, "root", "sym", ref)}
    meta["__root__"] = root_uuid
    (ctl_dir / "sch_meta.json").write_text(json.dumps(meta, indent=1),
                                           encoding="utf-8")


if __name__ == "__main__":
    main()
