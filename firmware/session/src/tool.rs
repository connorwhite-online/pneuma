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

/// The default tool set wired into a device.
pub fn default_registry() -> ToolRegistry {
    let mut r = ToolRegistry::new();
    r.register(Box::new(GetTime));
    r
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn runs_known_and_reports_unknown() {
        let r = default_registry();
        assert!(r.run("get_time", "{}").contains("3:00 PM"));
        assert!(r.run("nope", "{}").contains("unknown tool"));
    }
}
