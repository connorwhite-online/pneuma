# Pneuma — Architecture

Pneuma is a **standalone, screenless, voice-first AI device** with on-demand
vision and a pluggable ("bring your own") model. It carries its own cellular
connection — **no phone, no companion app** — and is **ephemeral**: it stores
nothing except one small, curated memory file.

This document is the synthesis of the research in [`RESEARCH.md`](RESEARCH.md).
Genuine forks are captured as **Architecture Decision Records (ADRs)** at the end.

Status: **design, pre-implementation.** This is the blueprint, built for the
*right* core rather than a throwaway prototype.

> **Name & principle.** *Pneuma* (πνεῦμα) = breath / spirit. Each interaction is
> breath — it happens and is gone. The one persistent memory file is the spirit
> that endures. The device is otherwise stateless.

---

## 1. System overview

There is no phone in the loop. Three tiers, all on or beyond the device itself:

| Tier | What it is | Job | Power |
|------|------------|-----|-------|
| **Wake island** | Tiny always-on MCU (nRF52840 / Syntiant) | Wake word, button, sensors; powers the session tier up/down | µA–mA, always on |
| **Session brain** | Small Linux SoC (Rockchip RV1106-class) + **Cat-1 bis modem** + camera | Provider router, realtime session over cellular, on-demand photo, audio I/O | watts, **on-demand only** |
| **Provider (brain)** | User's chosen cloud model | Reasoning + (Tier 1) speech | remote, user's API key |

```
   ┌───────────────── PNEUMA DEVICE ──────────────────┐
   │                                                   │
   │  ┌───────────────┐   wake/power   ┌────────────┐  │      cellular (Cat-1 bis)
   │  │  WAKE ISLAND  │ ─────────────▶ │  SESSION   │  │  ─────────────────────────▶  ┌──────────┐
   │  │  (always on)  │                │   BRAIN    │  │     LC3/Opus audio + JPEG     │ PROVIDER │
   │  │ • wake word   │ ◀───────────── │ (Linux SoC │  │  ◀─────────────────────────   │ (your    │
   │  │ • button      │   done/sleep   │  + modem   │  │       audio reply             │  API key)│
   │  │ • mic monitor │                │  + camera) │  │                               └──────────┘
   │  └───────────────┘                └─────┬──────┘  │
   │                                         │         │
   │                              ┌──────────┴───────┐ │
   │                              │  memory file     │ │  ← the only persistent state
   │                              │  (bounded, ~KB)  │ │
   │                              └──────────────────┘ │
   └───────────────────────────────────────────────────┘
```

**Why a Linux SoC, not an MCU:** standalone realtime voice over cellular needs a
real WebRTC/TLS stack, hardware JPEG, OTA, and robust connection management.
Every shipping standalone-cellular voice device works this way (the Humane Ai Pin
used a phone-class Snapdragon). See ADR-0001.

**Why the wake island exists:** the Linux SoC + modem are power- and heat-hungry,
so they must be *off* almost always. A tiny always-on MCU listens for the wake
word and only powers the session tier up to answer, then cuts it. This on-demand
duty cycle is what keeps the device cool and the battery alive (see §6).

---

## 2. The interaction loop

```
   ┌──────────────────────────────────────────────────────────────────────┐
   │  SLEEP — session brain powered OFF; wake island listening (µA–mA)      │
   └───────────────┬────────────────────────────────────────────────────────┘
                   │ "Hey Pneuma"  (or button)  → wake island powers up brain
                   ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  CONNECT — Linux SoC boots/resumes, modem attaches, loads memory file  │
   │  earcon (rising chime) + LED + haptic tap                              │
   └───────────────┬────────────────────────────────────────────────────────┘
                   │  (intent appears visual? "what am I looking at?")
                   ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  CAPTURE (on-demand only) — power camera, grab ONE JPEG, then off      │
   │  visible/audible capture indicator                                     │
   └───────────────┬────────────────────────────────────────────────────────┘
                   ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  CONVERSE — stream audio (+frame) to chosen provider over cellular;    │
   │  play voice reply; (optionally) update the memory file                 │
   └───────────────┬────────────────────────────────────────────────────────┘
                   │  silence / "thanks" / timeout
                   ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  FORGET & SLEEP — drop all audio/frames/context, power modem + SoC     │
   │  down, return to wake island. Nothing kept but the memory file.        │
   └────────────────────────────────────────────────────────────────────────┘
```

The expensive tier lives only inside CONNECT→CONVERSE; the rest of the time the
device is asleep but listening. Camera is powered only inside CAPTURE.

---

## 3. The provider abstraction (the core of "bring your own LLM")

This runs **on the device** (in the Linux session brain), not in any app.
Providers expose their "brain" two ways; Pneuma implements both behind one
interface.

