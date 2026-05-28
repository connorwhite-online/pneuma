# Pneuma — The Companion App

The pendant has no internet and knows nothing about AI models. **The app is where
"bring your own LLM" actually lives.** It is the device's brain-router, gateway to
the network, and the only place credentials exist.

Status: **design, pre-implementation.** See also
[`ARCHITECTURE.md`](ARCHITECTURE.md) (system context, ADRs) and
[`PROTOCOL.md`](PROTOCOL.md) (the BLE contract the app and firmware share).

---

## 1. What the app is responsible for

| Responsibility | Detail |
|----------------|--------|
| **Credential vault** | Stores the user's API key / OAuth in the OS secure enclave (iOS Keychain / Android Keystore). Never written to the pendant. Mints short-lived ephemeral tokens for direct device→provider where the provider supports it (OpenAI, Gemini). |
| **Provider router** | A registry of provider drivers implementing one interface; routes each session to a Tier-1 (`RealtimeProvider`) or Tier-2 (`ComposedProvider`) backend. The software embodiment of ADR-0002. |
| **BLE bridge** | Connects/pairs with the pendant, decodes LC3 audio and chunked JPEG frames, sends audio replies back. Implements the client side of [`PROTOCOL.md`](PROTOCOL.md). |
| **Session engine** | Runs the interaction state machine (listening → thinking → speaking), turn-taking, and surfaces MCP tool calls. |
| **Connectivity** | Provides the internet path the pendant lacks (cloud providers), or points at a LAN/self-hosted endpoint (local models). |
| **Human surface** | Onboarding, settings, privacy controls, and on-device interaction history. |

---

## 2. Internal architecture

The app is deliberately split so the engine is reusable beyond a phone:

```
┌───────────────────────────── platform shell (per-OS) ─────────────────────────────┐
│  UI / onboarding / settings    secure keyvault    BLE radio    audio routing /     │
│  (Flutter widgets)             (Keychain/Keystore) access      mic+speaker perms   │
└───────────────────────────────────────┬────────────────────────────────────────────┘
                                         │  calls
┌────────────────────────────────── pneuma-core (pure Dart) ───────────────────────────┐
│  Session engine (state machine)   Provider router   BLE protocol codec   MCP client   │
│                                         │                                              │
│                          ┌──────────────┴───────────────┐                              │
│                          ▼                              ▼                               │
│                  RealtimeProvider drivers        ComposedProvider drivers               │
│                  • OpenAI gpt-realtime           • Anthropic Claude (STT→LLM→TTS)        │
│                  • Gemini Live                   • Local / Ollama (STT→LLM→TTS)          │
│                  • xAI Grok (OpenAI-compatible)  • (pluggable STT/TTS choices)           │
│                  • AWS Nova Sonic                                                        │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

**`pneuma-core`** is pure Dart with no Flutter/UI/OS dependencies, so the exact
same engine can run headless inside an optional **Pneuma hub** (desktop / Raspberry
Pi) for users who want local models or a shared household brain.

### The provider driver interface (illustrative Dart)

```dart
abstract class Provider {
  ProviderCapabilities get capabilities;     // native voice? vision? off-grid?
  Future<Session> startSession(SessionOptions opts);
}

abstract class Session {
  void pushAudio(Uint8List lc3Chunk);        // mic audio up
  void pushImage(Uint8List jpeg);            // on-demand camera frame up
  Stream<Uint8List> get audioReply;          // voice down (native or from TTS)
  Stream<String> get transcript;             // text, for history/tools
  Stream<ToolCall> get toolCalls;            // MCP tool invocations
  Future<void> endTurn();
  Future<void> close();
}
```

`RealtimeProvider` maps these onto a single WebRTC/WebSocket socket.
`ComposedProvider` fans them out to STT → LLM → TTS. **The pendant firmware is
identical in both cases** — it only ever speaks audio + optional JPEG over BLE.
Adding a new model = adding one driver (+ a key).

---

## 3. Topology: direct-to-provider by default

```
DEFAULT (mobile, no server):   pendant ──BLE──▶ phone app ──HTTPS/WS──▶ provider
                               (keys never leave the phone)

OPTIONAL (power user / off-grid):
                               pendant ──BLE──▶ phone app ──LAN──▶ Pneuma hub
                                                                   (local STT+LLM+TTS,
                                                                    same pneuma-core)
```

- **Default = the app talks directly to the chosen provider.** No Pneuma server
  sits in the loop; your key and audio go phone → provider and nowhere else. This
  is the core trust story.
- **Optional self-hostable hub** runs the same engine headless for local-model /
  off-grid / shared use. Nothing about the device or app requires it.

---

## 4. Tech stack (recommended)

**Flutter (Dart).** Rationale:
- Single codebase for iOS + Android; strong fit for an open-source project that
  wants contributors and reach.
- Mature BLE (`flutter_blue_plus`), WebRTC (`flutter_webrtc`) for OpenAI Realtime,
  and WebSocket for Gemini Live — covers both provider tiers on-device.
- Lets `pneuma-core` be pure Dart and reused by a headless hub.
- Precedent: the closest fully-open wearable (Omi) ships a Flutter app.

Main alternative: **React Native / Expo** (TypeScript) — viable, with
`react-native-ble-plx`; choose it if the contributor pool skews TS. Native
Swift/Kotlin gives the best audio/BLE control at 2× the surface area.

See ADR-0004.

---

## 5. Onboarding & UX (screenless device, normal phone app)

Minimal first-run:
1. **Pair** the pendant (BLE scan → connect).
2. **Pick your model** (OpenAI / Gemini / Grok / Claude / local).
3. **Add credentials** — paste API key or sign in via OAuth.
4. **Try it** — "Say *Hey Pneuma*." Confirms the loop end-to-end.

Steady-state, the phone app is mostly *out of the way* — the device is the
interface. The app surfaces:
- **Settings:** wake word on/off + push-to-talk, capture-indicator behavior,
  earbud fallback, voice/persona, per-provider config.
- **Privacy:** an always-visible reminder that capture is on-demand; controls to
  view/delete history; ephemeral-token status.
- **History:** a lightweight, on-device, deletable log of *discrete interactions*
  (your Q&As) — not a continuous recording, because there isn't one.
- **Device:** battery, firmware version, OTA updates, re-pair.

---

## 6. Privacy properties (must hold)

- Credentials live only in the phone secure enclave; never on the pendant.
- Default topology has no Pneuma-operated server; audio/keys go to *your* chosen
  provider only.
- History is local-first and deletable; on-demand capture means there is no
  background audio/video to leak.
- These mirror the device-side posture in [`ARCHITECTURE.md`](ARCHITECTURE.md) §7.
