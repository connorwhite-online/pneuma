# Pneuma — Enclosure, Thermal & RF (mechanical design)

The body is not just a shell — it is the **heat exchanger**, the **waterproof
barrier**, and part of the **antenna system** all at once. These three jobs
interact, so they're designed together here. Rationale tie-ins:
[`ARCHITECTURE.md`](ARCHITECTURE.md) §6 + ADR-0006/0007;
[`RESEARCH.md`](RESEARCH.md) §thermal.

Status: **design.** Enclosure is intended to be iterated (3D-printed first).

---

## 1. Aluminum body as the heat exchanger

Approach (cf. iPhone 17 Pro: metal mass + heat spreader): conduct heat from the
hot parts into the aluminum unibody and let the whole body radiate.

**What gets hot (strap these, ignore the rest):**
1. **Cellular modem PA during TX** — ~0.7–0.8 A ≈ ~3 W while connected. #1 source.
2. **Linux SoC** (A7 + NPU during a session). #2.
3. Camera (brief), battery (while charging).

**Thermal path:** modem PA + SoC → thermal interface material (TIM/pad) →
graphite spreader → **aluminum unibody**.

**Why it works here:** on-demand bursts (30–60 s) dump little energy into a
comparatively large metal mass → temperature barely rises; the body soaks and
re-radiates afterward. *Continuous* operation overruns thermal mass (what cooked
the Ai Pin); Pneuma doesn't do that (ADR-0006).

**Skin-side caveat:** the body also contacts the chest, and metal feels hot faster
than plastic (effusivity). The **≤43 °C** limit applies to the skin-facing metal.
So **radiate from the outward face; insulate / stand off the skin side** (low-
conductivity layer between hot side and skin). The thin-slab + plateau layout (§4)
does this structurally: hot parts live in the **outward aluminum plateau**, the
skin side is the **cool battery slab**. Short bursts likely stay well under the
limit; design for the long-session case anyway.

---

## 2. Waterproofing (target IP68)

A printed **silicone gasket** compressed between **two aluminum shells** seals the
body (target IP68). Anodize the aluminum (scratch/corrosion); the silicone can
extend into an external **bumper** for drop protection. Four things sealing
touches, designed back in:

- **Acoustic membranes** over the mic and speaker (Gore/Saati) — pass sound, block
  water. One also serves as the **pressure-equalization vent** a sealed device
  needs.
- **USB-C charging + data** (chosen over portless Qi/pogo): Qi won't pass the
  aluminum body, and a data port is worth keeping — flashing the Linux SoC,
  dev/debug, recovery from a bad OTA, and a non-cellular firmware-update path. The
  cost is that the port is the one genuine waterproofing weak point; solve it the
  way IP68 phones do — a **gasketed/waterproof USB-C receptacle** sealed to the
  PCB so water can enter the cavity, drain, and never reach the interior, with the
  silicone gasket **wrapping the opening**.
- **RF window = the gasket** — a real **slot/aperture in the aluminum**, filled by
  the RF-transparent silicone gasket, both seals and lets the antenna radiate
  through (§3).
- **LED indicator window** — an *optical* gap: a clear polycarbonate insert or
  **translucent silicone** over the LED (so the gasket glows), or a sealed
  light-pipe. Sealed either way.

**Whole-body heat — a thermal-break caveat:** silicone between the two aluminum
shells is a *thermal break*, so heat strapped to the plateau shell won't flow into
the other shell on its own. Either **accept it** (with on-demand bursts the
plateau shell has ample surface — start here) or **bridge it** with a small
metal-to-metal contact / thermal strap across the gasket at one spot (more sealing
complexity). Decide from bench data.

