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
>
> **Links:** Buy/CAD links go to the product page where verified, otherwise a
> Digi-Key / SnapEDA **search by part number** (always resolves the part) — confirm
> stock and the exact variant at checkout. The part numbers are the durable
> reference; URLs drift.

---

## 1. Bill of materials (buildable)

| # | Block | Orderable part | Buy at | ~$ | CAD/STEP | Notes |
|---|-------|----------------|--------|----|----------|-------|
| 1 | **Cellular modem** | **Quectel EG915U-EU** (Cat-1 bis, LGA-126, 23.6×19.9×2.4 mm) | [LCSC `C5248292`](https://jlcpcb.com/partdetail/Quectel-EG915UEU/C5248292) · [4gltemall](https://www.4gltemall.com/quectel-eg915u.html) | 8–12 | [SnapEDA](https://www.snapeda.com/search/?q=EG915U) | Design part; LGA = **reflow only** (see prototyping path). |
| 2 | **Session SoC** | **Rockchip RV1106G3** (256 MB — the G3 RAM matters for the TLS/audio stack) | bare: [LCSC](https://www.lcsc.com/search?q=RV1106) · dev: [Luckfox Pico Ultra](https://www.luckfox.com/EN-Luckfox-Pico-Ultra) | ~6–10 | [wiki `.step`](https://wiki.luckfox.com/Luckfox-Pico-RV1106/Downloads/) | Price = **bare chip** (the $25 Pico Ultra is a *dev* cost, not a board component). Confirmed by SoC deep pass (RESEARCH §8 / ADR-0009). Productize on a custom bare-RV1106G3 PCB. Fallback for one-chip BT: RK3566. |
| 2b | **Bluetooth-audio chip** | **Microchip BM83** (BM83SM1-00Tx, AT/source firmware) | [DigiKey](https://www.digikey.com/en/products/result?keywords=BM83SM1-00TA) · [Microchip](https://www.microchip.com/en-us/product/bm83) | ~12 | [Microchip BM83](https://www.microchip.com/en-us/product/bm83) | Owns A2DP **source** + HFP (earbud mic) + AAC via I²S + UART — offloads BT audio off the RV1106's weak BlueZ (ADR-0009). Needs its own 2.4 GHz antenna. |
| 3 | **Camera** | **SC3336 3MP Module (B)** (MIPI-CSI, F2.0) | [Waveshare](https://www.waveshare.com/sc3336-3mp-camera-b.htm) · luckfox.com | 9 | ✘ measure | Luckfox-native FFC; **confirm 15P vs 20P** against the Ultra connector. |
| 4 | **Wake-island MCU** | **Raytac MDBT50Q-1MV2** (nRF52840, 10.5×15.5×2.05 mm) | [Adafruit `4078`](https://www.adafruit.com/product/4078) · [Digi-Key](https://www.digikey.com/en/products/result?keywords=MDBT50Q-1MV2) | 6 | [SnapEDA](https://www.snapeda.com/search/?q=MDBT50Q-1MV2) | nRF52840 does the always-on KWS itself (Syntiant dropped — see gotchas). BLE for setup. |
| 5 | **Microphone** | **Infineon IM69D130V01XTSA1** (PDM, 4.0×3.0 mm) | [Digi-Key](https://www.digikey.com/en/products/result?keywords=IM69D130V01XTSA1) · breakout [Adafruit `4346`](https://www.adafruit.com/product/4346) | 2–3 | [SnapEDA](https://www.snapeda.com/search/?q=IM69D130) | Bottom-port. |
| 6 | **Audio amp** | **MAX98357A** (bare, or Adafruit `3006`) | [Adafruit `3006`](https://www.adafruit.com/product/3006) · [Digi-Key](https://www.digikey.com/en/products/result?keywords=MAX98357AETE%2BT) | 1–6 | [SnapEDA](https://www.snapeda.com/search/?q=MAX98357A) | I2S Class-D. |
| 7 | **Speaker** | **PUI Audio AS01808MR-R** (18 mm, 8 Ω, 1 W, wire leads) | [Digi-Key](https://www.digikey.com/en/products/result?keywords=AS01808MR-R) · maker: [Adafruit `3923`](https://www.adafruit.com/product/3923) / [SparkFun](https://www.sparkfun.com/mini-speaker-1w-8-ohm.html) | 2–4 | [Digi-Key](https://www.digikey.com/en/products/result?keywords=AS01808MR-R) | In stock, ships same-day. Fire upward toward the face. (Same Sky CES-20134-088PM was out of stock.) |
| 8 | **Haptic driver** | **DRV2605L** (bare, or Adafruit `2305`) | [Adafruit `2305`](https://www.adafruit.com/product/2305) · [Digi-Key](https://www.digikey.com/en/products/result?keywords=DRV2605LDGSR) | 2–8 | [SnapEDA](https://www.snapeda.com/search/?q=DRV2605L) | |
| 9 | **LRA** | **Vybronics VG1040003D** (10×3 mm, Z-axis) | [Vybronics](https://www.vybronics.com/coin-vibration-motors/lra/v-g1040003d) · [Digi-Key](https://www.digikey.com/en/products/result?keywords=VG1040003D) | 3–6 | [Vybronics drawing](https://www.vybronics.com/coin-vibration-motors/lra/v-g1040003d) | |
| 10 | **Indicator** | RGB LED (e.g. WS2812B) + optical window | [Adafruit `1938`](https://www.adafruit.com/product/1938) · [Digi-Key](https://www.digikey.com/en/products/result?keywords=WS2812B) | 0.50 | ✔ generic | Window sealed (§ENCLOSURE). |
| 11 | **PMIC / power-path** | **TI BQ24074** (bare, 1.5 A power-path) | [Digi-Key](https://www.digikey.com/en/products/result?keywords=BQ24074RGTR) · proto [Adafruit `4755`](https://www.adafruit.com/product/4755) | 2 | [SnapEDA](https://www.snapeda.com/search/?q=BQ24074) | Step up to **BQ25895** (5 A, I²C) if TX headroom demands. |
| 12 | **Battery** | **PKCell LP803860** 2000 mAh (8×36×60 mm, JST-PH) | [Adafruit `2011`](https://www.adafruit.com/product/2011) | 12.50 | datasheet drawing | Standard catalog cell (see §ENCLOSURE for the slab geometry). |
| 13 | **Waterproof USB-C** | **GCT USB4500-03-1-A** (IP67/68, mid-mount) | [Digi-Key](https://www.digikey.com/en/products/result?keywords=USB4500-03-1-A) · [GCT](https://gct.co) | 1–2 | [GCT STEP](https://gct.co) | Power **+ data**. Verified IP67 alt: GCT USB4715 ([Mouser](https://www.mouser.com/ProductDetail/GCT/USB4715-GF-A?qs=vvQtp7zwQdPhXuRDaiXpdQ%3D%3D), [STEP](https://gct.co/connector/usb4715)). |
| 14 | **Cellular antenna** | proto: **Molex 2091420180** flex (85×14.5 mm, U.FL); product: **Pulse W3796** SMD (**40×7×3 mm**, 698–2700 MHz, >65% eff.) | [flex (Digi-Key)](https://www.digikey.com/en/products/detail/molex/2091420180/10057542) · [W3796 (Digi-Key)](https://www.digikey.com/en/products/result?keywords=W3796) · pigtail [Adafruit `852`](https://www.adafruit.com/product/852) | 3–7 | [Molex 3D](https://www.molex.com/en-us/products/part-detail/2091420180) | Flex = plug-and-play U.FL for the bench. **W3796 halves the footprint on the product PCB** (full band; needs a ground-plane keepout). Tinier chips (Ignion NN03-310, 30×3 mm) want a ~100 mm ground plane → low-band drops on our 80 mm body. |
| 15 | **SIM / data** | **removable IoT SIM** — Soracom Plan01s *or* Hologram (single-unit, cuts to nano) | [Soracom](https://store.soracom.io/product/soracom-global-iot-industrial-sim/) · [Amazon 1-pack](https://us.amazon.com/dp/B01M30ZYR5) · [Hologram](https://store.hologram.io/) | ~5–6 + data | n/a | Pops into the LilyGO/Waveshare SIM slot — **this is what you order**. The **MFF2 solderable eSIM** (Soracom SGEIL01 / sysmocom, sold in packs) is a **production-PCB-only** item, not needed now. |
| 16 | **Acoustic vents** | **Gore GAW331** (IP67/68) over mic + speaker | [Gore](https://www.gore.com/products/categories/venting) (sample) | sample | n/a | MOQ/sample-gated; generic ePTFE adhesive vent for prototypes. |
| 17 | **Thermal** | aluminum unibody + graphite spreader + TIM pads (modem PA & SoC) + skin-side insulator | Digi-Key (TIM) / fab | 3–8 | — | Body *is* the heat exchanger (ADR-0006/0007). |
| 18 | **Waterproof seal** | printed **silicone gasket** (seal + RF window + LED window) | fab / cast | 1 | — | Target IP68; two anodized aluminum shells. |
| 19 | **Attachment** | magnet clamp (passive skin-side) / lanyard / clip | — | 1–3 | — | Skin-side piece stays passive + cool (Ai Pin lesson). |

### Component total (one board's worth of parts, qty 1)

The parts **are** cheap individually — they just sum across ~25 line items:

| Big-ticket items | ~$ |
|---|---|
| Battery (2000 mAh) | 12.5 |
| BM83 Bluetooth-audio | 12 |
| Cellular modem (EG915U) | 10 |
| Camera (SC3336) | 8 |
| SoC (bare RV1106G3) | 8 |
| nRF52840 module | 6 |
| LRA + speaker + thermal/graphite | ~12 |
| Everything else (mic, amp, PMIC, LED, USB-C, antenna, SIM, gasket, magnet, passives, FFC/BTB connectors) | ~35 |
| **Σ ≈** | **~$95–130 / board** |

So **the bill of *materials* is ~$110 — that part is genuinely cheap.** What makes a
*first custom board* expensive is **not the parts**; it's assembly setup + respins
(next section). Per-unit drops toward this ~$110 at volume.

### Development path (cost-optimized — don't buy a pile of breakouts)

What needs validating before a custom PCB is mostly **software/integration, not
tuning** — and it's cheap to retire on **one or two integrated dev boards**, not a
bag of breakouts. The actual *tuning* (RF, power, thermal) can't be done until the
real board + enclosure exist, so it happens *on* the PCB regardless (plan ≥2 spins).

**Recommended dev kit (~$55–65, validate → then commit the PCB):**
- **Laptop** — the Rust session app already runs here (mocks). **$0.**
- **Luckfox Pico Ultra (~$30)** — one board that *is* RV1106 + onboard audio codec +
  mic + Wi-Fi/BT + camera connector + eMMC. It replaces ~5 breakouts, and it's the
  right board to answer the **make-or-break BT-audio question** (same AIC8800-class BT
  you'd ship). *(This supersedes the earlier "skip the Ultra" note — for a
  no-breakouts plan the Ultra is the cheapest path once you count the parts it bundles.)*
- **Cellular board (~$20–28)** — [LilyGO T-A7670G R2](https://lilygo.cc) or
  [Waveshare SIM7670G HAT](https://www.waveshare.com/sim7670g-lte-cat-1-gnss-hat.htm)
  (modem + SIM slot + antenna) to bring up the realtime cellular loop.
- **IoT SIM (~$5)** + a **small speaker (~$2)**. *(optional)* **BM83 EVB** only if you
  want to prove the dedicated-chip A2DP path specifically.
- **Skip** the mic/amp/Wi-Fi/charger/LED breakouts — redundant with the Pico Ultra.

**If you own a Raspberry Pi:** use it for the cloud/architecture proof ($0; *not* the
real SoC), then treat custom-PCB spin #1 as your RV1106 bring-up — saves the Ultra,
but accepts RV1106-specific risk (its BT/ISP/power) landing first on a real board.

**Straight to a custom PCB as board-spin-1?** You *can* bench a custom board — but for
*this* stack it's a gamble, because two unknowns are painful to discover on a ~$300
board yet trivial on a $30 one:
1. **Does A2DP-to-earbuds actually work** on your chosen BT path?
2. **Does the RV1106 run app + camera + modem concurrently** under your stack?
Find those on the Pico Ultra + cellular board first; *then* lay out the PCB.

**What you genuinely can't pre-tune (so expect ≥2 PCB spins regardless):** antenna
matching + 4-radio co-existence, the RF window, power-path under modem TX bursts, and
skin-side thermals — all need the real board in the real enclosure. So you're right
that there's little *pre-PCB tuning* — but a ~$60 integration spike still saves a
wasted spin.

**Production-only (don't order now):** bare Quectel EG915U (reflow → dev board), MFF2
eSIM chip (→ removable SIM), Gore vent (MOQ → generic ePTFE for proto), Pulse W3796
antenna (dev board has its own), bare ICs (the Ultra/EVB cover them).

**Link caveats:** Digi-Key / SnapEDA links are *search-by-part-number* (always
resolve + show stock); vendor deep links may drift — the **part number is the durable
reference**. Confirm the **SC3336 FFC pin count (15P vs 20P)** and the **BM83
"AT"/source firmware** before ordering.

### Manufacturing cost reality (it's *iteration*, not parts)
**The parts are cheap (~$110 above).** What makes a *first custom board* cost real
money is the one-time assembly + respins — not the components:
- **Bare PCB fab:** 4–6 layers + controlled impedance (USB/MIPI/RF), qty ~5 → **~$30–100**.
- **Assembly (PCBA):** RV1106/EG915U/BM83 are BGA/LGA — **can't be hand-soldered**, so
  an assembly house charges stencil + setup + per-part fees → **~$100–200/run** (one-time).
- **One assembled prototype board ≈ ~$150–300** = the ~$110 of parts + a share of that
  one-time setup for a small run.
- **The scary ~$500–1,500 is the *program* cost if you respin 2–3×** (each respin
  repeats fab + assembly + setup), which the RF/power/thermal tuning usually needs.
  It's an **iteration** cost, not a parts cost.
- **"Cheap" is a volume property:** per-unit approaches the ~$110 BOM + a few $ assembly
  only at **hundreds–thousands** of units.
- **Levers:** JLCPCB/PCBWay PCBA with their **in-stock parts library** (dodges MOQ +
  bundles cheap assembly) · a modem **module** (not bare EG915U) on early spins ·
  design to the fab's standard stackup (no exotic HDI).
- **Why the dev-board step pays for itself:** a problem caught on a $30 board vs. a
  board spin is a **~10–50× difference** in money + weeks of lead time.

### Sourcing gotchas + workarounds
- **EG915U-EU is not a US radio.** Bands are EMEA (B1/3/5/7/8/20/28). There is no
  EG915U-NA; Portland / AT&T / T-Mobile need a NA SKU (e.g. EG915Q-NA / EG800Q-NA
  class, or whatever the LilyGO/Waveshare HAT actually ships). Sharing B5 is not
  coverage. Pick the regional modem before schematic.
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

### Optional capability add-ons (location, Bluetooth audio)
- **GNSS / location:** use a **GNSS-capable modem** (the prototyping SIM7670G /
  LilyGO A7670**G** already include GNSS; the bare EG915U does **not** — add a GNSS
  chip like u-blox MAX-M10 / Quectel L76) **+ a small GNSS antenna** (~7 mm GPS chip
  antenna, or a **cellular+GNSS combo flex** = one part, two U.FL leads). Enables the
  `get_location` / `directions` tools (ARCHITECTURE §8).
- **Bluetooth audio out (AirPods / BT headphones) — table-stakes (ADR-0008/0009).**
  A2DP *source* for private/clear AI voice + music. **Decided: a dedicated
  Microchip BM83** (row 2b) owns A2DP source + AAC via I²S, offloading the
  RV1106's weak BlueZ. **HFP Audio Gateway (earbud mic) is not in the BM83 AT
  Tx-mode firmware** — A2DP-out is real; two-way via AirPods mic is not, on this
  chip. See [`../docs/FEASIBILITY.md`](../docs/FEASIBILITY.md). Adds a
  **2.4 GHz BT antenna** + a pairing flow; the module itself is 32×15 mm with an
  onboard PCB antenna. (On an RK3566-class SoC you could instead use BlueZ A2DP
  directly, ~$0 — the one-chip fallback.)
- **Spotify:** software only — **librespot** (MIT, Rust) on the SoC; needs Spotify
  Premium. Music over cellular ~1 MB/min — prefer Wi-Fi.

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
| Sleep (wake island + modem registered-idle) | ~few–20 mA | SoC suspend or off; **modem stays attached** (~13 mA idle typical on EG915U). Full radio-off makes wake-to-talk too slow. |
| Active session (streaming) | ~2–4 W | modem ~0.8 A + SoC; the heat driver |
| Camera capture (brief) | + sensor power | gated off otherwise |

- Skin-facing surface must stay **≤43 °C** (target ≤40–42 °C). Strategy: on-demand
  bursts + passive graphite/Cu spreading to an outward face + skin-side insulation.
- LTE draws steadily during a session (no 2 G micro-spikes) → single LiPo + bulk
  cap + power-path PMIC; no supercap required.
- Runtime (order-of-magnitude): a 2000 mAh / 3.7 V cell is **7.4 Wh**. At the
  ~3 W session budget that is **~2.5 h of continuous talk** (2000 mAh / ~0.8 A
  LTE TX is the same answer). **All-day / multi-day only on an on-demand duty
  cycle**, and only if idle current stays in the tens of mA — which argues
  against fully powering off the modem every session. See
  [`../docs/FEASIBILITY.md`](../docs/FEASIBILITY.md).

---

## 4. Open items before schematic capture

- [ ] Confirm session SoC (Luckfox Pico Ultra / RV1106) against the realtime
      WebRTC/TLS + camera workload and its idle/boot-time power.
- [ ] Measure **wake-to-first-audio** with the modem already registered-idle vs.
      fully powered off. Full power-off is expected to be 15–40 s (see
      [`../docs/FEASIBILITY.md`](../docs/FEASIBILITY.md)) and is likely
      product-infeasible; this number decides the power architecture.
- [ ] Validate wake-island → SoC cold-boot/resume latency (affects "feel").
- [ ] Bench modem TX current + needed bulk capacitance on the chosen cell.
- [ ] Thermal mock-up: skin-side temp during a sustained session; size the
      graphite spreader; resolve antenna-vs-spreader contention for the outer face.
- [ ] Confirm SC3336 FFC pin count + GCT USB-C IP suffix on datasheets.
- [ ] eSIM (Soracom/SGP.32) provisioning + data plan.
- [ ] Secure storage for keys + memory file (SoC secure boot / encrypted flash).
