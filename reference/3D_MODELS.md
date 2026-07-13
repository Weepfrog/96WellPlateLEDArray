# 3D Model Status

Audit of every footprint in `scripts/design_data.py` `FP{}` (2026-07-13).
Stock models live under `${KICAD10_3DMODEL_DIR}` (`C:\Program Files\KiCad\10.0\share\kicad\3dmodels`);
project models under `libraries/jlc_parts.3dshapes/`, referenced as
`${KIPRJMOD}/../libraries/jlc_parts.3dshapes/<file>` (both `.kicad_pro` files sit one level below repo root).

## Status table

| FP key | Footprint | Model | Status |
|---|---|---|---|
| led | jlc_parts:LED-SMD_3P-L3.5-W3.5_NLW3535AV2 | jlc_parts.3dshapes/LED-SMD_3P-L3.5-W3.5_NLW3535AV2.wrl | OK (path fixed) |
| pt4115 | jlc_parts:SOT-89-5_L4.5-W2.5-P1.50-LS4.5-BR | jlc_parts.3dshapes/SOT-89-5_L4.5-W2.5-H1.5-LS4.1-P1.50.wrl | OK (path fixed) |
| mux | jlc_parts:SOIC-24_L15.4-W7.5-P1.27-LS10.3-BL | jlc_parts.3dshapes/SOIC-24_L15.4-W7.5-H2.7-LS10.3-P1.27.wrl | OK (path fixed) |
| button | jlc_parts:SW-SMD_4P-L5.1-W5.1-P3.70-LS6.5-TL_H1.5 | jlc_parts.3dshapes/SW-SMD_4P-...-TL_H1.5.wrl | OK (path fixed) |
| screw2 | jlc_parts:TerminalBlock_KF301-5.0-2P_1x02_P5.00mm | jlc_parts.3dshapes/CONN-TH_P5.00_KF301-5.0-2P.wrl | OK (was broken, see below) |
| r0603 | Resistor_SMD:R_0603_1608Metric | Resistor_SMD.3dshapes/R_0603_1608Metric.step | OK |
| r0805 | Resistor_SMD:R_0805_2012Metric | Resistor_SMD.3dshapes/R_0805_2012Metric.step | OK |
| c0603 | Capacitor_SMD:C_0603_1608Metric | Capacitor_SMD.3dshapes/C_0603_1608Metric.step | OK |
| c0805 | Capacitor_SMD:C_0805_2012Metric | Capacitor_SMD.3dshapes/C_0805_2012Metric.step | OK |
| elec8 | Capacitor_SMD:CP_Elec_8x10 | Capacitor_SMD.3dshapes/CP_Elec_8x10.step | OK |
| elec63 | Capacitor_SMD:CP_Elec_6.3x7.7 | Capacitor_SMD.3dshapes/CP_Elec_6.3x7.7.step | OK |
| led0805 | LED_SMD:LED_0805_2012Metric | LED_SMD.3dshapes/LED_0805_2012Metric.step | OK |
| sma | Diode_SMD:D_SMA | Diode_SMD.3dshapes/D_SMA.step | OK |
| swpa4030 | Inductor_SMD:L_Sunlord_SWPA4030S | Inductor_SMD.3dshapes/L_Sunlord_SWPA4030S.step | OK |
| swpa6045 | Inductor_SMD:L_Sunlord_SWPA6045S | Inductor_SMD.3dshapes/L_Sunlord_SWPA6045S.step | OK |
| soic8 | Package_SO:SOIC-8_3.9x4.9mm_P1.27mm | Package_SO.3dshapes/SOIC-8_3.9x4.9mm_P1.27mm.step | OK |
| tssop28 | Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm | Package_SO.3dshapes/TSSOP-28_4.4x9.7mm_P0.65mm.step | OK |
| vssop10 | Package_SO:TSSOP-10_3x3mm_P0.5mm | Package_SO.3dshapes/TSSOP-10_3x3mm_P0.5mm.step | OK |
| sot23 | Package_TO_SOT_SMD:SOT-23 | Package_TO_SOT_SMD.3dshapes/SOT-23.step | OK |
| idc50 | Connector_IDC:IDC-Header_2x25_P2.54mm_Vertical | Connector_IDC.3dshapes/IDC-Header_2x25_P2.54mm_Vertical.step | OK |
| idc20 | Connector_IDC:IDC-Header_2x10_P2.54mm_Horizontal | Connector_IDC.3dshapes/IDC-Header_2x10_P2.54mm_Horizontal.step | OK |
| sock19 | Connector_PinSocket_2.54mm:PinSocket_1x19_P2.54mm_Vertical | Connector_PinSocket_2.54mm.3dshapes/PinSocket_1x19_P2.54mm_Vertical.step | OK |
| barrel | Connector_BarrelJack:BarrelJack_Horizontal | Connector_BarrelJack.3dshapes/BarrelJack_Horizontal.step | OK |
| hdr2 | Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical | Connector_PinHeader_2.54mm.3dshapes/PinHeader_1x02_P2.54mm_Vertical.step | OK |
| hole | MountingHole:MountingHole_3.2mm_M3 | — | no model (correct: it's a hole) |
| tp | TestPoint:TestPoint_Pad_1.5x1.5mm | — | no model (correct: bare copper pad, KiCad ships none for pad-type TPs) |

## Changes made

1. **jlc_parts model paths fixed** (led, pt4115, mux, button): were bare-relative
   `jlc_parts.3dshapes/<f>.wrl`, which KiCad cannot resolve from either project dir.
   Rewritten to `${KIPRJMOD}/../libraries/jlc_parts.3dshapes/<f>.wrl` in
   `libraries/jlc_parts.pretty/*.kicad_mod` **and** in the embedded copies inside both
   `.kicad_pcb` files (regenerating via `scripts/gen_pcbs.py` now also produces the fixed paths).
2. **KF301 screw terminal (J6, C474881)**: previously referenced
   `${KICAD10_3DMODEL_DIR}/TerminalBlock.3dshapes/TerminalBlock_MaiXu_MX126-...step`,
   which does not exist in KiCad 10 (no generic `TerminalBlock.3dshapes` lib ships).
   Fetched the real KF301-5.0-2P model via
   `easyeda2kicad --3d --lcsc_id C474881` →
   `libraries/jlc_parts.3dshapes/CONN-TH_P5.00_KF301-5.0-2P.{step,wrl}` (STEP verified ISO-10303-21).
   Footprint + embedded PCB copy now reference the WRL with **offset (2.5, 0, 0) mm**
   (EasyEDA footprint origin = pin midpoint; ours = pin 1, pin 2 at +5 mm; same body
   orientation, rotation 0). The easyeda2kicad-generated duplicate footprint
   `CONN-TH_P5.00_KF301-5.0-2P.kicad_mod` was deleted; design keeps
   `TerminalBlock_KF301-5.0-2P_1x02_P5.00mm` (1.4 mm drills).
3. **ESP32-DevKitC-38** full-board STEP added:
   `libraries/jlc_parts.3dshapes/ESP32-DevKitC-38.step` (7.6 MB, verified ISO-10303-21,
   products: board / ESP32-WROOM-32D / micro usb / buttons). Source: SnapEDA/Espressif
   "ESP32-DEVKITC-32D" model as redistributed in github.com/BlueAndi/Pixelix
   (`doc/boards/pixelix/v2.1/3D-files/`). No WRL exists for it; STEP renders fine in KiCad.
   **Not attached to any footprint** — see below.

## Attaching the DevKitC model (manual step)

The module plugs into two `PinSocket_1x19` (J10 left/3V3 row at (140, 130), J11 right/GND
row at (165.4, 130), rows 25.4 mm apart, pins running +y). Attach the model to **J10 only**:

PCB editor → J10 → Footprint Properties → 3D Models → add
`${KIPRJMOD}/../libraries/jlc_parts.3dshapes/ESP32-DevKitC-38.step` with:

| Offset X | Offset Y | Offset Z | Rot X | Rot Y | Rot Z |
|---|---|---|---|---|---|
| +12.7 mm | −22.86 mm | +8.5 mm | −90° | 0° | 0° |

Rationale: the STEP's insertion point is the center of the 2×19 pin field with the board
in the XZ plane (convention confirmed from the Pixelix reference footprint, which uses
offset (0, −3, 3.5) / rotate (−90, 0, 0) on a footprint whose origin is that center).
X +12.7 = half the 25.4 mm row spacing from J10's pin 1; Y −22.86 = half the 45.72 mm pin
span (dialog +Y is up in board view); Z +8.5 = socket insulator height, i.e. module PCB
underside resting on the sockets. Check in the 3D viewer: if the module faces the wrong
way (antenna end swapped), set Rot Z = 180° and keep the same offsets; nudge Z to taste.

## Remaining gaps

- None blocking: every populated footprint resolves a model. MountingHole and
  TestPoint_Pad intentionally have no 3D model.
- DevKitC model is not auto-attached (J10/J11 are generic pin sockets shared by both
  rows); attach manually per the table above, or add the `(model ...)` block to J10's
  footprint instance in `control-board.kicad_pcb` / teach `gen_pcbs.py` to inject it.
- WRL variant of the DevKitC model unavailable (STEP only).
