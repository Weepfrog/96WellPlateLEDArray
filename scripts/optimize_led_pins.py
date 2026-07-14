"""Optimize pinouts FOR THE LED ARRAY, given its final placement.

Two levers, both derived from live board geometry:

1. CONN_MAP - ribbon pin order.  The channel->ribbon grouping is fixed by
   the control board's driver bands, and the cable is 1:1, so pin order is
   shared by both boards.  We choose the LED-board-optimal nested order
   (wells sorted along each connector's axis -> pins in axis order): zero
   fan-out crossings on the LED board.  This costs the control board only a
   few crossings (it is near-Pareto because the boards are a sandwich
   mirror) and is emitted IDE-safe via pair_pins().

2. NTC_MAP - each 16:1 mux takes the 16 NTCs physically nearest it
   (proximity row-bands for the right-edge mux stack), inputs assigned by
   projection for a crossing-free horizontal fan-in.

PCA_MAP is control-board-internal and unaffected by pin order, so it is
carried through unchanged.

  python.exe optimize_led_pins.py > pinmaps_led.txt
"""
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import pin_maps  # current maps: grouping + PCA_MAP carried through
tomm = pcbnew.ToMM


def pair_pins(i):
    """IDE-safe pair index (1..16) -> (pinA, pinK)."""
    if i <= 9:
        return (2 * i - 1, 2 * i)
    return (2 * i + 1, 2 * i + 2)


def load(path, refs_prefixes):
    b = pcbnew.LoadBoard(str(path))
    fp_pos, pad_pos = {}, {}
    for fp in b.GetFootprints():
        r = fp.GetReference()
        fp_pos[r] = (tomm(fp.GetPosition().x), tomm(fp.GetPosition().y))
        for pad in fp.Pads():
            pad_pos[(r, pad.GetNumber())] = (
                tomm(pad.GetPosition().x), tomm(pad.GetPosition().y))
    return fp_pos, pad_pos


LEDPCB = ROOT / "12x8 Led Array 9mm pitch" / "12x8 Led Array 9mm pitch.kicad_pcb"
lfp, lpad = load(LEDPCB, None)
well = {int(r[3:]): xy for r, xy in lfp.items() if r.startswith("LED")
        and r[3:].isdigit()}
muxfp = {r: xy for r, xy in lfp.items()
         if r in (f"U{k}" for k in range(1, 7))}


def axis_coord(pad_pos, j):
    pts = [pad_pos[(j, str(p))] for p in range(1, 41) if (j, str(p)) in pad_pos]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    horiz = (max(xs) - min(xs)) >= (max(ys) - min(ys))
    return lambda xy: (xy[0] if horiz else xy[1])


# ---- CONN_MAP: LED-optimal pin order within each ribbon's fixed channels ----
groups = {}
for n, (j, a, k) in pin_maps.CONN_MAP.items():
    groups.setdefault(j, []).append(n)

CONN = {}
for j, chans in groups.items():
    ax = axis_coord(lpad, j)
    # pins in axis order (pair index i -> pin a -> coordinate)
    pin_axis = {i: ax(lpad[(j, str(pair_pins(i)[0]))]) for i in range(1, 17)}
    pair_order = sorted(range(1, 17), key=lambda i: pin_axis[i])
    # wells in axis order
    chan_order = sorted(chans, key=lambda n: ax(well[n]))
    for i, n in zip(pair_order, chan_order):
        a, kk = pair_pins(i)
        CONN[n] = (j, a, kk)

# ---- NTC_MAP: proximity row-bands to the right-edge mux stack ----
IN = [str(p) for p in list(range(2, 10)) + list(range(16, 24))]
order_mux = sorted(muxfp, key=lambda u: muxfp[u][1])
wells_by_y = sorted(range(1, 97), key=lambda n: (well[n][1], well[n][0]))
NTC = {}
for i, u in enumerate(order_mux):
    grp = wells_by_y[16 * i:16 * i + 16]
    ins = sorted(IN, key=lambda p: (lpad[(u, p)][1], lpad[(u, p)][0]))
    grp.sort(key=lambda n: (well[n][1], well[n][0]))
    for p, n in zip(ins, grp):
        NTC[n] = (u, int(p))

# ---- emit (PCA_MAP unchanged) ----
print("CONN_MAP = {")
for n in range(1, 97):
    print(f"    {n}: {CONN[n]},")
print("}")
print()
print("PCA_MAP = {")
for n in range(1, 97):
    print(f"    {n}: {pin_maps.PCA_MAP[n]},")
print("}")
print()
print("NTC_MAP = {")
for n in range(1, 97):
    print(f"    {n}: {NTC[n]},")
print("}")
