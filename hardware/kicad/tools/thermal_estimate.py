"""First-order thermal estimate for Pneuma Rev A.  Lumped model, not CFD.

Question: does this device need a copper spreader, or does the burst duty cycle carry it?

Chain per heat source:  part -> PCB (spreads almost instantly) -> gap -> shell -> air.
Everything here is order-of-magnitude; Phase 0 bench numbers replace it.
"""
import math

AMBIENT = 25.0
SKIN_LIMIT = 43.0          # IEC 62368-1 long-contact limit
SESSION_W = 3.0            # modem TX ~1.5-2 W + SoC ~1 W
MODEM_W = 1.5

# device: 60 x 119 x 12 mm soft shell
SKIN_AREA = 2 * 0.060 * 0.119 + 2 * (0.060 + 0.119) * 0.012      # m^2
H_OUT = 10.0               # natural convection + radiation, W/m^2K
MASS_G = 60.0              # boards + battery + shells + carrier + modules
CP = 1200.0                # J/kgK, mixed plastics/PCB/cell

# PNM-PWR board under the modem
BOARD_A = 0.041 * 0.039    # m^2
BOARD_C = 10.0             # J/K, 4-layer board + copper
GAP_MM = 1.5               # board top to shell inner face


def r_gap(area, mm, k_fill=0.026, h_rad=6.0):
    """Air gap (conduction) in parallel with radiation across it."""
    r_cond = (mm / 1000.0) / (k_fill * area)
    r_rad = 1.0 / (h_rad * area)
    return 1.0 / (1.0 / r_cond + 1.0 / r_rad)


def r_wall(area, mm=1.0, k=0.2):
    return (mm / 1000.0) / (k * area)


def report():
    r_out = 1.0 / (H_OUT * SKIN_AREA)
    c_dev = MASS_G / 1000.0 * CP
    print(f"skin area {SKIN_AREA*1e4:.0f} cm^2 -> to-air resistance {r_out:.1f} K/W")
    print(f"device heat capacity ~{c_dev:.0f} J/K\n")

    print("A. WHOLE DEVICE, steady state (the hard ceiling, any material):")
    for w in (1.0, 2.0, 3.0):
        print(f"   {w:.1f} W continuous -> +{w*r_out:4.1f} K  = {AMBIENT + w*r_out:4.1f} C skin")
    print(f"   -> {SKIN_LIMIT:.0f} C skin limit is hit at {(SKIN_LIMIT-AMBIENT)/r_out:.1f} W continuous\n")

    print("B. SHORT SESSION, whole-device average rise (thermal mass):")
    for sec in (30, 60, 180, 600):
        tau = c_dev * r_out
        rise = SESSION_W * r_out * (1 - math.exp(-sec / tau))
        print(f"   {sec:4d} s at {SESSION_W} W -> +{rise:4.1f} K (time constant {tau/60:.0f} min)")
    print()

    print("C. MODEM -> SHELL, local step (this is what a spreader would fix):")
    for name, r in (("bare 1.5 mm air gap", r_gap(BOARD_A, GAP_MM)),
                    ("one silicone gap pad (3 W/mK)", r_gap(BOARD_A, GAP_MM, k_fill=3.0)),
                    ("gap pad + conductive shell (1.5 W/mK)", r_gap(BOARD_A, GAP_MM, k_fill=3.0) + r_wall(BOARD_A, 1.0, 1.5))):
        tau = BOARD_C * r
        steady = MODEM_W * r
        t60 = steady * (1 - math.exp(-60 / tau))
        t600 = steady * (1 - math.exp(-600 / tau))
        print(f"   {name:38s} R={r:5.1f} K/W  60 s:+{t60:4.1f} K  10 min:+{t600:4.1f} K  steady:+{steady:4.1f} K")
    print()
    print("Reading: the ceiling in (A) is set by skin area, not by the spreader. (B) says a"
          "\n30-60 s question never gets near it. (C) says even a bare air gap only costs a few"
          "\ndegrees over a minute - the gap only matters for sustained modes (nav, music, long calls).")


if __name__ == "__main__":
    report()
