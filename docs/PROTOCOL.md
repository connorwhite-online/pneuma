# Pneuma — Internal Interfaces

With no phone and no app, the important seam is **inside** the device: between the
always-on **wake island** (MCU) and the on-demand **session brain** (Linux SoC).
This is the contract the two firmwares must share. (The earlier phone↔app BLE
protocol is gone with the companion app — see ADR-0004.)

Status: **draft v0** (pre-implementation; expect revision after bench bring-up).

---

## Wake island ↔ Session SoC

Physical link: **UART** (control) + a **power-enable GPIO** (wake island → PMIC/SoC).

### Power control
- `SOC_EN` (GPIO, wake island → PMIC): assert to boot/resume the SoC + permit
  modem power; deassert (after the SoC acks "sleep") to cut the session tier.

### Control messages (UART, line- or TLV-framed)

Wake island → SoC:
| Msg | Meaning |
|-----|---------|
| `WAKE reason=wakeword` | wake word detected — start a session |
| `WAKE reason=button tap\|double\|long` | button event |
| `BATT level=NN` | battery state (if the gauge is on the island) |
| `CANCEL` | user dismissed / timeout before SoC ready |

SoC → wake island:
| Msg | Meaning |
|-----|---------|
| `READY` | session tier up, modem attaching |
| `STATE listening\|capturing\|conversing\|speaking\|error` | drive LED/haptic cues |
| `SLEEP` | session done; island may cut `SOC_EN` |
| `LED ...` / `HAPTIC ...` | request a cue (if island owns LED/LRA) |

The wake island owns the always-on UX (wake chime, "listening" LED) so cues fire
instantly without waiting for the SoC to boot; the SoC takes over cues once
`READY`.

---

## Session brain ↔ Provider (cloud)

Runs on the SoC; see [`ARCHITECTURE.md`](ARCHITECTURE.md) §3 for the
`RealtimeProvider` / `ComposedProvider` abstraction. Summary:

- **Transport:** WebRTC or TLS-WebSocket over the cellular (Cat-1 bis) link.
- **Up:** LC3/Opus audio; on-demand a single JPEG (from the camera ISP).
- **Down:** audio reply (native, or from cloud TTS in composed mode).
- **Context:** the [memory file](MEMORY.md) is injected at session start; updates
  applied on session end.
- **Auth:** key from encrypted storage; ephemeral tokens where the provider
  supports them.

---

## Camera (on-demand)

- SoC asserts `CAM_EN` → camera powers up → one frame captured via MIPI-CSI ISP →
  JPEG → sent to provider → `CAM_EN` deasserted (camera off). No video, no
  retention.

## Provisioning transport

Setup-only (BLE / Wi-Fi SoftAP / USB), enabled during provisioning and disabled
after. See [`PROVISIONING.md`](PROVISIONING.md).
