# Pneuma — Bill of Materials & Interconnect

Hardware for the **standalone cellular** Pneuma device: an always-on **wake-island
MCU** that powers an on-demand **Linux session SoC** + **LTE Cat-1 bis modem** +
camera. Rationale: [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) (ADR-0001,
-0006, -0007); evidence: [`../docs/RESEARCH.md`](../docs/RESEARCH.md).

> **Sourcing status (verified 2026-05).** Every line below is single-unit
> orderable by a solo maker. Prices are ~qty-1 USD, ±20%. **STEP/CAD found for 5
> of 7 enclosure-critical parts** (only the camera and a prototyping carrier need
> caliper measurement). Verify the camera FFC pin count and the exact USB-C IP
> suffix on datasheets before ordering.

---

## 1. Bill of materials (buildable)

| # | Block | Orderable part | Buy at | ~$ | CAD/STEP | Notes |
|---|-------|----------------|--------|----|----------|-------|
| 1 | **Cellular modem** | **Quectel EG915U-EU** (Cat-1 bis, LGA-126, 23.6×19.9×2.4 mm) | LCSC `C5248292`, 4gltemall | 8–12 | ✔ SnapEDA (`EG915UEUAB-N05-SNNSA`) | Design part; LGA = **reflow only** (see prototyping path). |
| 2 | **Session SoC** | **Luckfox Pico Ultra** (RV1106G3, 256 MB, 8 GB eMMC, MIPI-CSI) | luckfox.com, Waveshare | 23–28 | ✔ official wiki `.step` | In stock, single unit. Alt: Pico Max (~$13). |
| 3 | **Camera** | **SC3336 3MP Module (B)** (MIPI-CSI, F2.0) | luckfox.com | 9 | ✘ measure | Luckfox-native FFC; **confirm 15P vs 20P** against the Ultra connector. |
| 4 | **Wake-island MCU** | **Raytac MDBT50Q-1MV2** (nRF52840, 10.5×15.5×2.05 mm) | Digi-Key, Adafruit `4078` | 6 | ✔ SnapEDA/UL STEP | nRF52840 does the always-on KWS itself (Syntiant dropped — see gotchas). BLE for setup. |
| 5 | **Microphone** | **Infineon IM69D130V01XTSA1** (PDM, 4.0×3.0 mm) | Digi-Key | 2–3 | ✔ SnapEDA/UL STEP | Bottom-port; Adafruit `4346` breakout for breadboarding. |
| 6 | **Audio amp** | **MAX98357A** (bare, or Adafruit `3006`) | Digi-Key / Adafruit | 1–6 | ✔ bare-IC SnapEDA STEP | I2S Class-D. |
| 7 | **Speaker** | **Same Sky/CUI CES-20134-088PM** (20 mm, 8 Ω, 0.8 W) | Digi-Key | 3–5 | ✔ Same Sky STEP | Fire upward toward the face. |
| 8 | **Haptic driver** | **DRV2605L** (bare, or Adafruit `2305`) | Digi-Key / Adafruit | 2–8 | ✔ bare-IC SnapEDA STEP | |
| 9 | **LRA** | **Vybronics VG1040003D** (10×3 mm, Z-axis) | Digi-Key | 3–6 | ✔ Vybronics drawing/STEP | |
| 10 | **Indicator** | RGB LED (e.g. WS2812B) + optical window | Digi-Key | 0.50 | ✔ generic | Window sealed (§ENCLOSURE). |
| 11 | **PMIC / power-path** | **TI BQ24074** (bare, 1.5 A power-path) | Digi-Key | 2 | ✔ SnapEDA STEP | Adafruit `4755` to prototype. Step up to **BQ25895** (5 A, I²C) if TX headroom demands. |
| 12 | **Battery** | **PKCell LP803860** 2000 mAh (8×36×60 mm, JST-PH) | Adafruit `2011` | 12.50 | ✔ datasheet drawing | Standard catalog cell (see §ENCLOSURE for the slab geometry). |
| 13 | **Waterproof USB-C** | **GCT USB4500-03-1-A** (IP67/68, mid-mount) | Mouser | 1–2 | ✔ GCT STEP | Power **+ data** (flash/dev/recovery). |
| 14 | **Cellular antenna** | **Taoglas FXUB63.07.0150C** (698–3000 MHz FPC, 96×21×0.2 mm, U.FL) | Digi-Key `931-1329-ND` | 6.50 | ✔ TraceParts STEP | Mounts on an edge behind the gasket RF window. |
| 15 | **eSIM (MFF2)** | **Soracom** `SGEIL01-01-10` / **sysmocom** sysmoEUICC1 (5×6×0.75 mm) | Soracom store / sysmocom | ~5–10/ea | ✔ std MFF2 footprint | Sold in packs. SGP.32 IoT-eSIM in pre-order. Or a nano-SIM slot to start. |
| 16 | **Acoustic vents** | **Gore GAW331** (IP67/68) over mic + speaker | Gore sample request | sample | n/a | Generic ePTFE adhesive vent for prototypes. |
| 17 | **Thermal** | aluminum unibody + graphite spreader + TIM pads (modem PA & SoC) + skin-side insulator | Digi-Key (TIM) / fab | 3–8 | — | Body *is* the heat exchanger (ADR-0006/0007). |
| 18 | **Waterproof seal** | printed **silicone gasket** (seal + RF window + LED window) | fab / cast | 1 | — | Target IP68; two anodized aluminum shells. |
| 19 | **Attachment** | magnet clamp (passive skin-side) / lanyard / clip | — | 1–3 | — | Skin-side piece stays passive + cool (Ai Pin lesson). |

