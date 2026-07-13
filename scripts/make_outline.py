"""Draw a board outline around the user's LED board placement.

- Relocates stray mounting holes H2/H4/H5 (still at old draft coords)
- Deletes the old draft Edge.Cuts rectangle
- Adds a rounded-rectangle outline = footprint-bbox + margin

Run with KiCad python:
  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" make_outline.py
"""
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
BOARD = ROOT / "12x8 Led Array 9mm pitch" / "12x8 Led Array 9mm pitch.kicad_pcb"
MARGIN = 4.0     # mm beyond outermost footprint copper/courtyard
RADIUS = 3.0     # corner radius


def mm(v):
    return pcbnew.FromMM(v)


def tomm(v):
    return pcbnew.ToMM(v)


board = pcbnew.LoadBoard(str(BOARD))

# 1. relocate stray holes (chosen to be clear of muxes/connectors/TPs)
strays = {"H2": (52.0, 128.0), "H4": (227.0, 128.0), "H5": (196.0, 32.0)}
for fp in board.GetFootprints():
    r = fp.GetReference()
    if r in strays:
        fp.SetPosition(pcbnew.VECTOR2I(mm(strays[r][0]), mm(strays[r][1])))
        print(f"moved {r} -> {strays[r]}")

# 2. bbox of all footprints (no text)
x0 = y0 = 1e18
x1 = y1 = -1e18
for fp in board.GetFootprints():
    bb = fp.GetBoundingBox(False)
    x0 = min(x0, tomm(bb.GetLeft()))
    y0 = min(y0, tomm(bb.GetTop()))
    x1 = max(x1, tomm(bb.GetRight()))
    y1 = max(y1, tomm(bb.GetBottom()))
print(f"footprint extents: ({x0:.1f},{y0:.1f}) - ({x1:.1f},{y1:.1f})")
x0, y0, x1, y1 = (round(x0 - MARGIN, 1), round(y0 - MARGIN, 1),
                  round(x1 + MARGIN, 1), round(y1 + MARGIN, 1))
print(f"outline: ({x0},{y0}) - ({x1},{y1})  = {x1-x0:.1f} x {y1-y0:.1f} mm")

# 3. delete existing Edge.Cuts shapes
for d in list(board.GetDrawings()):
    if isinstance(d, pcbnew.PCB_SHAPE) and d.GetLayer() == pcbnew.Edge_Cuts:
        board.Remove(d)
        print("removed old Edge.Cuts", d.GetShapeStr())

# 4. rounded rect
r = RADIUS


def seg(ax, ay, bx, by):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pcbnew.VECTOR2I(mm(ax), mm(ay)))
    s.SetEnd(pcbnew.VECTOR2I(mm(bx), mm(by)))
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(mm(0.1))
    board.Add(s)


def arc(cx, cy, sx, sy, angle_deg):
    a = pcbnew.PCB_SHAPE(board)
    a.SetShape(pcbnew.SHAPE_T_ARC)
    a.SetCenter(pcbnew.VECTOR2I(mm(cx), mm(cy)))
    a.SetStart(pcbnew.VECTOR2I(mm(sx), mm(sy)))
    a.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(angle_deg, pcbnew.DEGREES_T), False)
    a.SetLayer(pcbnew.Edge_Cuts)
    a.SetWidth(mm(0.1))
    board.Add(a)


seg(x0 + r, y0, x1 - r, y0)                 # top
arc(x1 - r, y0 + r, x1 - r, y0, 90)         # top-right
seg(x1, y0 + r, x1, y1 - r)                 # right
arc(x1 - r, y1 - r, x1, y1 - r, 90)         # bottom-right
seg(x1 - r, y1, x0 + r, y1)                 # bottom
arc(x0 + r, y1 - r, x0 + r, y1, 90)         # bottom-left
seg(x0, y1 - r, x0, y0 + r)                 # left
arc(x0 + r, y0 + r, x0, y0 + r, 90)         # top-left

pcbnew.SaveBoard(str(BOARD), board)
print("saved")
