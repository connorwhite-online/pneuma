# Pneuma companion app

The brain-router and BLE gateway for the Pneuma pendant. This is where "bring your
own LLM" lives — credentials, the provider router, and the session engine.

**Design:** [`../docs/APP.md`](../docs/APP.md) · **BLE contract:**
[`../docs/PROTOCOL.md`](../docs/PROTOCOL.md)

Status: **not yet scaffolded.** Planned stack (ADR-0004):

```
app/
├── pneuma_core/     # pure-Dart engine: provider router, session, BLE codec, MCP
│   └── providers/   # one driver per backend (OpenAI, Gemini, Grok, Claude, local)
└── pneuma_app/      # Flutter shell: UI, keyvault, BLE radio, audio routing
```

The `pneuma_core` package has no UI/OS dependencies so it can also run headless
inside an optional self-hosted hub (ADR-0005).
