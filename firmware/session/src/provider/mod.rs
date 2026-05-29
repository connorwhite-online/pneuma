//! Provider abstraction — the heart of "bring your own LLM".
//!
//! Two tiers (see docs/ARCHITECTURE.md §3):
//!  - **Tier 1 `Realtime`** — native speech-to-speech (OpenAI Realtime, Gemini
//!    Live, Grok, Nova Sonic): one streaming socket, audio up, voice down.
//!  - **Tier 2 `Composed`** — STT → text LLM → TTS, orchestrated on-device
//!    (Claude and local models, which have no native speech-to-speech).
//!
//! Both implement the same `Provider`/`Session` surface, so the interaction
//! state machine in `crate::state` is provider-agnostic. Adding a model = adding
//! one driver here + a stored key.

pub mod composed;
pub mod mock;
pub mod openai;

use crate::config::DeviceConfig;
use crate::secure::KeyStore;

/// Build the configured provider driver — the router entry point. Maps the
/// provisioned provider id to a Tier-1 (realtime) or Tier-2 (composed) driver and
/// wires the API key from secure storage. See docs/ARCHITECTURE.md §3.
pub fn build(config: &DeviceConfig, keys: &dyn KeyStore) -> Result<Box<dyn Provider>, ProviderError> {
    match config.provider.as_str() {
        "mock" => Ok(Box::new(mock::MockProvider)),
        "mock-composed" => Ok(Box::new(composed::mock_composed())),
        "openai" => {
            let api_key = keys.get(&config.key_ref)?;
            Ok(Box::new(openai::OpenAiRealtime {
                api_key,
                model: config.model.clone(),
            }))
        }
        // Claude has no native speech-to-speech → Tier-2 composed (driver TODO).
        "claude" => Err(ProviderError::Unsupported(
            "claude (composed STT→LLM→TTS) driver not implemented yet — see provider/composed.rs"
                .to_string(),
        )),
        other => Err(ProviderError::Unsupported(format!(
            "unknown provider '{other}'"
        ))),
    }
}

/// A chunk of mic audio (PCM/Opus; encoding negotiated per provider).
pub type AudioChunk = Vec<u8>;
/// A single JPEG frame captured on demand.
pub type ImageFrame = Vec<u8>;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Tier {
    /// Native speech-to-speech.
    Realtime,
    /// STT → text LLM → TTS, composed on-device.
    Composed,
}

/// A durable-memory change the model asked for during a turn.
#[derive(Debug, Clone)]
pub enum MemoryOp {
    Remember(String),
    Forget(String),
}

/// Events streamed back from a live session.
#[derive(Debug, Clone)]
pub enum SessionEvent {
    /// Voice audio to play to the user.
    AudioReply(AudioChunk),
    /// Incremental transcript text (for memory/tools/logging — not retained).
    Transcript(String),
    /// The model proposed a durable memory update.
    MemoryUpdate(MemoryOp),
    /// A tool/function call (MCP).
    ToolCall { name: String, args: String },
    /// The model finished its turn.
    TurnComplete,
    /// Session-level error.
    Error(String),
}

/// Options for opening a session.
pub struct SessionOpts {
    pub model: String,
    /// Memory-file contents injected as context at session start.
    pub memory_context: String,
    pub system_prompt: String,
}

/// A provider knows how to start a live session.
pub trait Provider: Send {
    fn name(&self) -> &str;
    fn tier(&self) -> Tier;
    fn start_session(
        &self,
        opts: SessionOpts,
    ) -> Result<(Box<dyn Session>, std::sync::mpsc::Receiver<SessionEvent>), ProviderError>;
}

/// A live conversation session. Events come back on the `Receiver` handed out by
/// `start_session`.
pub trait Session: Send {
    /// Push a chunk of mic audio up.
    fn push_audio(&mut self, chunk: AudioChunk) -> Result<(), ProviderError>;
    /// Push an on-demand captured frame up.
    fn push_image(&mut self, frame: ImageFrame) -> Result<(), ProviderError>;
    /// Signal the end of the user's turn (e.g. on detected silence).
    fn end_turn(&mut self) -> Result<(), ProviderError>;
    /// Hand back the result of a tool the model asked for, so it can continue the
    /// turn. Default: no-op (providers that don't request tools ignore it).
    fn push_tool_result(&mut self, _name: &str, _result: String) -> Result<(), ProviderError> {
        Ok(())
    }
    /// Close the session and release resources.
    fn close(&mut self);
}

#[derive(Debug)]
pub enum ProviderError {
    Network(String),
    Auth(String),
    Unsupported(String),
    Other(String),
}

impl std::fmt::Display for ProviderError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ProviderError::Network(s) => write!(f, "network error: {s}"),
            ProviderError::Auth(s) => write!(f, "auth error: {s}"),
            ProviderError::Unsupported(s) => write!(f, "unsupported: {s}"),
            ProviderError::Other(s) => write!(f, "error: {s}"),
        }
    }
}

impl std::error::Error for ProviderError {}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::DeviceConfig;
    use crate::secure::MockKeyStore;

    fn cfg(p: &str) -> DeviceConfig {
        DeviceConfig {
            provider: p.into(),
            model: "m".into(),
            key_ref: "secure://none".into(),
        }
    }

    #[test]
    fn router_builds_both_tiers_and_rejects_unknown() {
        let k = MockKeyStore;
        assert_eq!(build(&cfg("mock"), &k).unwrap().tier(), Tier::Realtime);
        assert_eq!(
            build(&cfg("mock-composed"), &k).unwrap().tier(),
            Tier::Composed
        );
        assert!(build(&cfg("nope"), &k).is_err());
    }
}
