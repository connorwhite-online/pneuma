//! The bounded memory file — the device's only persistent state (the "spirit").
//! See docs/MEMORY.md. A small, human-readable, curated profile; never a log.

use crate::provider::MemoryOp;
use std::path::Path;

/// Default hard cap on the serialized memory file.
pub const DEFAULT_CAP_BYTES: usize = 4096;

pub struct Memory {
    fields: Vec<(String, String)>,
    facts: Vec<String>,
    cap_bytes: usize,
}

impl Memory {
    pub fn new(cap_bytes: usize) -> Self {
        Memory {
            fields: Vec::new(),
            facts: Vec::new(),
            cap_bytes,
        }
    }

    pub fn set(&mut self, key: &str, value: &str) {
        if let Some(entry) = self.fields.iter_mut().find(|(k, _)| k == key) {
            entry.1 = value.to_string();
        } else {
            self.fields.push((key.to_string(), value.to_string()));
        }
    }

    pub fn get(&self, key: &str) -> Option<&str> {
        self.fields
            .iter()
            .find(|(k, _)| k == key)
            .map(|(_, v)| v.as_str())
    }

    pub fn facts(&self) -> &[String] {
        &self.facts
    }

    /// Apply a model-proposed durable change.
    pub fn apply(&mut self, op: MemoryOp) {
        match op {
            MemoryOp::Remember(fact) => {
                if !self.facts.iter().any(|f| f == &fact) {
                    self.facts.push(fact);
                }
            }
            MemoryOp::Forget(needle) => {
                self.facts.retain(|f| !f.contains(&needle));
            }
        }
    }

    /// Enforce the byte cap. Scaffold: drop oldest facts until under the cap.
    /// TODO: the real device asks the model to summarize/merge facts so the
    /// memory stays small without simply losing the oldest ones.
    pub fn compact(&mut self) {
        while self.serialize().len() > self.cap_bytes && !self.facts.is_empty() {
            self.facts.remove(0);
        }
    }

    /// Context injected into a session at start.
    pub fn to_context(&self) -> String {
        let mut s = String::from("What you durably know about the user:\n");
        for (k, v) in &self.fields {
            s.push_str(&format!("- {k}: {v}\n"));
        }
        if !self.facts.is_empty() {
            s.push_str("Facts:\n");
            for f in &self.facts {
                s.push_str(&format!("- {f}\n"));
            }
        }
        s
    }

    pub fn serialize(&self) -> String {
        let mut out = String::from("# pneuma memory v1\n");
        for (k, v) in &self.fields {
            out.push_str(&format!("{k} = \"{v}\"\n"));
        }
        out.push_str("\n[facts]\n");
        for f in &self.facts {
            out.push_str(&format!("- \"{f}\"\n"));
        }
        out
    }

    pub fn parse(text: &str, cap_bytes: usize) -> Memory {
        let mut m = Memory::new(cap_bytes);
        let mut in_facts = false;
        for line in text.lines() {
            let line = line.trim();
            if line.is_empty() || line.starts_with('#') {
                continue;
            }
            if line == "[facts]" {
                in_facts = true;
                continue;
            }
            if in_facts {
                if let Some(rest) = line.strip_prefix("- ") {
                    m.facts.push(unquote(rest));
                }
            } else if let Some((k, v)) = line.split_once('=') {
                m.fields.push((k.trim().to_string(), unquote(v.trim())));
            }
        }
        m
    }

    pub fn load(path: &Path) -> std::io::Result<Memory> {
        let text = std::fs::read_to_string(path)?;
        Ok(Memory::parse(&text, DEFAULT_CAP_BYTES))
    }

    /// Atomic save: write a temp file then rename, so a power loss mid-write
    /// can't corrupt the memory file.
    pub fn save(&self, path: &Path) -> std::io::Result<()> {
        let tmp = path.with_extension("tmp");
        std::fs::write(&tmp, self.serialize())?;
        std::fs::rename(&tmp, path)?;
        Ok(())
    }
}

fn unquote(s: &str) -> String {
    s.trim().trim_matches('"').to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn roundtrip_and_apply() {
        let mut m = Memory::new(DEFAULT_CAP_BYTES);
        m.set("name", "Connor");
        m.apply(MemoryOp::Remember("Likes coffee".to_string()));
        // Duplicate remember is a no-op.
        m.apply(MemoryOp::Remember("Likes coffee".to_string()));

        let text = m.serialize();
        let m2 = Memory::parse(&text, DEFAULT_CAP_BYTES);
        assert_eq!(m2.get("name"), Some("Connor"));
        assert_eq!(m2.facts().iter().filter(|f| *f == "Likes coffee").count(), 1);
    }

    #[test]
    fn forget_removes_matching_facts() {
        let mut m = Memory::new(DEFAULT_CAP_BYTES);
        m.apply(MemoryOp::Remember("Drinks coffee".to_string()));
        m.apply(MemoryOp::Remember("Lives in Portland".to_string()));
        m.apply(MemoryOp::Forget("coffee".to_string()));
        assert_eq!(m.facts().len(), 1);
        assert_eq!(m.facts()[0], "Lives in Portland");
    }

    #[test]
    fn compact_enforces_cap() {
        let mut m = Memory::new(120); // tiny cap
        for i in 0..50 {
            m.apply(MemoryOp::Remember(format!("fact number {i}")));
        }
        m.compact();
        assert!(m.serialize().len() <= 120);
    }
}
