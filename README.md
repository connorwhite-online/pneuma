# Pneuma

**A standalone, screenless AI device with sight and sound — no phone, no app, no
memory of you except what it chooses to keep.**

Pneuma is firmware (and hardware) for a small wearable you can talk with, and —
*only when you ask* — let it see what you see. It carries its own cellular
connection, so it works on its own out in the world. You bring your own model (an
API key for a frontier provider). It is **ephemeral**: it stores no conversations,
no audio, no photos — nothing but one small, curated **memory file**.

> *Pneuma* (πνεῦμα) is Greek for **breath / spirit**. Each interaction is breath —
> it happens, then it's gone. The single memory file is the spirit that endures.

> Status: **early design / pre-implementation.** This repo currently holds the
> architecture and research; no firmware is written yet. Start with
> [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), then
> [`docs/RESEARCH.md`](docs/RESEARCH.md).

## What Pneuma is (and isn't)

- **Voice-first, screenless.** You speak; it speaks back. Wake word + button +
  haptics + audio cues — never a display.
- **Standalone.** Onboard **cellular (LTE Cat-1 bis)** — no phone, no companion
  app. Setup is a one-time web page the device hosts itself.
- **Vision on demand, not always-watching.** The camera powers on to grab a single
  frame *when you ask something visual*, then powers off. The opposite of the
  always-recording pendants that drew privacy backlash.
- **Bring your own LLM.** The brain is pluggable — OpenAI, Gemini, Grok, Claude.
  Your key is stored on the device, set once at setup.
- **Ephemeral + one memory file.** No history, no recordings. The only persistent
  state is a bounded (~KB), model-curated, user-resettable, portable memory file.

## How it works (one picture)

```
   ┌───────────────── PNEUMA DEVICE ──────────────────┐
   │  ┌───────────────┐   wake/power   ┌────────────┐  │   cellular (Cat-1 bis)
   │  │  WAKE ISLAND  │ ─────────────▶ │  SESSION   │  │  ──────────────────────▶  ┌──────────┐
   │  │  (always on,  │                │   BRAIN    │  │   audio + on-demand JPEG  │ PROVIDER │
   │  │   µA–mA)      │ ◀───────────── │ (Linux SoC │  │  ◀──────────────────────  │ your key │
   │  │ wake word/btn │   done/sleep   │ +modem+cam)│  │      audio reply          └──────────┘
   │  └───────────────┘                └─────┬──────┘  │
   │                              ┌──────────┴───────┐ │
   │                              │  memory file ~KB │ │  ← only persistent state
   │                              └──────────────────┘ │
   └───────────────────────────────────────────────────┘
```

A tiny always-on chip listens for the wake word; it powers up the Linux SoC +
cellular modem **only on demand** to answer, then shuts them off. That on-demand
burst (not continuous streaming) is what keeps it cool and the battery alive — the
thing the Humane Ai Pin got wrong. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Repository layout

```
pneuma/
├── README.md
├── docs/
│   ├── ARCHITECTURE.md  ← system design, provider abstraction, ADRs
│   ├── MEMORY.md        ← the memory-file spec (the "spirit")
│   ├── PROVISIONING.md  ← one-time, app-less device setup
│   ├── PROTOCOL.md      ← internal wake-island ↔ Linux-SoC interface
│   └── RESEARCH.md       ← sourced research the design is built on
├── hardware/
│   └── BOM.md           ← bill of materials + interconnect map
└── firmware/            ← (planned) wake-island MCU + Linux session software
```

## Hardware core

A tiny always-on **wake-island MCU** (nRF52840 / Syntiant) + an on-demand **Linux
SoC** (Rockchip RV1106-class) + a **Quectel EG915U** LTE Cat-1 bis modem + a MIPI
camera, micro-speaker, mic, haptics, LED, and a ~500–1000 mAh LiPo with passive
graphite thermal spreading. It's a tiny wearable Linux computer (Ai-Pin-class),
engineered to dodge what killed the Ai Pin. Full BOM:
[`hardware/BOM.md`](hardware/BOM.md); rationale in ADR-0001.

## License

Intended to be fully open source (license TBD — leaning permissive, e.g. MIT).
