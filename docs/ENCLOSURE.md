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

A printed **silicone gasket** seals the body halves. Three things sealing breaks,
designed back in:

- **Acoustic membranes** over the mic and speaker (Gore/Saati) — pass sound, block
  water. One also serves as the **pressure-equalization vent** a sealed device
  needs.
- **Portless charging** — no USB-C (a port is the worst waterproofing weak point,
  and we need no data port: setup is app-less over BLE/SoftAP). With an **aluminum
  body, lean magnetic pogo-pin** contacts: Qi won't pass through aluminum (same
  Faraday issue as the antenna), so wireless would need yet another non-metal
  window. Pogo removes a hole and avoids that.
- **Sealed RF window** — the gasket seals *around* the antenna window (§3).

(Conduction-only cooling is unaffected by sealing — there's no airflow at this
scale regardless, so waterproofing doesn't hurt the thermal design.)

---

## 3. Antenna vs. aluminum body — the central RF tension

**A sealed aluminum body is a Faraday cage; the antenna cannot live inside the
metal.** The "spot for the antenna" must be a deliberate **non-conductive RF
window** (plastic/ceramic) in the body, electrically isolated from the aluminum
(like the plastic antenna breaks in phone metal frames). The silicone gasket seals
around it.

**It competes with the thermal radiator for the outward face.** Resolve in 3D:
- **Aluminum body** = structural mass + radiator (outward + sides).
- **RF window** = plastic section at the **top or bottom edge**, positioned *away
  from the body* (better SAR, less tissue detuning), FPC antenna behind it, PCB
  ground + battery shielding toward the chest.

Get these two zones not overlapping/fighting and the layout resolves.

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

**Battery dimensioning** (the slab is the battery): a LiPo pouch of roughly
**5–7 mm × ~36 × ~72 mm** (≈ usable footprint less ~2 mm walls) yields
**~2,000–2,500 mAh** at commodity density (~130–160 mAh/cm³). A ~6 mm cell → thin
section ≈ 8–10 mm (battery + walls + PCB).

**Thermal payoff:** put the hot parts (**modem PA + SoC**) in the **outward
aluminum plateau** → the bump radiates *away from the body* while the cool battery
slab sits against the skin. This resolves the radiator-vs-skin-contact tension by
geometry (see §1).

**Wearability:** average thickness well under 20 mm; a deliberate design language,
not a brick. Levers to slim further later: **iSIM**, smaller battery (the
on-demand model tolerates it), PCB stacking / flex-rigid, aluminum body as
structure.

---

## Open mechanical items

- [ ] Thermal mock-up: skin-side temp during a sustained session; size the TIM +
      graphite + Al mass; pick the skin-side insulator.
- [ ] RF window material + placement; antenna efficiency/SAR with the metal body
      present; confirm no thermal/antenna face conflict.
- [ ] Charging method (Qi vs pogo) + sealing of the charge interface; coil heat if Qi.
- [ ] Acoustic membrane parts + port geometry for mic/speaker; vent placement.
- [ ] Gasket geometry for a printed silicone seal; long-term seal/clamp design.
