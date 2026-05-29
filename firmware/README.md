# Pneuma firmware

Two pieces of software run on the device (no phone, no app):

## 1. Wake-island firmware (always-on MCU — nRF52840 / Syntiant)
- Always-on wake-word KWS (Cortex-M DS-CNN via TFLite-Micro + CMSIS-NN, or
  Syntiant NDP120 front-end)
- Button handling (tap / double / long)
- Powers the Linux session SoC up/down (`SOC_EN`) on demand
- Owns the instant UX cues (wake chime, "listening" LED) before the SoC boots
- BLE for one-time provisioning

## 2. Session software (Linux SoC — Rockchip RV1106-class)
- The provider router (Tier-1 realtime / Tier-2 composed) — see ARCHITECTURE §3
- Cellular session over Cat-1 bis (WebRTC / TLS-WebSocket)
- On-demand camera capture (MIPI-CSI ISP → JPEG)
- Audio I/O (PDM mic in, I2S → MAX98357A out), haptics/LED
- Loads/updates the bounded memory file (encrypted); ephemeral otherwise
- OTA updates; secure storage for keys + memory

**References:** [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) ·
[`../docs/PROTOCOL.md`](../docs/PROTOCOL.md) (internal interface) ·
[`../docs/MEMORY.md`](../docs/MEMORY.md) ·
[`../docs/PROVISIONING.md`](../docs/PROVISIONING.md) ·
[`../hardware/BOM.md`](../hardware/BOM.md)

Status: **not yet scaffolded.**
