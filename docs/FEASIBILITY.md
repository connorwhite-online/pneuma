# Pneuma — Is this device actually feasible?

**Verdict:** the *idea* is feasible. The *current spec, taken as a v1 wearable*,
is not — not because any one block is science fiction, but because the ADRs have
stacked into an Ai-Pin-class hardware program while still assuming a solo-maker
BOM and an instant "Hey Pneuma" response.

A desk prototype that talks to a realtime model over cellular is a near-term,
buildable thing. A sealed aluminum puck that wakes instantly, stays cool on
skin, runs four radios, is IP68, has no phone and no server, and works all day
in Portland is a different device. This note separates those.

Status: independent review of the design in this repo (ARCHITECTURE, RESEARCH,
BOM, ENCLOSURE), checked against datasheets and published bring-up numbers.
Not a lab measurement.

---

## 1. Three different products (do not conflate them)

| | What | Feasible? |
|---|---|---|
| **A. Desk demo** | Luckfox Pico Ultra + Cat-1 HAT + IoT SIM + laptop-proven session code, talking to OpenAI/Grok over cellular | **Yes.** Weeks to a first voice round-trip. This is the right next step. |
| **B. Personal wearable** | Custom PCB in a 3D-printed body, nano-SIM, speaker + optional earbuds, on-demand Q&A, you are the only user | **Maybe**, with 2–4 board spins and a willingness to drop IP68 / aluminum / eSIM / projection / live nav. Months of hardware, not a weekend. |
| **C. Sellable consumer device** | The full ADR stack: standalone cellular, app-less, IP68 aluminum, SGP.32, FCC/PTCRB/SAR, all-day, instant wake | **Hard.** Same class of program as the Humane Ai Pin. The architecture is *better* than the Pin's (on-demand vs continuous), but certification, RF, and wake latency are still product-scale problems. |

The repo currently describes **C** while costing **A**. That gap is the main
feasibility issue.

---

## 2. What is actually sound

These choices are right, and they are why the device is not a fantasy:

- **On-demand, not continuous.** The Ai Pin failed thermally because it was a
  phone that never slept. Bursting a session then cutting power is the correct
  lesson. Short Q&A (30–60 s) is in a different thermal regime than streaming.
- **Cloud brain, modest SoC.** Do not put a Snapdragon 720G in a pendant. An
  RV1106-class chip plus a module modem is the right size of computer.
- **Cat-1 bis for the radio tier.** Voice is tens of kb/s; Cat-1's ~10/5 Mbps
  and <100 ms typical latency are enough. LTE-M/NB-IoT are the wrong tier.
- **Opus-over-TLS-WebSocket rather than full WebRTC** as the first transport.
  A single Cortex-A7 can encode Opus. libwebrtc on 256 MB is a much worse bet.
- **OpenAI Realtime over WebSocket with the API key on-device** does *not*
  require a Pneuma server. Ephemeral tokens are a browser/WebRTC concern.
  (Stolen-device key leakage is a product risk, not a protocol blocker.)
- **On-demand camera, not always-watching.** Technically easier than live video,
  and it sidesteps the privacy backlash that hit Friend / Bee.
- **Parts exist and are orderable.** That part of the BOM work is real.
- **The earlier phone-tethered nRF design is highly feasible** — it is what Omi
  / Bee / Limitless already shipped. It was abandoned for product reasons, not
  physics.

Thermal mass for a *short* burst is also fine. A ~40 g aluminum shell
(~36 J/K) absorbing 3 W × 60 s = 180 J rises ~5 K if you ignore cooling. Skin
limit 43 °C is not the problem for a one-minute question. It *is* the problem
for a ten-minute conversation or for Spotify/nav as specified (see §4).

---

## 3. Load-bearing errors in the current spec

These are not nits. They change whether v1 works.

### 3.1 Battery math: "~10 h continuous talk" is wrong

A 2000 mAh / 3.7 V cell is **7.4 Wh**. At the stated ~3 W session:

`7.4 Wh / 3 W ≈ 2.5 hours`

LTE TX typical on the EG915U is ~0.77 A; 2000 mAh / 770 mA ≈ **2.6 h**, before
the SoC, PA inefficiency, or poor-signal current. The BOM's "~10 h+ continuous
talk" looks like 2000 mAh was divided by ~200 mA instead of ~800 mA.

**All-day is still plausible on an on-demand duty cycle** (twenty 45-second
sessions is ~15 minutes of radio time). It is not plausible as hours of
continuous talk, and it is not free: it depends on *idle* current staying in
the tens of mA, which fights full power-off of the modem (next item).

### 3.2 Wake-to-ready latency is the real make-or-break

The interaction loop assumes: wake word → earcon → converse. That only works
if the session tier is already *almost* up.

Measured / specified numbers:

