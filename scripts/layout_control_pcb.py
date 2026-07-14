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
FY = lambda r: 40.0 + (r - 1) * 12.0


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
    "J2": (30.0, 26.5, 90), "J1": (116.0, 26.5, 90),
    "J3": (37.2, 136.8, 90), "J4": (110.0, 136.8, 90),
    "J5": (14.0, 80.15, 180),
    "U101": (24.0, 47.0, 90), "U102": (24.0, 71.0, 90),
    "U103": (24.0, 95.0, 90),
    "C121": (32.0, 47.0, 0), "C122": (32.0, 71.0, 0), "C123": (32.0, 95.0, 0),
    "J10": (184.0, 46.0, 0), "J11": (209.4, 46.0, 0),
    "R210": (196.0, 92.0, 0), "R211": (196.0, 95.0, 0),
    "U104": (184.0, 112.0, 90), "U105": (184.0, 124.0, 90),
    "U106": (184.0, 136.0, 90),
    "C124": (192.0, 112.0, 0), "C125": (192.0, 124.0, 0),
    "C126": (192.0, 136.0, 0),
    "J6": (10.0, 143.0, 180), "J7": (10.0, 131.0, 180),
    "U110": (20.0, 106.0, 0), "L101": (20.0, 114.0, 0),
    "D101": (20.0, 121.5, 0), "C110": (28.5, 105.0, 90),
    "C111": (28.5, 115.0, 90),
    "C101": (8.0, 17.5, 90), "C102": (18.0, 17.5, 90),
    "C103": (8.0, 30.5, 90), "C104": (18.0, 30.5, 90),
    "SW1": (198.0, 145.0, 0), "SW2": (205.5, 145.0, 0), "SW3": (213.0, 145.0, 0),
    "LED1": (198.0, 138.5, 0), "LED2": (205.5, 138.5, 0), "LED3": (213.0, 138.5, 0),
    "R203": (198.0, 135.5, 0), "R204": (205.5, 135.5, 0), "R205": (213.0, 135.5, 0),
    "J8": (208.0, 122.0, 90), "Q1": (200.0, 122.0, 0),
    "R201": (196.0, 118.0, 90), "R202": (196.0, 126.0, 90),
    "D102": (204.0, 128.5, 0),
    "U111": (200.0, 100.0, 0),
    "TP1": (196.0, 18.0, 0), "TP2": (201.0, 18.0, 0), "TP3": (206.0, 18.0, 0),
    "TP4": (211.0, 18.0, 0), "TP5": (196.0, 22.5, 0), "TP6": (201.0, 22.5, 0),
    "TP7": (206.0, 22.5, 0), "TP8": (211.0, 22.5, 0), "TP9": (196.0, 27.0, 0),
    "TP10": (201.0, 27.0, 0), "TP11": (206.0, 27.0, 0), "TP12": (211.0, 27.0, 0),
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
