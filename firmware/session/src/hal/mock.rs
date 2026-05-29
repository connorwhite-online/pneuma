//! Mock HAL — laptop-runnable fakes for every hardware interface.

use super::*;
use std::collections::VecDeque;

/// Yields a fixed number of audio chunks per turn, then `None` (end of turn),
/// then re-arms for the next turn.
pub struct MockMic {
    per_turn: usize,
    left: usize,
    followups_left: usize,
}

impl MockMic {
    /// A single-turn interaction of roughly `seconds` of speech.
    pub fn with_seconds(seconds: usize) -> Self {
        Self::conversation(seconds, 0)
    }

    /// A multi-turn conversation: an initial turn plus `followups` more.
    pub fn conversation(seconds: usize, followups: usize) -> Self {
        let n = seconds * 5; // ~5 chunks/sec, placeholder
        MockMic {
            per_turn: n,
            left: n,
            followups_left: followups,
        }
    }
}

impl AudioIn for MockMic {
    fn next_chunk(&mut self) -> Option<AudioChunk> {
        if self.left == 0 {
            self.left = self.per_turn; // re-arm for the next turn
            return None;
        }
        self.left -= 1;
        Some(vec![0u8; 320]) // ~20 ms placeholder frame
    }

    fn awaiting_followup(&mut self) -> bool {
        if self.followups_left > 0 {
            self.followups_left -= 1;
            true
        } else {
            false
        }
    }
}

pub struct MockSpeaker;

impl AudioOut for MockSpeaker {
    fn play(&mut self, chunk: &AudioChunk) {
        println!(
            "  [speaker] \"{}\"",
            String::from_utf8_lossy(chunk)
        );
    }
}

pub struct MockCamera;

impl Camera for MockCamera {
    fn capture(&mut self) -> Option<ImageFrame> {
        println!("  [camera] powered on → captured 1 JPEG → powered off");
        Some(b"<<jpeg>>".to_vec())
    }
}

pub struct MockModem {
    online: bool,
}

impl MockModem {
    pub fn offline() -> Self {
        MockModem { online: false }
    }
}

impl Modem for MockModem {
    fn is_online(&self) -> bool {
        self.online
    }
    fn connect(&mut self) -> bool {
        println!("  [modem] attaching to LTE Cat-1 bis … online");
        self.online = true;
        true
    }
}

pub struct MockWake {
    queue: VecDeque<WakeReason>,
}

impl MockWake {
    pub fn with(reasons: Vec<WakeReason>) -> Self {
        MockWake {
            queue: reasons.into(),
        }
    }
}

impl WakeLink for MockWake {
    fn next_wake(&mut self) -> Option<WakeReason> {
        self.queue.pop_front()
    }
    fn power_down(&mut self) {
        println!("[wake-island] session tier powered down; listening (µA)");
    }
}
