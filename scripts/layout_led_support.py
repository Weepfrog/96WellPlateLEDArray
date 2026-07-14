"""Copy the user's control-board topology onto the LED board:

  J1, J4  -> left edge, vertical   (control rot 0  -> LED rot 180)
  J2, J3  -> top edge, horizontal  (control rot -90 -> LED rot 90)
  J5, J6  -> bottom edge           (control rot -90 -> LED rot 90)
  J9      -> right edge, low       (mirrors control J9 at y~115)
  U1-U6   -> right strip, stacked horizontal (like control's PCA stack)
  C1-C6   -> beside their mux

Everything stays >= 15mm from the LED-array courtyard bbox, inside the
existing 173.8 x 137.8 outline. Collision-checked before saving.

  python.exe layout_led_support.py check|save
"""
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
BOARD = ROOT / "12x8 Led Array 9mm pitch" / "12x8 Led Array 9mm pitch.kicad_pcb"
tomm = pcbnew.ToMM
frommm = pcbnew.FromMM

BORDER = 15.0          # keep-out from LED array bbox
EDGE = 1.0             # min courtyard-to-board-edge

board = pcbnew.LoadBoard(str(BOARD))
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}


def box(ref):
    fp = fps[ref]
    c = fp.GetCourtyard(pcbnew.F_CrtYd)
    bb = c.BBox() if c.OutlineCount() else fp.GetBoundingBox()
    return (tomm(bb.GetLeft()), tomm(bb.GetTop()),
            tomm(bb.GetRight()), tomm(bb.GetBottom()))


def place(ref, rot, cx=None, cy=None, left=None, right=None, top=None, bot=None):
    """Set rotation, then translate so the courtyard bbox lands as asked."""
    fp = fps[ref]
    fp.SetOrientationDegrees(rot)
    l, t, r, b = box(ref)
    p = fp.GetPosition()
    px, py = tomm(p.x), tomm(p.y)
    if cx is not None:
        dx = cx - (l + r) / 2
    elif left is not None:
        dx = left - l
    elif right is not None:
        dx = right - r
    else:
        dx = 0
    if cy is not None:
        dy = cy - (t + b) / 2
    elif top is not None:
        dy = top - t
    elif bot is not None:
        dy = bot - b
    else:
        dy = 0
    fp.SetPosition(pcbnew.VECTOR2I(frommm(px + dx), frommm(py + dy)))
    return box(ref)


# ---- geometry ----
xs, ys = [], []
for d in board.GetDrawings():
    if d.GetLayerName() == "Edge.Cuts":
        bb = d.GetBoundingBox()
        xs += [tomm(bb.GetLeft()), tomm(bb.GetRight())]
        ys += [tomm(bb.GetTop()), tomm(bb.GetBottom())]
BL, BT, BR, BB_ = min(xs), min(ys), max(xs), max(ys)

al = at = 1e9
ar = ab = -1e9
for n in range(1, 97):
    l, t, r, b = box(f"LED{n}")
    al, at, ar, ab = min(al, l), min(at, t), max(ar, r), max(ab, b)
print(f"# board ({BL},{BT})-({BR},{BB_})  array ({al:.2f},{at:.2f})-({ar:.2f},{ab:.2f})")

CX, CY = (BL + BR) / 2, (BT + BB_) / 2
x_lim_l = al - BORDER      # support must end left of this ...
x_lim_r = ar + BORDER      # ... or start right of this
y_lim_t = at - BORDER
y_lim_b = ab + BORDER

moved = {}

# ---- left edge: J1 upper, J4 lower (vertical, rot 180 = control 0 + 180) ----
GAP = 4.0
moved["J1"] = place("J1", 180, right=x_lim_l - 0.5, bot=CY - GAP / 2)
moved["J4"] = place("J4", 180, right=x_lim_l - 0.5, top=CY + GAP / 2)

# ---- top edge: J2 left, J3 right (rot 90, keep y row 26.5) ----
moved["J2"] = place("J2", 90, right=CX - GAP / 2, cy=26.5)
moved["J3"] = place("J3", 90, left=CX + GAP / 2, cy=26.5)
# ---- bottom edge: J5 left, J6 right ----
moved["J5"] = place("J5", 90, right=CX - GAP / 2, cy=135.3)
moved["J6"] = place("J6", 90, left=CX + GAP / 2, cy=135.3)

# ---- right strip: muxes stacked horizontal, J9 low (control J9 y~115) ----
rx = (x_lim_r + BR - EDGE) / 2
# find rotation that puts SOIC long axis horizontal
fps["U1"].SetOrientationDegrees(0)
l, t, r, b = box("U1")
mux_rot = 0 if (r - l) >= (b - t) else 90
mh = None
y0 = 22.5   # below H3 courtyard
step = None
for i in range(6):
    ref = f"U{i + 1}"
    bb = place(ref, mux_rot, cx=rx, top=0)   # rot set; measure height
    if mh is None:
        mh = bb[3] - bb[1]
        step = mh + 3.2
    bb = place(ref, mux_rot, cx=rx, top=y0 + i * step)
    moved[ref] = bb
    # decoupling cap in the gap below the mux
    moved[f"C{i + 1}"] = place(f"C{i + 1}", 0, cx=rx, top=bb[3] + 0.7)

# ---- J9 right edge, low ----
moved["J9"] = place("J9", 0, cx=rx, cy=117.0)

# ---- checks ----
def overlap(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[3 - 3 + 1]) \
        if False else not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])

static = [r for r in fps if r.startswith(("TP", "H"))]
allboxes = dict(moved)
for r in static:
    allboxes[r] = box(r)

errs = []
names = sorted(allboxes)
for i, a in enumerate(names):
    for bn in names[i + 1:]:
        if overlap(allboxes[a], allboxes[bn]):
            errs.append(f"OVERLAP {a} {allboxes[a]} <-> {bn} {allboxes[bn]}")
arr15 = (x_lim_l, y_lim_t, x_lim_r, y_lim_b)
for r, bb in moved.items():
    inside_x = bb[2] > x_lim_l and bb[0] < x_lim_r
    inside_y = bb[3] > y_lim_t and bb[1] < y_lim_b
    if inside_x and inside_y:
        errs.append(f"BORDER {r} {bb} intrudes 15mm zone {arr15}")
    if bb[0] < BL + EDGE - 0.01 or bb[2] > BR - EDGE + 0.01 \
            or bb[1] < BT + EDGE - 0.01 or bb[3] > BB_ - EDGE + 0.01:
        errs.append(f"OFFBOARD {r} {bb}")

for r in sorted(moved):
    fp = fps[r]
    p = fp.GetPosition()
    print(f"{r:4s} pos ({tomm(p.x):7.2f},{tomm(p.y):7.2f}) rot {fp.GetOrientationDegrees():6.1f}  "
          f"box ({moved[r][0]:.1f},{moved[r][1]:.1f})-({moved[r][2]:.1f},{moved[r][3]:.1f})")
print()
if errs:
    print("ERRORS:")
    for e in errs:
        print(" ", e)
else:
    print("clean: no overlaps, border respected")

if len(sys.argv) > 1 and sys.argv[1] == "save" and not errs:
    pcbnew.SaveBoard(str(BOARD), board)
    print("SAVED")
