"""Generate both .kicad_sch files (parts placed, no wiring).

Symbols are copied verbatim from the installed KiCad 10 stock libraries and the
project jlc_parts library, so pin numbering is authoritative. Every net entry
in design_data is validated against the real symbol pins before emitting.

Run with system Python:  python gen_schematics.py
"""
import json
import re
import uuid
import sys
from pathlib import Path

import design_data as dd

KICAD_SYMS = Path(r"C:\Program Files\KiCad\10.0\share\kicad\symbols")
ROOT = Path(__file__).resolve().parent.parent
JLC_SYMS = ROOT / "libraries" / "jlc_parts.kicad_sym"

SCH_VERSION = "20260306"
GEN_VERSION = "10.0"

# stable UUIDs so re-runs don't churn git history
NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def suuid(*key):
    return str(uuid.uuid5(NAMESPACE, "/".join(str(k) for k in key)))


# ------------------------------------------------------------ lib parsing

_lib_cache = {}


def lib_text(lib_name):
    if lib_name not in _lib_cache:
        p = JLC_SYMS if lib_name == "jlc_parts" else KICAD_SYMS / f"{lib_name}.kicad_sym"
        _lib_cache[lib_name] = p.read_text(encoding="utf-8")
    return _lib_cache[lib_name]


def find_block(text, header):
    """Return the balanced s-expr block starting at `header` occurrence."""
    i = text.find(header)
    if i < 0:
        return None
    depth, j, in_str = 0, i, False
    while j < len(text):
        ch = text[j]
        if in_str:
            if ch == '"' and text[j - 1] != "\\":
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[i:j + 1]
        j += 1
    raise ValueError(f"unbalanced block for {header}")


def extract_symbol(lib_id):
    """Return (block_text, pins) with block renamed to the full lib_id."""
    lib, name = lib_id.split(":", 1)
    text = lib_text(lib)
    block = find_block(text, f'(symbol "{name}"')
    if block is None:
        raise KeyError(f"symbol {lib_id} not found")
    m = re.search(r'\(extends\s+"([^"]+)"\)', block)
    if m:
        parent = m.group(1)
        pblock = find_block(text, f'(symbol "{parent}"')
        pblock = pblock.replace(f'(symbol "{parent}"', f'(symbol "{name}"', 1)
        pblock = pblock.replace(f'"{parent}_', f'"{name}_')
        block = pblock
    # rename outer symbol name to the full lib id; inner sub-symbol names
    # (e.g. "R_0_1") must stay unprefixed or KiCad rejects the file
    block = block.replace(f'(symbol "{name}"', f'(symbol "{lib_id}"', 1)
    pins = pin_map(block)
    return block, pins


def pin_map(block):
    """{number: name} from a symbol block."""
    pins = {}
    for pm in re.finditer(
            r'\(pin\s+\S+\s+\S+\s*\(at[^)]*\)\s*\(length[^)]*\)'
            r'(?:\s*\(hide\s+\w+\))?\s*\(name\s+"((?:[^"\\]|\\.)*)"'
            r'.*?\(number\s+"((?:[^"\\]|\\.)*)"', block, re.S):
        name, num = pm.group(1), pm.group(2)
        pins.setdefault(num, name)
    if not pins:  # fallback: looser pairing
        names = re.findall(r'\(name\s+"((?:[^"\\]|\\.)*)"', block)
        nums = re.findall(r'\(number\s+"((?:[^"\\]|\\.)*)"', block)
        pins = dict(zip(nums, names))
    return pins


# ------------------------------------------------------------ emission

