"""Apply a kicad-cli kicadxml netlist to a PCB's pads (direct re-net).

Use after regenerating schematics so the boards pick up net changes
without an interactive F8 sync:

  python.exe apply_netlist.py <netlist.xml> <board.kicad_pcb>
"""
import sys
import xml.etree.ElementTree as ET

import pcbnew

xml_path, pcb_path = sys.argv[1], sys.argv[2]

want = {}
root = ET.parse(xml_path).getroot()
for net in root.find("nets"):
    name = net.get("name")
    for node in net.findall("node"):
        want[(node.get("ref"), node.get("pin"))] = name

board = pcbnew.LoadBoard(pcb_path)

changed = kept = 0
for fp in board.GetFootprints():
    ref = fp.GetReference()
    for pad in fp.Pads():
        key = (ref, pad.GetNumber())
        if key not in want:
            if pad.GetNetname():
                pad.SetNetCode(0)
                changed += 1
            continue
        name = want[key]
        if pad.GetNetname() == name:
            kept += 1
            continue
        nets = board.GetNetsByName()
        if not nets.has_key(name):
            board.Add(pcbnew.NETINFO_ITEM(board, name))
            nets = board.GetNetsByName()
        pad.SetNet(nets[name])
        changed += 1

pcbnew.SaveBoard(pcb_path, board)
print(f"{pcb_path}: {changed} pads re-netted, {kept} already correct")
