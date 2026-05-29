//! Pneuma session brain — scaffold entry point.
//!
//! Wires the mock HAL + mock provider into the interaction state machine and
//! runs two simulated wake events (a voice query and a visual query) so you can
//! watch the full Sleep → Connect → Capture → Converse → Forget loop, and see
//! the memory file persist across interactions. Runs on a laptop, no hardware.

mod config;
mod hal;
mod memory;
mod provider;
mod state;

use config::DeviceConfig;
use hal::mock::{MockCamera, MockMic, MockModem, MockSpeaker, MockWake};
use hal::{WakeLink, WakeReason};
use memory::Memory;
use provider::mock::MockProvider;
use state::Pneuma;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("=== Pneuma session brain (scaffold: mock HAL + mock provider) ===\n");

    let mem_path = std::env::temp_dir().join("pneuma_memory.toml");
    let memory = match Memory::load(&mem_path) {
        Ok(m) => {
            println!("[boot] loaded memory from {}", mem_path.display());
            m
        }
        Err(_) => {
            println!("[boot] no memory file yet; seeding a fresh one");
            let mut m = Memory::new(memory::DEFAULT_CAP_BYTES);
            m.set("name", "Connor");
            m.set("units", "metric");
            m
        }
    };

    let mut device = Pneuma::new(
        Box::new(MockMic::with_seconds(2)),
        Box::new(MockSpeaker),
        Box::new(MockCamera),
        Box::new(MockModem::offline()),
        Box::new(MockProvider),
        memory,
        mem_path.clone(),
        DeviceConfig::default(),
    );

    // The wake island would feed these; here we simulate a voice query then a
    // visual ("what am I looking at?") query.
    let mut wake = MockWake::with(vec![WakeReason::WakeWord, WakeReason::Visual]);
    while let Some(reason) = wake.next_wake() {
        println!("\n--- wake: {reason:?} ---");
        device.run_once(reason)?;
        wake.power_down();
    }

    println!("\n=== memory file now ({}) ===", mem_path.display());
    println!("{}", device.memory().serialize());
    Ok(())
}
