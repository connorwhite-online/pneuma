# Pneuma — Architecture

This document describes the intended system design for Pneuma: a screenless,
voice-first wearable AI device with on-demand vision and a pluggable ("bring your
own") model. It is the synthesis of the research recorded in
[`RESEARCH.md`](RESEARCH.md). Where a design choice was a genuine fork, it is
captured as an **Architecture Decision Record (ADR)** at the end.

Status: **design, pre-implementation.** Nothing here is built yet; this is the
blueprint we intend to build against. We are designing for the *best* core, not a
throwaway prototype — the enclosure/mechanical will be iterated separately.

---

## 1. System overview

Pneuma splits cleanly into three tiers, each with a single clear job:

| Tier | What it is | Responsibilities | Holds secrets? |
|------|------------|------------------|----------------|
| **Pendant** | The wearable (nRF5340) | Wake word, mic capture, on-demand camera, audio out, haptics/LED, BLE link | **No** |
| **Companion app** | Phone (or optional home hub) | Credential storage, provider routing, connectivity, session orchestration | **Yes** |
| **Provider (brain)** | User's chosen model | Reasoning, and (Tier 1) speech | Remote/local |

```
        ┌─────────────────┐  BLE (LC3 audio + JPEG frame)  ┌────────────────────┐
        │     PENDANT      │  ───────────────────────────▶  │   COMPANION APP    │
        │  (credential-    │   on-demand photo over BLE     │   (keys + router)  │
        │   free)          │  ◀───────────────────────────  │                    │
        │                  │        audio reply             └─────────┬──────────┘
        └─────────────────┘                                          │
                                                          ┌──────────┴───────────┐
                                                          │      THE BRAIN        │
                                                          │  Tier 1 / Tier 2      │
                                                          └───────────────────────┘
```

**Why the pendant holds no credentials:** it keeps the most-exposed, most-easily-
lost physical object free of secrets; it lets the open hardware be trivially
reproducible; and it is the right privacy story. The phone is already a battery,
a modem, and a compute host — offloading to it keeps the pendant tiny and cheap.

**Why a single radio (BLE) is enough:** the device is fundamentally an *I/O node*
— the LLM lives in the phone/cloud. It only ever needs to move compressed audio
and, on demand, a single JPEG to the phone. Both fit comfortably over BLE, so no
Wi-Fi (and no second SoC) is required. See ADR-0001.

---

## 2. The interaction loop

```
   ┌──────────────────────────────────────────────────────────────────────┐
   │  idle (low-power, mic listening for wake word on-device)               │
   └───────────────┬────────────────────────────────────────────────────────┘
                   │ "Hey Pneuma"  (or button press = push-to-talk)
                   ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  LISTENING   → earcon (rising chime) + LED + haptic tap                │
   │  stream LC3 audio over BLE to the companion app                        │
   └───────────────┬────────────────────────────────────────────────────────┘
                   │ (intent appears visual? e.g. "what am I looking at?")
                   ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  CAPTURE (on-demand only)  → power up camera, grab ONE JPEG frame      │
   │  visible capture indicator (LED + sound); send frame over BLE (<1s)    │
   │  then power the camera back down                                       │
   └───────────────┬────────────────────────────────────────────────────────┘
                   ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  THINKING  → app routes to chosen provider (Tier 1 or Tier 2)          │
   └───────────────┬────────────────────────────────────────────────────────┘
                   ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  SPEAKING  → audio reply played on pendant speaker; "done" earcon      │
   └────────────────────────────────────────────────────────────────────────┘
```

The camera is **never** powered except inside an explicit, indicated CAPTURE
step. There is no continuous video, no background recording. Physically, the
camera sits behind a load switch the firmware only closes for the capture.

---

## 3. The provider abstraction (the core of "bring your own LLM")

Providers expose their "brain" in two fundamentally different shapes. To support
*any* model the user brings, the companion app implements **both**, behind one
interface.

### Tier 1 — `RealtimeProvider` (native speech-to-speech)
One streaming socket: audio (and sometimes video) up, voice down. ASR +
reasoning + TTS + turn-taking happen server-side. Lowest latency, least code.

- **OpenAI** `gpt-realtime` (GA) — audio + image input, WebRTC/WS, ephemeral tokens.
- **Google Gemini Live** — audio + **native video input (~1 fps)**, WebSocket, ephemeral tokens.
- **xAI Grok Voice** — audio, WebSocket, **OpenAI-Realtime-protocol-compatible** (so one driver targets both OpenAI and Grok by swapping the base URL).
- **AWS Nova Sonic** — audio, HTTP/2 bidi, AWS SigV4.

### Tier 2 — `ComposedProvider` (STT → text LLM → TTS)
Pneuma orchestrates the pipeline itself. **Required** for any model with no
native voice API:

- **Anthropic Claude** — text/vision only (Messages API); no native S2S.
- **Local models** (Ollama / llama.cpp) — text only; this tier is what makes a
  **fully off-grid mode** possible (local STT like Whisper/Moonshine + local LLM
  + local TTS like Piper/Kokoro).

Orchestration can lean on existing open frameworks (Pipecat, LiveKit Agents,
Kyutai Unmute) rather than reinventing the pipeline.

### Interface sketch

```
interface Provider {
  startSession(opts): Session        // opens whatever transport the backend needs
}

interface Session {
  pushAudio(chunk)                   // mic audio in
  pushImage(frame)                   // on-demand camera frame in
  onAudioReply(cb)                   // voice out (Tier 1 native; Tier 2 from TTS)
  onTranscript(cb)                   // text, for logging/tools
  endTurn() / close()
}
```

`RealtimeProvider` maps these onto a single socket; `ComposedProvider` fans them
out to STT → LLM → TTS. The pendant firmware is **identical** in both cases — it
only ever speaks "audio + optional JPEG" to the app over BLE. All provider
complexity is hidden in the app.

### Tooling / glue
Adopt **MCP (Model Context Protocol)** for the tool/provider layer — both Omi and
xiaozhi-esp32 converged on MCP as the model-agnostic way to give the brain tools
and route between models.

### Capability matrix (what the router must reason about)

| Provider | Native voice | Vision input | Off-grid | Auth |
|----------|--------------|--------------|----------|------|
| OpenAI `gpt-realtime` | ✅ | image | ❌ | key + ephemeral token |
| Gemini Live | ✅ | ✅ video ~1fps | ❌ | key + ephemeral token |
| xAI Grok | ✅ (OpenAI-compatible) | audio | ❌ | key |
| AWS Nova Sonic | ✅ | audio | ❌ | SigV4 |
| Anthropic Claude | ❌ → Tier 2 | image | ❌ | key |
| Local (Ollama) | ❌ → Tier 2 | VLM-dependent | ✅ | none |

---

## 4. Hardware core: single nRF5340 + SPI camera

One SoC handles compute, BLE, mic, speaker, and (via SPI) the camera. See
**ADR-0001** for the full reasoning and the alternatives we rejected.

| Function | Part | Connection to nRF5340 |
|----------|------|------------------------|
| MCU + radio | **Nordic nRF5340** (module, e.g. Raytac MDBT53-1M) | — |
| Camera | **ArduCAM Mega 3MP/5MP** (SPI, on-chip JPEG) | SPI + power-gate GPIO |
| Microphone | **Infineon IM69D130** (PDM MEMS) | PDM (CLK + DATA) |
| Audio amp | **MAX98357A** (I2S Class-D) | I2S (BCLK/LRCLK/DIN) + shutdown GPIO |
| Speaker | 20 mm 8 Ω | amp output |
| Haptics | **LRA + DRV2605L** driver | I2C + enable GPIO |
| Indicator | RGB LED (or WS2812) | GPIO |
| Input | momentary button | GPIO (interrupt) |
| Charger | **MCP73831** (or BQ25180) | USB-C VBUS in |
| Fuel gauge | **MAX17048** | I2C |
| Battery | LiPo ~250 mAh | via charger |

Full BOM with part numbers, prices, and the complete interconnect map lives in
[`../hardware/BOM.md`](../hardware/BOM.md).

### Power profile
The dominant state is *idle-but-listening*. On an nRF5340 this is a few mA
(CPU + PDM + periodic BLE), versus ~25–40 mA for an ESP32-S3 (which cannot run
wake-word detection from deep sleep). That ~5–8× difference yields roughly
**33–67 h on a 250 mAh cell** for the nRF design. The camera's ~55–150 mA only
applies during the brief on-demand capture and is gated off otherwise.

### Transport
- **Audio:** LC3 over BLE (LE Audio) — native to the nRF5340's audio subsystem.
  (Opus is also feasible; LC3 is the natural LE Audio choice.)
- **Camera:** a single JPEG over BLE GATT at 2M PHY — a 10–50 KB frame transfers
  in ~0.06–0.4 s, well under a second. No Wi-Fi needed because we never stream
  video, only fetch one frame on demand.

---

## 5. Wake word & screenless UX

- **Engine: a Cortex-M keyword-spotting model** (DS-CNN class) running on the
  nRF5340 via TFLite-Micro + CMSIS-NN. Note: **microWakeWord does *not* port** —
  it depends on the ESP32-S3's Xtensa vector instructions and PSRAM. A single
  wake word fits the M33's 512 KB RAM easily; this is a shipping pattern in
  hearables. Training data can still be generated with the open
  Piper/openWakeWord synthetic-sample pipeline; we train a Cortex-M-suitable
  model and keep it open (avoid Porcupine, whose custom words are proprietary).
- **Wake phrase: "Hey Pneuma."** "Pneuma" alone is brandable but acoustically
  weak as a trigger (silent "p" + soft nasal onset = little energy at word start,
  which streaming detectors rely on). A stressed carrier improves detection.
  Validate false-accept/false-reject with a real training run.
- **Inputs:** single button — `tap` = start/stop listening (push-to-talk),
  `double-tap` = secondary, `long-press` = power/pairing.
- **Feedback (no screen):** LRA **haptics** (DRV2605L) + **RGB LED** + a small set
  of **earcons** — rising chime = listening, soft tone = done, low tone = error.
  Always give a *deliberate, visible/audible* signal when the camera captures.

---

## 6. Audio output

**I2S micro-speaker (MAX98357A + 20 mm 8 Ω), firing upward toward the face.**
Bone conduction was evaluated and **rejected for a pendant**: it requires firm
skull contact a free-hanging necklace can't maintain, and the collarbone is the
worst-rated location for it. The micro-speaker is the only reliably intelligible
option for a chest-worn device. Caveats: it is weak outdoors/in noise and is
**not private** (bystanders hear it). Offer optional Bluetooth-earbud fallback
for privacy/noise, accepting that this trades against the "no earbuds" ideal.

---

## 7. Privacy & trust posture

This is a product principle, not just a feature:

- **On-demand capture only.** No continuous audio recording, no background video.
  Camera is physically powered off (behind a load switch) except during an
  explicit, indicated CAPTURE step.
- **No secrets on the device.** Keys live in the companion app.
- **Visible/audible capture indicator** is mandatory (category table-stakes).
- **Open + self-hostable** end to end, so the device can't be bricked or have its
  trust model changed by an acquisition — the failure mode that has repeatedly
  burned this category.

---

## Architecture Decision Records

### ADR-0001 — The core is a single nRF5340 + SPI camera (not ESP32-S3, not dual-MCU)

**Status:** Accepted. (Supersedes the earlier single-ESP32-S3 decision, which was
made under a "fastest off-the-shelf v1" framing we have since dropped in favor of
designing the best core outright.)

**Context.** The device is a brain-offloaded I/O node: always-on wake word,
audio over BLE, and a single on-demand photo. Three cores were evaluated:
(A) single ESP32-S3, (B) dual-MCU (nRF for always-on audio + ESP32-S3 woken only
for the camera), (C) single nRF5340 with an SPI camera.

**Decision.** Build on a **single nRF5340 driving an ArduCAM Mega SPI camera.**

**Rationale.**
1. **Power.** An ESP32-S3 cannot run wake-word detection from deep sleep, so it
   sits at ~25–40 mA in the always-listening state; an nRF is ~3–8 mA — a 5–8×
   gap in the state the device lives in ~99% of the time. This rules out (A).
2. **One frame over BLE is fast enough.** A 10–50 KB JPEG transfers in
   ~0.06–0.4 s at 2M PHY. We never stream video, so the only thing that would
   force Wi-Fi / an ESP32 (sustained throughput) never arises — this collapses
   the choice between (B) and (C) toward (C).
3. **The camera does the hard part.** The ArduCAM Mega outputs compressed JPEG
   over plain SPI, so the nRF's lack of a camera (DCMI) interface is irrelevant.
4. **It's a proven integration.** Nordic maintains an nRF5340 + ArduCAM Mega
   Zephyr driver (`take_picture` sample) and official BLE image-transfer demos.
5. **One chip covers the rest.** nRF5340 has native PDM (mic), I2S (speaker),
   LC3/LE Audio, and BLE — no second SoC, radio, or firmware image.

**Consequences / tradeoffs.**
- Wake word must use a Cortex-M KWS model, not microWakeWord (see §5).
- Real BLE throughput depends on the connecting phone's negotiated PHY/connection
  interval — validate sub-1s photo transfer on target phones.
- JPEG size is scene-dependent — validate the 10–50 KB assumption empirically.
- We forgo Wi-Fi (no phone-free cloud), live video, and heavy on-device vision/ML.
  None are in scope; if any becomes a hard requirement, revisit (B).

### ADR-0002 — The provider layer is a two-tier abstraction (Realtime + Composed)

**Status:** Accepted.

**Context.** "Bring your own LLM" must work for backends with native
speech-to-speech (OpenAI/Gemini/Grok/Nova) *and* backends with none (Claude, all
local models). A single-shape integration would silently exclude Claude and
off-grid local use.

**Decision.** Implement two backends behind one `Provider` interface:
`RealtimeProvider` (single S2S socket) and `ComposedProvider` (STT → LLM → TTS,
via Pipecat/LiveKit/Unmute-style orchestration). The pendant firmware is
identical in both cases and only ever exchanges audio + optional JPEG with the
app.

**Consequences.** More app-side code, but it is the only design that honors
"bring your own LLM" universally — and it is what resurrects a **fully off-grid
mode** (local STT + LLM + TTS) as a first-class option.

### ADR-0003 — Audio output is a micro-speaker, not bone conduction

**Status:** Accepted. See §6 for rationale (skull-contact requirement makes bone
conduction unsuitable for a free-hanging pendant; collarbone is its worst
location).

### ADR-0004 — The companion app is Flutter, with a pure-Dart `pneuma-core` engine

**Status:** Accepted.

**Context.** The app must do BLE, on-device WebRTC (OpenAI Realtime) + WebSocket
(Gemini Live), secure credential storage, and the provider router — on both iOS
and Android, as an open-source project that wants contributors.

**Decision.** Build the app in **Flutter**, with all provider/router/session/BLE
logic in a **pure-Dart `pneuma-core`** package that has no UI/OS dependencies.

**Rationale.** Single cross-platform codebase; mature BLE/WebRTC/WebSocket
libraries; `pneuma-core` is reusable headless inside an optional self-hosted hub;
precedent set by Omi's Flutter app. React Native/Expo is the main alternative.
See [`APP.md`](APP.md) §4.

### ADR-0005 — Default topology is direct-to-provider; the hub is optional

**Status:** Accepted.

**Context.** "Bring your own LLM" with a credible privacy story requires deciding
whether a Pneuma-operated server sits between the user and their model.

**Decision.** **No Pneuma server by default.** The app talks directly to the
user's chosen provider; keys and audio go phone → provider only. A self-hostable
**Pneuma hub** (running the same `pneuma-core` headless) is an *optional* path for
local-model / off-grid / shared-household use.

**Consequences.** The trust story is clean (no middleman); Tier-2 composed
pipelines and local models run from the app or the user's own hub, never our
infrastructure. See [`APP.md`](APP.md) §3.