### Tier 1 — `RealtimeProvider` (native speech-to-speech)
One streaming socket: audio (and sometimes video) up, voice down. Lowest latency,
least local compute — ideal over cellular.
- **OpenAI** `gpt-realtime` — audio + image, WebRTC/WS.
- **Google Gemini Live** — audio + **native video (~1 fps)**, WebSocket.
- **xAI Grok Voice** — audio, WebSocket, **OpenAI-Realtime-compatible** (one driver → two providers).
- **AWS Nova Sonic** — audio, HTTP/2.

### Tier 2 — `ComposedProvider` (STT → text LLM → TTS)
Device orchestrates the pipeline (calling cloud STT/TTS APIs). **Required** for:
- **Anthropic Claude** — text/vision only, no native S2S.
- (Future) on-device/off-grid models, if the Linux SoC's NPU is ever used for a local fallback.

### Interface (illustrative)
```
Provider.startSession(opts) -> Session
Session:
  pushAudio(chunk)      // mic up
  pushImage(jpeg)       // on-demand frame up
  audioReply -> stream  // voice down
  transcript -> stream  // text, for memory updates / tools
  toolCalls  -> stream  // MCP
  endTurn(); close()
```
Adding a model = adding one driver + a stored key. The memory file is injected
into the session as context at start (see §5).

### Capability matrix
| Provider | Native voice | Vision | Auth |
|----------|--------------|--------|------|
| OpenAI `gpt-realtime` | ✅ | image | key + ephemeral token |
| Gemini Live | ✅ | ✅ video ~1fps | key + ephemeral token |
| xAI Grok | ✅ (OpenAI-compatible) | audio | key |
| AWS Nova Sonic | ✅ | audio | SigV4 |
| Anthropic Claude | ❌ → Tier 2 | image | key |

Glue: **MCP** for tools/routing. Keys are stored on-device (secure element /
encrypted flash), set once during provisioning (see [`PROVISIONING.md`](PROVISIONING.md)).

---

## 4. Hardware core

| Function | Part (indicative) | Notes |
|----------|-------------------|-------|
| **Wake island** | Nordic **nRF52840** (or Syntiant **NDP120** for <1 mW KWS + beamforming) | always-on KWS (DS-CNN/TFLM), button, BLE for setup, powers the SoC |
| **Session SoC** | Rockchip **RV1106** (Cortex-A7 + ISP + ~0.5–1 TOPS NPU, tiny) | Linux; native MIPI camera ISP + HW JPEG; runs the provider router |
| **Cellular** | Quectel **EG915U** (LTE **Cat-1 bis**, single antenna, ~24×20×2.4 mm) | full-duplex, <100 ms; data-only (voice-over-data) |
| **Camera** | small MIPI-CSI sensor (via RV1106 ISP) | on-demand single JPEG; powered off otherwise |
| **Mic** | Infineon **IM69D130** (PDM) | monitored by wake island for KWS; routed to SoC in session |
| **Audio out** | **MAX98357A** (I2S) + 20 mm 8 Ω speaker | fire upward toward face |
| **Haptics** | LRA + **DRV2605L** | state cues without a screen |
| **Indicator** | RGB LED | + earcons |
| **SIM** | **SGP.32 eSIM** or on-die **iSIM** | remote-provisionable, no UI needed |
| **Power** | LiPo ~500–1000 mAh + power-path PMIC + 100–470 µF bulk cap | LTE = steady ~0.8 A draw (no 2G spikes), so no supercap needed |
| **Thermal** | graphite/Cu heat spreader; outward radiating face; skin-side insulation | passive only (see §6) |
| **Storage** | SoC SPI-NAND/eMMC | holds OS + the memory file |

Full BOM + interconnect: [`../hardware/BOM.md`](../hardware/BOM.md).
Internal wake-island ↔ SoC interface: [`PROTOCOL.md`](PROTOCOL.md).

---

## 5. Ephemerality & the memory file

**Ephemeral by default.** No transcripts, no audio, no photos are retained. A
session's audio and any captured frame are streamed to the provider and dropped.
Nothing about *what you said or saw* persists.

**The memory file — the only persistent state.** A single bounded file (target a
few KB, hard cap) the model curates:
- **Content:** durable facts about the user (name, preferences, a handful of
  standing instructions) — *not* a conversation log.
- **Lifecycle:** read into the session as context at CONNECT; the model may
  propose updates during CONVERSE; on FORGET the device keeps only the updated
  memory file and discards everything else.
- **Bounded:** when near the cap, the model must *summarize/compress* rather than
  append — a rolling memory, so it never grows into a log.
- **On-device only:** never uploaded except as context to the user's *own* chosen
  model during a session. Stored in encrypted flash.
- **User-controlled:** viewable/editable during provisioning; **factory reset =
  forget me**; ideally **portable** (export/import to move your "self" to another
  Pneuma).

See ADR-0005.

---

## 6. Thermal & power (the make-or-break)

The Humane Ai Pin proved standalone-cellular AI is **thermally** hard: continuous
LTE streaming (~3 W modem) + an always-on app SoC is 2–6 W in a sealed body, which
throttled it. Skin-facing surfaces must stay **≤43 °C** (target ≤40–42 °C).

