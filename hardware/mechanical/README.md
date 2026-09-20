# Enclosure K / electronics interface

Status: mechanical prototype, 2026-09-17. No fabricated or electrically validated custom PCB exists in this repo. `enclosure-k-interface.json` records CAD datums and provisional envelopes, not verified component footprints. Dimensions are millimeters. A blank mounting-hole field means undecided, not zero holes.

The current enclosure has two perimeter frames and two soft membranes. The rear rim is flush with its frame; the center recesses 0.65 mm. The internal upper spaces are opened up, and the USB wiring route connects to the main cavity. This supersedes the **mechanical concept** of a solid aluminum plateau/unibody described in older notes, but does not replace the outstanding thermal/RF analysis.

## Mounts we can establish now

Use frame-referenced rigid support for the main electronics and camera; use the TPU for cushioning and sealing. Avoid fastening alignment-critical optics into flexible membrane alone. The camera axis is 30 degrees toward the top. An angled mechanical carrier can hold the existing camera module and its FFC; an angled custom camera PCB is not required solely to set that angle.

Keep the newly opened upper volume available for a camera carrier, possible mic/LED board, speaker and cabling. It is not all free PCB area: speaker acoustics, camera lens projection, FFC bends, frame catches, antenna and thermal keepouts consume space. Final board shapes must be checked as populated assemblies, not bare rectangles.

Do not yet cut final screw bosses or hole patterns. Confirm board variants/outlines, height, mounting holes, connector entry and tool access first. An adjustable/removable carrier is preferable for early fit experiments. Choose screw size and boss geometry after measuring available wall and installation clearances.

## Board partition proposed for review

1. Main compute/power board or initial module carrier, referenced to the frame. Do not freeze a bare-RV1106 design before integration bring-up.
2. Camera module on an angled rigid carrier, native MIPI FFC back to compute.
3. Optional small mic/LED daughterboard near their ports. The IM69D130 is bottom-port: the PCB and seal need an aligned acoustic path. Do not connect two PDM clock drivers together; decide microphone ownership/routing explicitly.
4. Speaker held separately in a retained, sealed acoustic seat, with a removable wire connection. The 18 mm BOM speaker does not imply an 18 mm exterior opening, and the existing small outlet row has not been acoustically validated.
5. USB-C board/connector positively retained against cable insertion load, with the open interior wiring route. Choose the exact connector and power/data routing before mounting holes.
6. Touch electrode behind the thin touch area. Controller, electrode shape, ground keepout and sensitivity are not yet specified in the BOM.

The four enclosure pieces remain four pieces. Additional rigid electronic carriers, if selected, are internal assembly parts and need their own drawings.

## Decisions before schematic/placement freeze

- Existing development boards and intended cellular region/carrier. The BOM itself flags EG915U-EU as unsuitable for the proposed US use.
- Exact SC3336 module drawing and connector pin count/pinout; vendor module identity alone is insufficient for a footprint.
- Confirm whether two-way earbud microphone support is required. The repo's BM83 Tx-mode notes do not establish HFP Audio Gateway support.
- USB-C variant, input power requirement, charging/current budget, battery protection and temperature sensing. Do not treat the current mouth cutout as a verified connector fit.
- Antenna layout and thermal path for a perimeter-metal/soft-face enclosure. The old unibody heat-spreader assumption no longer applies.
- Main board thickness, stackup, connector heights and practical service/removal order.

## KiCad workflow

Create schematic sheets for power, wake/touch, compute, cellular, audio and interconnect only after sourcing the corresponding manufacturer reference designs and pinouts. Link each symbol/footprint to a checked part variant. Keep unknown values explicitly unresolved; do not substitute convenient footprints.

Export populated board STEP models from KiCad into enclosure coordinates. Check component bodies, solder joints, underside parts, connector mating and removal space, cable bends and screw access. Only then transfer actual board-hole coordinates into CAD and export new meshes.

Run ERC and DRC with a documented fab stackup, impedance constraints and reviewed exceptions. Passing these checks is not electrical validation. Bench-test power rails/current limiting, wake latency, audio, camera, modem bursts and thermal behavior before a fully integrated board spin. Fabrication outputs should be released only after the pending decisions and reviews are resolved.

## First bench milestones

Record exact board/firmware variants and wiring, then bring up each power domain separately on a suitable current-limited supply. Prove camera capture and audio locally, then add modem connectivity and the realtime workload. Measure peak current, wake-to-first-audio and sustained temperatures. Fit inert board/component dummies into the enclosure before installing a live battery. Log measured results and failures in the repo; no bench measurements have been performed as part of K.

For PLA enclosure fit, start with the latch coupon. The new geometry is a test iteration, not an SLM spring design or seal qualification.

## Manufacturer references checked during this update

- [Waveshare SC3336 Camera B](https://www.waveshare.com/wiki/SC3336_3MP_Camera_%28B%29): the B version changes the copper-plated fixing-hole provision. Confirm actual mechanical retention on the purchased module rather than assuming the A variant mounting details.
- [Infineon IM69D130 datasheet](https://www.infineon.com/assets/row/public/documents/24/49/infineon-im69d130-datasheet-en.pdf): package and acoustic-port guidance; use the manufacturer land pattern in the PCB design.
- [Microchip BM83 features](https://onlinedocs.microchip.com/oxy/GUID-414904F5-364E-4377-B959-9226AD29D6A9-en-US-8/GUID-90AB7782-7237-42CB-802D-B4DB2B9C5608.html): AT mode lists A2DP source or A2DP/HFP sink. That does not establish the HFP Audio Gateway role needed for an earbud microphone.
- [KiCad CLI documentation](https://docs.kicad.org/9.0/en/cli/cli.html): PCB STEP/GLB export for enclosure integration. Use documentation matching the installed version. KiCad was not installed on the workstation at this update; no ERC/DRC or native KiCad file validation has been run.

## Enclosure L (next): electronics interface for Rev A

Rev A boards are placed, and the enclosure grows **+10 mm** (a straight insert at y = −10; the camera end is unchanged).
[`enclosure-L-electronics.json`](enclosure-L-electronics.json) carries everything in these axes:
- board outlines, z-levels and M1.6 hole positions
- every part courtyard and side
- mic ports, LED, the USB-C mouth (z 6.46) and service access
- off-board envelopes: battery, FFC, speaker, LRA, camera

Requirements are listed in [`../REV-A.md`](../REV-A.md) §6. Populated STEPs come from `hardware/kicad/tools/build.sh`.
