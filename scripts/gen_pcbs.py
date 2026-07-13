"""Generate both .kicad_pcb files with all footprints pre-placed.

Run with KiCad's bundled Python so the native pcbnew API writes the files:

  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" gen_pcbs.py

Footprints come from the stock KiCad 10 libraries plus the project jlc_parts
library. Nets are NOT assigned here - wire the schematic per CONNECTIONS.md,
then use Update PCB from Schematic (F8). Footprints carry the schematic
symbol UUID paths (from sch_meta.json), so F8 links them directly.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_data as dd  # noqa: E402

import pcbnew  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STOCK = Path(r"C:\Program Files\KiCad\10.0\share\kicad\footprints")
JLC = ROOT / "libraries" / "jlc_parts.pretty"


def mm(v):
    return pcbnew.FromMM(v)


def load_fp(lib_id):
    nick, name = lib_id.split(":", 1)
    libdir = JLC if nick == "jlc_parts" else STOCK / f"{nick}.pretty"
    fp = pcbnew.FootprintLoad(str(libdir), name)
    if fp is None:
        raise KeyError(f"footprint not found: {lib_id}")
    return fp


def build(board_def, out_path, meta_path):
    meta = json.loads(meta_path.read_text(encoding="utf-8")) \
        if meta_path.exists() else {}
    root_uuid = meta.get("__root__", "")

    board = pcbnew.NewBoard(str(out_path))
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(board_def["layers"])

    w, h = board_def["size"]
    edge = pcbnew.PCB_SHAPE(board)
    edge.SetShape(pcbnew.SHAPE_T_RECT)
    edge.SetStart(pcbnew.VECTOR2I(mm(0), mm(0)))
    edge.SetEnd(pcbnew.VECTOR2I(mm(w), mm(h)))
    edge.SetLayer(pcbnew.Edge_Cuts)
    edge.SetWidth(mm(0.1))
    board.Add(edge)

    placed = 0
    for p in board_def["parts"]:
        fp = load_fp(p["footprint"])
        try:
            fp.SetFPIDAsString(p["footprint"])
        except Exception:
            pass
        fp.SetPosition(pcbnew.VECTOR2I(mm(p["pcb_xy"][0]), mm(p["pcb_xy"][1])))
        try:
            fp.SetOrientationDegrees(p["pcb_rot"])
        except AttributeError:
            fp.SetOrientation(pcbnew.EDA_ANGLE(float(p["pcb_rot"])))
        fp.Reference().SetText(p["ref"])
        fp.Value().SetText(p["value"])
        if p["lcsc"]:
            try:
                fp.SetField("LCSC", p["lcsc"])
            except Exception:
                pass
        if p["dnp"]:
            try:
                fp.SetDNP(True)
            except Exception:
                pass
        if p["ref"] in meta and root_uuid:
            fp.SetPath(pcbnew.KIID_PATH(
                f"/{root_uuid}/{meta[p['ref']]['uuid']}"))
        board.Add(fp)
        placed += 1

    # title text on silkscreen
    txt = pcbnew.PCB_TEXT(board)
    txt.SetText(board_def["title"])
    txt.SetPosition(pcbnew.VECTOR2I(mm(w / 2), mm(h - 2.5)))
    txt.SetLayer(pcbnew.F_SilkS)
    txt.SetTextSize(pcbnew.VECTOR2I(mm(1.5), mm(1.5)))
    board.Add(txt)

    # helper zones (no net yet - assign GND/+24V after schematic sync)
    zone_layers = []
    if board_def["layers"] == 4:
        zone_layers = [(pcbnew.In1_Cu, "GND plane - assign net GND"),
                       (pcbnew.In2_Cu, "signal/GND - assign net GND"),
                       (pcbnew.B_Cu, "thermal back - per-LED cathode islands "
                                     "+ GND fill (see CONNECTIONS.md)")]
    else:
        zone_layers = [(pcbnew.F_Cu, "+24V pour - assign net +24V"),
                       (pcbnew.B_Cu, "GND pour - assign net GND")]
    for layer, name in zone_layers:
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetZoneName(name)
        z.SetIsFilled(False)
        ol = z.Outline()
        idx = ol.NewOutline()
        for (zx, zy) in [(1, 1), (w - 1, 1), (w - 1, h - 1), (1, h - 1)]:
            ol.Append(mm(zx), mm(zy), idx)
        z.SetLocalClearance(mm(0.3))
        z.SetMinThickness(mm(0.25))
        try:
            z.SetThermalReliefGap(mm(0.3))
            z.SetThermalReliefSpokeWidth(mm(0.4))
        except Exception:
            pass
        board.Add(z)

    pcbnew.SaveBoard(str(out_path), board)
    print(f"wrote {out_path} ({placed} footprints, "
          f"{board_def['layers']} layers, {w}x{h}mm)")


def main():
    led = dd.build_led_board()
    ctl = dd.build_control_board()
    led_dir = ROOT / "12x8 Led Array 9mm pitch"
    ctl_dir = ROOT / "control-board"
    build(led, led_dir / "12x8 Led Array 9mm pitch.kicad_pcb",
          led_dir / "sch_meta.json")
    build(ctl, ctl_dir / "control-board.kicad_pcb",
          ctl_dir / "sch_meta.json")


if __name__ == "__main__":
    main()
