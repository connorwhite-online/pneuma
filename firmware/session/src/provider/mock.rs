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
            }),
            rx,
        ))
    }
}

struct MockSession {
    tx: mpsc::Sender<SessionEvent>,
    audio_bytes: usize,
    images: usize,
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
        } else {
            let _ = self
                .tx
                .send(SessionEvent::AudioReply(b"Hi Connor, how can I help?".to_vec()));
        }
        let _ = self.tx.send(SessionEvent::TurnComplete);
        Ok(())
    }

    fn close(&mut self) {}
}
