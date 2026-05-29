//! Device configuration: which provider/model to use and a reference to the API
//! key in secure storage. Set once during provisioning (see docs/PROVISIONING.md).
//! The key itself lives in the secure element / encrypted store — never here.

#[derive(Debug, Clone)]
pub struct DeviceConfig {
    /// Provider id, e.g. "openai", "gemini", "claude", "mock".
    pub provider: String,
    /// Model id, e.g. "gpt-realtime".
    pub model: String,
    /// Opaque handle to the API key in secure storage. Read by real provider
    /// drivers (the mock ignores it).
    #[allow(dead_code)]
    pub key_ref: String,
}

impl Default for DeviceConfig {
    fn default() -> Self {
        DeviceConfig {
            provider: "mock".to_string(),
            model: "mock-1".to_string(),
            key_ref: "secure://none".to_string(),
        }
    }
}
