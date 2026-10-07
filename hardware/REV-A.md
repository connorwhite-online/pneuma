# Pneuma Rev A: board and BOM freeze (bench, then enclosure L)

Status, 2026-09-19. **Frozen:** architecture, part selection, schematics, board outlines, component placement,
inter-board pinout and the enclosure interface. **Not done:** copper routing, fab outputs and any electrical
validation. The PCBs are *placed, not routed*. Nothing here has been built or powered.

| Artifact | Where |
|---|---|
| Single source of truth (every part, pin and net) | [`kicad/tools/design.py`](kicad/tools/design.py) |
| KiCad 10 projects (schematic + placed PCB) | [`kicad/pneuma-main/`](kicad/pneuma-main), [`kicad/pneuma-pwr/`](kicad/pneuma-pwr) |
| Board BOMs (grouped, with MPNs) | [`kicad/out/pneuma-main-bom.csv`](kicad/out/pneuma-main-bom.csv), [`kicad/out/pneuma-pwr-bom.csv`](kicad/out/pneuma-pwr-bom.csv) |
| Populated board STEPs (KiCad export) | `kicad/out/pneuma-main.step`, `kicad/out/pneuma-pwr.step` |
| Enclosure-L interface (all coordinates, z-levels, envelopes) | [`mechanical/enclosure-L-electronics.json`](mechanical/enclosure-L-electronics.json) |
| Layout plan + side view | [`kicad/out/layout-L.png`](kicad/out/layout-L.png) |
| Thermal estimate (why there's no spreader) | [`kicad/tools/thermal_estimate.py`](kicad/tools/thermal_estimate.py) |
| Regenerate everything | `hardware/kicad/tools/build.sh` |
| Camera module RFQ (blocking enclosure L) | [`CAMERA-RFQ.md`](CAMERA-RFQ.md) |

Checks run on the generated files with KiCad 10.0.6 `kicad-cli`:
- **ERC:** 0 errors on both boards.
- **DRC:** 0 violations apart from unrouted nets.
- **3D:** a solid-intersection check of boards, battery, FFC, speaker, LRA and camera envelopes found 0 interferences.

None of these checks is electrical validation.

---

## 1. What changed from the old BOM, and why

| Old | Rev A | Reason |
|---|---|---|
| Quectel **EG915U-EU** | **EG800Q-NA** (Cat-1 bis, B2/4/5/12/13/66, LGA-109 15.8×17.7×2.4) | EG915U-EU has no US bands. EG800Q-NA covers AT&T/Verizon LTE and T-Mobile except B71. It is stocked at JLCPCB (C41406928). |
| Bare RV1106G3 custom SoC | **Luckfox Core1106-1408** SoM (RV1106G3, 256 MB, 8 GB eMMC, WiFi6/BT5.2) | Your choice: the SoC, DDR, eMMC, PMIC and radio are Luckfox-validated, so first-spin risk drops. |
| Microchip BM83 | **Removed** (Core1106 BT5.2 for A2DP, validated on the bench first) | 32×15 mm doesn't fit. The BM83 AT firmware also has no HFP-AG role. |
| SC3336 3MP Camera (B) | **Connector/pinout frozen (Luckfox 20P); the module itself is NOT chosen** — see §7 | The (B) is 25×24 mm with a 23.95 mm M12 lens stack and can't fit even tilted. The board doesn't care which module you use; the enclosure bump does. |
| PKCell LP803860 2000 mAh | **LP702040, 500 mAh / 1.85 Wh, 7.0×20×40 mm** with PCM + wires | Volume. See §4. (The 550 mAh version of the same cell is 41 mm long and needs 1 mm more bay.) |
| PUI AS01808MR-R 18 mm speaker | **PUI AS01508MR-LWC40 class, 15 mm** | 18 mm collides with the camera over the Core. |
| USB-C GCT USB4500 (IP67) | **GCT USB4105-GF-A** | K's port isn't sealed yet. The IP67 part returns with the seal design. |
| BQ24074 on VSYS for everything | BQ24074, but **modem on VBAT** | BQ24074 OUT regulates to **4.4 V**, above the EG800Q's 4.3 V maximum (TI datasheet, device comparison table). |
| Aluminum perimeter frames + TPU membranes (K) | **Two-piece silicone/TPU shell, no metal**, plus a rigid internal carrier | A metal ring around the whole device was the biggest unsolved LTE-antenna problem. Soft skin also feels cooler at the same temperature. |
| Aluminum unibody as heat sink + graphite | **PCB copper does the spreading; two off-the-shelf silicone gap pads** carry board→shell | Measured first: a 60 s session lifts the device ~2.3 K, and the 43 °C ceiling is set by skin area (~3.3 W continuous) regardless of internals. A vapor chamber doesn't fit and only spreads; a copper-foil + rigid-post stack can't hold pressure against a soft shell. |

## 2. Architecture (two boards + FFC)

```
 camera end ─────────────────────────────────────────────────────────────── USB end
 PNM-MAIN (45×44 mm pebble cap, 4L 0.8 mm)   battery bay   PNM-PWR (41×39 mm + USB tongue)
  top:  Core1106-1408 (RV1106G3 + WiFi/BT)    ≤7×20×40      top: EG800Q-NA, nano-SIM, USB-C,
        status LED, speaker/LRA pads,         LiPo           FFC, JST-GH battery, TVS, SIM ESD
        10 test pads                                          btm: BQ24074, LC709203F gauge,
  btm:  nRF52840 (MDBT50Q), 2 mics, amp,                           FSUSB42 USB mux, 2× TXB0104,
        DRV2605L, load switch, camera FPC,                         AT42QT1011 touch, U.FL, 12 TPs
        FFC, Tag-Connect SWD
        └──────── 30-way 0.5 mm FFC, straight-through, runs UNDER the battery ────────┘
```

**Power.** USB-C → BQ24074 (1.21 A input limit, 270 mA charge) → VSYS (3.5–4.4 V).
- VSYS feeds the Core1106 (through the TPS22917 load switch; the module's own PMIC accepts 2.7–5.5 V), the nRF VDDH, the MAX98357A and the DRV2605L.
- The modem runs from VBAT with 2×47 µF, a TVS and an HF cap array, as Quectel recommends.
- The nRF52840 runs in high-voltage mode, and its REG0 output is the always-on 3.3 V rail (+3V3_AON, ≤25 mA).

**Control.** The nRF52840 is the always-on wake island. It owns:
- the PDM wake mic
- SoC power (enable and reset) and wake/IRQ lines
- the modem's PWRKEY, RESET, STATUS, RI and DTR
- the I²C bus to the haptic driver and fuel gauge
- the USB mux select
- the touch input, charge status and RGB LED

**Data.**
- SoC ↔ modem: USB 2.0 through the FSUSB42 mux (SEL=1). The default, SEL=0, routes the SoC's USB to USB-C for flashing and ADB. There's also a 4-wire UART5 link through a level shifter.
- SoC ↔ nRF: UART3.
- Camera: MIPI-CSI, 2 lanes.
- Audio out: I²S to the MAX98357A.
- Audio in: an analog MEMS mic into the RV1106 codec for session audio.

**Inter-board FFC (30P, pin n ↔ pin n):**

| Pin | Net | Pin | Net | Pin | Net |
|---|---|---|---|---|---|
| 1 | GND | 11 | MDM_RXD_3V3 | 21 | MDM_STATUS |
| 2–5 | VSYS (4×0.5 A) | 12 | MDM_TXD_3V3 | 22 | MDM_RI |
| 6, 7 | GND | 13 | MDM_RTS_3V3 | 23 | MDM_DTR |
| 8 | USB_SOC_DP | 14 | MDM_CTS_3V3 | 24 | USB_SEL |
| 9 | USB_SOC_DN | 15 | GND | 25 | CHG_N |
| 10 | GND | 16 | +3V3_AON | 26 | VBUS_DET_3V3 |
| | | 17, 18 | I2C_SCL / SDA | 27 | TOUCH_OUT |
| | | 19, 20 | MDM_PWRKEY / RESET | 28 | +3V3_SOC |
| | | | | 29, 30 | GND |

### Design rules that firmware and bring-up must respect
1. **Program UICR.REGOUT0 = 3.3 V** on the nRF's first boot; the factory default is 1.8 V. Configure P0.18 as PSELRESET.
2. **Leave Core1106 pins 60/61/62/67 and 63/64/68/69 unused.** On the Wi-Fi variant they are tied through 1 kΩ to WL_EN/HOST_WAKE or carry the BT UART (Luckfox schematic).
3. **No back-powering.** While SOC_EN is low, the nRF must hold every SoC-facing line low or Hi-Z. The modem-UART translator's VCCB is +3V3_SOC, so it switches off along with the SoC.
4. **Charge termination.** The modem loads VBAT directly, which can block termination while charging. Keep the modem in DRX/sleep while on USB, or accept timer-based termination.
5. **Default USB mode.** The SoC's USB comes up routed to USB-C. Host mode toward the modem needs a device-tree role switch (usb-role-switch).

## 3. What stretches the boards

Courtyard areas from the placed PCBs:

| Board (area) | Biggest items | Why it's fixed |
|---|---|---|
| **PNM-MAIN** (1651 mm²) | Core1106 32×32 (**1023 mm², 62%**); nRF module 16.6×11.6 (192); FFC 21.2×8 (169); camera FPC 16.2×8 (129) | The Core's underside parts force a **24.2×21.3 mm cutout** through the carrier, so ~515 mm² of the *bottom* side under it is unusable. Everything else has to crowd into an L-shaped strip 6–12 mm wide around it. |
| **PNM-PWR** (1185 mm²) | EG800Q-NA 18.8×16.9 (**317**); nano-SIM 14.7×15.5 (**228**); FFC 21.2×8 (169); USB-C 10.7×9 (97); JST-GH 7×6.5 (46) | The modem alone is taller (17.7 mm) than K's whole lower bay (~16 mm). The SIM holder is nearly as big as the modem. The FFC connector (2.0 mm tall) can't go underneath, where there's only 1.5 mm of clearance. |

Length budget along the device (L interior ≈ 94 mm):
- main board: 45 mm (Core 30 mm plus a 6 mm nRF/FFC strip and an 8 mm top cap)
- battery: 21 mm
- power board: 26 mm (modem row 17 mm, FFC/battery-connector row 8 mm)
- USB tongue: in the channel

**Shrinking the boards, most to least effective:**
1. **Bare RV1106G3 instead of the Core1106** (Rev B): recovers the ~515 mm² cutout and the module's 1.6 mm PCB. It's the only change that gets back toward 1000+ mAh. The cost is the risk you chose to defer.
2. **MFF2 eSIM (5×6 mm) instead of the nano-SIM**: saves ~220 mm² on PNM-PWR. You'd lose SIM swapping on the bench, and the eUICC needs provisioning.
3. **Solder the battery leads instead of the JST-GH**: saves ~46 mm².
4. **Custom low-profile FPC connectors** (≤1.0 mm, e.g. Hirose FH19C class): would let the FFC move to the underside. That needs new footprints; there are no stock KiCad ones.

## 4. What keeping K's exact size would have cost

K interior is ~84 mm long; L adds 10 mm. At K length, one of these has to give:
- **Keep this layout:** the battery bay shrinks from 21 to ~11 mm, about **250–300 mAh**, roughly half of L.
- **Or keep ~450–500 mAh** by taking items 2–4 above together:
  - an eSIM instead of the removable nano-SIM
  - battery leads soldered directly
  - no modem keep-out margin, which makes rework harder
  - low-profile connectors that need custom footprints

  That's still ~20% less battery than L.

What L gives you: ~550–600 mAh (2.0–2.2 Wh), which works out to about 40 min of continuous LTE talk at ~3 W, or ~30 h of registered-idle standby at ~18 mA. These are estimates to bench-measure, not results. Keep in mind that the old "2000 mAh / ~10 h" figure never fit K either.

## 5. Bench plan

### Phase 0: dev kits (buy now, no custom boards)
Each item matches a Rev A part so code and wiring carry over.

| Item | Why | ~$ |
|---|---|---|
| Luckfox **Pico Ultra W** (RV1106G3 + WiFi6/BT5.2) | Same SoC and radio family as Core1106-1408. Answers the A2DP-on-BT5.2 question. | 30 |
| Luckfox **SC3336 3MP Camera (B)** | Same Luckfox 20P pinout as J4 on PNM-MAIN | 9 |
| **Quectel EG800 EVB, NA variant** (DigiKey), or skip and bring up on a PNM-PWR | Same modem and AT set as Rev A. The Electromaker listing is the EU variant. | EVB |
| Adafruit **Feather nRF52840 Express** (MDBT50Q-1MV2) | Same module as U3. Wake word, UART to SoC, power sequencing. | 25 |
| MAX98357A (Adafruit 3006), DRV2605L (Adafruit 2305) + Vybronics **VG1040003D**, PUI **AS01508MR-LWC40** | Audio and haptics chain as on the board | ~25 |
| BQ24074 (Adafruit 4755) + LC709203F gauge breakout + a 500–600 mAh 1S cell | Power path and fuel-gauge firmware | ~25 |
| US IoT nano-SIM (Hologram or Soracom plan-US), U.FL LTE antenna (Molex 2091420180) + pigtail | Real network attach on US bands | ~15 |
| Tag-Connect TC2030-CTX-NL + SWD probe | Same programming path as Rev A | ~40 |

**Numbers Phase 0 must produce before fab:**
- wake-to-first-audio, with the modem in registered-idle vs. powered off
- idle current (target < 20 mA)
- modem TX peak current and VBAT droop
- whether A2DP to earbuds works on BT5.2
- whether RV1106 runs app + camera + modem at once
- SoC-surface temperature over a 60 s session

### Phase 1: Rev A boards (after routing)
- **Fab:** 4-layer, 0.8 mm, ENIG, 0.1/0.1 mm rules, controlled impedance for USB (90 Ω), MIPI (100 Ω) and a 50 Ω RF feed. JLC assembles everything except the Core1106, which is a hand-solderable stamp-hole module. The EG800Q LGA must be machine-placed.
- **Bring-up order:**
  1. VBUS/VSYS on a current-limited supply
  2. nRF (SWD, UICR, +3V3_AON)
  3. SoC_EN → Core boot on USB-C (ADB)
  4. camera
  5. audio
  6. modem PWRKEY → AT over USB (USB_SEL=1) → attach
  7. touch
  8. charge
- **Fit:** check the PLA fit of the L prototype with dummy boards (the exported STEPs) before installing a live battery.

## 6. Requirements for enclosure L

Everything is in [`mechanical/enclosure-L-electronics.json`](mechanical/enclosure-L-electronics.json), in K's axes.

0. **Construction:**
   - Two soft shells, front (+z, outward: camera, touch, LED) and rear (skin side, kept insulating), in silicone or TPU, 0.8–1.2 mm walls. **No aluminum frame.**
   - A rigid internal carrier (PC, nylon or PA12) locates the boards, battery, speaker, LRA and camera, and takes the M1.6 screws. The shells seal and cushion around it.
1. **Length +10 mm:** insert a straight section at y = −10. The camera end is unchanged; everything at the USB end moves −10 mm, so the interior spans y −59…+47.6.
2. **Board supports:**
   - PNM-MAIN underside at **z 4.7** (top 5.5). PNM-PWR underside at **z 4.0** (top 4.8).
   - Rear floor stays at z 2.45. The lowest parts sit at z 2.56 (main-board FFC connector) and z 2.66 (power board).
   - M1.6 holes: main (−11.8, 41.5) and (12.8, 41.35); power (15.6, −21.6) and (−19.8, −22.6).
   - Use a rigid frame-referenced carrier, not screws into TPU (same guidance as K).
3. **Headroom over the Core:** extend the camera-bump pocket down to y ≈ 2.5 so everything stacked on the Core fits:
   - speaker Ø15×3.5 at **(−8, 12.4)**, top z 12.1 — nudged +2.2 mm so it clears the touch pad
   - LRA Ø10×4 at **(−10.5, 30.5)**, top z 12.6 (moved off the Core1106 Wi-Fi/BT chip antenna at x 10.5–13.7, y 10.5–13.5)
   - SoC thermal post
   - camera envelope: 11×11×6 mm on the 30° axis at K's aperture (0, 26, 16.8)
4. **Battery pocket (LP702040, 7.0×20×40 mm):** x −20.4…19.6, y −19.3…1.3, z 2.85…9.85, with the FFC (16.5 mm wide) underneath at z 2.5–2.8. The FFC needs an S-bend clearance at PNM-PWR J5: y −21.4…−19.3, z up to 6.8.
5. **USB-C:** mouth at y −58.8, centre z **6.46** (K had 6.1). The exterior wall around the port must be thin or counterbored so a standard plug (overmold ~12.4×6.5) seats fully.
6. **Openings in the front skin:**
   - mic ports above MK1 (−15.9, 17.3) and MK2 (−15.9, 22.1), with gaskets
   - speaker vents over (−8, 10.2)
   - LED light pipe at (0.7, 44.3)
   - **touch pad: 24 × 16 mm electrode on the front membrane's inner face, x −12…12, y −12…4** — i.e. ~10 mm below the camera bump's lower edge. Spring contact to **PNM-MAIN TP11** at (11.0, 4.6); the AT42QT1011 front-end (U6) is on the main board beside the nRF, so the electrode run is short and TOUCH_OUT no longer crosses the FFC
7. **RF:**
   - No copper or metal in the keep-out at x 9–23.5, y 2–16. That covers the nRF chip antenna and the Core1106 Wi-Fi/BT antenna.
   - **LTE antenna pockets** in the soft USB-end wall on either side of the USB channel: x −21…−7.5 and 7.5…18, y −50.5…−47, z 3–10. This only works because there's no metal frame. The FPC antenna part is still to be picked.
8. **Thermal — no spreader, no cutting.** Numbers from [`kicad/tools/thermal_estimate.py`](kicad/tools/thermal_estimate.py):

   | | |
   |---|---|
   | Skin area 186 cm², to-air ≈ **5.4 K/W** | **43 °C skin is reached at ~3.3 W continuous** — that ceiling is set by surface area, not by anything inside |
   | Device heat capacity ≈ 72 J/K, time constant ≈ 6 min | **A 60 s session at 3 W lifts the whole device ~2.3 K** |
   | Modem → shell across a bare 1.5 mm air gap | +8 K at 60 s, but **+36 K at 10 min** |
   | Same step with **one silicone gap pad** | +0.5 K |

   So the burst interaction needs no thermal hardware at all, and the gap pads exist for sustained modes.
   - **The PCB is the spreader.** 4-layer copper goes isothermal in milliseconds. Routing must put a thermal via field under the EG800Q-NA ground pads into both inner planes, stitch the Core1106 GND stamp pads in, and not neck inner copper around the modem. Zero parts, zero assembly.
   - **Two off-the-shelf silicone gap pads**, ≥3 W/mK, 3 mm, pre-cut squares: one on the modem lid (x −15…−3, y −42.5…−31), one on the Core1106 top between the LRA and camera (x −5…2, y 31…37). Compressible, so they absorb the tolerance of a soft shell — which a rigid post cannot. Non-conductive, so unlike copper they impose no antenna or touch keep-outs.
   - **Firmware duty limiting is the real control**, because the ceiling is skin area.
   - **If the bench disagrees:** cast the front shell in thermally conductive silicone (k 1–3, no extra parts, just a different material at mould time), or peel-and-stick pre-cut graphite pads inside the front shell.
   - **Rejected:** the ATS-VC-042 vapor chamber (100 × 40 × 3 mm, 18 g, rated 124 W) — longer than the cavity, no 3 mm layer spare, and it only spreads. Also rejected: the copper-foil + shim-post + putty stack I specced first. It was fiddly to assemble and depended on a rigid post holding pressure against a silicone wall.

## 7. Open items (not frozen, need a decision or a measurement)
- **Routing** both boards: impedance-controlled USB, MIPI and RF; power pours; via-in-pad under the LGA. This is the next KiCad task.
- **LTE antenna part:** pick an FPC antenna (698–2700 MHz, MHF1 pigtail) that fits the USB-end pockets (§6.7), then tune the pi-match. With the metal frame gone this is ordinary RF work. The bench uses an external antenna on the U.FL.
- **CAMERA MODULE — not chosen, and it blocks enclosure L.** The PCB is unaffected (J4's 20P pinout is frozen and every option below uses it), but the bump cannot be modeled until this is settled:
  - **The choice of sensor is much wider than Luckfox's "supported" page suggests.** Their RV1106 SDK ships ISP tuning (IQ) files for `sc3336, sc3338, sc2336, sc230ai, sc231hai, sc200ai, sc4336, sc401ai, sc500ai, sc501ai, sc530ai, sc301iot, gc2053, gc1084, gc2093, gc4023, gc4653, mis2032, mis5001, os02h10, os02k10, os04a10, imx415, sc031gs`, and the SDK kernel carries ~150 sensor drivers. **GC2053 is tuned and supported**, which matters because it's the sensor in most small MIPI FPC modules sold for RK/RV platforms.
  - **Height comes from the lens, not the sensor.** The Waveshare (A)/(B) are ~22 mm tall because of an M12 holder; Hampo's GC2053 module is 18.6 mm because of a 150° F1.9 lens. A 90–110° board lens on the same sensor is far shorter.
  - **What the mechanics actually allow** (measured by sweeping solid clashes, not estimated). The limit is *not* the bump — it's the Core1106 top at z 8.42, the speaker and the LRA sitting right under the module:

    | Bump growth | Largest module that clears |
    |---|---|
    | none | **12 × 12 × 6 mm** (11 × 11 × 6 with the LRA where it is now) |
    | +1 mm | 16 × 16 × 6 mm |
    | +2 mm | 16 × 16 × 7 mm |
    | +3 mm | 16 × 16 × 8 mm |
    | +4 mm | 16 × 16 × 9 mm |

    Anything past 12 × 12 also needs the LRA moved off the camera footprint.
  - **Option A — ship the SC3336 (B) ($9, verified):** needs a Ø14 × 22 mm angled barrel housing. No sourcing, but it's a periscope, not a wearable bump.
  - **Option B — board-lens FPC module (recommended):** RFQ ready to send in [`CAMERA-RFQ.md`](CAMERA-RFQ.md). any sensor from the tuned list above, ≤12 × 12 × 6 mm, 90–110° FOV. Module houses (Sincere, Hampo, CK Vision, Sinoseen) quote at MOQ 3–10. Send them the envelope, the FOV and the pinout; ask for the shortest board lens they stock.
  - **Option C — drop the 30° tilt:** shortens the bump, changes the framing K was designed around.
  - **Connector caveat:** J4 is 20P on the Luckfox pinout, which is what the bench (B) uses. Many compact modules are **24P**. Regenerating J4 for a 24P module is a small change to `design.py`, but the module's drawing and pinout have to come first.
- **Thermal numbers:** skin temperature over a 60 s and a 10 min session, with and without the copper spreader (Phase 0 mock-up: copper tape inside a printed TPU shell).
- **Speaker acoustics** (front volume, vents) — note the vents now sit just above the touch pad.
- **Sustained-mode thermals:** 10 min at 3 W is where the gap pads and duty limiting earn their place. Measure it in Phase 0 before deciding whether the front shell needs conductive silicone.
- **Touch sensitivity:** the battery pouch is ~1–2 mm behind the pad's lower half and the speaker sits just above it; both reduce sensitivity. Tune C25 (Cs) against the final electrode, and consider a foam spacer to hold the electrode off the metal.
- **RF pi-match** R14/C13/C14 values, tuned on the real antenna.
- **Passive specs** in the CSVs are value + footprint only. Use X5R/X7R ≥6.3 V (≥10 V on VBUS/VSYS bulk) and 1% resistors. Pick LCSC part numbers at order time.
