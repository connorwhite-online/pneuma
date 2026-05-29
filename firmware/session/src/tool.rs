//! Tool calling (MCP-style). Mid-turn, the model can ask the device to run a
//! tool; the device executes it and hands the result back, and the model
//! continues with it. Tools are how Pneuma *does* things (time, search, home
//! control, …) beyond talking. See docs/ARCHITECTURE.md §3 (MCP glue).
//!
//! Real MCP servers register here too; the trait is the local-tool surface.

use std::collections::HashMap;

/// A callable tool. `call` takes JSON-ish args and returns a JSON-ish result.
pub trait Tool: Send + Sync {
    fn name(&self) -> &str;
    fn description(&self) -> &str;
    fn call(&self, args: &str) -> Result<String, String>;
}

/// The tools available to a session.
#[derive(Default)]
pub struct ToolRegistry {
    tools: HashMap<String, Box<dyn Tool>>,
}

impl ToolRegistry {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn register(&mut self, tool: Box<dyn Tool>) {
        self.tools.insert(tool.name().to_string(), tool);
    }

    /// Run a tool by name. Errors (including unknown tool) come back as a JSON
    /// error string so the model can see and recover, never as a panic.
    pub fn run(&self, name: &str, args: &str) -> String {
        match self.tools.get(name) {
            Some(t) => match t.call(args) {
                Ok(out) => out,
                Err(e) => format!("{{\"error\":\"{e}\"}}"),
            },
            None => format!("{{\"error\":\"unknown tool '{name}'\"}}"),
        }
    }

    pub fn names(&self) -> Vec<&str> {
        self.tools.keys().map(|s| s.as_str()).collect()
    }
}

/// A built-in demo tool. Returns a fixed reading so the scaffold is deterministic
/// (a real one would read the RTC).
pub struct GetTime;
impl Tool for GetTime {
    fn name(&self) -> &str {
        "get_time"
    }
    fn description(&self) -> &str {
        "Get the current local time."
    }
    fn call(&self, _args: &str) -> Result<String, String> {
        Ok("{\"time\":\"3:00 PM\"}".to_string())
    }
}

/// Location from the GNSS receiver (needs a GNSS-capable modem + antenna — see BOM).
pub struct GetLocation;
impl Tool for GetLocation {
    fn name(&self) -> &str {
        "get_location"
    }
    fn description(&self) -> &str {
        "Get the device's current GPS location."
    }
    fn call(&self, _args: &str) -> Result<String, String> {
        Ok("{\"lat\":45.5152,\"lon\":-122.6784,\"accuracy_m\":8}".to_string())
    }
}

/// Directions to a destination (calls a maps API in the real impl). On-demand
/// ("how do I get to X?"); live turn-by-turn is the sustained nav power mode.
pub struct Directions;
impl Tool for Directions {
    fn name(&self) -> &str {
        "directions"
    }
    fn description(&self) -> &str {
        "Walking directions to a destination from the current location."
    }
    fn call(&self, args: &str) -> Result<String, String> {
        Ok(format!(
            "{{\"dest\":\"{}\",\"summary\":\"head north 400 m, then left for 200 m\",\"eta_min\":7}}",
            args.trim()
        ))
    }
}

/// Play music from the linked Spotify (Premium) account via librespot, out to a
/// Bluetooth sink or the speaker. Real impl gates on account + a BT-audio path.
pub struct PlayMusic;
impl Tool for PlayMusic {
    fn name(&self) -> &str {
        "play_music"
    }
    fn description(&self) -> &str {
        "Play music from the linked Spotify account."
    }
    fn call(&self, args: &str) -> Result<String, String> {
        Ok(format!(
            "{{\"playing\":\"{}\",\"source\":\"spotify\",\"output\":\"bluetooth\"}}",
            args.trim()
        ))
    }
}

/// The default tool set wired into a device. Real builds register a tool only when
/// its hardware/config is present (GNSS for location, a BT-audio path + Spotify
/// account for music).
pub fn default_registry() -> ToolRegistry {
    let mut r = ToolRegistry::new();
    r.register(Box::new(GetTime));
    r.register(Box::new(GetLocation));
    r.register(Box::new(Directions));
    r.register(Box::new(PlayMusic));
    r
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn runs_known_and_reports_unknown() {
        let r = default_registry();
        assert!(r.run("get_time", "{}").contains("3:00 PM"));
        assert!(r.run("get_location", "{}").contains("lat"));
        assert!(r.run("directions", "the park").contains("eta_min"));
        assert!(r.run("play_music", "lo-fi beats").contains("spotify"));
        assert!(r.run("nope", "{}").contains("unknown tool"));
    }
}
