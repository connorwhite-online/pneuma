# Pneuma — BLE Protocol (firmware ↔ app contract)

This is the agreement the **pendant firmware** and the **companion app** must both
implement. It is the seam between the two halves of the project; keep it stable
and versioned. Status: **draft v0** (pre-implementation — expect revision once
validated on the bench).

Transport: **Bluetooth Low Energy**, GATT. Request **2M PHY**, **Data Length
Extension**, and a large **ATT MTU (~247+)** at connection — these are what make
sub-1s JPEG transfer possible (see [`RESEARCH.md`](RESEARCH.md) §6).

> UUIDs below are placeholders (`PNxx...`). Assign real 128-bit UUIDs from a single
> base when implementation starts.

---

## Services overview

| Service | UUID | Purpose |
|---------|------|---------|
| Battery (standard) | `0x180F` | Battery level |
| Device Information (standard) | `0x180A` | Model, firmware revision |
| **Pneuma Control** | `PN01...` | Device state, events, commands |
| **Pneuma Audio** | `PN02...` | LC3 mic uplink + speaker downlink |
| **Pneuma Camera** | `PN03...` | On-demand capture + chunked JPEG |

---

## Pneuma Control Service (`PN01...`)

| Characteristic | Props | Payload |
|----------------|-------|---------|
| **State** | Notify | 1 byte enum: `0 idle · 1 listening · 2 capturing · 3 streaming · 4 speaking · 5 error` |
| **Event** | Notify | 1 byte enum: `0 wakeword · 1 button_tap · 2 button_double · 3 button_long`, + 1 byte detail |
| **Command** | Write | opcode + args (see below) |

**Command opcodes (app → pendant):**
- `0x01 SET_STATE` — force a state (e.g. start/stop listening for push-to-talk).
- `0x02 PLAY_EARCON` — play a built-in cue (listening / done / error).
- `0x03 SET_LED` — RGB + pattern.
- `0x04 SET_HAPTIC` — DRV2605L effect id.
- `0x05 SET_VOLUME` — 0–100.

---

## Pneuma Audio Service (`PN02...`)

| Characteristic | Props | Payload |
|----------------|-------|---------|
| **MicStream** (pendant → app) | Notify | `[seq:1][LC3 frame(s)]` — uplink voice |
| **SpeakerStream** (app → pendant) | Write No Response | `[seq:1][LC3 frame(s)]` — downlink TTS/voice reply |
| **AudioConfig** | Read | codec id, sample rate (e.g. 16 kHz), frame size |

- Codec: **LC3** (LE Audio native to nRF5340). A fallback PCM16 mode may be
  advertised for debugging.
- Framing follows the Omi-style pattern (small fixed frames per notification) to
  fit BLE MTU; `AudioConfig` declares the exact frame geometry.

---

## Pneuma Camera Service (`PN03...`)

| Characteristic | Props | Payload |
|----------------|-------|---------|
| **CaptureControl** (app → pendant) | Write | `0x01 CAPTURE [res:1][quality:1]` · `0x02 ABORT` |
| **ImageTransfer** (pendant → app) | Notify | chunked JPEG (see below) |
| **CaptureStatus** (pendant → app) | Notify | `0 capturing · 1 transferring · 2 done · 3 error` |

**ImageTransfer framing:**
- First packet (header): `[0x00][frame_id:1][total_size:4 LE][res:1]`
- Data packets: `[seq:2 LE][jpeg bytes...]` until `total_size` received.
- App reassembles by `frame_id`/`seq`; on gap, request retransmit via
  `CaptureControl` (or restart capture).

**Flow:** app writes `CAPTURE` → firmware closes the camera load switch, grabs one
JPEG from the ArduCAM SPI FIFO → streams it over `ImageTransfer` → opens the load
switch (camera off). One frame per request; **no continuous video**.

---

## Connection lifecycle

1. Pendant advertises (low duty cycle when idle).
2. App connects → negotiates 2M PHY + DLE + MTU.
3. App subscribes to State/Event/MicStream/CaptureStatus/ImageTransfer notifies.
4. Steady state: pendant notifies wake/button events; app drives sessions and
   downlinks audio; camera frames flow only on explicit `CAPTURE`.
5. Battery via standard Battery Service.

## Security

- Use BLE bonding (LE Secure Connections) for the pendant↔app link.
- **No provider credentials ever traverse BLE** — they stay in the app's secure
  enclave (see [`APP.md`](APP.md) §1).
