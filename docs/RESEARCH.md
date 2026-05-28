# Pneuma — Research Notes

The evidence base behind [`ARCHITECTURE.md`](ARCHITECTURE.md). Compiled from a
multi-source web research pass (May 2026). Each section notes confidence and
flags fast-changing or low-confidence items honestly. This is a *living* document
— prices, model names, and APIs in this space change month to month.

**Confidence legend:** `[high]` well-sourced / multiple sources · `[med]`
plausible, single or secondary source · `[low]` inferred or unverified.

---

## 1. Realtime / "live" speech-to-speech model APIs

The model "brain" is exposed two ways, which forces a two-tier abstraction.

### Native speech-to-speech (Tier 1)
- **OpenAI `gpt-realtime`** — GA since Aug 28 2025 (first OpenAI GA realtime
  model). Native audio in/out (single model, not a chain). **Image input yes,
  video no.** Transports: WebRTC (recommended for devices), WebSocket, SIP.
  Pricing ~$32/1M audio input tokens, ~$64/1M output. Auth: server API key +
  **ephemeral client secrets** (~2h TTL) for device/browser. `[high]`
  - https://openai.com/index/introducing-gpt-realtime/
  - https://developers.openai.com/api/docs/guides/realtime-webrtc
  - Latency: ~200–350ms first audio; ~300–600ms subsequent turns (third-party
    measured, not an SLA). `[med]`
- **Google Gemini Live API** — bidirectional native audio (30 voices, 24 langs)
  and **native video-frame input (~1 fps)** in the same WebSocket session — the
  only major API with live video input. API key + **ephemeral tokens** for
  direct device connections. Preview status; model names churn
  (`gemini-3.1-flash-live-preview` etc.). `[high]` on capability, `[med]` on
  exact current model name/pricing.
  - https://ai.google.dev/gemini-api/docs/live-api/capabilities
  - https://ai.google.dev/gemini-api/docs/live-api/ephemeral-tokens