def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def emit_symbol_instance(p, pins, project, root_uuid):
    x, y = p["sch_xy"]
    su = suuid(project, p["ref"])
    lines = [
        "\t(symbol",
        f'\t\t(lib_id "{p["lib_id"]}")',
        f"\t\t(at {x} {y} 0)",
        "\t\t(unit 1)",
        "\t\t(exclude_from_sim no)",
        "\t\t(in_bom yes)",
        "\t\t(on_board yes)",
        f'\t\t(dnp {"yes" if p["dnp"] else "no"})',
        f'\t\t(uuid "{su}")',
    ]

    def prop(name, val, dy, hide):
        lines.append(f'\t\t(property "{esc(name)}" "{esc(val)}"')
        lines.append(f"\t\t\t(at {round(x + 2.54, 3)} {round(y + dy, 3)} 0)")
        lines.append("\t\t\t(effects")
        lines.append("\t\t\t\t(font")
        lines.append("\t\t\t\t\t(size 1.27 1.27)")
        lines.append("\t\t\t\t)")
        lines.append("\t\t\t\t(justify left)")
        if hide:
            lines.append("\t\t\t\t(hide yes)")
        lines.append("\t\t\t)")
        lines.append("\t\t)")

    prop("Reference", p["ref"], -5.08, False)
    prop("Value", p["value"], -2.54, False)
    prop("Footprint", p["footprint"], 0, True)
    prop("Datasheet", "~", 2.54, True)
    if p["lcsc"]:
        prop("LCSC", p["lcsc"], 5.08, True)
    if p["desc"]:
        prop("Description", p["desc"], 7.62, True)
    for num in pins:
        lines.append(f'\t\t(pin "{esc(num)}"')
        lines.append(f'\t\t\t(uuid "{suuid(project, p["ref"], "pin", num)}")')
        lines.append("\t\t)")
    lines.append("\t\t(instances")
    lines.append(f'\t\t\t(project "{esc(project)}"')
    lines.append(f'\t\t\t\t(path "/{root_uuid}"')
    lines.append(f'\t\t\t\t\t(reference "{esc(p["ref"])}")')
    lines.append("\t\t\t\t\t(unit 1)")
    lines.append("\t\t\t\t)")
    lines.append("\t\t\t)")
    lines.append("\t\t)")
    lines.append("\t)")
    return "\n".join(lines)


def emit_text(txt, x, y, size, project, key):
    return "\n".join([
        "\t(text \"%s\"" % esc(txt),
        "\t\t(exclude_from_sim no)",
        f"\t\t(at {dd.snap(x)} {dd.snap(y)} 0)",
        "\t\t(effects",
        "\t\t\t(font",
        f"\t\t\t\t(size {size} {size})",
        "\t\t\t)",
        "\t\t\t(justify left bottom)",
        "\t\t)",
        f'\t\t(uuid "{suuid(project, "text", key)}")',
        "\t)",
    ])


def texts_for(board):
    """Annotation texts per board."""
    out = []
    name = board["name"]
    if name.startswith("12x8"):
        for n in range(1, 97):
            r, c = dd.ch_rc(n)
            p = next(q for q in board["parts"] if q["ref"] == f"LED{n}")
            x, y = p["sch_xy"]
            out.append((f"CH{n}", x - 5, y - 10, 2.0, f"ch{n}"))
        out.append(("NTC MUXES  (U1..U6 = channels 1-16 / 17-32 / 33-48 / "
                    "49-64 / 65-80 / 81-96)", 55, 500, 2.5, "muxhdr"))
        out.append(("RIBBONS TO CONTROL BOARD", 700, 40, 2.5, "connhdr"))
        out.append(("Wire per CONNECTIONS.md - LED pin1=A(+), pin2=K(-), "
                    "pin3=thermal: tie to pin2", 30, 20, 3.0, "note1"))
    else:
        for n in range(1, 97):
            p = next(q for q in board["parts"] if q["ref"] == f"U{n}")
            x, y = p["sch_xy"]
            out.append((f"CH{n}", x - 30, y - 15, 2.0, f"ch{n}"))
        out.append(("PCA9685 PWM BANK (0x40-0x45)", 50, 585, 2.5, "pcahdr"))
        out.append(("5V RAIL + 24V INPUT + BULK", 530, 685, 2.5, "pwrhdr"))
        out.append(("ESP32 DEVKITC-38 SOCKET", 990, 60, 2.5, "esphdr"))
        out.append(("UI: BUTTONS + STATUS LEDS", 940, 585, 2.5, "uihdr"))
        out.append(("FAN", 890, 670, 2.5, "fanhdr"))
        out.append(("RIBBONS TO LED BOARD", 1100, 40, 2.5, "connhdr"))
        out.append(("Wire per CONNECTIONS.md - one PT4115 buck per LED, "
                    "channel n = row-major (row-1)*12+col", 40, 25, 3.0,
                    "note1"))
    return out


