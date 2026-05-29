//! Secure storage for secrets (API keys), set during provisioning.
//!
//! On the device this is the secure element / encrypted flash; the key never
//! appears in `DeviceConfig` or in logs. Provider drivers resolve a `key_ref`
//! (from config) to the actual secret through this trait. See
//! docs/PROVISIONING.md and docs/ARCHITECTURE.md §3.

use crate::provider::ProviderError;

pub trait KeyStore: Send {
    /// Resolve an opaque key reference to the secret it points at.
    fn get(&self, key_ref: &str) -> Result<String, ProviderError>;
}

/// Laptop/dev keystore: returns a dummy for the mock providers, otherwise reads
/// the secret from the `PNEUMA_API_KEY` environment variable. Lets the real
/// driver code path be exercised without a secure element.
pub struct MockKeyStore;

impl KeyStore for MockKeyStore {
    fn get(&self, key_ref: &str) -> Result<String, ProviderError> {
        if key_ref == "secure://none" {
            return Ok("dummy-key".to_string());
        }
        std::env::var("PNEUMA_API_KEY")
            .map_err(|_| ProviderError::Auth(format!("no key for {key_ref} (set PNEUMA_API_KEY)")))
    }
}
