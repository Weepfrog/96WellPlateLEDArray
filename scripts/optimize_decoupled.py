"""Decoupled pinout optimization, minimizing REAL anode+cathode crossings.

The driver serving a well need NOT share its index: a ribbon SLOT
(connector Jk + IDE-safe pin-pair) is the logical channel.  Each board is
optimized on its own geometry; the cable wires slot p of Jk on one board
to slot p of Jk on the other.

Per board: balanced min-distance grouping (0 crossings BETWEEN connectors),
then within each connector the 16 members are ordered by angle and refined
with 2-opt against the true two-wire (anode+cathode) ratsnest.

Emits pin_maps.py:
  WELL_CONN[w], DRV_CONN[d] = (Jref, pinA, pinK)
  PCA_MAP[d] = (pca_ref, pin)   NTC_MAP[w] = (mux_ref, pin)

  python.exe optimize_decoupled.py > pinmaps.txt
"""
import sys, math
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
import pcbnew

ROOT = Path(__file__).resolve().parent.parent
tomm = pcbnew.ToMM
Js = [f"J{k}" for k in range(1, 7)]


def pair_pins(i):
    return (2 * i - 1, 2 * i) if i <= 9 else (2 * i + 1, 2 * i + 2)


def load(path):
    b = pcbnew.LoadBoard(str(path))
    fp, jpad, allpad = {}, {}, {}
    for f in b.GetFootprints():
        r = f.GetReference()
        fp[r] = (tomm(f.GetPosition().x), tomm(f.GetPosition().y))
        for pad in f.Pads():
            allpad[(r, pad.GetNumber())] = (tomm(pad.GetPosition().x),
                                            tomm(pad.GetPosition().y))
            if r in Js:
                jpad[(r, pad.GetNumber())] = allpad[(r, pad.GetNumber())]
    return b, fp, jpad, allpad


def conn_geo(jpad):
    cen, hor = {}, {}
    for j in Js:
        pts = [jpad[(j, str(p))] for p in range(1, 35) if (j, str(p)) in jpad]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        cen[j] = (np.mean(xs), np.mean(ys))
        hor[j] = (max(xs) - min(xs)) >= (max(ys) - min(ys))
    return cen, hor


def ccw(a, b, c):
    return (c[1]-a[1])*(b[0]-a[0])-(b[1]-a[1])*(c[0]-a[0])


def seg_cross(s1, s2):
    a, b = s1; c, d = s2
    return ccw(a, c, d)*ccw(b, c, d) < 0 and ccw(a, b, c)*ccw(a, b, d) < 0


def optimize_board(pos, jpad, apos, kpos):
    """pos: item -> footprint center (grouping/ordering). apos/kpos: true
    anode/cathode pad positions (crossing metric). Returns item -> (J,pA,pK)
    minimizing real anode+cathode ratsnest crossings."""
    cen, hor = conn_geo(jpad)
    items = list(pos)
    # balanced min-distance grouping (0 inter-connector crossings)
    cols, colj = [], []
    for j in Js:
        for _ in range(16):
            colj.append(j); cols.append(cen[j])
    C = np.array([[math.hypot(pos[w][0]-c[0], pos[w][1]-c[1]) for c in cols]
                  for w in items])
    ri, ci = linear_sum_assignment(C)
    group = {j: [] for j in Js}
    for r, c in zip(ri, ci):
        group[colj[c]].append(items[r])

    def segs_for(assign):
        s = []
        for w, (j, pa, pk) in assign.items():
            s.append((apos[w], jpad[(j, str(pa))]))
            s.append((kpos[w], jpad[(j, str(pk))]))
        return s

    def xings(assign):
        s = segs_for(assign)
        return sum(1 for i in range(len(s)) for k in range(i+1, len(s))
                   if seg_cross(s[i], s[k]))

    # angle-order each connector's members, mapped to axis-ordered pin pairs
    assign = {}
    for j in Js:
        ax_h = hor[j]
        pin_axis = {i: jpad[(j, str(pair_pins(i)[0]))][0 if ax_h else 1]
                    for i in range(1, 17)}
        pair_order = sorted(range(1, 17), key=lambda i: pin_axis[i])
        cx, cy = cen[j]
        ws = sorted(group[j], key=lambda w: math.atan2(pos[w][1]-cy,
                                                       pos[w][0]-cx))
        k0 = (pos[ws[0]][0] if ax_h else pos[ws[0]][1])
        k1 = (pos[ws[-1]][0] if ax_h else pos[ws[-1]][1])
        if k0 > k1:
            ws = ws[::-1]
        for i, w in zip(pair_order, ws):
            a, kk = pair_pins(i)
            assign[w] = (j, a, kk)

    # 2-opt: swap pin-pairs within a connector while it helps
    for _ in range(8):
        improved = False
        for j in Js:
            ws = group[j]
            for a in range(len(ws)):
                for c in range(a+1, len(ws)):
                    wa, wc = ws[a], ws[c]
                    before = xings(assign)
                    assign[wa], assign[wc] = assign[wc], assign[wa]
                    if xings(assign) < before:
                        improved = True
                    else:
                        assign[wa], assign[wc] = assign[wc], assign[wa]
        if not improved:
            break
    return assign, xings(assign)


