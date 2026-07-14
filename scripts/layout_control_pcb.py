"""Arrange the control board PCB to mirror the LED board (sandwich stack).

Phases (separate processes to dodge pcbnew SWIG crashes):
  place  - move all footprints, apply schematic netlist, save
  zones  - redraw outline, assign/resize +24V & GND pours, fill, save

Run with KiCad python:
  python.exe layout_control_pcb.py place
  python.exe layout_control_pcb.py zones
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
BOARD = ROOT / "control-board" / "control-board.kicad_pcb"
NETXML = Path(r"C:\Users\housm\AppData\Local\Temp\claude"
              r"\E--Projects-12x8-Led-Array-9mm-pitch"
              r"\6f0e8799-9c3a-42f9-bbd2-5db327b4d5c2\scratchpad\ctl_v3.xml")

mm = pcbnew.FromMM

W, H = 218.0, 137.7
X0, Y0 = 0.0, 11.3
X1, Y1 = X0 + W, Y0 + H
CX = X0 + W / 2
HOLES = {"H1": (CX - 81.35, 16.8), "H3": (CX + 81.35, 16.8),
         "H2": (CX - 81.35, 143.5), "H4": (CX + 81.35, 143.5)}

FX = lambda c: 40.0 + (12 - c) * 12.0
FY = lambda r: 39.5 + (r - 1) * 12.25


def ch_rc(n):
    return ((n - 1) // 12 + 1, (n - 1) % 12 + 1)


def cell_positions(n):
    r, c = ch_rc(n)
    px, py = FX(c), FY(r)
    return {
        f"U{n}":       (px - 3.0, py - 2.8, 0),
        f"L{n}":       (px + 3.3, py - 3.0, 0),
        f"D{n}":       (px - 2.6, py + 2.9, 0),
        f"R{n}":       (px + 2.2, py + 2.9, 90),
        f"C{n}":       (px + 4.4, py + 2.9, 90),
        f"R{100 + n}": (px + 2.2, py + 5.55, 0),
    }


SINGLES = {
    "J2": (96.0, 26.5, 270), "J1": (182.0, 26.5, 270),
    "J3": (103.2, 136.8, 270), "J4": (176.0, 136.8, 270),
    "J5": (14.0, 80.15, 180),
    "U101": (24.0, 46.0, 90), "U102": (24.0, 64.0, 90),
    "U103": (24.0, 82.0, 90),
    "C121": (32.0, 46.0, 0), "C122": (32.0, 64.0, 0), "C123": (32.0, 82.0, 0),
    "J10": (187.5, 46.0, 0), "J11": (212.9, 46.0, 0),
    "R210": (206.0, 52.0, 0), "R211": (206.0, 55.5, 0),
    "U104": (187.5, 100.0, 90), "U105": (187.5, 115.5, 90),
    "U106": (187.5, 130.5, 90),
    "C124": (195.5, 100.0, 0), "C125": (195.5, 115.5, 0),
    "C126": (195.5, 130.5, 0),
    "J6": (10.0, 143.0, 180), "J7": (10.0, 131.0, 180),
    "U110": (19.5, 101.0, 0), "L101": (20.5, 109.0, 0),
    "D101": (20.5, 116.5, 0), "C110": (28.5, 101.0, 90),
    "C111": (28.5, 112.0, 90),
    "C101": (7.0, 103.0, 90), "C102": (7.0, 114.0, 90),
    "C103": (197.0, 109.0, 90), "C104": (206.0, 109.0, 90),
    "SW1": (198.0, 145.0, 0), "SW2": (205.5, 145.0, 0), "SW3": (213.0, 145.0, 0),
    "LED1": (198.0, 138.5, 0), "LED2": (205.5, 138.5, 0), "LED3": (213.0, 138.5, 0),
    "R203": (198.0, 135.5, 0), "R204": (205.5, 135.5, 0), "R205": (213.0, 135.5, 0),
    "J8": (214.0, 122.0, 90), "Q1": (205.0, 122.0, 0),
    "R201": (196.0, 118.0, 90), "R202": (196.0, 126.0, 90),
    "D102": (204.0, 128.5, 0),
    "U111": (203.0, 84.0, 0),
    "TP1": (196.0, 61.0, 0), "TP2": (201.5, 61.0, 0), "TP3": (207.0, 61.0, 0),
    "TP4": (196.0, 66.0, 0), "TP5": (201.5, 66.0, 0), "TP6": (207.0, 66.0, 0),
    "TP7": (196.0, 71.0, 0), "TP8": (201.5, 71.0, 0), "TP9": (207.0, 71.0, 0),
    "TP10": (196.0, 76.0, 0), "TP11": (201.5, 76.0, 0), "TP12": (207.0, 76.0, 0),
}


def do_place(b):
    fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
    target = {}
    for n in range(1, 97):
        target.update(cell_positions(n))
    for r, (x, y, rot) in SINGLES.items():
        target[r] = (x, y, rot)
    for r, (x, y) in HOLES.items():
        target[r] = (x, y, 0)
    missing = [r for r in target if r not in fps]
    if missing:
        print("MISSING:", missing)
    for r, (x, y, rot) in target.items():
        if r in fps:
            fps[r].SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            fps[r].SetOrientationDegrees(rot)
    xml = ET.parse(str(NETXML)).getroot()
    want, netnames = {}, set()
    for net in xml.iter("net"):
        netnames.add(net.get("name"))
        for node in net.iter("node"):
            want[(node.get("ref"), node.get("pin"))] = net.get("name")
    existing = {str(k) for k in b.GetNetsByName().keys()}
    for name in sorted(netnames - existing):
        b.Add(pcbnew.NETINFO_ITEM(b, name))
    names2 = b.GetNetsByName()
    setn = 0
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            key = (fp.GetReference(), pad.GetNumber())
            if key in want:
                pad.SetNetCode(names2[want[key]].GetNetCode())
                setn += 1
    print("pads netted:", setn)
    print("saved:", pcbnew.SaveBoard(str(BOARD), b))


def do_zones(b):
    gnd = b.GetNetsByName()["GND"].GetNetCode()
    p24 = b.GetNetsByName()["+24V"].GetNetCode()
    # zones FIRST - object wrappers go stale after any Remove()
    for z in b.Zones():
        z.SetNetCode(p24 if z.GetLayer() == pcbnew.F_Cu else gnd)
        ol = z.Outline()
        ol.RemoveAllContours()
        idx = ol.NewOutline()
        for (zx, zy) in [(X0 + 3.2, Y0 + 3.2), (X1 - 3.2, Y0 + 3.2),
                         (X1 - 3.2, Y1 - 3.2), (X0 + 3.2, Y1 - 3.2)]:
            ol.Append(mm(zx), mm(zy), idx)
        z.SetMinThickness(mm(0.25))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
        if z.GetLayer() == pcbnew.F_Cu:
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    print("zones set")
    for d in list(b.GetDrawings()):
        if isinstance(d, pcbnew.PCB_SHAPE) and d.GetLayer() == pcbnew.Edge_Cuts:
            b.Remove(d)
    r = 3.0

    def seg(ax, ay, bx, by):
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(mm(ax), mm(ay)))
        s.SetEnd(pcbnew.VECTOR2I(mm(bx), mm(by)))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); b.Add(s)

    def arc(cx2, cy2, sx, sy):
        a = pcbnew.PCB_SHAPE(b)
        a.SetShape(pcbnew.SHAPE_T_ARC)
        a.SetCenter(pcbnew.VECTOR2I(mm(cx2), mm(cy2)))
        a.SetStart(pcbnew.VECTOR2I(mm(sx), mm(sy)))
        a.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(90.0, pcbnew.DEGREES_T), False)
        a.SetLayer(pcbnew.Edge_Cuts); a.SetWidth(mm(0.1)); b.Add(a)

    seg(X0 + r, Y0, X1 - r, Y0)
    arc(X1 - r, Y0 + r, X1 - r, Y0)
    seg(X1, Y0 + r, X1, Y1 - r)
    arc(X1 - r, Y1 - r, X1, Y1 - r)
    seg(X1 - r, Y1, X0 + r, Y1)
    arc(X0 + r, Y1 - r, X0 + r, Y1)
    seg(X0, Y1 - r, X0, Y0 + r)
    arc(X0 + r, Y0 + r, X0, Y0 + r)

    b.BuildConnectivity()
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    print("saved:", pcbnew.SaveBoard(str(BOARD), b))


def main():
    phase = sys.argv[1] if len(sys.argv) > 1 else "place"
    b = pcbnew.LoadBoard(str(BOARD))
    if phase == "place":
        do_place(b)
    elif phase == "zones":
        do_zones(b)


if __name__ == "__main__":
    main()
