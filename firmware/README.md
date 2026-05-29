# Pneuma firmware

Two programs, matching the two-tier brain (see [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)).

## `session/` — the session brain (Rust, Linux SoC)

The on-demand brain: the **provider router** (Tier-1 realtime / Tier-2 composed),
the **interaction state machine** (Sleep → Connect → Capture → Converse → Forget),
and the bounded **memory file**. Hardware (modem, audio, camera, wake-island link)
sits behind traits in `session/src/hal`, with mock implementations so the whole
loop **builds and runs on your laptop today** — no hardware, no network, no keys.

```sh
cargo run  --manifest-path session/Cargo.toml    # run the mock interaction loop
cargo test --manifest-path session/Cargo.toml    # memory-file tests
```

Dependency-free for now (std only). Real drivers — an async runtime, a
WebSocket/WebRTC client to the provider, TLS, and vendor audio/camera libs — plug
in behind the existing traits. The OpenAI realtime driver stub (with the
implementation plan) is in `session/src/provider/openai.rs`.

Layout:
| Path | Job |
|------|-----|
| `src/state.rs` | the multi-turn interaction state machine |
| `src/provider/` | `Provider`/`Session` traits, `build()` router, Tier-1 (`mock`, `openai` stub) + Tier-2 `composed` (STT→LLM→TTS) |
| `src/hal/` | hardware traits (`AudioIn`+VAD, `Camera`, `Modem`, …) + mocks |
| `src/memory.rs` | the bounded memory file (load/save/compact + tests) |
| `src/secure.rs` | `KeyStore` — resolves the API key from secure storage |
| `src/config.rs` | device config (provider/model/key handle) |

`provider::build(&config, &keystore)` is the router: it maps the provisioned
provider id to a Tier-1 or Tier-2 driver and pulls the key from the keystore. Both
tiers run on the laptop via mocks (`cargo run` shows a realtime conversation and a
composed query back to back).

## `wake-island/` — always-on co-processor (C, nRF52840 / nRF Connect SDK)

Wake-word + button, and power control of the session SoC. Builds against the
Nordic nRF Connect SDK (Zephyr) — not part of this repo's tooling. Scaffold only.

The interface between the two programs is specified in
[../docs/PROTOCOL.md](../docs/PROTOCOL.md).