Indicative core electronics cost (qty 1, ex-PCB/enclosure): **~$90–130**, dominated
by the SoC board, modem, and battery.

### Prototyping path (before a custom PCB)
- **Cellular without reflow:** **LilyGO T-A7670G R2** (SIMCom A7670 Cat-1 + SIM
  slot + USB + charger), ~$18–23 — get the cellular link working, then move to a
  bare EG915U on your own PCB (its SnapEDA STEP gives the pad layout).
- **Brain:** Luckfox Pico Ultra + SC3336 camera (both Luckfox-native, plug in).
- **Breadboard the rest:** Adafruit breakouts for the mic (`4346`), amp (`3006`),
  haptics (`2305`), charger (`4755`) — solder later.

### Sourcing gotchas + workarounds
- **EG915U is reflow-only** (LGA-126). Prototype on the LilyGO A7670 board; reflow
  the EG915U at home with a stencil + hotplate for the final build.
- **Syntiant NDP120 isn't buyable bare** (NDA/volume). Workaround: **drop it** —
  the nRF52840 alone handles always-on wake-word. (Arduino Nicla Voice carries an
  NDP120 if you ever want the ultra-low-power KWS path.)
- **eSIM has no clean single-unit** — buy a Soracom/sysmocom 10-pack, or start with
  a nano-SIM slot.
- **Gore vents aren't on distributors** — request samples, or use a generic ePTFE
  vent for prototypes.
- **No vendor STEP** for the SC3336 camera or LilyGO carrier — measure with calipers
  (both are simple rectangular boards).

---

## 2. Interconnect map

```
   USB-C ──VBAT/charge──▶ PMIC (power-path) ──▶ system rails ──┬─────────────────────┐
                                                              │                      │
   ┌──────────── WAKE ISLAND (nRF52840, always on) ───────────┴───┐                  │
   │  PDM mic (IM69D130) ─▶ wake-word KWS (DS-CNN/TFLM)            │                  │
   │  BUTTON ─▶ GPIO (IRQ)                                         │                  │
   │  BLE ─▶ provisioning (setup only)                            │                  │
   │  GPIO_SOC_EN ─▶ SoC power enable (load switch / PMIC EN)      │                  │
   │  UART  ◀───────────────────────────────────────────────────┐ │                  │
   └────────────────────────────────────────────────────────────┼─┘                  │
                                                                 │ control            │
   ┌──────────── SESSION BRAIN (RV1106 Linux, on-demand) ────────┴──────────────────┐ │
   │  UART  ◀─▶ wake island (wake reason, state, "done/sleep")                       │ │
   │  USB / UART(PPP) ─▶ Quectel EG915U modem ──▶ [eSIM/iSIM] ──▶ FPC antenna        │◀┘
   │  MIPI-CSI ◀─ camera sensor      GPIO_CAM_EN ─▶ camera power gate                 │
   │  I2S ─▶ MAX98357A ─▶ speaker    PDM/I2S ◀─ mic (in session)                      │
   │  I2C ─▶ DRV2605L (haptics), fuel gauge      GPIO ─▶ RGB LED                      │
   │  SPI-NAND/eMMC ─▶ OS + memory file (encrypted)                                   │
   └──────────────────────────────────────────────────────────────────────────────────┘
```

