# Pneuma — Bill of Materials & Interconnect

Hardware for the **standalone cellular** Pneuma device: an always-on **wake-island
MCU** that powers an on-demand **Linux session SoC** + **LTE Cat-1 bis modem** +
camera. Rationale: [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) (ADR-0001,
-0006); evidence: [`../docs/RESEARCH.md`](../docs/RESEARCH.md).

> **Altitude note.** Block-level BOM + interconnect — enough to order parts and
> prototype, and to structure the firmware. Not a schematic: exact passives, PMIC
> rails, RF matching/antenna, thermal stackup, and mechanical come after bench
> validation. Prices are rough, one-off.

---

## 1. Bill of materials

| # | Block | Recommended part | ~Price | Notes / alternates |
|---|-------|------------------|--------|--------------------|
| 1 | **Wake island MCU** | Nordic **nRF52840** module | ~$5 | Always-on KWS + button + power control + BLE (setup). Alt: **Syntiant NDP120** (<1 mW KWS + beamforming) as a front-end. |
| 2 | **Session SoC** | Rockchip **RV1106(G3)** (Cortex-A7 + ISP + ~0.5–1 TOPS NPU) | ~$8–12 | Tiny Linux; native MIPI camera ISP + HW JPEG. Alt: Allwinner V851S, NXP i.MX 8M (more power/heat). |
| 3 | **Cellular modem** | Quectel **EG915U** (LTE Cat-1 bis, ~24×20×2.4 mm) | ~$8–15 | Single antenna, full-duplex, data-only (voice-over-data). Alt: Sequans Calliope 2, Telit ELS63. |
| 4 | **Camera** | small **MIPI-CSI** sensor (e.g. OV/GC 2–5 MP) via RV1106 ISP | ~$3–8 | On-demand single JPEG; power-gated off otherwise. |
| 5 | **Microphone** | Infineon **IM69D130** (PDM MEMS) | ~$3 | Monitored by wake island for KWS; routed to SoC in session. |
| 6 | **Audio amp** | **MAX98357A** (I2S Class-D) | ~$6 | Driven by SoC I2S during sessions. |
| 7 | **Speaker** | 20 mm 8 Ω ~1 W | ~$2 | Fire upward toward the face. |
| 8 | **Haptics** | LRA + **DRV2605L** | ~$4 | State cues. |
| 9 | **Indicator** | RGB LED (or WS2812) + optical window (clear PC / translucent silicone / light-pipe) | ~$0.50 | + earcons. Window is sealed (§ENCLOSURE). |
| 10 | **Button** | momentary tactile | ~$0.20 | To wake island (wake / push-to-talk / power). |
| 11 | **SIM** | **SGP.32 eSIM** or on-die **iSIM** | ~$1–3 | Remote-provisionable, no UI. iSIM (e.g. Sony ALT-class) saves most space. |
| 12 | **PMIC / power-path** | power-path charger+regulator (e.g. TI BQ25xxx; or RV1106 ref PMIC) | ~$2–4 | Holds system rail up during modem TX while cell sags. |
| 13 | **Bulk cap** | 100–470 µF low-ESR + MLCC array at modem VBAT | ~$1 | LTE = steady draw, no 2G spikes → no supercap needed. |
| 14 | **Battery** | LiPo pouch ~**5–7 × 36 × 72 mm → ~2000–2500 mAh** (forms the thin slab) | ~$6–10 | ~10 h+ talk / multi-day on-demand. Shrink later if slimming thickness. |
| 15 | **Charging + data** | **waterproof USB-C** receptacle (gasket-sealed to PCB) | ~$1–3 | Power + data: flashing, dev/debug, OTA recovery. Sealed IP68-phone-style; gasket wraps the opening. |
| 16 | **Thermal** | **aluminum unibody** (radiator) + TIM/pads on modem PA & SoC + graphite spreader + skin-side insulator | ~$3–8 | Body *is* the heat exchanger (ADR-0006/0007). Strap the 2 hot parts only. |
| 17 | **Antenna** | FPC PIFA (LTE) behind a **non-conductive RF window**, isolated from the aluminum, edge-placed away from body | ~$1 | Metal body = Faraday cage; the window is mandatory (ADR-0007). |
| 18 | **Waterproof seal** | printed **silicone gasket** | ~$1 | Seals body halves + around RF window; target IP68. |
| 19 | **Acoustic membranes** | Gore/Saati waterproof vents over mic + speaker | ~$1–2 | Pass sound, block water; one doubles as pressure-equalization vent. |
| 20 | **Attachment** | magnet clamp (passive skin-side) / lanyard / clip | ~$1–3 | Skin-side piece must stay passive + cool (Ai Pin lesson). |

Indicative core cost (one-off, ex-PCB/enclosure): **~$60–100**, dominated by SoC,
modem, and camera.

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
- Runtime: ~1–3 h continuous talk; all-day on the on-demand burst model.

---

## 4. Open items before schematic capture

- [ ] Confirm session SoC (RV1106 vs Allwinner V vs i.MX 8M) against the realtime
      WebRTC/TLS + camera workload and its idle/boot-time power.
- [ ] Validate wake-island → SoC cold-boot/resume latency (affects "feel").
- [ ] Bench modem TX current + needed bulk capacitance on the chosen cell.
- [ ] Thermal mock-up: measure skin-side temp during a sustained session; size the
      graphite spreader; resolve antenna-vs-spreader contention for the outer face.
- [ ] eSIM (SGP.32) vs iSIM module selection + data provider (Soracom/Hologram).
- [ ] Camera sensor + lens choice (and default resolution/quality for transfer size).
- [ ] Secure storage for keys + memory file (SoC secure boot / encrypted flash).
