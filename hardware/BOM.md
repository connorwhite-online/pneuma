# Pneuma — Bill of Materials & Interconnect

Hardware core for the Pneuma pendant: a **single Nordic nRF5340** driving an
**ArduCAM Mega SPI camera**, with native audio in/out and BLE. Rationale is in
[`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) (ADR-0001); the evidence is
in [`../docs/RESEARCH.md`](../docs/RESEARCH.md).

> **Altitude note.** This is a *block-level* BOM and interconnect map — enough to
> order parts and breadboard the system, and to drive the firmware peripheral
> setup. It is **not** a schematic: exact passives (decoupling, pull-ups,
> matching network), the RF antenna layout, and final mechanical/enclosure design
> come after this is validated on the bench. Prices are rough and for one-off
> quantities.

---

## 1. Bill of materials

| # | Block | Recommended part | Interface | ~Price | Notes / alternates |
|---|-------|------------------|-----------|--------|--------------------|
| 1 | **MCU + BLE** | Nordic **nRF5340** module — Raytac **MDBT53-1M** (certified, antenna onboard) | — | ~$10 | Alt: Fanstel module, or bare nRF5340 if you do your own RF. Seeed XIAO nRF52840 is a cheaper/more-accessible fallback but lacks the audio PLL / LC3 headroom. |
| 2 | **Camera** | **ArduCAM Mega 3MP** SPI (on-chip JPEG) | SPI + 1 GPIO (power gate) | ~$30 | 5MP (autofocus) ~$40–50. SPI SCLK ≤ 8 MHz. |
| 3 | **Microphone** | Infineon **IM69D130** (PDM MEMS, 69 dB SNR, 130 dBSPL AOP) | PDM (CLK + DATA) | ~$3 | Alt: Knowles SPH0645 (I2S, hobbyist-friendly), TDK T5838 (PDM + acoustic-activity wake). |
| 4 | **Audio amp** | **MAX98357A** (I2S Class-D, 1.8 W @ 8 Ω) | I2S (BCLK/LRCLK/DIN) + SD GPIO | ~$6 (breakout) | Bare IC cheaper at volume. |
| 5 | **Speaker** | 20 mm 8 Ω ~1 W micro speaker | amp output | ~$2 | Fire upward toward the face. |
| 6 | **Haptics** | LRA + **TI DRV2605L** driver | I2C + EN GPIO | ~$4 | LRA > ERM (crisper, lower power). |
| 7 | **Indicator** | RGB LED (common-cathode) or single WS2812 | 3× GPIO (or 1 for WS2812) | ~$0.50 | Glanceable state, redundant w/ haptics. |
| 8 | **Button** | momentary tactile switch | GPIO (interrupt + wake) | ~$0.20 | tap / double-tap / long-press. |
| 9 | **Charger** | Microchip **MCP73831** (500 mA linear LiPo) | USB-C VBUS → BAT | ~$1 | Alt: TI **BQ25180** (I2C, tiny, ship-mode) for the smallest build. |
| 10 | **Fuel gauge** | Analog Devices **MAX17048** (<5 µA, no sense R) | I2C | ~$2 | Optional but recommended for battery %. |
| 11 | **Camera power gate** | Load switch **TPS22919** (µA-class off-leakage) | controlled by 1 GPIO | ~$0.50 | Keeps the camera fully off except during capture. |
| 12 | **Battery** | LiPo pouch ~250 mAh (single cell, 3.7 V) | via charger/PMIC | ~$5 | 250 mAh ≈ sweet spot (~33–67 h listening). 500 mAh for ~2× runtime. |
| 13 | **USB-C** | USB-C receptacle + 2× 5.1 kΩ CC pulldowns | VBUS → charger; D+/D- → nRF USB (DFU) | ~$1 | Charging + firmware DFU/flashing. |
| 14 | **Regulation** | nRF5340 **internal DC/DC** (enable it) + LDO/buck for 3.3 V camera rail | — | ~$1 | nRF current specs assume DC/DC on. |

Indicative core cost (one-off, ex-enclosure/PCB): **~$70–90**, dominated by the
camera and module.

---

## 2. Interconnect map (which nRF5340 peripheral talks to what)

```
                              ┌──────────────────────────┐
        USB-C ──VBUS──▶ MCP73831 ──▶ LiPo 250mAh ──┐      │
          │  (CC 5.1kΩ ×2)                          │      │
          └── D+/D- ───────────────────────────────┼──────┤ nRF5340 USB (DFU/flash)
                                                    │      │
                                  ┌── 3V3 rail ◀────┘      │
                                  │   (nRF internal DC/DC) │
                                  ▼                        │
   ┌─────────── SPI ────────────────────────┐             │
   │  SCK, MOSI(→cam), MISO(←cam), CS        │── ArduCAM Mega (SPI slave, ≤8MHz)
   │  + GPIO_CAM_EN ─▶ TPS22919 load switch ─┼──▶ camera 3V3 (gated ON only to shoot)
   └─────────────────────────────────────────┘             │
                                                            │
   PDM:  GPIO_PDM_CLK ─▶ IM69D130 CLK                       │
         IM69D130 DATA ─▶ GPIO_PDM_DIN                      │   nRF5340
                                                            │  (app core:
   I2S:  BCLK, LRCLK(WS), SDOUT ─▶ MAX98357A ─▶ speaker     │   audio + KWS;
         GPIO_AMP_SD ─▶ MAX98357A shutdown                  │   net core: BLE)
                                                            │
   I2C (shared bus, pull-ups):                              │
         SDA/SCL ─▶ DRV2605L (haptics)  ─ GPIO_HAP_EN       │
         SDA/SCL ─▶ MAX17048 (fuel gauge)                   │
                                                            │
   GPIO: BUTTON ─▶ GPIO (IRQ + wake-from-sleep)             │
         RGB LED ─▶ 3× GPIO  (or 1× GPIO → WS2812)          │
                                                            │
   SWD:  SWDIO / SWCLK pads (programming/debug)             │
                              └──────────────────────────────┘
```

### Bus / pin allocation summary
| Bus | nRF peripheral | Devices |
|-----|----------------|---------|
| SPI (≤8 MHz) | SPIM | ArduCAM Mega (slave) |
| PDM | PDM | IM69D130 mic |
| I2S | I2S | MAX98357A amp → speaker |
| I2C | TWIM | DRV2605L, MAX17048 |
| GPIO | — | button (IRQ/wake), camera load-switch EN, amp SD, RGB LED, haptic EN |
| USB | USBD | charging + DFU/flashing |
| SWD | — | debug/programming |

---

## 3. Power states (design targets, validate on bench)

| State | Approx current | Notes |
|-------|----------------|-------|
| Deep sleep (button-wake only) | ~µA | System OFF; RAM off |
| Idle, listening for wake word | ~3–8 mA | CPU + PDM + periodic BLE — the dominant state |
| Streaming audio (in conversation) | ~5–10 mA | LC3 over BLE |
| Camera capture (brief) | +55–150 mA | ArduCAM active; gated off otherwise |
| BLE photo transfer (brief) | radio-bound | 10–50 KB JPEG in ~0.06–0.4 s @ 2M PHY |

Battery life on 250 mAh (≈80% usable) at the dominant listening current:
**~33–67 h** depending on duty cycle. (See RESEARCH.md for sourcing and caveats.)

---

## 4. Open items before schematic capture

- [ ] Bench-validate single-JPEG-over-BLE transfer time on target phones (iOS +
      Android negotiate PHY/connection interval and may cap throughput).
- [ ] Bench-validate ArduCAM Mega JPEG size for typical scenes/quality (the
      10–50 KB band is extrapolated, not from a spec table).
- [ ] Select and train the Cortex-M wake-word model; measure real always-on KWS
      current on the nRF5340 (no published benchmark found).
- [ ] Decide camera resolution/quality default (QVGA–VGA keeps frames small;
      higher res for "read this text" use cases at the cost of transfer time).
- [ ] Confirm module choice (Raytac MDBT53-1M vs bare nRF5340 + own RF) and the
      3.3 V camera rail regulator.
- [ ] Antenna keep-out / placement for the chosen module (feeds enclosure design).