- **xAI Grok Voice Agent API** — launched Dec 17 2025. Native S2S over WebSocket,
  **OpenAI-Realtime-API-compatible** (swap base URL to `wss://api.x.ai/v1/realtime`).
  <1s time-to-first-audio, ~$0.05/min (~half OpenAI's voice cost). `[high]`
  - https://x.ai/news/grok-voice-agent-api
- **AWS Nova Sonic (Bedrock)** — native S2S via bidirectional HTTP/2 stream;
  AWS SigV4/IAM auth; Nova 2 Sonic is current gen. `[high]`
  - https://aws.amazon.com/about-aws/whats-new/2025/04/amazon-nova-sonic-speech-to-speech-conversations-bedrock/
- **Azure OpenAI GPT Realtime** — GA (preview deprecates Apr 30 2026); WebRTC +
  WebSocket. Azure **Voice Live API** wraps realtime + Azure Speech. `[high]`
  - https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/realtime-audio

### No native voice → must be composed (Tier 2)
- **Anthropic Claude** — **no native speech-to-speech or standalone STT/TTS API**
  as of May 2026. Messages API is text/vision only. "Voice mode" exists only
  inside Claude's consumer apps, not as a callable API. To use Claude as the
  brain, voice must be composed: STT → Claude Messages API → TTS. `[high]`
  - https://www.datastudios.org/post/claude-voice-features-explained-current-status-and-upcoming-real-time-updates
- **Local models (Ollama / llama.cpp)** — text only; no listening/speaking. S2S
  requires composing external STT + LLM + TTS. `[high]`
  - https://github.com/ollama/ollama/issues/11021
  - Local end-to-end option: MiniCPM-o 2.6 (real-time bilingual S2S, EN/ZH) or
    running Kyutai Moshi locally for true full-duplex. `[med]`

### Open-source orchestration / S2S stacks
- **Kyutai Unmute** — open pipeline (STT + *any* text LLM + TTS), explicitly
  "bring your own text LLM"; best OSS fit for BYO-LLM composed mode. `[high]`
  https://kyutai.org/blog/2025-07-03-tts-unmute-open-source
- **Kyutai Moshi** — open full-duplex speech-native model, ~200ms practical
  latency on an L4. `[high]` https://github.com/kyutai-labs/moshi
- **Pipecat** (frame-based VAD→STT→LLM→TTS, transport-agnostic, swap any
  provider) and **LiveKit Agents** (WebRTC + plugins, can also wrap OpenAI/Gemini
  realtime). The standard way to build BYO-LLM voice today. `[high]`
  - https://github.com/pipecat-ai/pipecat
  - https://docs.livekit.io/agents/models/realtime/plugins/gemini/

**Takeaways:** Grok being OpenAI-compatible means one driver serves both. Gemini
is uniquely able to take a live camera stream. Claude + local models require the
composed pipeline — so a universal "bring your own LLM" device *must* implement
both tiers.

*Fast-changing flags:* Gemini Live model names/pricing churn; OpenAI
`gpt-realtime-2` family mid-rollout; third-party latency numbers are not SLAs.

---

## 2. ESP32-S3 pendant hardware platform

### Seeed XIAO ESP32-S3 Sense
- **21 × 17.5 mm** thumb-size; ESP32-S3R8 dual-core LX7 @ up to 240 MHz with
  vector/ML instructions. **8MB PSRAM + 8MB flash, ~512KB SRAM.** `[high]`
- **Camera: OmniVision OV2640** (2MP, up to UXGA 1600×1200, JPEG/RGB565/YUV,
  ~125mW at 15fps UXGA, detachable; OV5640 5MP swap-in option). `[high]`
- **Mic: digital PDM MEMS** on the Sense board (part commonly cited
  MSM261D3526H1CPM — `[med]`). **Wireless: 2.4GHz Wi-Fi b/g/n + BLE 5.0.** `[high]`
- **Onboard LiPo charge management**; battery solder pads (add JST-PH for a
  3.7V LiPo). Default charge current ~100mA (not officially confirmed — `[low-med]`).
- **Price ~$14** (Sense); ~$7.50 (non-Sense). `[high]`
- Power modes (Seeed doc): modem-sleep ≈ 26.5mA, light-sleep ≈ 2.2mA,
  deep-sleep ≈ 14µA spec (real-world deep sleep higher on the Sense board). `[high]`
  - https://wiki.seeedstudio.com/XIAO_ESP32S3_Consumption/
  - https://docs.edgeimpulse.com/hardware/boards/seeed-xiao-esp32s3-sense

### Battery reality (250–500 mAh LiPo)
Engineering estimates anchored to the **Owl** project (XIAO ESP32-S3 Sense,
continuous capture+stream) which recommends 1200mAh→~8h, 540mAh→~4h, implying
~135–150mA continuous. `[high for anchor]`
- Wake-word listening (radios idle): ~30–50mA `[med]`
- BLE audio streaming: ~40–80mA avg (peaks 80–130mA) `[med]`
- Camera capture: spikes ~150–250mA for the seconds it's on `[med]`
- Wi-Fi active: ~100–240mA (much worse than BLE) `[high]`
- **Conclusion:** continuous-stream-everything ≈ 3–5h; wake-word-gated ≈ 6–12h on
  250–500mAh. A **charge-daily** device, not multi-day. `[high]`
  - https://github.com/OwlAIProject/Owl/blob/main/docs/xiao_esp32s3_sense_setup.md

### On-device wake word while streaming — feasible
- **microWakeWord** (basis of ESPHome `micro_wake_word`): streaming
  Inception/CNN on TFLite-Micro, **<10ms per 20ms stride** on ESP32-S3, needs
  PSRAM (XIAO Sense qualifies). Plenty of headroom to also stream audio (run
  inference on one core, BLE/audio on the other). `[high]`
- **ESP-SR / WakeNet9** runs on S3 but conventionally pauses after detection. `[high]`
- **openWakeWord NOT viable on S3** (seconds per frame; it's for Pi-class Linux). `[high]`
  - https://www.home-assistant.io/blog/2024/02/21/voice-chapter-6/

### Connectivity for a mobile pendant
- **BLE → companion phone = the standard** (Bee, Limitless, Friend/Omi). Lowest
  pendant power; phone does heavy lifting. `[high]`
- **Onboard Wi-Fi → cloud:** avoids phone dependence indoors but ~100–240mA and
  useless when roaming; good only for opportunistic bulk upload. `[high]`
- **Cellular/LTE (e.g. Nordic nRF9160):** true phone-free mobility but heaviest
  cost/power/size + SIM + certification; not standard for consumer pendants. `[high]`

### SoC alternatives
- **nRF52840** (Friend/Omi): Cortex-M4F, BLE5, ~1.5µA sleep, ~40–50× lower BLE
  advertising current than ESP32-S3 → month vs. ~month-vs-year battery edge. **No
  camera, no Wi-Fi, weaker ML.** Best for audio-only multi-day pendants. `[high]`
- **ESP32-S3** wins when you need camera + Wi-Fi + heavier on-device ML in one
  cheap chip — Pneuma's case — at the cost of idle power. `[high]`
- **nRF5340** — more compute, still BLE-only/no-camera. **nRF9160** — only if
  cellular is mandatory. `[med]`
  - https://blefyi.com/compare/nrf52840-vs-esp32-s3/

*Uncertainty flags:* exact XIAO charge IC/current `[low-med]`; exact PDM mic part
`[med]`; per-state mA figures are estimates that firmware choices will move
substantially `[med]`.

---

## 3. Existing open-source AI pendants

### Omi (Based Hardware) — the reference design
- **Two products trace to the original "Friend" project — don't conflate them.**
  **Omi** (Based Hardware / Nik Shevchenko) = open productivity pendant. **Friend**
  (friend.com / Avi Schiffmann) = separate, *closed* companionship pendant. `[high]`
- Hardware: DevKit1 = Seeed **XIAO nRF52840 (Sense)**, Zephyr RTOS (nRF alone,
  not nRF+ESP32). DevKit2/CV1 = **Nordic nRF5340** + 8GB flash + speaker + button
  (`[med]`, from secondary source). PDM MEMS mic, 16kHz. **ESP32-S3 appears only
  in OmiGlass** (the camera variant, with `esp32-camera`). `[high]`
- Audio: **Opus over BLE GATT notifications** — 6 Opus frames × 40 bytes (240B)
  per notification; storage records 444B; LC3 added in newer codec enums. `[high]`
- Architecture: pendant —BLE Opus→ Flutter app —HTTPS/WS→ Python/FastAPI backend
  (VAD, diarization, Deepgram STT, then LLM). App supports local/offline WAL
  buffering. `[high]`
- **On-device wake word: none found** — continuous/VAD-gated capture,
  cloud-side STT. `[med]`
- Battery: DevKit1 ~6h; DevKit2 ~150mAh, ~10–14h. Price ~$70 kit / $89 consumer.
  `[med-high]`
- **License: MIT across firmware + app + backend + hardware CAD** — one of the
  most fully-open wearables. Self-hostable backend. Markets "use the AI model of
  your choice" + ships an **MCP server**. `[high]`
  - https://github.com/BasedHardware/omi
  - Notable: Omi app ships connection drivers for *competitor* hardware
    (`limitless_connection.dart`, `fieldy_connection.dart`) — reverse-engineered
    BLE protocols. `[high]`

### Others
- **Limitless Pendant** — coin-size, beamforming mic array, BLE+Wi-Fi, ~100h
  battery (stores locally, batch-syncs), visible always-on LED, "Consent Mode"
  (voice-ID pauses for new speakers). **Closed.** Acquired by **Meta, Dec 5 2025.** `[high]`
- **Bee** — $49.99 + sub, 7-day battery, always-on, BLE-offload to phone.
  **Acquired by Amazon, Jul 2025.** Closed. `[high]`
- **Plaud** — cloud LLM wrapper (GPT/Claude). Closed (third-party `openplaud`
  exists). `[high]`
- **Friend (friend.com)** — $99–129 always-listening companion, Claude-powered,
  closed; heavy privacy backlash (defaced subway ads). `[high]`
- **ADeus** — MIT, fully open, XIAO ESP32C3 / Coral / Pi Zero, Supabase
  self-host, BYO-LLM. `[high]` https://github.com/adamcohenhillel/ADeus
- **xiaozhi-esp32** — popular MIT ESP32-S3 AI chatbot, **MCP-based,
  model-agnostic**, on-device wake word. `[high]` https://github.com/78/xiaozhi-esp32

### Lessons for Pneuma
- **On-demand (push-to-capture) sidesteps the category's biggest failure** —
  the always-on surveillance backlash that tainted Friend/Bee. Lead with it. `[high]`
- Still need a deliberate, visible **capture indicator** (consent table-stakes). `[high]`
- **Opus over BLE** for audio; **camera over Wi-Fi/BLE-burst** (OmiGlass jumped
  to ESP32-S3+Wi-Fi for images). `[high]`
- BYO-LLM precedents to copy: Omi (MCP + "model of your choice"), xiaozhi (MCP),
  ADeus (BYO-LLM + self-host). **MCP is the emerging provider-agnostic glue.** `[high]`
- **Vendor lock-in/brick risk is real** (Rewind app killed Dec 2025; Bee→Amazon,
  Limitless→Meta). Open + self-hostable + BYO-key is a concrete trust advantage. `[high]`
- **License bar: MIT across firmware+app+backend(+hardware)** — anything less
  reads as "open-washing" to this audience. `[high]`

*Uncertainty flags:* exact MEMS mic part numbers (no public BOM) `[low]`;
DevKit2 nRF5340 from secondary source `[med]`; Limitless internal chipset
undisclosed `[low]`.

---

## 4. Screenless audio output

### Micro-speaker + I2S amp (recommended)
- **MAX98357A** — I2S Class-D, 1.8W into 8Ω, 2.5–5.5V, ~2.4mA quiescent. Best if
  the SoC outputs I2S (ESP32-S3 does). Breakout ~$5.95. `[high]`
  https://www.analog.com/media/en/technical-documentation/data-sheets/max98357a-max98357b.pdf
- **PAM8302** — analog-input alternative, 1.5W into 8Ω, ~$3.95 (needs a DAC if
  SoC is I2S-only). `[high]`
- **20mm 8Ω micro speakers** ~$1–2. `[high]`
- Power: amp idle trivial; playback ~0.3–1W → ~100–300mA peaks during speech. `[med]`
- **Intelligibility:** fine in a quiet room; **degrades fast in noise** —
  confirmed by Humane Ai Pin reviews ("struggled to hear it on NYC streets,"
  "tinny at louder volume"). Not private — bystanders hear it. `[high]`
  https://www.engadget.com/the-humane-ai-pin-is-the-solution-to-none-of-technologys-problems-120002469.html

### Bone conduction — rejected for a pendant
- Needs **firm bone contact**; works in glasses/headbands because they clamp the
  skull. Adafruit #1674 transducer (8Ω, 1W). `[high]`
- **Research rates the collarbone the worst location** for bone conduction;
  energy transfer "drops exponentially" with loose contact. A free-hanging
  necklace can't maintain the contact → degrades into a weak, leaky air-conduction
  buzzer — worst of both worlds. `[high for collarbone-worst; med-high inference
  for the pendant case — no study tested a free-hanging pendant directly]`
  https://www.sciencedirect.com/science/article/abs/pii/S0003687010001523

### Verdict
| Criterion | Micro speaker | Bone conduction |
|-----------|---------------|-----------------|
| Intelligible worn loose on chest | **Yes** (quiet); degrades in noise | **No** (needs skull contact) |
| Privacy | Poor | Good *only if* skull-coupled (not a pendant) |
| BOM (breakouts) | ~$5–8 | ~$12–16 |

**Micro-speaker is the only reliably intelligible option for a necklace.**
Parametric/"audio spotlight" is genuinely directional but too large/power-hungry
to miniaturize into a pendant today. True privacy on a pendant practically means
Bluetooth-earbud fallback — which fights the "no earbuds" goal. `[high]`

---

## 5. Wake word & screenless interaction

### On-device wake-word engines (open-source lens)
- **microWakeWord — recommended.** Apache-2.0 framework + openly-distributed
  models; runs on-S3 via ESPHome `micro_wake_word`; INT8 TFLM. Train a custom
  word with the Piper sample generator + openWakeWord augmentation. No published
  FAR/FRR numbers; author warns good models take tuning. `[high]`
  https://www.kevinahrendt.com/micro-wake-word
- **openWakeWord** — code Apache-2.0 but **pretrained models are CC-BY-NC-SA
  (non-commercial)** → can't ship without retraining; also host-side, not MCU. `[high]`
  https://github.com/dscripka/openWakeWord
- **Espressif ESP-SR / WakeNet** — on-device, but **custom wake word is a
  paid/gated Espressif service** (or heavy DIY corpus: >500 speakers). A few words
  free. `[high]`
- **Picovoice Porcupine** — tiny (~20KB RAM), polished, but **custom keywords are
  proprietary**; free tier ≤3 active users/month for commercial. `[high]`
  https://github.com/Picovoice/porcupine

→ **For an open-source product, microWakeWord is the only choice without a
proprietary/paid gate on the custom word.**

### Choosing the word
- Best practice: 2–4 syllables, distinctive phonemes, uncommon in speech,
  phonetically far from other triggers (Amazon keeps wake candidates ≥3 Hamming
  distance apart). `[high/med]` https://picovoice.ai/blog/complete-guide-to-wake-word/
- **"Pneuma":** great branding/uniqueness (low false-accept), but silent-p + soft
  nasal onset = weak word-start energy for streaming detectors. **Prefer "Hey
  Pneuma"** (stressed carrier improves robustness, cf. "Hey/OK Google"). `[med]`

### Screenless interaction patterns
- **Single button = primary input** across shipping pendants (Limitless mark
  button; Friend tap-to-talk with color LED). Vocabulary: tap = listen,
  double-tap = secondary, long-press = power/pairing. `[high]`
- **Haptics:** use an **LRA over ERM coin motor** (crisp tap, faster, more
  power-efficient). Driver **TI DRV2605L** (I²C, auto-resonance, effect library)
  → map distinct haptic "earcons." `[high]` https://www.ti.com/lit/ds/symlink/drv2605l.pdf
- Pair haptics with an **RGB LED** for redundant glanceable state. `[high]`
- **Earcons:** rising chime = listening; soft tone = done; low/descending = error.
  Keep short, branded, consistent. `[high]`
  https://www.nngroup.com/articles/audio-signifiers-voice-interaction/
- **PTT vs wake word:** PTT is most privacy-clear + lowest power; wake word is
  hands-free but means continuous listening + accidental-trigger risk. For an
  always-worn pendant, offer **both**, with an unmistakable "listening" chime. `[high]`

*Source-access flag:* several primary pages (GitHub, Picovoice, NN/g) returned
403 to direct fetch; those claims rest on search-engine summaries of the same
pages and are marked `[med]` where not read verbatim.

---

## Method & caveats

- Research conducted via parallel multi-source web search + fetch, May 2026.
- This is a **fast-moving space**: model names, prices, API capabilities, and
  even which company owns which pendant change frequently. Re-verify
  load-bearing facts before committing hardware or a provider integration.
- Confidence levels and uncertainty flags are preserved deliberately — treat
  `[low]` items as leads to confirm, not settled facts.
