//! The interaction state machine: Sleep → Connect → Capture → Converse → Forget.
//! Provider- and hardware-agnostic — it drives `dyn Provider` over `dyn` HAL
//! traits, so the same logic runs on mocks (laptop) or real drivers (device).
//! See docs/ARCHITECTURE.md §2.

use std::error::Error;
use std::path::PathBuf;

use crate::config::DeviceConfig;
use crate::hal::{AudioIn, AudioOut, Camera, Modem, WakeReason};
use crate::memory::Memory;
use crate::provider::{MemoryOp, Provider, SessionEvent, SessionOpts};

const SYSTEM_PROMPT: &str = "You are Pneuma, a concise, warm voice companion. \
Answer briefly. Use the user's memory for context. Only mention what you see when asked.";

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum State {
    Sleep,
    Connect,
    Capture,
    Converse,
    Forget,
}

pub struct Pneuma {
    mic: Box<dyn AudioIn>,
    speaker: Box<dyn AudioOut>,
    camera: Box<dyn Camera>,
    modem: Box<dyn Modem>,
    provider: Box<dyn Provider>,
    memory: Memory,
    memory_path: PathBuf,
    config: DeviceConfig,
}

impl Pneuma {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        mic: Box<dyn AudioIn>,
        speaker: Box<dyn AudioOut>,
        camera: Box<dyn Camera>,
        modem: Box<dyn Modem>,
        provider: Box<dyn Provider>,
        memory: Memory,
        memory_path: PathBuf,
        config: DeviceConfig,
    ) -> Self {
        Pneuma {
            mic,
            speaker,
            camera,
            modem,
            provider,
            memory,
            memory_path,
            config,
        }
    }

    pub fn memory(&self) -> &Memory {
        &self.memory
    }

    /// Run one full interaction, triggered by a wake event from the wake island.
    pub fn run_once(&mut self, wake: WakeReason) -> Result<(), Box<dyn Error>> {
        // CONNECT — bring the cellular link up and open a provider session.
        println!("  [state] {:?}", State::Connect);
        if !self.modem.is_online() {
            self.modem.connect();
        }
        let opts = SessionOpts {
            model: self.config.model.clone(),
            memory_context: self.memory.to_context(),
            system_prompt: SYSTEM_PROMPT.to_string(),
        };
        println!(
            "  [provider:{}] starting session (model={})",
            self.provider.name(),
            opts.model
        );
        let (mut session, events) = self.provider.start_session(opts)?;

        // CAPTURE — on demand only; camera is otherwise powered off.
        if wake.wants_vision() {
            println!("  [state] {:?}", State::Capture);
            if let Some(frame) = self.camera.capture() {
                session.push_image(frame)?;
            }
        }

        // CONVERSE — stream the turn's mic audio up, then close the turn.
        println!("  [state] {:?}", State::Converse);
        while let Some(chunk) = self.mic.next_chunk() {
            session.push_audio(chunk)?;
        }
        session.end_turn()?;

        let mut pending: Vec<MemoryOp> = Vec::new();
        for ev in events.iter() {
            match ev {
                SessionEvent::AudioReply(audio) => self.speaker.play(&audio),
                SessionEvent::Transcript(t) => println!("  [transcript] {t}"),
                SessionEvent::MemoryUpdate(op) => {
                    println!("  [memory] proposed: {op:?}");
                    pending.push(op);
                }
                SessionEvent::ToolCall { name, args } => println!("  [tool] {name}({args})"),
                SessionEvent::TurnComplete => break,
                SessionEvent::Error(e) => {
                    eprintln!("  [error] {e}");
                    break;
                }
            }
        }
        session.close();

        // FORGET & SLEEP — apply memory updates, then keep ONLY the memory file.
        println!("  [state] {:?}", State::Forget);
        for op in pending {
            self.memory.apply(op);
        }
        self.memory.compact();
        self.memory.save(&self.memory_path)?;
        println!(
            "  [memory] saved ({} bytes); audio/frames/context discarded",
            self.memory.serialize().len()
        );
        Ok(())
    }
}
