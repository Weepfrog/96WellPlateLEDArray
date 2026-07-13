"""Compare kicad-cli exported netlists against design_data's intended nets.

Usage: python verify_netlist.py <led_netlist.xml> <ctl_netlist.xml>
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_data as dd


def load_netlist(path):
    root = ET.parse(path).getroot()
    nets = {}
    for net in root.iter("net"):
        name = net.get("name").lstrip("/")
        members = {(node.get("ref"), node.get("pin"))
                   for node in net.iter("node")
                   if not node.get("ref").startswith("#")}
        nets[name] = members
    comps = {c.get("ref") for c in root.iter("comp")}
    return nets, comps


def check(board, xml_path):
    nets, comps = load_netlist(xml_path)
    want_refs = {p["ref"] for p in board["parts"] if p["lib_id"]}
    missing_refs = want_refs - comps
    extra_refs = {c for c in comps - want_refs if not c.startswith("#")}
    errs = []
    if missing_refs:
        errs.append(f"missing components: {sorted(missing_refs)[:10]} "
                    f"({len(missing_refs)} total)")
    if extra_refs:
        errs.append(f"unexpected components: {sorted(extra_refs)[:10]}")
    import re
    internal = re.compile(r"^SW\d+$")   # sub-sheet-internal: match by members
    member_index = {frozenset(v): k for k, v in nets.items()}
    for name, members in board["nets"].items():
        want = {(r, p) for r, p in members}
        if internal.match(name):
            if frozenset(want) not in member_index:
                errs.append(f"net {name}: no netlist net has exactly "
                            f"these members {sorted(want)}")
            continue
        got = nets.get(name)
        if got is None:
            errs.append(f"net {name}: MISSING from netlist")
        elif got != want:
            only_want = want - got
            only_got = got - want
            errs.append(f"net {name}: want-not-got {sorted(only_want)[:6]} "
                        f"| got-not-want {sorted(only_got)[:6]}")
    print(f"{board['name']}: {len(board['nets'])} intended nets, "
          f"{len(nets)} netlist nets, {len(comps)} components")
    if errs:
        print(f"  !! {len(errs)} problems:")
        for e_ in errs[:30]:
            print("   ", e_)
        return False
    print("  ALL NETS MATCH")
    return True


ok = True
ok &= check(dd.build_led_board(), sys.argv[1])
ok &= check(dd.build_control_board(), sys.argv[2])
sys.exit(0 if ok else 1)
