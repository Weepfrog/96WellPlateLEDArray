"""Optimize driver-board pinouts from actual placement (both boards read).

- CONN_MAP: per-ribbon pair permutation minimizing combined fan-out
  disorder on BOTH boards (pairs ordered along each connector's axis).
- PCA_MAP: each PCA9685's LED0-15 outputs assigned to its bank's DIM
  lines by geometric order (chips are stacked vertically).

Writes tables to stdout; run with KiCad python:
  python.exe optimize_driver_pins.py > pinmap_driver.txt
"""
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
tomm = pcbnew.ToMM

# IDE-safe pair -> (pinA, pinK)
def pair_pins(i):
    if i <= 9:
        return (2 * i - 1, 2 * i)
    return (2 * i + 1, 2 * i + 2)


def read(board_path, anchor_prefix):
    b = pcbnew.LoadBoard(str(board_path))
    anchors, pads = {}, {}
    for fp in b.GetFootprints():
        r = fp.GetReference()
        p = fp.GetPosition()
        if r.startswith(anchor_prefix) and r[len(anchor_prefix):].isdigit():
            n = int(r[len(anchor_prefix):])
            if 1 <= n <= 96:
                anchors[n] = (tomm(p.x), tomm(p.y))
        if r in (f"J{k}" for k in range(1, 7)):
            for pad in fp.Pads():
                pp = pad.GetPosition()
                pads[(r, int(pad.GetNumber()))] = (tomm(pp.x), tomm(pp.y))
    return anchors, pads


cells, cpads = read(ROOT / "control-board" / "control-board.kicad_pcb", "U")
wells, lpads = read(ROOT / "12x8 Led Array 9mm pitch" /
                    "12x8 Led Array 9mm pitch.kicad_pcb", "LED")
# control board U refs include U101+ etc - filter to 1..96 handled above
print("# cells:", len([n for n in cells if n <= 96]),
      " wells:", len(wells), file=sys.stderr)


def axis_param(pads, j):
    """Project pad positions onto the connector's long axis -> pair order."""
    pts = [pads[(j, pair_pins(i)[0])] for i in range(1, 17)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    horiz = (max(xs) - min(xs)) >= (max(ys) - min(ys))
    return [(p[0] if horiz else p[1]) for p in pts], horiz


CONN, PCA = {}, {}
for k in range(1, 7):
    j = f"J{k}"
    chans = list(range(16 * (k - 1) + 1, 16 * k + 1))
    tvals, horiz_c = axis_param(cpads, j)
    _, horiz_l = axis_param(lpads, j)
    # pair order along control connector axis
    pair_order = sorted(range(1, 17), key=lambda i: tvals[i - 1])
    # channel order: combined rank of control-cell and led-well projection
    def proj(pos, horiz):
        return pos[0] if horiz else pos[1]
    rank_c = {n: r for r, n in enumerate(
        sorted(chans, key=lambda n: proj(cells[n], horiz_c)))}
    rank_l = {n: r for r, n in enumerate(
        sorted(chans, key=lambda n: proj(wells[n], horiz_l)))}
    chan_order = sorted(chans, key=lambda n: rank_c[n] + rank_l[n])
    for i, n in zip(pair_order, chan_order):
        a, kk = pair_pins(i)
        CONN[n] = (j, a, kk)

# PCA outputs: chip k pads 6-13,15-22, sorted along chip axis
b = pcbnew.LoadBoard(str(ROOT / "control-board" / "control-board.kicad_pcb"))
OUT_PINS = list(range(6, 14)) + list(range(15, 23))
for k in range(6):
    ref = f"U{101 + k}"
    padpos = {}
    for fp in b.GetFootprints():
        if fp.GetReference() == ref:
            for pad in fp.Pads():
                if pad.GetNumber().isdigit() and int(pad.GetNumber()) in OUT_PINS:
                    pp = pad.GetPosition()
                    padpos[int(pad.GetNumber())] = (tomm(pp.x), tomm(pp.y))
    xs = [p[0] for p in padpos.values()]; ys = [p[1] for p in padpos.values()]
    horiz = (max(xs) - min(xs)) >= (max(ys) - min(ys))
    pins_sorted = sorted(OUT_PINS,
                         key=lambda pin: padpos[pin][0 if horiz else 1])
    chans = list(range(16 * k + 1, 16 * k + 17))
    chans_sorted = sorted(chans, key=lambda n: (cells[n][1], cells[n][0]))
    for pin, n in zip(pins_sorted, chans_sorted):
        PCA[n] = (ref, pin)

# NTC_MAP: each mux owns 2 LED columns (U1=cols 1-2 ... U6=cols 11-12);
# input pads and wells zipped in geometric order for a crossing-free fan-in.
lb = pcbnew.LoadBoard(str(ROOT / "12x8 Led Array 9mm pitch" /
                           "12x8 Led Array 9mm pitch.kicad_pcb"))
mux_pads = {}
for fp in lb.GetFootprints():
    r = fp.GetReference()
    if r in (f"U{k}" for k in range(1, 7)):
        for pad in fp.Pads():
            mux_pads[(r, pad.GetNumber())] = (
                tomm(pad.GetPosition().x), tomm(pad.GetPosition().y))
INPUT_PINS = [str(p) for p in list(range(2, 10)) + list(range(16, 24))]
col_of = {n: (n - 1) % 12 + 1 for n in range(1, 97)}
row_of = {n: (n - 1) // 12 + 1 for n in range(1, 97)}
NTC = {}
for k in range(1, 7):
    u = f"U{k}"
    wells96 = [n for n in range(1, 97) if col_of[n] in (2 * k - 1, 2 * k)]
    # NTC lines arrive from the array (left of the mux stack): sort pads
    # by (y, x) and wells by (row, col) - rows map onto pad rows cleanly
    ins = sorted(INPUT_PINS, key=lambda p: (mux_pads[(u, p)][1],
                                            mux_pads[(u, p)][0]))
    wells96.sort(key=lambda n: (row_of[n], col_of[n]))
    for pin, n in zip(ins, wells96):
        NTC[n] = (u, int(pin))

print("CONN_MAP = {")
for n in range(1, 97):
    print(f"    {n}: {CONN[n]},")
print("}")
print()
print("PCA_MAP = {")
for n in range(1, 97):
    print(f"    {n}: {PCA[n]},")
print("}")
print()
print("NTC_MAP = {")
for n in range(1, 97):
    print(f"    {n}: {NTC[n]},")
print("}")