(Conduction-only cooling is unaffected by sealing — there's no airflow at this
scale regardless, so waterproofing doesn't hurt the thermal design.)

---

## 3. Antenna vs. aluminum body — the central RF tension

**A sealed aluminum body is a Faraday cage; the antenna cannot live inside the
metal.** The fix: a real **slot/aperture in the aluminum**, filled by the
RF-transparent **silicone gasket itself** (one part, two jobs — seal + RF window),
with the FPC antenna behind it. (Like the plastic antenna breaks in phone metal
frames.)

**Tuning caveat:** the antenna must be tuned *with the metal aperture present* —
the surrounding aluminum edges become part of its electrical picture (the slot can
radiate/detune), so expect an RF simulation-and-tweak pass during bring-up rather
than dropping in a generic FPC antenna.

**It competes with the thermal radiator for the outward face.** Resolve in 3D:
- **Aluminum body** = structural mass + radiator (outward + sides).
- **RF window** = plastic section at the **top or bottom edge**, positioned *away
  from the body* (better SAR, less tissue detuning), FPC antenna behind it, PCB
  ground + battery shielding toward the chest.

Get these two zones not overlapping/fighting and the layout resolves.

**Antenna size — how small can you go?** Two regimes:
- **Self-contained radiators** keep full LTE band (incl. 700 MHz): the 85×14.5 mm
  **flex** (Molex 2091420180, plug-and-play U.FL — prototype) or, on the product PCB,
  the **~40×7×3 mm Pulse W3796** SMD (full 698–2700 MHz, >65% eff., needs a ground-
  plane keepout). The W3796 ~halves the footprint → a smaller **~45×12 mm RF window**,
  leaving *more* aluminum for the heat spreader (same direction as the thermal goal).
- **Ground-plane boosters** (tiny chips, e.g. Ignion NN03-310, 30×3×1 mm) go smaller
  still but use the PCB ground as the radiator and want a **~100 mm** ground plane;
  on our 80 mm body, low-band efficiency drops — skip unless you accept mid-band-only.

So: **prototype on the flex, ship the ~40 mm W3796** on the PCB (still no chassis RF).

**Antenna technology — and how hard the "frame antenna" really is.** The Molex
adhesive flex is the *prototype* antenna (cheap, no tooling, on-air in a day; a
0.1 mm ribbon that hides along an edge). The product-grade options, easiest → hardest:

1. **Flex (FPC)** behind the non-metal RF window — prototype + early product; tune
   empirically with a VNA.
2. **Ground-plane-coupled chip antenna** (e.g. Ignion "Virtual Antenna" / mXTEND, or
   Taoglas/Antenova with their tuning service) — tiny standard SMD that uses the PCB
   ground as part of the radiator; the vendor helps tune. *Near-frame performance
   without DIY chassis RF — the recommended "integrated" step.*
3. **LDS antenna** lasered onto a plastic carrier / the window insert — the
   smartwatch standard; needs a vendor + volume.
4. **Hybrid frame** — keep the body grounded as the heat spreader, but isolate **one
   plastic-broken segment** of the frame as the radiator, fed by a flex. Many
   products that *look* like frame antennas are actually this.
5. **Full metal-frame/slot antenna** (phone-style) — the **hardest** option:
   slot + feed + matching network + EM simulation (HFSS/CST) + anechoic-chamber
   tuning, tightly coupled to frozen mechanics, with body-proximity detuning and
   SAR complications on the surface you touch. *Endgame only, with an RF engineer —
   not a prototype or DIY-blind path.*

So: **ship on flex; if you want the integrated look, hire the tuning out** (a
ground-coupled chip or LDS) rather than hand-rolling a chassis antenna.

---

## 4. Form factor & size — thin slab + plateau (iPhone-Air-style)

**Envelope: ~40 × 80 mm footprint**, but *not* a uniform 20 mm brick. Instead two
zones:

```
        ┌──────── plateau / bump ────────┐   ← ~14–18 mm
   ┌────┤  camera · SoC · modem · speaker├─────────────────┐
   │    └────────────────────────────────┘                 │  ← thin slab ~8–10 mm
   │  battery slab + PCB                                    │
   └───────────────────────────────────────────────────────┘
     (skin side)
```

- **Thin slab (skin side):** battery + main PCB. Flat, cool, comfortable against
  the chest.
- **Plateau / bump (outward):** camera (lens depth), speaker (~3–5 mm cavity), SoC,
  modem — the parts that need vertical room.

This maps to a **two-board stack** — a main/battery board in the slab and a
SoC+modem board in the plateau, joined by one board-to-board connector or short
flex; camera/antenna/speaker/mic/USB-C hang off on flex/JST (see BOM interconnect).

**Battery dimensioning** (the slab is the battery): the standard off-the-shelf cell
is **~8 × 36 × 60 mm / 2,000 mAh** (e.g. PKCell LP803860, single-unit orderable) →
thin section ≈ 10–11 mm. A thinner/longer cell (~5–7 × 36 × ~72 mm, same ~2,000–
2,500 mAh) is a **custom/volume** option if you want to slim the slab further.

**Thermal payoff:** put the hot parts (**modem PA + SoC**) in the **outward
aluminum plateau** → the bump radiates *away from the body* while the cool battery
slab sits against the skin. This resolves the radiator-vs-skin-contact tension by
geometry (see §1).

**Wearability:** average thickness well under 20 mm; a deliberate design language,
not a brick. Levers to slim further later: **iSIM**, smaller battery (the
on-demand model tolerates it), PCB stacking / flex-rigid, aluminum body as
structure.

---

## 5. Enclosure openings (cutout sizes)

Design-start sizes for every penetration, from the BOM parts. **Authoritative
cutout = each part's datasheet "recommended panel cutout" / STEP** — confirm before
final CAD. Every opening must be sealed by its matching method.

| Opening | Cutout | Sealing | Notes |
|---|---|---|---|
| **USB-C** | mouth ~9.0 × 3.3 mm; plug recess ~12 × 7 mm | connector IP67 flange + gasket | Thin wall (≤~2 mm) / counterbore so the cable overmold seats. GCT USB4500 datasheet is authoritative. |
| **Camera** | ~6 mm Ø aperture; clear window ~8 mm Ø | sealed clear window (sapphire/PC) | Clears SC3336 lens + ~98° FOV; chamfer inner edge to avoid vignetting. |
| **Antenna** | RF window ~85×15 mm (proto flex) or **~45×12 mm** (product W3796 SMD) | gasket fills it (RF-transparent) | Smaller antenna → smaller window → more metal body (§3). |
| **LED** | ~3 mm Ø window (or 1.5–2 mm light-pipe) | clear/translucent insert or translucent silicone | Light-pipe keeps the LED off the surface. |
| **Mic** | ~1.0 mm Ø port | waterproof acoustic membrane | Membrane also serves as the pressure-equalization vent. |
| **Speaker** | grille ~5–9 × 1.0–1.5 mm holes (or ~10 mm slotted) | acoustic membrane behind grille | Many small holes seal better than one big hole. |
| **Button** | ~5 mm Ø | silicone dome / overmold over a tact switch | Or avoid the hole with a capacitive / Hall (magnet) button. |

Add 0.1–0.3 mm clearance around connectors and account for gasket compression.

## 6. Attachment / wear mode

The Humane Ai Pin used a **magnetic clamp through fabric**: the Pin on the outside,
a magnetic piece behind the cloth — either the passive **"Latch"** or the
**"Battery Booster"** (magnet + battery powering the Pin through the clothing).

**Lesson baked in:** the Booster was an *active, warm* part against the body and
reviewers found it uncomfortably hot. So if Pneuma goes magnetic, the **skin-side
piece must be a passive magnet only — never a heat source.** Our layout cooperates
(heat is in the outward plateau; the skin side is the cool battery slab).

Options: **magnetic clamp** (most "Pneuma," keep the inner piece dumb + cool),
**lanyard loop**, or a **clip**. Choose during industrial design.

## Open mechanical items

- [ ] Thermal mock-up: skin-side temp during a sustained session; size the TIM +
      graphite + Al mass; pick the skin-side insulator.
- [ ] Antenna: prototype on the Molex flex (U.FL); on the product PCB use the Pulse
      W3796 (~40×7 mm SMD, full band, ground-plane keepout) → ~45×12 mm RF window.
      Confirm placement + tuning.
- [ ] RF window material + placement; antenna efficiency/SAR with the metal body
      present; confirm no thermal/antenna face conflict.
- [ ] Seal the USB-C interface: gasketed IP67 receptacle + panel-cutout per the GCT
      datasheet; wall thinned/counterbored for plug-overmold clearance.
- [ ] Acoustic membrane parts + port geometry for mic/speaker; vent placement.
- [ ] Gasket geometry for a printed silicone seal; long-term seal/clamp design.
