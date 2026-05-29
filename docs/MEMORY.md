# Pneuma — The Memory File

The device is **ephemeral**: it keeps no conversations, audio, or photos. The
**memory file** is the single exception — the only persistent state, and the
product's identity. *Pneuma* (breath/spirit): interactions are breath; this file
is the spirit that endures.

Status: **design.** This spec defines behavior the firmware must implement.

---

## Principles

1. **One small, bounded file.** Target a few KB; a **hard cap** (e.g. 4–8 KB). It
   is a *curated profile*, never a log.
2. **Curated, not accumulated.** Near the cap, the model **summarizes/compresses**
   — a rolling memory. It must not grow into a transcript.
3. **On-device only.** Stored in encrypted flash. Never uploaded except as context
   to the user's *own* chosen model during a session.
4. **User-owned.** Viewable/editable at provisioning; **factory reset = forget
   me**; **portable** (export/import to move your "self" to another Pneuma).
5. **Durable facts only.** Identity, preferences, standing instructions — not "what
   we talked about yesterday."

---

## What goes in it

- **Who you are:** name, how you like to be addressed, language, units.
- **Preferences:** voice/verbosity, default provider/model, tone.
- **Standing instructions:** "always answer in metric," "I'm vegetarian," etc.
- **A few durable facts:** the handful the model judges worth keeping long-term.

What does **not** go in it: conversation history, transcripts, captured images,
timestamps of interactions, anything resembling a journal.

---

## Lifecycle

```
CONNECT   → load memory file → inject as system context for the session
CONVERSE  → model may emit a "remember(...)" / "forget(...)" intent
FORGET    → apply pending memory updates (re-summarize if near cap),
            persist ONLY the memory file, discard all session audio/frames/text
```

- Updates are **deliberate** — triggered by the user ("remember that…") or a clear
  model decision — not automatic logging of everything said.
- A write is atomic (write-temp + rename) so a power loss can't corrupt it.

---

## Format (proposed)

Small, human-readable, diffable. A capped Markdown/TOML-ish document, e.g.:

```toml
# pneuma memory — v1 — keep under 8 KB
name = "Connor"
address_as = "Connor"
language = "en"
units = "metric"
voice = "calm, concise"
default_model = "openai:gpt-realtime"

[facts]
- "Prefers vegetarian food suggestions"
- "Based in Portland, Oregon"
- "Dislikes long-winded answers"
```

Human-readable matters: the user can audit and edit exactly what their device
"knows," which is core to the trust story.

---

## Open questions

- [ ] Exact cap + the compaction prompt/strategy when full.
- [ ] Encryption + key storage (tie to SoC secure boot).
- [ ] Export format for portability (same file? signed bundle?).
- [ ] Whether to expose a spoken command to review/clear memory hands-free.
