//! OpenAI `gpt-realtime` driver (Tier 1) — STUB.
//!
//! Real implementation:
//!  1. Mint an ephemeral token from the user's API key.
//!  2. Open a TLS WebSocket to `wss://api.openai.com/v1/realtime?model=...`.
//!  3. Send `session.update` with audio format + `instructions` built from the
//!     system prompt and the injected memory context.
//!  4. Stream mic audio up as `input_audio_buffer.append`; push frames as image
//!     content; commit on `end_turn`.
//!  5. Translate `response.audio.delta` → `AudioReply`, `response.text.delta` →
//!     `Transcript`, `response.function_call_arguments.*` → `ToolCall`.
//!
//! Needs an async runtime (tokio) + `tokio-tungstenite` + TLS — added when we
//! move past the dependency-free scaffold.
#![allow(dead_code)]

use super::*;

pub struct OpenAiRealtime {
    pub api_key: String,
    pub model: String,
}

impl Provider for OpenAiRealtime {
    fn name(&self) -> &str {
        "openai"
    }
    fn tier(&self) -> Tier {
        Tier::Realtime
    }
    fn start_session(
        &self,
        _opts: SessionOpts,
    ) -> Result<(Box<dyn Session>, std::sync::mpsc::Receiver<SessionEvent>), ProviderError> {
        Err(ProviderError::Unsupported(
            "OpenAI realtime driver not implemented yet — see module docs for the plan".to_string(),
        ))
    }
}
