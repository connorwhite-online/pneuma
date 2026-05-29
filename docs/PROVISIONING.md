# Pneuma — Provisioning (app-less setup)

There is **no companion app.** First-run setup is a web page the **device hosts
itself**, reachable from any browser once, then disabled. After setup the device
is fully standalone. (Replaces the earlier companion-app design — see ADR-0004.)

Status: **design.**

---

## What setup has to accomplish

1. **Network / SIM** — activate the eSIM (SGP.32) or iSIM profile; pick a data
   provider (or use a preloaded profile).
2. **Provider + key** — choose the model (OpenAI / Gemini / Grok / Claude) and
   enter the API key (or OAuth). Stored on-device in encrypted flash / secure
   element; never leaves the device except as auth to that provider.
3. **Memory seed** — optionally pre-fill the [memory file](MEMORY.md) (name,
   units, preferences).
4. **Wake word check** — confirm "Hey Pneuma" triggers; set push-to-talk vs.
   wake-word.

---

## How the browser reaches the device (one-time)

The wake island brings up a temporary local setup link; the SoC serves the page.
Options (pick at implementation):

- **BLE** to a small web/native bridge (most phone-friendly), or
- **Wi-Fi SoftAP** — device briefly becomes an access point hosting a captive
  config page (classic IoT pattern, works from a laptop), or
- **USB** — device enumerates as a serial/RNDIS config endpoint when plugged in.

Whichever transport, it is **setup-only**: enabled during provisioning, off
afterward. No persistent connection, no app to keep installed.

```
[any browser] ──(BLE / SoftAP / USB, one time)──▶ [Pneuma setup page]
      enter: SIM profile · model + key · memory seed · wake word
                              │
                              ▼
            stored on-device (encrypted)  → setup link disabled
                              │
                              ▼
                   device is standalone
```

---

## Notes

- Re-running setup (e.g. to change provider/key) is an explicit user action
  (button combo) — not a background service.
- Keys and the memory file share the device's encrypted-storage scheme; treat
  both as secrets.
- Keep the setup page self-contained and offline-capable (served from the device),
  so no external site is required to configure your own hardware.