| Step | Typical if fully powered off |
|---|---|
| RV1106 default Buildroot boot | **~14 s** (Luckfox Pico Ultra users) |
| RV1106 aggressively fastbooted | **~1–5 s** (research writeup ~1 s; vendor fastboot is BusyBox ramfs, read-only, little RAM left for a Rust TLS client) |
| EG915U PWRKEY + init | **≥2 s** PWRKEY low, then firmware init |
| LTE attach from radio-off | **~5–20 s** (network-dependent; multi-IMSI IoT SIMs can be worse) |
| TLS + realtime session | **1–3 s** |

**Full power-off of SoC + modem, as drawn, is a 15–40 s "Hey Pneuma."** That
is not a voice assistant. It is a walkie-talkie with a long wakeup.

The devices that feel instant (Apple Watch LTE, phones) keep the modem
**registered-idle**. EG915U idle with USB disconnected is specified around
**13 mA**. LTE sleep (paging) is ~1.2–1.6 mA. Either is thermally nothing
and still all-day on 2000 mAh.

So the feasible power architecture is **not** "cut the session tier to zero":

- **Keep the modem registered** (idle or DRX), and
- **Keep the SoC in suspend-to-RAM or a ~1 s fast path**, and
- Use the wake island for the word / button / cues.

RV1106 suspend quality is unverified (IPC chips are often weak at S3). That
is a bench item, not an ADR to accept on paper. Vendor "FASTBOOT" images
run the rootfs in DDR, drop Buildroot, and leave little room for the actual
app — they are not a free 1-second boot of the planned Rust stack.

Until wake-to-first-audio is measured under **1–3 s**, do not freeze
"SoC+modem fully off" as the product behavior.

### 3.3 The BOM modem does not cover the US

The design part is **Quectel EG915U-EU**. That SKU is EMEA/AU/NZ: LTE bands
**B1/3/5/7/8/20/28**. There is no EG915U-NA. Portland / AT&T / T-Mobile want
**B2, B4, B12, B13, B66, B71**. Sharing B5 is not coverage.

A US build needs a different module (e.g. EG915Q-NA / EG800Q-NA class, or
whatever the LilyGO/Waveshare HAT actually ships). Regional SKUs also change
certification. This is a one-line BOM fix that currently makes the production
part unusable where the project is based.

### 3.4 BM83 does not give you the AirPods microphone

ADR-0008/0009 sell the Microchip **BM83** as A2DP source **and** HFP (earbud
mic). The BM83 **Audio Transceiver (AT) v1.0** feature matrix is explicit:

- Tx mode: A2DP **source** = yes. **HFP Audio Gateway = no.**
- Rx mode: A2DP/HFP **sink** (the BM83 is the headset) = yes. HFP AG = still no.

HFP AG is the role Pneuma needs to be "the phone" and use AirPods as a
headset mic. This firmware does not do that. A2DP-out to earbuds is real;
discreet two-way via the earbud mic is not, on this chip/firmware.

The module is also **32 × 15 × 2.5 mm** with an onboard PCB antenna and a
ground-plane keepout under the module. That is a large brick to drop into a
40 × 80 mm aluminum Faraday cage that already needs an LTE window. It is a
bench-audio solution, not a "fits the puck" solution.

### 3.5 Navigation and Spotify fight the thermal thesis

ARCHITECTURE §8 adds sustained modes: nav at 0.3–0.7 W, media at 0.5–1 W,
and (optional) projection. ADR-0006's whole point is *do not generate heat
continuously*.

Natural convection from a ~40 × 80 mm body is on the order of **0.05–0.1 W/K**.
Sustained 3 W implies a **30–60 K** rise — unwearable, Ai Pin territory.
Sustained 0.5–1 W might be tolerable on the outward plateau; it is not "the
thermal problem is solved by duty cycle." Treat those modes as a later
product, or as Wi-Fi-only, not as v1 requirements.

### 3.6 Several "app-less / no server" items are not v1-shaped

- **SGP.32 eSIM** from a page the device hosts: EG915U eUICC/SGP.32 is
  firmware-gated and poorly documented; field reports of profile download
  failing on this family exist. A **nano-SIM** is the honest v1. The BOM
  already says this in the fine print; provisioning still leads with eSIM.
- **Four 2.4 GHz-adjacent radios** (LTE + nRF BLE + BM83 BR/EDR + GNSS) in
  aluminum, body-worn, with SAR: this is RF-engineer work and anechoic-chamber
  time, not a first custom PCB.
- **IP68 aluminum + gasketed USB-C + acoustic membranes + RF window** as a
  coupled problem: phones do it; a first enclosure should be plastic, IP54,
  and ugly.
