# Pneuma Rev A: KiCad projects (generated)

| Project | Board |
|---|---|
| `pneuma-main/` | PNM-MAIN: Luckfox Core1106-1408, nRF52840 (MDBT50Q), mics, MAX98357A, DRV2605L, camera FPC |
| `pneuma-pwr/`  | PNM-PWR: USB-C, BQ24074, LC709203F, EG800Q-NA, nano-SIM, FSUSB42, TXB0104 ×2, AT42QT1011 |

**Everything is generated from [`tools/design.py`](tools/design.py).** Edit the design there, then run
`tools/build.sh` (KiCad 10; `CQ_PY` must point to a Python with `cadquery shapely matplotlib` for the 3D check).
If you hand-edit the `.kicad_sch` or `.kicad_pcb` files, the next regeneration overwrites those edits. The exception is
**routing**: once routing starts in the KiCad GUI, stop running `gen_pcb.py` and use *Update PCB from Schematic*.
Footprint paths are set to the schematic symbol UUIDs to make that work.

- `lib/`: project symbols/footprints (Core1106 with carrier cutout, EG800Q-NA LGA-109 from the Quectel V1.1 drawings,
  RGB LED, pads) + 3D bodies
- `vendor/luckfox-core1106/`: Luckfox's KiCad symbol/footprint/STEP, pinout and schematic, unmodified
- `out/`: build output, **regenerated, mostly not versioned**. `build.sh` writes the board STEPs, schematic PDFs,
  ERC/DRC reports and the spreader DXF here; git keeps only the small readable ones (BOM CSVs, `layout-L.png`,
  `interference-L.json`, `spreader-stock-pads.json`). The STEP/DXF deliverables also go to the Desktop handoff folder.

Regeneration is deterministic in what matters: identical part placement, nets and coordinates every run
(`design.REV_DATE` freezes the title-block date; override with `PNEUMA_REV_DATE`). KiCad still assigns fresh
internal UUIDs and writes footprints in its own order, so the files are not byte-identical between runs.

Status: schematics pass ERC (0 errors); PCBs are placed with DRC 0 violations; **unrouted**. See [`../REV-A.md`](../REV-A.md).
