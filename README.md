# Pneuma

**An open-source, screenless AI device with sight and sound — bring your own model.**

Pneuma is firmware (and a companion app) for a small wearable that lets you talk
with an AI and, *only when you ask*, let it see what you see. No screen. No
always-on recording. No vendor lock-in. You supply your own model — an API key
for a frontier provider, or a local endpoint you run yourself — and Pneuma is
the *body*: ears, mouth, an eye you point on demand, and a consistent set of
wake words and gestures.

> Status: **early design / pre-implementation.** This repository currently
> contains the founding architecture and research. No firmware has been written
> yet. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the plan and
> [`docs/RESEARCH.md`](docs/RESEARCH.md) for the evidence behind it.

## What Pneuma is (and isn't)

- **Voice-first, screenless.** You speak; it speaks back. Interaction is wake
  word + button + haptics + a few audio cues — never a display.
- **Vision on demand, not always-watching.** The camera captures a frame *when
  you ask something visual* ("what am I looking at?"), gated by intent. This is
  deliberately the opposite of the always-recording pendants that have drawn
  privacy backlash.
- **Bring your own LLM.** The "brain" is pluggable. Point Pneuma at OpenAI,
  Google Gemini, xAI Grok, Anthropic Claude, or your own local model. Your
  credentials live in the companion app, never on the device.
- **Open and self-hostable.** Firmware, companion app, and any backend are meant
  to be fully open and runnable by you — no account required to own your data.

## Why it's different

The wearable-AI category's recurring wound is *always-on recording*: it triggers
bystander-consent problems, public backlash, and a collapse of trust when the
maker gets acquired. Pneuma's **on-demand capture + open-source + self-hostable +
bring-your-own-key** posture is a coherent, trustworthy alternative the
incumbents structurally can't offer.

## How the model works (in one diagram)

```
        ┌─────────────────┐        BLE (Opus audio)        ┌────────────────────┐
        │     PENDANT      │  ───────────────────────────▶  │   COMPANION APP    │
        │  (credential-    │   Wi-Fi burst (camera frame)   │   (holds keys,     │
        │   free)          │  ───────────────────────────▶  │   routes provider) │
        │                  │  ◀───────────────────────────  │                    │
        │ • wake word      │        audio reply             └─────────┬──────────┘
        │ • mic capture    │                                          │
        │ • on-demand cam  │                                          │  user's own
        │ • speaker/haptic │                          ┌───────────────┴───────────────┐
        └─────────────────┘                          │         THE BRAIN              │
                                                      │  Tier 1: native speech-to-     │
                                                      │   speech (OpenAI / Gemini /    │
                                                      │   Grok)                        │
                                                      │  Tier 2: composed STT→LLM→TTS  │
                                                      │   (Claude / local Ollama)      │
                                                      └────────────────────────────────┘
```

The companion app speaks to whichever provider you chose through a **two-tier
abstraction** so "bring your own LLM" works for *every* backend — including the
ones (Claude, local models) that have no native voice API. See
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Repository layout (planned)

```
pneuma/
├── README.md            ← you are here
├── docs/
│   ├── ARCHITECTURE.md  ← system design, provider abstraction, ADRs
│   └── RESEARCH.md       ← sourced research the design is built on
├── firmware/            ← (planned) ESP32-S3 firmware
├── app/                 ← (planned) companion app + provider router
└── hardware/            ← (planned) BOM, schematics, wiring, enclosure
```

## Hardware target (v1)

A single **Seeed XIAO ESP32-S3 Sense** (~21×17.5 mm, camera + PDM mic + BLE +
Wi-Fi onboard, ~$14) + a micro-speaker, a button, a haptic motor, an RGB LED, and
a small LiPo. Chosen so anyone can buy the board off the shelf and flash it. Full
BOM and wiring will live in `hardware/`. See ADR-0001 in
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for why.

## License

Intended to be fully open source (license TBD — leaning permissive, e.g. MIT, to
match the openness bar set by projects like Omi). Contributions welcome once the
initial scaffold lands.
