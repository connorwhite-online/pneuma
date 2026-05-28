# Pneuma — Architecture

This document describes the intended system design for Pneuma: a screenless,
voice-first wearable AI device with on-demand vision and a pluggable ("bring your
own") model. It is the synthesis of the research recorded in
[`RESEARCH.md`](RESEARCH.md). Where a design choice was a genuine fork, it is
captured as an **Architecture Decision Record (ADR)** at the end.

Status: **design, pre-implementation.** Nothing here is built yet; this is the
blueprint we intend to build against.

---

## 1. System overview

Pneuma splits cleanly into three tiers, each with a single clear job:

| Tier | What it is | Responsibilities | Holds secrets? |
|------|------------|------------------|----------------|
| **Pendant** | The wearable (ESP32-S3) | Wake word, mic capture, on-demand camera, audio out, haptics/LED, BLE/Wi-Fi link | **No** |
| **Companion app** | Phone (or optional home hub) | Credential storage, provider routing, connectivity, session orchestration | **Yes** |
| **Provider (brain)** | User's chosen model | Reasoning, and (Tier 1) speech | Remote/local |

```
        ┌─────────────────┐        BLE (Opus audio)        ┌────────────────────┐
        │     PENDANT      │  ───────────────────────────▶  │   COMPANION APP    │
        │  (credential-    │   Wi-Fi burst (camera frame)   │   (keys + router)  │
        │   free)          │  ───────────────────────────▶  │                    │
        │                  │  ◀───────────────────────────  │                    │
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

---

## 2. The interaction loop

```
   ┌──────────────────────────────────────────────────────────────────────┐
   │  idle (light-sleep, mic listening for wake word on-device)             │
   └───────────────┬────────────────────────────────────────────────────────┘
                   │ "Hey Pneuma"  (or button press = push-to-talk)
                   ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  LISTENING   → earcon (rising chime) + LED + haptic tap                │
   │  stream Opus audio over BLE to the companion app                       │
   └───────────────┬────────────────────────────────────────────────────────┘
                   │ (intent appears visual? e.g. "what am I looking at?")
                   ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  CAPTURE (on-demand only)  → wake camera, grab ONE frame               │
   │  visible capture indicator (LED + sound); send frame over Wi-Fi burst  │
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

The camera is **never** woken except inside an explicit, indicated CAPTURE step.
There is no continuous video, no background recording.

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
only ever speaks "audio/Opus + optional frame" to the app. All provider
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

## 4. Hardware platform (v1)

**Single Seeed XIAO ESP32-S3 Sense.** One chip handles mic + camera + on-device
wake word + BLE + Wi-Fi. See **ADR-0001** for the reasoning (and the dual-MCU
alternative we deliberately deferred).

Indicative v1 component set (full BOM/wiring to live in `hardware/`):

| Function | Part | Notes |
|----------|------|-------|
| Compute + camera + mic | Seeed XIAO ESP32-S3 Sense | OV2640 2MP cam, PDM mic, 8MB PSRAM, BLE+Wi-Fi, ~21×17.5mm, ~$14 |
| Audio amp | MAX98357A (I2S) | ~$6; 1.8W into 8Ω |
| Speaker | 20mm 8Ω ~1W | ~$2; fire upward toward face |
| Haptics | LRA + DRV2605L driver | crisp taps, low power, effect library |
| Indicator | RGB LED | glanceable state, redundant with haptics |
| Input | momentary button | tap / double / long-press |
| Power | LiPo 250–500 mAh + charge circuit | "charge daily" device |

**Power reality (honest):** continuous-stream-everything ≈ 3–5 h; wake-word-gated
with light-sleep ≈ 6–12 h on 250–500 mAh. This is a charge-daily wearable, which
is acceptable for an on-demand (not always-on) device. Multi-day battery is the
main reason one might later move to the dual-MCU design (ADR-0001).

### Transport
- **Audio:** Opus over BLE GATT notifications (category standard; Omi's
  6×40-byte-per-notification framing is a good reference). Consider LC3 if moving
  to BLE Audio later.
- **Camera frames:** Wi-Fi burst — images are too large for comfortable BLE
  throughput (this is exactly why Omi's camera variant uses ESP32-S3 + Wi-Fi).

---

## 5. Wake word & screenless UX

- **Engine: microWakeWord** (Apache-2.0) running on the ESP32-S3. It is the only
  mainstream on-MCU engine that lets an open-source project train and ship a
  *custom* wake word with no proprietary or per-unit-paid gate. (openWakeWord's
  pretrained models are non-commercial; Porcupine and Espressif ESP-SR gate
  custom words behind paid/proprietary terms.)
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

**I2S micro-speaker (MAX98357A + 20mm 8Ω), firing upward toward the face.**
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
  Camera fires only inside an explicit, indicated CAPTURE step.
- **No secrets on the device.** Keys live in the companion app.
- **Visible/audible capture indicator** is mandatory (category table-stakes).
- **Open + self-hostable** end to end, so the device can't be bricked or have its
  trust model changed by an acquisition — the failure mode that has repeatedly
  burned this category.

---

## Architecture Decision Records

### ADR-0001 — v1 uses a single ESP32-S3, not a dual-MCU (nRF + ESP32-S3) design

**Status:** Accepted for v1 (revisitable for v2).

**Context.** The proven low-power audio pendants (e.g. Omi) use Nordic nRF52840 +
Zephyr for month-long BLE battery, but the nRF has no camera and no Wi-Fi, and
images are too large for plain BLE — which is why camera variants jump to an
ESP32-S3 + Wi-Fi. Pneuma needs *both* mic and camera. The fork is: one ESP32-S3
that does everything (simpler, ~6–12h battery) vs. a dual-MCU board (nRF for
always-on audio + ESP32-S3 woken for camera; multi-day audio battery, more
complexity).

**Decision.** Ship v1 on a **single off-the-shelf Seeed XIAO ESP32-S3 Sense.**

**Rationale.**
1. **Contributor accessibility.** An open-source v1 must be buyable and flashable
   by anyone; the XIAO is a $14 stock board. Dual-MCU needs a custom PCB *before*
   anyone can participate.
2. **The camera neutralizes nRF's advantage.** Pneuma is fundamentally a vision
   device; using the camera wakes an S3-class chip + Wi-Fi anyway, so nRF's
   ultra-low-power BLE superpower is largely wasted.
3. **On-demand duty cycle suits the S3.** nRF wins for *continuous* always-on
   streaming, which Pneuma explicitly is not. Wake-word-gated + light-sleep is
   within the S3's acceptable range.
4. **Charge-daily is an accepted norm** (AirPods, Apple Watch) for an
   intermittent-use device.

**Consequences / mitigations.** Battery is ~6–12h (charge daily). To keep the
door open to dual-MCU later, firmware will use a **hardware-abstraction layer**
so the audio/wake-word path can move to an nRF co-processor *without changing the
app or provider layers*. Revisit if real-world battery feedback demands multi-day.

### ADR-0002 — The provider layer is a two-tier abstraction (Realtime + Composed)

**Status:** Accepted.

**Context.** "Bring your own LLM" must work for backends with native
speech-to-speech (OpenAI/Gemini/Grok/Nova) *and* backends with none (Claude, all
local models). A single-shape integration would silently exclude Claude and
off-grid local use.

**Decision.** Implement two backends behind one `Provider` interface:
`RealtimeProvider` (single S2S socket) and `ComposedProvider` (STT → LLM → TTS,
via Pipecat/LiveKit/Unmute-style orchestration). The pendant firmware is
identical in both cases and only ever exchanges audio + optional frame with the
app.

**Consequences.** More app-side code, but it is the only design that honors
"bring your own LLM" universally — and it is what resurrects a **fully off-grid
mode** (local STT + LLM + TTS) as a first-class option.

### ADR-0003 — Audio output is a micro-speaker, not bone conduction

**Status:** Accepted. See §6 for rationale (skull-contact requirement makes bone
conduction unsuitable for a free-hanging pendant; collarbone is its worst
location).
