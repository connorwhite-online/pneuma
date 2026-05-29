//! Pneuma session brain — scaffold entry point.
//!
//! Wires the mock HAL through the provider **router** (`provider::build`) into the
//! interaction state machine, and runs two demos so you can watch the full
//! Sleep → Connect → Capture → Converse → Forget loop on a laptop, no hardware:
//!   1. a Tier-1 *realtime* provider over a two-turn voice conversation + a visual query;
//!   2. a Tier-2 *composed* (STT→LLM→TTS) provider — the Claude/local path —
//!      reusing the memory the first demo saved (the only state that survives).
#![allow(dead_code)] // scaffold: the full trait/enum surface is exercised by real drivers + tests

mod config;
mod hal;
mod memory;
mod provider;
mod secure;
mod state;
mod tool;

use std::path::Path;

use config::DeviceConfig;
use hal::mock::{MockCamera, MockMic, MockModem, MockSpeaker, MockWake};
use hal::{WakeLink, WakeReason};
use memory::Memory;
use secure::MockKeyStore;
use state::Pneuma;

fn boot_memory(path: &Path) -> Memory {
    match Memory::load(path) {
        Ok(m) => {
            println!("[boot] loaded memory from {}", path.display());
            m
        }
        Err(_) => {
            println!("[boot] no memory file yet; seeding a fresh one");
            let mut m = Memory::new(memory::DEFAULT_CAP_BYTES);
            m.set("name", "Connor");
            m.set("units", "metric");
            m
        }
    }
}

fn run_demo(
    title: &str,
    config: DeviceConfig,
    mic: MockMic,
    wakes: Vec<WakeReason>,
    mem_path: &Path,
) -> Result<(), Box<dyn std::error::Error>> {
    println!("\n========== {title} ==========");

    // The router picks the driver from config and pulls the key from secure storage.
    let keys = MockKeyStore;
    let provider = provider::build(&config, &keys)?;

    let memory = boot_memory(mem_path);
    let mut device = Pneuma::new(
        Box::new(mic),
        Box::new(MockSpeaker),
        Box::new(MockCamera),
        Box::new(MockModem::offline()),
        provider,
        memory,
        mem_path.to_path_buf(),
        config,
    );

    // The wake island would feed these wake events; here they're simulated.
    let mut wake = MockWake::with(wakes);
    while let Some(reason) = wake.next_wake() {
        println!("\n--- wake: {reason:?} ---");
        device.run_once(reason)?;
        wake.power_down();
    }
    println!("\nmemory now:\n{}", device.memory().serialize());
    Ok(())
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("=== Pneuma session brain (scaffold: mock HAL + provider router) ===");
    let mem_path = std::env::temp_dir().join("pneuma_memory.toml");

    // Demo 1 — Tier-1 realtime: a two-turn voice conversation, then a visual query.
    run_demo(
        "Tier-1 realtime (mock)",
        DeviceConfig {
            provider: "mock".into(),
            model: "mock-realtime".into(),
            key_ref: "secure://none".into(),
        },
        MockMic::conversation(2, 1),
        vec![WakeReason::WakeWord, WakeReason::Visual],
        &mem_path,
    )?;

    // Demo 2 — Tier-2 composed (STT→LLM→TTS), the Claude/local path. Loads the
    // memory demo 1 saved, proving persistence across the only surviving state.
    run_demo(
        "Tier-2 composed (mock)",
        DeviceConfig {
            provider: "mock-composed".into(),
            model: "claude-ish".into(),
            key_ref: "secure://none".into(),
        },
        MockMic::conversation(1, 0),
        vec![WakeReason::Visual],
        &mem_path,
    )?;

    Ok(())
}
