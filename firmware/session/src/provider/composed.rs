//! Tier-2 **Composed** provider — STT → text LLM → TTS, orchestrated on-device.
//!
//! This is the path for models with no native speech-to-speech (Anthropic Claude
//! today) and for future on-device/local models. The three stages are separate
//! traits, so each can be a different vendor (e.g. a cloud STT + Claude + a cloud
//! TTS) or, later, local implementations — without the interaction state machine
//! knowing the difference. See docs/ARCHITECTURE.md §3.

use super::*;

/// Speech-to-text stage.
pub trait Stt: Send {
    fn transcribe(&self, audio: &[AudioChunk]) -> Result<String, ProviderError>;
}

/// Text LLM stage.
pub trait Llm: Send {
    fn complete(&self, req: LlmRequest) -> Result<LlmReply, ProviderError>;
}

/// Text-to-speech stage.
pub trait Tts: Send {
    fn synthesize(&self, text: &str) -> Result<AudioChunk, ProviderError>;
}

/// What the LLM stage gets for a turn.
pub struct LlmRequest<'a> {
    pub system_prompt: &'a str,
    pub memory_context: &'a str,
    /// In-session conversation so far (ephemeral; RAM-only, never persisted).
    pub history: &'a [(String, String)],
    pub user_text: &'a str,
    pub image: Option<&'a ImageFrame>,
}

/// What the LLM stage returns.
pub struct LlmReply {
    pub text: String,
    pub memory_ops: Vec<MemoryOp>,
}

type Stages = (Box<dyn Stt>, Box<dyn Llm>, Box<dyn Tts>);

/// A composed provider. Holds a factory so each session gets fresh stage
/// instances (a real one closes over API keys / endpoints).
pub struct ComposedProvider {
    name: String,
    make: Box<dyn Fn() -> Stages + Send + Sync>,
}

impl ComposedProvider {
    pub fn new(
        name: impl Into<String>,
        make: impl Fn() -> Stages + Send + Sync + 'static,
    ) -> Self {
        ComposedProvider {
            name: name.into(),
            make: Box::new(make),
        }
    }
}

impl Provider for ComposedProvider {
    fn name(&self) -> &str {
        &self.name
    }
    fn tier(&self) -> Tier {
        Tier::Composed
    }
    fn start_session(
        &self,
        opts: SessionOpts,
    ) -> Result<(Box<dyn Session>, std::sync::mpsc::Receiver<SessionEvent>), ProviderError> {
        let (stt, llm, tts) = (self.make)();
        let (tx, rx) = std::sync::mpsc::channel();
        Ok((
            Box::new(ComposedSession {
                tx,
                stt,
                llm,
                tts,
                system_prompt: opts.system_prompt,
                memory_context: opts.memory_context,
                audio_buf: Vec::new(),
                image: None,
                history: Vec::new(),
            }),
            rx,
        ))
    }
}

struct ComposedSession {
    tx: std::sync::mpsc::Sender<SessionEvent>,
    stt: Box<dyn Stt>,
    llm: Box<dyn Llm>,
    tts: Box<dyn Tts>,
    system_prompt: String,
    memory_context: String,
    audio_buf: Vec<AudioChunk>,
    image: Option<ImageFrame>,
    history: Vec<(String, String)>,
}

impl Session for ComposedSession {
    fn push_audio(&mut self, chunk: AudioChunk) -> Result<(), ProviderError> {
        self.audio_buf.push(chunk);
        Ok(())
    }

    fn push_image(&mut self, frame: ImageFrame) -> Result<(), ProviderError> {
        self.image = Some(frame);
        Ok(())
    }

    fn end_turn(&mut self) -> Result<(), ProviderError> {
        // STT → LLM → TTS, in order, on-device.
        let user_text = self.stt.transcribe(&self.audio_buf)?;
        self.audio_buf.clear();
        let _ = self
            .tx
            .send(SessionEvent::Transcript(format!("user: {user_text}")));

        let reply = self.llm.complete(LlmRequest {
            system_prompt: &self.system_prompt,
            memory_context: &self.memory_context,
            history: &self.history,
            user_text: &user_text,
            image: self.image.as_ref(),
        })?;
        self.image = None;

        for op in &reply.memory_ops {
            let _ = self.tx.send(SessionEvent::MemoryUpdate(op.clone()));
        }
        let audio = self.tts.synthesize(&reply.text)?;
        let _ = self.tx.send(SessionEvent::AudioReply(audio));
        self.history.push((user_text, reply.text));
        let _ = self.tx.send(SessionEvent::TurnComplete);
        Ok(())
    }

    fn close(&mut self) {
        // Ephemeral: the in-session conversation is dropped, never persisted.
        self.history.clear();
    }
}

// ---- mock stages: a laptop-runnable Tier-2 provider (stands in for Claude) ----

/// A composed provider wired from mock stages, so the Tier-2 path runs on a
/// laptop with no network or keys.
pub fn mock_composed() -> ComposedProvider {
    ComposedProvider::new("mock-composed", || {
        (
            Box::new(MockStt) as Box<dyn Stt>,
            Box::new(MockLlm) as Box<dyn Llm>,
            Box::new(MockTts) as Box<dyn Tts>,
        )
    })
}

struct MockStt;
impl Stt for MockStt {
    fn transcribe(&self, audio: &[AudioChunk]) -> Result<String, ProviderError> {
        let bytes: usize = audio.iter().map(|c| c.len()).sum();
        Ok(format!("(transcribed {bytes} bytes of speech)"))
    }
}

struct MockLlm;
impl Llm for MockLlm {
    fn complete(&self, req: LlmRequest) -> Result<LlmReply, ProviderError> {
        if req.image.is_some() {
            Ok(LlmReply {
                text: "It's a cappuccino.".to_string(),
                memory_ops: vec![MemoryOp::Remember("Drinks cappuccino".to_string())],
            })
        } else {
            Ok(LlmReply {
                text: format!("Composed reply (turn {}).", req.history.len() + 1),
                memory_ops: vec![],
            })
        }
    }
}

struct MockTts;
impl Tts for MockTts {
    fn synthesize(&self, text: &str) -> Result<AudioChunk, ProviderError> {
        Ok(text.as_bytes().to_vec())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn composed_runs_stt_llm_tts() {
        let p = mock_composed();
        assert_eq!(p.tier(), Tier::Composed);
        let (mut s, events) = p
            .start_session(SessionOpts {
                model: "claude".into(),
                memory_context: String::new(),
                system_prompt: "sys".into(),
            })
            .unwrap();
        s.push_image(b"<<jpeg>>".to_vec()).unwrap();
        s.push_audio(vec![0u8; 100]).unwrap();
        s.end_turn().unwrap();

        let mut reply_bytes = 0;
        let mut memory_ops = 0;
        for ev in events.iter() {
            match ev {
                SessionEvent::AudioReply(a) => reply_bytes = a.len(),
                SessionEvent::MemoryUpdate(_) => memory_ops += 1,
                SessionEvent::TurnComplete => break,
                _ => {}
            }
        }
        assert!(reply_bytes > 0, "TTS should produce audio");
        assert_eq!(memory_ops, 1, "image turn should propose one memory op");
    }
}
