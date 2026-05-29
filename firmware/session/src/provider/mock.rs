//! A mock provider so the whole interaction loop runs on a laptop with no
//! network or API key. It pretends to be a Tier-1 realtime provider: it counts
//! the audio/image it receives and, on `end_turn`, emits a canned reply and a
//! sample memory update.

use super::*;
use std::sync::mpsc;

pub struct MockProvider;

impl Provider for MockProvider {
    fn name(&self) -> &str {
        "mock"
    }
    fn tier(&self) -> Tier {
        Tier::Realtime
    }
    fn start_session(
        &self,
        opts: SessionOpts,
    ) -> Result<(Box<dyn Session>, mpsc::Receiver<SessionEvent>), ProviderError> {
        println!(
            "  [provider:mock] session up (injected {} bytes of memory context)",
            opts.memory_context.len()
        );
        let (tx, rx) = mpsc::channel();
        Ok((
            Box::new(MockSession {
                tx,
                audio_bytes: 0,
                images: 0,
                tools_used: false,
            }),
            rx,
        ))
    }
}

struct MockSession {
    tx: mpsc::Sender<SessionEvent>,
    audio_bytes: usize,
    images: usize,
    tools_used: bool,
}

impl Session for MockSession {
    fn push_audio(&mut self, chunk: AudioChunk) -> Result<(), ProviderError> {
        self.audio_bytes += chunk.len();
        Ok(())
    }

    fn push_image(&mut self, _frame: ImageFrame) -> Result<(), ProviderError> {
        self.images += 1;
        Ok(())
    }

    fn end_turn(&mut self) -> Result<(), ProviderError> {
        let _ = self.tx.send(SessionEvent::Transcript(format!(
            "(received {} bytes audio, {} image(s))",
            self.audio_bytes, self.images
        )));
        if self.images > 0 {
            let _ = self
                .tx
                .send(SessionEvent::AudioReply(b"That looks like a cup of coffee.".to_vec()));
            let _ = self
                .tx
                .send(SessionEvent::MemoryUpdate(MemoryOp::Remember("Drinks coffee".to_string())));
            let _ = self.tx.send(SessionEvent::TurnComplete);
        } else if !self.tools_used {
            // First voice turn: demonstrate a tool round-trip. We ask for a tool
            // and DON'T complete the turn — we wait for `push_tool_result`.
            self.tools_used = true;
            let _ = self.tx.send(SessionEvent::ToolCall {
                name: "get_time".to_string(),
                args: "{}".to_string(),
            });
        } else {
            let _ = self
                .tx
                .send(SessionEvent::AudioReply(b"Anything else?".to_vec()));
            let _ = self.tx.send(SessionEvent::TurnComplete);
        }
        Ok(())
    }

    fn push_tool_result(&mut self, _name: &str, result: String) -> Result<(), ProviderError> {
        // The model now has the tool result and finishes the turn.
        let _ = self.tx.send(SessionEvent::AudioReply(
            format!("Got it ({result}). Hi Connor, how can I help?").into_bytes(),
        ));
        let _ = self.tx.send(SessionEvent::TurnComplete);
        Ok(())
    }

    fn close(&mut self) {}
}