# ---- LED board ----  (anode = LED pad 1, cathode = LED pad 2)
lb, lfp, ljpad, lallpad = load(ROOT / "12x8 Led Array 9mm pitch" /
                              "12x8 Led Array 9mm pitch.kicad_pcb")
well = {int(r[3:]): xy for r, xy in lfp.items()
        if r.startswith("LED") and r[3:].isdigit()}
wA = {w: lallpad[(f"LED{w}", "1")] for w in well}
wK = {w: lallpad[(f"LED{w}", "2")] for w in well}
WELL_CONN, lx = optimize_board(well, ljpad, wA, wK)
print(f"# LED board real A/K crossings: {lx}", file=sys.stderr)

# NTC proximity muxing
muxfp = {r: xy for r, xy in lfp.items() if r in (f"U{k}" for k in range(1, 7))}
muxpad = {}
for f in lb.GetFootprints():
    if f.GetReference() in muxfp:
        for pad in f.Pads():
            muxpad[(f.GetReference(), pad.GetNumber())] = (
                tomm(pad.GetPosition().x), tomm(pad.GetPosition().y))
IN = [str(p) for p in list(range(2, 10)) + list(range(16, 24))]
order_mux = sorted(muxfp, key=lambda u: muxfp[u][1])
wells_by_y = sorted(range(1, 97), key=lambda n: (well[n][1], well[n][0]))
NTC = {}
for i, u in enumerate(order_mux):
    grp = wells_by_y[16 * i:16 * i + 16]
    ins = sorted(IN, key=lambda p: (muxpad[(u, p)][1], muxpad[(u, p)][0]))
    grp.sort(key=lambda n: (well[n][1], well[n][0]))
    for p, n in zip(ins, grp):
        NTC[n] = (u, int(p))

# ---- control board ----  (anode = U.4 CSN, cathode = L.2 inductor out)
cb, cfp, cjpad, callpad = load(ROOT / "control-board" / "control-board.kicad_pcb")
drv = {int(r[1:]): xy for r, xy in cfp.items()
       if r[:1] == "U" and r[1:].isdigit() and 1 <= int(r[1:]) <= 96}
dA = {d: callpad[(f"U{d}", "4")] for d in drv}
dK = {d: callpad[(f"L{d}", "2")] for d in drv}
DRV_CONN, cx = optimize_board(drv, cjpad, dA, dK)
print(f"# control board real A/K crossings: {cx}", file=sys.stderr)

# PCA banks: one PCA per ribbon driver-cluster (nearest), outputs by geometry
pca_fp = {r: xy for r, xy in cfp.items() if r in (f"U{101 + k}" for k in range(6))}
pcapad = {}
for f in cb.GetFootprints():
    if f.GetReference() in pca_fp:
        for pad in f.Pads():
            if pad.GetNumber().isdigit():
                pcapad[(f.GetReference(), int(pad.GetNumber()))] = (
                    tomm(pad.GetPosition().x), tomm(pad.GetPosition().y))
OUT_PINS = list(range(6, 14)) + list(range(15, 23))
cluster = {j: [d for d in range(1, 97) if DRV_CONN[d][0] == j] for j in Js}
ccen = {j: (np.mean([drv[d][0] for d in cluster[j]]),
            np.mean([drv[d][1] for d in cluster[j]])) for j in Js}
pcalist = list(pca_fp)
M = np.array([[math.hypot(ccen[j][0]-pca_fp[p][0], ccen[j][1]-pca_fp[p][1])
               for p in pcalist] for j in Js])
ri, ci = linear_sum_assignment(M)
ribbon_pca = {Js[r]: pcalist[c] for r, c in zip(ri, ci)}
PCA = {}
for j in Js:
    p = ribbon_pca[j]
    ax_h = (max(pcapad[(p, o)][0] for o in OUT_PINS) -
            min(pcapad[(p, o)][0] for o in OUT_PINS)) >= \
           (max(pcapad[(p, o)][1] for o in OUT_PINS) -
            min(pcapad[(p, o)][1] for o in OUT_PINS))
    outs = sorted(OUT_PINS, key=lambda o: pcapad[(p, o)][0 if ax_h else 1])
    ds = sorted(cluster[j], key=lambda d: (drv[d][1], drv[d][0]))
    for o, d in zip(outs, ds):
        PCA[d] = (p, o)


def emit(name, m):
    print(f"{name} = {{")
    for k in range(1, 97):
        print(f"    {k}: {m[k]},")
    print("}\n")


emit("WELL_CONN", WELL_CONN)
emit("DRV_CONN", DRV_CONN)
emit("PCA_MAP", PCA)
emit("NTC_MAP", NTC)