### Bus / interface summary
| Interface | Between | Purpose |
|-----------|---------|---------|
| UART | wake island ↔ SoC | wake reason, state handshake, sleep |
| GPIO (SOC_EN) | wake island → PMIC/SoC | power the session tier up/down |
| USB or UART+PPP | SoC ↔ modem | cellular data link |
| MIPI-CSI | camera → SoC ISP | on-demand JPEG |
| I2S | SoC → amp | speaker audio |
| PDM | mic → wake island (always) / SoC (session) | mic capture |
| I2C | SoC ↔ DRV2605L, fuel gauge | haptics, battery |
| BLE | wake island ↔ browser | one-time provisioning only |

### Physical interconnect: bench vs. enclosure

This device **can't be classically breadboarded** — the modem (USB), SoC↔camera
(MIPI-CSI), and antenna (RF) links break over jumper wires. Connect by bus speed:

**Bench (dev boards, not raw chips):**
- **Slow buses → Dupont jumpers** (optionally on a solderless breadboard hosting
  breakouts): I²C, UART, GPIO, power.
- **Fast/special links → native cables, never jumpers:** camera = FFC ribbon;
  modem = USB cable; antenna = U.FL coax pigtail.
- Boards: Luckfox Pico (RV1106), a Cat-1 modem carrier/HAT, nRF52840 dev kit,
  Adafruit/SparkFun breakouts (amp/mic/haptics). Optional next step: protoboard or
  a carrier PCB the modules plug into via headers.

**Enclosure (soldered, custom PCB):**
| Connector | Use |
|-----------|-----|
| Board-to-board (Hirose DF40 / BTB) | stack the two PCBs (slab ↔ plateau) |
| FFC/FPC flex (Molex/Hirose 0.5–1.0 mm) | camera; routing around corners |
| JST-PH / JST-SH | battery, speaker (removable) |
| U.FL / IPEX MHF | modem → FPC antenna coax |
| Pogo pins | programming/test points |

Maps to a **two-board stack**: main/battery board (slab) + SoC+modem board
(plateau), joined by one BTB connector or short flex; camera/antenna/speaker/mic/
USB-C hang off on flex/JST. USB and MIPI need impedance-controlled traces (a
KiCad PCB job, not hand wiring).

---

## 3. Power & thermal targets (validate on bench)

| State | Approx power | Notes |
|-------|--------------|-------|
| Sleep (wake island only) | µA–few mA | SoC + modem fully off |
| Active session (streaming) | ~2–4 W | modem ~0.8 A + SoC; the heat driver |
| Camera capture (brief) | + sensor power | gated off otherwise |

- Skin-facing surface must stay **≤43 °C** (target ≤40–42 °C). Strategy: on-demand
  bursts + passive graphite/Cu spreading to an outward face + skin-side insulation.
- LTE draws steadily during a session (no 2 G micro-spikes) → single LiPo + bulk
  cap + power-path PMIC; no supercap required.
- Runtime: ~10 h+ continuous talk on a 2000 mAh cell; multi-day on the on-demand
  burst model.

---

## 4. Open items before schematic capture

- [ ] Confirm session SoC (Luckfox Pico Ultra / RV1106) against the realtime
      WebRTC/TLS + camera workload and its idle/boot-time power.
- [ ] Validate wake-island → SoC cold-boot/resume latency (affects "feel").
- [ ] Bench modem TX current + needed bulk capacitance on the chosen cell.
- [ ] Thermal mock-up: skin-side temp during a sustained session; size the
      graphite spreader; resolve antenna-vs-spreader contention for the outer face.
- [ ] Confirm SC3336 FFC pin count + GCT USB-C IP suffix on datasheets.
- [ ] eSIM (Soracom/SGP.32) provisioning + data plan.
- [ ] Secure storage for keys + memory file (SoC secure boot / encrypted flash).
