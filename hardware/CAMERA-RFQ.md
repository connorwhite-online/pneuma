# Camera module RFQ — Pneuma Rev A

Send this to camera module houses (Sincere, Hampo, CK Vision, Sinoseen, or any Shenzhen module
supplier). It is written so you can paste §2–§7 straight into an email. Background and the reasoning
behind the numbers are in [`REV-A.md`](REV-A.md) §7; coordinates are in
[`mechanical/enclosure-L-electronics.json`](mechanical/enclosure-L-electronics.json).

**Why this is blocking:** the PCB is finished and does not depend on which module you pick (the FFC
connector and its pinout are frozen). The *enclosure* cannot be modeled until the module's outline,
height and FFC exit are known.

---

## 1. Shortlist to ask about first

Any sensor below already has both a kernel driver and an **ISP tuning (IQ) file** in the Luckfox
RV1106 SDK, so it works without commissioning new tuning. In rough order of preference:

| Sensor | Format | Notes |
|---|---|---|
| **GC2053** | 1/2.9", 2 MP | the sensor in most small MIPI FPC modules — most likely to exist off-the-shelf in a compact build |
| **SC3336** | 1/2.8", 3 MP | Luckfox's own tested camera; the bench module uses it |
| **SC3338**, **SC2336**, **SC230AI**, **SC200AI** | 2–3 MP | all tuned in the SDK |
| SC4336, SC401AI, SC500AI, SC530AI, MIS2032, OS02H10, GC1084 | 2–5 MP | also tuned; only if the above can't be made short enough |

Full list in the SDK at `media/isp/release_camera_engine_rkaiq_rv1106_*/isp_iqfiles/`.

**Sensors without SDK tuning are a non-starter** unless the supplier provides an RV1106 IQ file.

## 2. What we need

A **fixed-focus MIPI CSI-2 camera module on an FPC/FFC tail**, for a battery-powered wearable that
takes occasional stills (not continuous video). Host SoC is a **Rockchip RV1106G3** (Luckfox
Core1106). Quantities: **3–10 samples now**, then 50–200 for a pilot build.

## 3. Mechanical (the hard constraint)

| Item | Requirement |
|---|---|
| **Module outline** | **≤ 12 × 12 mm** board |
| **Total height** | **≤ 6.0 mm** including the lens, measured from the module PCB's underside |
| Lens barrel | must not protrude more than the 6.0 mm total; no M12 holder |
| FFC tail | exits one edge, ≥ 25 mm usable length, 0.5 mm pitch, must fold 180° |
| Mounting | 2 holes or adhesive pad face; tell us what the module offers |
| Tolerance | we need a **2D drawing (PDF or DXF) and ideally a STEP model** before ordering |

The module sits tilted **30° from vertical**, which is why the footprint matters as much as the
height: a wider board swings its corners down into the SoC below.

**If you can offer a taller or wider module, tell us the exact numbers anyway** — we can trade
enclosure bump height against module size:

| Camera bump grows by | Largest module that still fits |
|---|---|
| **0 mm (preferred)** | **12 × 12 × 6 mm** |
| 1 mm | 16 × 16 × 6 mm |
| 2 mm | 16 × 16 × 7 mm |
| 4 mm | 16 × 16 × 9 mm |

## 4. Optical

| Item | Requirement |
|---|---|
| FOV | **90–110° diagonal** (a 150° fisheye is what makes most modules tall; we don't need it) |
| Aperture | F2.0–F2.4 is fine; we do not need F1.6–F1.9 if it costs height |
| Focus | fixed focus, hyperfocal from ~30 cm to infinity. No VCM/autofocus |
| IR filter | **IR-cut fitted** (daylight/indoor use, no night vision) |
| Resolution | 2 MP minimum; 3 MP preferred. Stills, ~1–5 fps, not 30 fps video |

## 5. Electrical

| Item | Requirement |
|---|---|
| Interface | **MIPI CSI-2, 2 data lanes + clock** |
| Supply | single **3.3 V** into the module; on-board LDOs for AVDD/DOVDD/DVDD |
| Control | I²C (SCCB), plus **RESET** and an external **MCLK** input |
| MCLK | tell us the required frequency (24 MHz preferred) and whether the module has its own oscillator |
| I²C address | tell us the 7-bit address and whether it is strappable |

## 6. Connector and pinout

Our board has a **20-pin 0.5 mm FFC connector wired to the Luckfox camera pinout**:

| Pin | Signal | Pin | Signal | Pin | Signal | Pin | Signal |
|---|---|---|---|---|---|---|---|
| 1 | GND | 6 | GND | 11 | CSI_D1N | 16 | RESET |
| 2 | MCLK | 7 | CSI_CLK P | 12 | GND | 17 | GND |
| 3 | GND | 8 | CSI_CLK N | 13 | I2C SCL | 18 | GND |
| 4 | CSI_D0P | 9 | GND | 14 | I2C SDA | 19 | +3.3 V |
| 5 | CSI_D0N | 10 | CSI_D1P | 15 | GND | 20 | +3.3 V |

**A 24-pin module is equally acceptable** — send us your standard pinout and we will match the board
to it. Please state:
- pin count and pitch
- **contact side: same-side (type A) or opposite-side (type B)** on the module end
- FFC stiffener location

## 7. Questions to answer with the quote

1. Part number, and the **2D drawing + STEP** for the exact build
2. Module outline and **total height including lens** (mm)
3. Sensor, lens EFL, FOV, F-number, IR-cut yes/no
4. FFC pin count, pitch, contact side, tail length
5. MCLK requirement and I²C address
6. **Do you supply an RV1106/RK ISP tuning (IQ) file for this sensor+lens pair, or should we use the Luckfox SDK's?**
7. MOQ, unit price at 10 / 50 / 200, lead time for samples
8. Whether you can supply **one sample with a 20-pin Luckfox-pinout tail** for immediate bring-up

## 8. What we do while waiting

Bench work uses the **Waveshare/Luckfox SC3336 3MP Camera (B)** ($9), which matches J4's pinout
exactly. That proves the driver, ISP and capture path; only the mechanical fit depends on this RFQ.