Pneuma's strategy is to *not generate the heat continuously*:
- **On-demand duty cycle** — the modem + SoC are off except during a session; the
  device bursts and sleeps, the regime that lets Apple Watch LTE and kids' GPS
  watches stay cool. (This is why the wake island exists.)
- **Passive spreading** — graphite/copper spreader across the whole shell + a
  deliberate outward radiating face, with insulation toward the skin. An *active*
  heat exchanger is **not feasible** at pendant scale (a few cm² shed only
  ~0.1–0.3 W/°C; no room/power for fans/pumps).
- **Power** — LTE draws a steady ~0.7–0.8 A while connected (no 2 G micro-spikes),
  so a single LiPo + bulk cap + power-path PMIC suffices. Runtime ≈ hours of
  active talk; all-day on the on-demand model.

Tension to design around: the antenna *and* the heat spreader both want the
outward (away-from-body) face — a real pendant-scale layout conflict for the
enclosure phase. See ADR-0006.

---

## 7. Privacy & trust posture

- **Standalone, no app, no Pneuma server.** Audio/photos go only to *your* chosen
  provider, over your own SIM.
- **Ephemeral.** Nothing to leak — no history, no recordings; only the small,
  on-device, user-resettable memory file.
- **On-demand capture** — camera powered only during an indicated CAPTURE; no
  ambient recording. This is the differentiator the always-on incumbents
  (Friend, Bee, Limitless) structurally lack.
- **Open + self-hostable-ish** — fully open firmware; the only cloud dependency is
  the model *you* chose and pay for.

---

## Architecture Decision Records

> **Decision history.** Earlier drafts assumed a phone-tethered, credential-free
> pendant (first on a single ESP32-S3, then a single nRF5340). Both were
> superseded when the **standalone, no-phone** requirement surfaced: with no phone
> to provide internet or hold keys, the device must carry cellular + a real SoC
> itself. The ADRs below reflect the standalone design.

### ADR-0001 — Standalone cellular on a small Linux SoC + always-on wake island

**Status:** Accepted. (Supersedes the phone-tethered ESP32-S3 and nRF5340 cores.)

**Decision.** Build a standalone device: a tiny **always-on MCU** (wake word +
power control) that boots a small **Linux SoC** (Rockchip RV1106-class) + a
**Cat-1 bis modem** (Quectel EG915U) + camera **on demand** for each session.

**Rationale.** No phone → the device needs its own internet radio and its own
compute. Realtime voice over cellular requires a Linux-class WebRTC/TLS/OTA stack
(unproven on bare MCUs; the Ai Pin used a Snapdragon). Cat-1 bis is the right
cellular tier (full-duplex, <100 ms, single antenna); LTE-M is too jittery for
live voice. The wake island keeps the power/heat-hungry tier off ~99% of the time.

**Consequences.** This is a tiny wearable Linux computer (Ai-Pin-class), not a
cheap flashable MCU — higher cost/complexity, accepted deliberately. Thermal is
the binding constraint (ADR-0006). Runtime is hours-of-talk / all-day-on-demand.

### ADR-0002 — Two-tier provider abstraction, device-resident

**Status:** Accepted (revised: now runs on the device, not a phone app).

The `RealtimeProvider` / `ComposedProvider` split (see §3) lives in the Linux
brain. It is the only way "bring your own LLM" covers both native-voice providers
and Claude/local. Keys are stored on-device, set once at provisioning.

### ADR-0003 — Audio output is a micro-speaker, not bone conduction

**Status:** Accepted. Bone conduction needs skull contact a pendant can't provide
(collarbone is its worst location); a micro-speaker is the only reliably
intelligible option. Caveat: weak outdoors, not private; optional BT-earbud
fallback.

### ADR-0004 — No companion app; one-time on-device web provisioning

**Status:** Accepted. (Replaces the earlier Flutter-app decision.)

There is no phone app. First-run configuration (API key, model choice, eSIM
profile, memory seed) is served by a web page the **device itself** hosts over a
temporary setup link (BLE/Wi-Fi SoftAP/USB), reachable from any browser, then
disabled. See [`PROVISIONING.md`](PROVISIONING.md).

### ADR-0005 — Ephemeral device with a single bounded memory file

**Status:** Accepted.

The device retains **no** conversation/audio/photo history. The only persistent
state is one bounded (~KB), model-curated, on-device, user-resettable, portable
memory file (see §5). This is the privacy foundation and the product's identity
(*pneuma* = breath vs. spirit).

### ADR-0006 — Thermal: passive spreading + on-demand duty-cycling, no active cooling

**Status:** Accepted.

An active heat exchanger isn't feasible at pendant scale. The device stays within
the ≤43 °C skin limit by **not generating heat continuously** (on-demand bursts,
via the wake island) plus **passive graphite/Cu spreading** to an outward
radiating face with skin-side insulation. Continuous streaming — the regime that
throttled the Ai Pin — is explicitly avoided.