- **PDM mic to two chips at once.** The interconnect diagram shows the IM69D130
  feeding the nRF always and the SoC in session. PDM is a point-to-point clocked
  bus. Real options: mux (island releases the mic), island forwards PCM over
  UART (~32 kB/s at 16 kHz/16-bit), or two mics. Pick one before schematic.

### 3.7 Software is a scaffold, and the SoC Linux is a hard target

`firmware/session` is a laptop state machine with mock HAL and a stub OpenAI
driver. That is useful. It is not evidence the RV1106 can run the stack.

RV1106 practical constraints:

- **256 MB** total. ISP/VPU buffers eat a chunk. Fine for Opus + WSS; tight
  for Chromium WebRTC.
- Luckfox userland is **uClibc / musl**, kernel **5.10** vendor tree, **not
  glibc**. Rust should target `armv7-unknown-linux-musleabihf`.
- Fastboot images the vendor documents are **BusyBox-in-RAM**, read-only, and
  explicitly cramped. They conflict with "just run the Rust app."
- BlueZ A2DP on this BSP is the reason BM83 exists; that diagnosis is
  plausible and still unmeasured on hardware.

Wake-word on the nRF52840 is feasible (Cortex-M4 + CMSIS-NN DS-CNN) but
**microWakeWord does not port**, and there is no trained "Hey Pneuma" model
in the repo. Custom KWS is a project of its own (data, FAR in cafes, power).
A button-first v1 is the way shipping pendants actually work.

---

## 4. Thermal: short bursts yes, the Pin's workload no

| Workload | Energy / power | Skin-side outlook |
|---|---|---|
| 30–60 s Q&A at ~3 W | ~90–180 J into the metal | **OK** (~few K rise); then idle to dump heat |
| 10 min conversation at ~3 W | ~1.8 kJ | **Not OK** without throttling (~tens of K adiabatic; still hot with convection) |
| Spotify / nav sustained 0.5–1 W | continuous | Maybe on the outward plateau; **not** "solved" |
| Sleep, modem idle ~13 mA | ~50 mW | Trivial |

The aluminum-as-spreader idea is right for bursts. The silicone gasket
between shells is a thermal break (ENCLOSURE already flags this). Insulate
the skin side; radiate outward. Do not promise continuous LTE.

---

## 5. Cost, honestly

~$110 of parts at qty 1 is in the right ballpark **for the electronics** if
you ignore the enclosure CNC, the BM83 keepout, and the wrong regional modem.

What the current docs underweight for **C**:

- RF matching + body-worn SAR + 4-radio coexistence
- PTCRB/GCF even with a pre-certified module (the antenna is yours)
- FCC / CE / carrier
- Tooling for aluminum + silicone gasket
- 2–4 respins (the BOM is right that this, not the ICs, is the money)

A personal **B** build can skip most of that (pre-certified module, plastic
shell, you don't sell it). A product cannot.

---

## 6. What I would actually build next

Do not start with the unibody. Freeze a *smaller* device.

1. **Desk (this month).** Luckfox Pico Ultra W + a **US-banded** Cat-1 HAT
   (not the EU EG915U) + IoT SIM. Port the session brain far enough to do
   one OpenAI/Grok realtime round-trip over cellular. Measure: boot time,
   attach time, wake-to-first-audio, TX current, CPU/RAM, A2DP if you care.
   *This single experiment answers more than another ADR.*
2. **Drop from v1:** IP68, aluminum, SGP.32, projection, live turn-by-turn,
   Spotify-over-cellular, BM83-as-HFP, "no server" as a religion if WebRTC
   becomes necessary.
3. **Keep for v1:** wake island + on-demand session, button *and* wake word
   (button first), one JPEG camera, speaker, nano-SIM, BYO key, memory file,
   plastic body.
4. **Decide cellular vs phone-tether from the desk numbers.** If attach+boot
   cannot be made to feel like 1–3 s without leaving the modem up, either
   leave the modem up (and own the idle mA) or revive the BLE-to-phone
   architecture for a wearable you can actually wear this year.
5. **Custom PCB only after** (1) has talked to a model over LTE and (2)
   A2DP (if required) is proven on the real audio path.

---

## 7. Bottom line

**Feasible:** a screenless, on-demand, BYO-LLM gadget with a camera that is
off until asked. That device can be a cellular puck *or* a phone-tethered
pendant. Physics allows both.

**Not feasible as written, for v1:** every ADR at once, instant wake from a
cold Linux SoC and a cold LTE modem, 10-hour continuous talk, US use of an
EU-only module, AirPods-mic via BM83 AT firmware, IP68 aluminum, and
app-less SGP.32.

The Humane lesson in this repo is correct. The failure mode to avoid now is
the opposite one: specifying the finished consumer object before measuring
the two numbers that decide the product — **wake-to-first-audio** and
**idle current with the modem still registered**.
