"""Generate JLCPCB production files: BOM + CPL (pick-and-place) CSVs.

BOM comes from design_data (LCSC numbers already verified). CPL positions
come from the actual .kicad_pcb files via pcbnew, so they reflect the real
layout. THT connectors are excluded from both (hand-solder plan); DNP parts
excluded from BOM but kept in CPL as comments.

Run with KiCad python:
  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" gen_production.py
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_data as dd

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "production"

# hand-soldered THT parts: exclude from SMD assembly
HAND_SOLDER_PREFIX = ("J",)      # IDC headers, sockets, jacks, terminals
EXCLUDE_REFS = ("H",)            # mounting holes: no part


def board_positions(pcb_path):
    b = pcbnew.LoadBoard(str(pcb_path))
    pos = {}
    for fp in b.GetFootprints():
        p = fp.GetPosition()
        pos[fp.GetReference()] = (round(pcbnew.ToMM(p.x), 4),
                                  round(pcbnew.ToMM(p.y), 4),
                                  round(fp.GetOrientationDegrees(), 2),
                                  "bottom" if fp.IsFlipped() else "top")
    return pos


def export(board_def, pcb_path, tag):
    pos = board_positions(pcb_path)
    OUT.mkdir(exist_ok=True)

    # ---- BOM: group by (value, footprint, lcsc) ----
    groups = defaultdict(list)
    for p in board_def["parts"]:
        ref = p["ref"]
        if ref.startswith(EXCLUDE_REFS) or ref.startswith(HAND_SOLDER_PREFIX):
            continue
        if p["dnp"]:
            continue
        if not p["lcsc"]:
            continue
        groups[(p["value"], p["footprint"].split(":")[-1], p["lcsc"])].append(ref)

    bom = OUT / f"BOM_{tag}.csv"
    with open(bom, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC"])
        for (val, fpn, lcsc), refs in sorted(groups.items(),
                                             key=lambda kv: kv[0][2]):
            w.writerow([val, ",".join(sorted(refs)), fpn, lcsc])

    # ---- CPL ----
    cpl = OUT / f"CPL_{tag}.csv"
    n = 0
    with open(cpl, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for p in board_def["parts"]:
            ref = p["ref"]
            if ref.startswith(EXCLUDE_REFS) or ref.startswith(HAND_SOLDER_PREFIX):
                continue
            if p["dnp"] or not p["lcsc"]:
                continue
            if ref not in pos:
                print(f"  !! {ref} not on PCB")
                continue
            x, y, rot, side = pos[ref]
            # JLCPCB expects Y-up coordinates
            w.writerow([ref, f"{x}mm", f"{-y}mm", side, rot])
            n += 1
    print(f"{tag}: BOM {len(groups)} lines, CPL {n} placements")
    print(f"  NOTE: verify rotations in JLCPCB's preview - LED polarity and"
          f" SOT-89/SOIC rotations are the classic failure.")


export(dd.build_led_board(),
       ROOT / "12x8 Led Array 9mm pitch" / "12x8 Led Array 9mm pitch.kicad_pcb",
       "led-board")
export(dd.build_control_board(),
       ROOT / "control-board" / "control-board.kicad_pcb",
       "control-board")