def generate(board, out_path):
    project = board["name"]
    root_uuid = suuid(project, "root")
    # collect lib symbols + validate nets
    lib_blocks, sym_pins = {}, {}
    for p in board["parts"]:
        if p["lib_id"] and p["lib_id"] not in lib_blocks:
            block, pins = extract_symbol(p["lib_id"])
            lib_blocks[p["lib_id"]] = block
            sym_pins[p["lib_id"]] = pins

    ref_pins = {p["ref"]: sym_pins[p["lib_id"]]
                for p in board["parts"] if p["lib_id"]}
    errors = []
    for netname, members in board["nets"].items():
        for ref, pin in members:
            if ref not in ref_pins:
                errors.append(f"{netname}: unknown ref {ref}")
            elif pin not in ref_pins[ref]:
                errors.append(
                    f"{netname}: {ref} has no pin {pin} "
                    f"(has {sorted(ref_pins[ref])})")
    if errors:
        print(f"!! {project}: {len(errors)} net/pin mismatches:")
        for e in errors[:40]:
            print("   ", e)
        return False

    chunks = [
        "(kicad_sch",
        f"\t(version {SCH_VERSION})",
        '\t(generator "eeschema")',
        f'\t(generator_version "{GEN_VERSION}")',
        f'\t(uuid "{root_uuid}")',
        f'\t(paper "{board["paper"]}")',
        "\t(title_block",
        f'\t\t(title "{esc(board["title"])}")',
        '\t\t(date "2026-07-13")',
        '\t\t(comment 1 "Parts placed by generator - wire per CONNECTIONS.md")',
        "\t)",
        "\t(lib_symbols",
    ]
    for block in lib_blocks.values():
        chunks.append("\t\t" + block.replace("\n", "\n\t\t"))
    chunks.append("\t)")

    for txt, x, y, size, key in texts_for(board):
        chunks.append(emit_text(txt, x, y, size, project, key))

    for p in board["parts"]:
        if p["lib_id"]:
            chunks.append(emit_symbol_instance(
                p, ref_pins[p["ref"]], project, root_uuid))

    chunks += [
        "\t(sheet_instances",
        '\t\t(path "/"',
        '\t\t\t(page "1")',
        "\t\t)",
        "\t)",
        "\t(embedded_fonts no)",
        ")",
        "",
    ]
    out_path.write_text("\n".join(chunks), encoding="utf-8")
    print(f"wrote {out_path}  ({len(board['parts'])} parts, "
          f"{len(lib_blocks)} lib symbols)")

    # dump ref->uuid map + pin names for the PCB generator / docs
    meta = {p["ref"]: {"uuid": suuid(project, p["ref"]),
                       "pins": ref_pins.get(p["ref"], {})}
            for p in board["parts"]}
    meta["__root__"] = root_uuid
    (out_path.parent / "sch_meta.json").write_text(
        json.dumps(meta, indent=1), encoding="utf-8")
    return True


def write_lib_tables(proj_dir):
    (proj_dir / "sym-lib-table").write_text(
        '(sym_lib_table\n  (version 7)\n'
        '  (lib (name "jlc_parts")(type "KiCad")'
        '(uri "${KIPRJMOD}/../libraries/jlc_parts.kicad_sym")'
        '(options "")(descr "JLCPCB-sourced parts"))\n)\n', encoding="utf-8")
    (proj_dir / "fp-lib-table").write_text(
        '(fp_lib_table\n  (version 7)\n'
        '  (lib (name "jlc_parts")(type "KiCad")'
        '(uri "${KIPRJMOD}/../libraries/jlc_parts.pretty")'
        '(options "")(descr "JLCPCB-sourced parts"))\n)\n', encoding="utf-8")


def main():
    led = dd.build_led_board()
    ctl = dd.build_control_board()

    # print authoritative pin tables for parts whose pinout was assumed
    for lib_id in [dd.LIB["xl1509"], dd.LIB["fet"], dd.LIB["barrel"],
                   dd.LIB["pca"], dd.LIB["screw2"], dd.LIB["button"],
                   dd.LIB["led2"], dd.LIB["dsch"], dd.LIB["ntc"]]:
        _, pins = extract_symbol(lib_id)
        pretty = ", ".join(f"{n}={pins[n]}" for n in sorted(pins, key=lambda s: (len(s), s)))
        print(f"PINS {lib_id}: {pretty}")

    ok = True
    led_dir = ROOT / "12x8 Led Array 9mm pitch"
    ctl_dir = ROOT / "control-board"
    ctl_dir.mkdir(exist_ok=True)
    ok &= generate(led, led_dir / "12x8 Led Array 9mm pitch.kicad_sch")
    ok &= generate(ctl, ctl_dir / "control-board.kicad_sch")
    if not (ctl_dir / "control-board.kicad_pro").exists():
        (ctl_dir / "control-board.kicad_pro").write_text("{}", encoding="utf-8")
    write_lib_tables(led_dir)
    write_lib_tables(ctl_dir)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
