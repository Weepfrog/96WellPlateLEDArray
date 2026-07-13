"""Compute routing-optimal channel->connector-pin and NTC->mux assignments
from the user's actual LED board placement. Run with KiCad python:

  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" optimize_pins.py

Prints the mapping tables to paste into design_data.py.
"""
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
BOARD = ROOT / "12x8 Led Array 9mm pitch" / "12x8 Led Array 9mm pitch.kicad_pcb"


def mm(v):
    return v / 1e6


board = pcbnew.LoadBoard(str(BOARD))
pads = {}      # (ref, pin) -> (x, y)
fppos = {}     # ref -> (x, y)
for fp in board.GetFootprints():
    ref = fp.GetReference()
    p = fp.GetPosition()
    fppos[ref] = (mm(p.x), mm(p.y))
    for pad in fp.Pads():
        pp = pad.GetPosition()
        pads[(ref, pad.GetNumber())] = (mm(pp.x), mm(pp.y))

# ---- wells: channel n at 9mm grid; recover row/col from LED positions ----
led_xy = {}
for n in range(1, 97):
    led_xy[n] = fppos[f"LED{n}"]
xs = sorted({round(x, 2) for x, _ in led_xy.values()})
ys = sorted({round(y, 2) for _, y in led_xy.values()})
col_of = {x: i + 1 for i, x in enumerate(xs)}
row_of = {y: i + 1 for i, y in enumerate(ys)}
pos_rc = {}
for n, (x, y) in led_xy.items():
    pos_rc[n] = (row_of[round(y, 2)], col_of[round(x, 2)])
# sanity: generator numbering n == (r-1)*12+c ?
renumber_ok = all(n == (r - 1) * 12 + c for n, (r, c) in pos_rc.items())
print(f"# LED grid recovered; generator numbering intact: {renumber_ok}")

# ---- connectors: quadrant assignment ----
# front row (nearer field, smaller y) serves rows 5-8; back row serves 1-4.
# left pair serves cols 1-6, right pair cols 7-12.
jinfo = {j: fppos[j] for j in ("J1", "J2", "J3", "J4")}
xmid = sum(x for x, _ in jinfo.values()) / 4
field_ymid = (min(ys) + max(ys)) / 2
quad = {}
for j, (x, y) in jinfo.items():
    side = "L" if x < xmid else "R"
    depth = "top" if y < field_ymid else "bottom"
    quad[j] = (side, depth)
print(f"# connector quadrants: {quad}")

CONN = {}   # n -> (jref, pinA, pinK)
for j, (side, depth) in quad.items():
    cols = range(1, 7) if side == "L" else range(7, 13)
    rows = range(1, 5) if depth == "top" else range(5, 9)
    chans = [n for n, (r, c) in pos_rc.items() if r in rows and c in cols]
    # order pin pairs to match the connector's physical pin-1..50 direction:
    # sort channels by (column asc if pin1 is at the -x end else desc, row)
    p1x = pads[(j, "1")][0]
    p49x = pads[(j, "49")][0]
    ascending = p1x < p49x
    chans.sort(key=lambda n: (pos_rc[n][1] if ascending else -pos_rc[n][1],
                              pos_rc[n][0]))
    for i, n in enumerate(chans):
        CONN[n] = (j, 2 * i + 1, 2 * i + 2)

# ---- muxes: side-matched, chunked by proximity ----
MUX_INPUT_PIN = {k: 9 - k for k in range(8)}
MUX_INPUT_PIN.update({k: 31 - k for k in range(8, 16)})
left_m = sorted((u for u in ("U1", "U2", "U3", "U4", "U5", "U6")
                 if fppos[u][0] < 149), key=lambda u: fppos[u][1])
right_m = sorted((u for u in ("U1", "U2", "U3", "U4", "U5", "U6")
                  if fppos[u][0] >= 149), key=lambda u: fppos[u][1])
print(f"# left muxes (top->bottom): {left_m}, right: {right_m}")

NTC = {}    # n -> (mux_ref, input_pin)
for side, muxes, cols in (("L", left_m, range(1, 7)),
                          ("R", right_m, range(7, 13))):
    chans = [n for n, (r, c) in pos_rc.items() if c in cols]
    chans.sort(key=lambda n: (pos_rc[n][0], pos_rc[n][1]))   # row-major sweep
    for i, n in enumerate(chans):
        u = muxes[i // 16]
        NTC[n] = (u, MUX_INPUT_PIN[i % 16])

# ---- emit tables ----
print("\nCONN_MAP = {")
for n in range(1, 97):
    j, a, k = CONN[n]
    print(f"    {n}: (\"{j}\", {a}, {k}),")
print("}")
print("\nNTC_MAP = {")
for n in range(1, 97):
    u, p = NTC[n]
    print(f"    {n}: (\"{u}\", {p}),")
print("}")
