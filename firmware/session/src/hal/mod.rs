//! Hardware abstraction layer.
//!
//! Real drivers (cellular modem, PDM/I2S audio, MIPI camera, the wake-island
//! link) implement these traits; `src/hal/mock.rs` provides laptop-runnable
//! fakes so the session logic builds and runs with no hardware.

use crate::provider::{AudioChunk, ImageFrame};

pub mod mock;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum WakeReason {
    WakeWord,
    ButtonTap,
    ButtonLong,
    /// An explicit "look at this" trigger (e.g. button + camera gesture).
    Visual,
}

impl WakeReason {
    /// Hint that this interaction likely needs an on-demand camera frame.
    pub fn wants_vision(&self) -> bool {
        matches!(self, WakeReason::Visual)
    }
}

/// Microphone source (PDM/I2S). Returns `None` to mark the end of the user's turn.
pub trait AudioIn: Send {
    fn next_chunk(&mut self) -> Option<AudioChunk>;
}

/// Speaker sink (I2S → amp).
pub trait AudioOut: Send {
    fn play(&mut self, chunk: &AudioChunk);
}

/// On-demand camera: powered up, one JPEG, powered down.
pub trait Camera: Send {
    fn capture(&mut self) -> Option<ImageFrame>;
}

/// Cellular modem (LTE Cat-1 bis).
pub trait Modem: Send {
    fn is_online(&self) -> bool;
    fn connect(&mut self) -> bool;
}

/// Link to the always-on wake island (source of wake events; power control).
pub trait WakeLink: Send {
    fn next_wake(&mut self) -> Option<WakeReason>;
    fn power_down(&mut self);
}
