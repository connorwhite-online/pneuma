# Pneuma wake island (nRF52840)

Always-on co-processor firmware: wake-word + button detection and power control
of the Linux session SoC. C, on the **Nordic nRF Connect SDK (Zephyr)**.

```
west build -b nrf52840dk/nrf52840 firmware/wake-island
west flash
```
(Requires the nRF Connect SDK toolchain — not part of this repo's CI.)

## Layout
| File | Job |
|------|-----|
| `src/main.c` | the wake → power-up → hand-off → power-down loop |
| `src/wakeword.c` | always-on KWS on the PDM mic (TFLM/CMSIS-NN or Syntiant) |
| `src/button.c` | button gesture classification |
| `src/power.c` | `SOC_EN` control of the session tier |
| `src/uart_link.c` | control protocol to the SoC (see ../../docs/PROTOCOL.md) |

Status: **scaffold** — module bodies are TODO stubs.
