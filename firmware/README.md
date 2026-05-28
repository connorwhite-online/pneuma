# Pneuma pendant firmware

Firmware for the nRF5340 pendant: wake word, LC3 audio over BLE, on-demand
ArduCAM Mega capture, audio out, haptics/LED, button.

**Target:** Nordic nRF5340 · **SDK:** Zephyr / nRF Connect SDK · **Camera driver:**
ArduCAM Mega over SPI (Nordic maintains `ncs-arducam-mega-driver`).

**Hardware:** [`../hardware/BOM.md`](../hardware/BOM.md) ·
**BLE contract:** [`../docs/PROTOCOL.md`](../docs/PROTOCOL.md) ·
**Architecture:** [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md)

Status: **not yet scaffolded.** Planned responsibilities:
- Always-on wake-word KWS (Cortex-M DS-CNN via TFLite-Micro + CMSIS-NN)
- PDM mic capture → LC3 encode → BLE `MicStream`
- BLE `SpeakerStream` → LC3 decode → I2S → MAX98357A
- On-demand: power-gate camera, SPI JPEG read, chunked BLE `ImageTransfer`
- Control service: state/event notifies, LED/haptic/volume commands
- Power management: low-power listening, deep sleep, USB DFU
