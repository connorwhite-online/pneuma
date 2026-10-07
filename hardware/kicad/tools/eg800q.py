"""Quectel EG800Q-NA (LGA-109, 15.8 x 17.7 x 2.4 mm) pad map.

Source: Quectel EG800Q Series Hardware Design V1.1, Fig. 2 (pin assignment,
top view), Fig. 36 (bottom dimensions) and Fig. 37 (recommended footprint).
Coordinates: footprint origin at module centre, KiCad axes (x right, y down),
top view. Pin 1 is top-left.

Derived centre lines (mm from module centre):
  columns x: outer +-7.1, ring-2 +-5.0, ring-3 +-3.2
  rows    y: outer +-8.05, ring-2 +-5.95, ring-3 bottom row +4.15
  outer rows/cols pitch 1.1; ring-2/ring-3 pitch 1.2; centre GND pads 1.3 sq.
"""

BODY = (15.8, 17.7)


def pads():
    """[(number, x, y, w, h)] — w/h are copper sizes (x, y)."""
    out = []
    # outer ring: pads 0.6 wide along the edge, 1.0 deep
    for i, n in enumerate(range(1, 14)):                       # left column, top->bottom
        out.append((n, -7.1, -6.6 + 1.1 * i, 1.0, 0.6))
    for i, n in enumerate([95, 14, 15, 16, 17, 18, 19, 20, 21, 22, 96]):  # bottom row, L->R
        out.append((n, -5.5 + 1.1 * i, 8.05, 0.6, 1.0))
    for i, n in enumerate(range(35, 22, -1)):                  # right column, top->bottom
        out.append((n, 7.1, -6.6 + 1.1 * i, 1.0, 0.6))
    for i, n in enumerate([98, 44, 43, 42, 41, 40, 39, 38, 37, 36, 97]):  # top row, L->R
        out.append((n, -5.5 + 1.1 * i, -8.05, 0.6, 1.0))
    # ring 2: pads 0.7 x 1.0
    for i, n in enumerate([99, 45, 46, 47, 48, 49, 50, 51, 52, 53, 100]):
        out.append((n, -5.0, -6.0 + 1.2 * i, 1.0, 0.7))
    for i, n in enumerate([106, 72, 71, 70, 69, 68, 105]):
        out.append((n, -3.6 + 1.2 * i, -5.95, 0.7, 1.0))
    for i, n in enumerate([104, 67, 66, 65, 64, 63, 62, 61, 60, 59, 103]):
        out.append((n, 5.0, -6.0 + 1.2 * i, 1.0, 0.7))
    for i, n in enumerate([101, 54, 55, 56, 57, 58, 102]):
        out.append((n, -3.6 + 1.2 * i, 5.95, 0.7, 1.0))
    # ring 3
    for i, n in enumerate(range(73, 81)):
        out.append((n, -3.2, -4.25 + 1.2 * i, 1.0, 0.7))
    for i, n in enumerate([88, 87, 86, 85, 84, 83, 82, 81]):
        out.append((n, 3.2, -4.25 + 1.2 * i, 1.0, 0.7))
    for i, n in enumerate([107, 108, 109]):
        out.append((n, -1.2 + 1.2 * i, 4.15, 0.7, 1.0))
    # centre thermal/GND pads
    for n, x, y in [(89, -0.9, -1.8), (90, 0.9, -1.8), (91, -0.9, 0), (92, 0.9, 0), (93, -0.9, 1.8), (94, 0.9, 1.8)]:
        out.append((n, x, y, 1.3, 1.3))
    assert sorted(p[0] for p in out) == list(range(1, 110)), "pad set must be 1..109"
    return out


GND = [1, 10, 27, 34, 36, 37, 40, 41, 45, 46, 47, 48, 70, 71, 72, 73] + list(range(88, 96))
RESERVED = ([2, 3, 4, 5, 6, 8, 26, 44] + list(range(49, 59)) + [62, 63, 64, 65, 68, 69, 74, 75, 76, 77, 78, 80, 81,
            84, 85, 86] + list(range(97, 104)) + [106, 107, 108, 109])

SIGNALS = {
    7: ("PWRKEY", "input"), 9: ("ADC0", "input"), 11: ("USIM_DATA", "bidirectional"),
    12: ("USIM_RST", "output"), 13: ("USIM_CLK", "output"), 14: ("USIM_VDD", "power_out"),
    15: ("RESET_N", "input"), 16: ("NET_STATUS", "output"), 17: ("MAIN_RXD", "input"),
    18: ("MAIN_TXD", "output"), 19: ("MAIN_DTR", "input"), 20: ("MAIN_RI", "output"),
    21: ("MAIN_DCD", "output"), 22: ("MAIN_CTS", "output"), 23: ("MAIN_RTS", "input"),
    24: ("VDD_EXT", "power_out"), 25: ("STATUS", "output"), 28: ("AUX_RXD", "input"),
    29: ("AUX_TXD", "output"), 30: ("PCM_CLK", "output"), 31: ("PCM_SYNC", "output"),
    32: ("PCM_DIN", "input"), 33: ("PCM_DOUT", "output"), 35: ("ANT_MAIN", "bidirectional"),
    38: ("DBG_RXD", "input"), 39: ("DBG_TXD", "output"), 42: ("VBAT", "power_in"),
    43: ("VBAT", "power_in"), 59: ("USB_DP", "bidirectional"), 60: ("USB_DM", "bidirectional"),
    61: ("USB_VBUS", "input"), 66: ("I2C_SDA", "bidirectional"), 67: ("I2C_SCL", "output"),
    79: ("USIM_DET", "input"), 82: ("USB_BOOT", "input"), 83: ("PSM_IND", "output"),
    87: ("PSM_INT", "input"), 96: ("ADC1", "input"), 104: ("GRFC2", "output"), 105: ("GRFC1", "output"),
}


def pin_table():
    """[(number, name, etype)] for all 109 pins."""
    rows = []
    for n in range(1, 110):
        if n in SIGNALS:
            rows.append((n,) + SIGNALS[n])
        elif n in GND:
            rows.append((n, "GND", "power_in"))
        elif n in RESERVED:
            rows.append((n, "RESERVED", "no_connect"))
        else:
            raise ValueError(f"pin {n} unassigned")
    return rows


if __name__ == "__main__":
    print(len(pads()), "pads;", len(pin_table()), "pins")
