"""Rename connector/mux-side labels in the hand-edited LED schematic to the
optimized pin mapping (pin_maps.py). Matches each label by OLD net name +
proximity to the physical pin, so well-side labels are untouched.

Run: python remap_led_labels.py [--dry]
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_schematics as gs
from gen_schematics_hier import pin_abs, pin_geo
from pin_maps import CONN_MAP, NTC_MAP

ROOT = Path(__file__).resolve().parent.parent
SCH = ROOT / "12x8 Led Array 9mm pitch" / "12x8 Led Array 9mm pitch.kicad_sch"

MUX_INPUT_PIN = {k: 9 - k for k in range(8)}
MUX_INPUT_PIN.update({k: 31 - k for k in range(8, 16)})


import pin_maps_old


def old_conn(n):
    return pin_maps_old.CONN_MAP[n]


def old_mux(n):
    return pin_maps_old.NTC_MAP[n]


def main():
    dry = "--dry" in sys.argv
    text = SCH.read_text(encoding="utf-8")

    # symbol positions/rotations for J1-J4, U1-U6 from the schematic
    sym = {}
    for m in re.finditer(
            r'\(symbol\n\t\t\(lib_id "([^"]+)"\)\n\t\t\(at ([-\d.]+) '
            r'([-\d.]+) ([-\d.]+)\)[\s\S]{0,4000}?'
            r'\(property "Reference" "([^"]+)"', text):
        lib, x, y, rot, ref = m.groups()
        if ref in {f"J{i}" for i in range(1, 5)} | {f"U{i}" for i in range(1, 7)}:
            sym[ref] = (lib, float(x), float(y), int(float(rot)))

    geo_cache = {}

    def pin_pos(ref, pin):
        lib, x, y, rot = sym[ref]
        if lib not in geo_cache:
            geo_cache[lib] = pin_geo(lib)
        g = geo_cache[lib][str(pin)]
        pt = pin_abs((x, y), g, rot)
        return (pt[0], pt[1])

    # all labels with spans
    labels = []
    for m in re.finditer(
            r'\(label "((?:[^"\\]|\\.)*)"\s*\(at ([-\d.]+) ([-\d.]+) '
            r'([-\d.]+)\)', text):
        labels.append(dict(name=m.group(1), x=float(m.group(2)),
                           y=float(m.group(3)), start=m.start(1),
                           end=m.end(1), used=False))

    # build rename worklist: (ref, pin, old_net, new_net)
    work = []
    for n in range(1, 97):
        oj, oa, ok_ = old_conn(n)
        nj, na, nk = CONN_MAP[n]
        work.append((oj, oa, f"LED_A{n}", None))       # placeholder
    # Simpler: for every channel, the label NAMED for the old pin location
    # must become the name of whatever channel NOW owns that pin.
    # Invert both maps pin->channel:
    new_owner = {}
    for n, (j, a, k) in CONN_MAP.items():
        new_owner[(j, a)] = f"LED_A{n}"
        new_owner[(j, k)] = f"LED_K{n}"
    old_owner = {}
    for n in range(1, 97):
        j, a, k = old_conn(n)
        old_owner[(j, a)] = f"LED_A{n}"
        old_owner[(j, k)] = f"LED_K{n}"
    new_mux_owner = {}
    for n, (u, p) in NTC_MAP.items():
        new_mux_owner[(u, p)] = f"NTC{n}"
    old_mux_owner = {}
    for n in range(1, 97):
        u, p = old_mux(n)
        old_mux_owner[(u, p)] = f"NTC{n}"

    edits = []
    misses = []
    for owner_old, owner_new in ((old_owner, new_owner),
                                 (old_mux_owner, new_mux_owner)):
        for key, oldname in owner_old.items():
            newname = owner_new[key]
            if oldname == newname:
                continue
            px, py = pin_pos(*key)
            best, bestd = None, 1e9
            for lb in labels:
                if lb["used"] or lb["name"] != oldname:
                    continue
                d = (lb["x"] - px) ** 2 + (lb["y"] - py) ** 2
                if d < bestd:
                    best, bestd = lb, d
            if best is None or bestd > 15 ** 2:
                misses.append((key, oldname, newname,
                               None if best is None else bestd ** 0.5))
                continue
            best["used"] = True
            edits.append((best["start"], best["end"], newname))

    print(f"{len(edits)} label renames planned, {len(misses)} misses")
    for ms in misses[:15]:
        print("  MISS:", ms)
    if misses:
        sys.exit(1)
    if dry:
        return
    for start, end, newname in sorted(edits, reverse=True):
        text = text[:start] + newname + text[end:]
    SCH.write_text(text, encoding="utf-8")
    print("written")


if __name__ == "__main__":
    main()
