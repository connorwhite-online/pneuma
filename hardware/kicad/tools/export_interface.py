"""Dump the enclosure-facing interface of both placed PCBs to JSON (enclosure coords, mm).

Run with KiCad's Python after gen_pcb.py.  Output: hardware/mechanical/enclosure-L-electronics.json
"""
import json, os
import pcbnew
from gen_pcb import BOARD_Z, OUT, ROOT, enc_bbox

MECH = os.path.join(os.path.dirname(ROOT), "mechanical")
T = 0.8  # PCB thickness


def enc_xy(v):
    return [round(pcbnew.ToMM(v.x) - 100, 3), round(100 - pcbnew.ToMM(v.y), 3)]


# off-board parts: envelopes the enclosure must reserve (enclosure coords)
OFFBOARD = {
    "battery": {"what": "LP702040 1S LiPo, 500 mAh / 1.85 Wh, 7.0 x 20 x 40 mm incl. PCM and wires "
                        "(lipobattery.us MOQ 5; EEMB/PKCELL equivalents). NOTE: the 550 mAh version of this cell "
                        "is 41 mm long and needs 1 mm more bay",
                "box_min": [-20.4, -19.3, 2.85], "box_max": [19.6, 1.3, 9.85],
                "leads": "exit at -y end toward PNM-PWR J2 (JST-GH SM02B)"},
    "ffc": {"what": "30-way 0.5 mm FFC, straight-through, ~16.5 mm wide, 0.12 mm thick; runs UNDER the battery",
            "box_min": [-17.3, -21.4, 2.5], "box_max": [0.9, 2.3, 2.8],
            "note": "S-bend at PNM-PWR J5 (top side) needs y -21.4..-19.3, z 2.5..6.8"},
    "speaker": {"what": "PUI AS01508MR-LWC40 class, 15 mm round, 8 ohm, 1 W, wire leads -> PNM-MAIN J2 pads",
                "cyl_center": [-8.0, 12.4, 8.6], "diameter": 15.0, "height": 3.5,
                "why_here": "nudged +2.2 mm in y so it clears the touch pad (which ends at y 4). Keeping this 1 W "
                            "15 mm round rather than a 15x11 0.3 W part: ~5 dB louder, and beside the camera there "
                            "is only ~10 mm of width, where the only parts are 5 mW earpiece receivers",
                "note": "fires toward the front skin; needs a sealed front volume + vent holes in the front membrane"},
    "lra": {"what": "Vybronics VG1040003D, 10 mm x 4 mm, leads -> PNM-MAIN J3 pads",
            "cyl_center": [-10.5, 30.5, 8.6], "diameter": 10.0, "height": 4.0,
            "note": "moved off the Core1106 WiFi/BT chip antenna (module corner x 10.5..13.7, y 10.5..13.5); "
                    "bond to the rigid internal carrier for tactile transfer, not to the soft skin"},
    "camera": {"DECISION_REQUIRED": "No off-the-shelf compact module with an RV1106-supported sensor is verified to "
                                    "exist. This blocks enclosure L: the bump cannot be modeled until it is chosen. "
                                    "Options in REV-A.md section 7. The PCB is NOT blocked (J4 pinout is fixed).",
               "depth_budget_mm": {"k_bump_as_is": 9.7, "bump_plus_2mm": 12.0,
                                   "note": "measured along the 30 deg axis from the Core1106 top (z 8.42) to the "
                                           "aperture (z 16.8). Lens choice, not sensor, sets module height"},
               "sensors_with_rv1106_isp_tuning": ["sc3336", "sc3338", "sc2336", "sc230ai", "sc231hai", "sc200ai",
                                                  "sc4336", "sc401ai", "sc500ai", "sc501ai", "sc530ai", "sc301iot",
                                                  "gc2053", "gc1084", "gc2093", "gc4023", "gc4653", "mis2032",
                                                  "mis5001", "os02h10", "os02k10", "os04a10", "imx415", "sc031gs"],
               "source_of_that_list": "IQ files in LuckfoxTECH/luckfox-pico media/isp/..._rv1106_.../isp_iqfiles/; "
                                      "the SDK kernel also carries ~150 sensor drivers incl. gc2053.c, sc2336.c",
               "luckfox_tested": ["SC3336", "MIS5001"],
               "baseline_purchasable": {"part": "Waveshare/Luckfox SC3336 3MP Camera (B)", "usd": 9,
                                        "pcb_mm": [25, 24, 1.2], "lens_stack_mm": 23.95, "lens_dia_mm": 14,
                                        "verdict": "verified and cheap, but an M12 barrel at 30 deg makes an "
                                                   "unwearable bump; fine as the BENCH camera"},
               "size_vs_bump": {"note": "the limit is NOT the bump: it is the Core1106 top (z 8.42), the speaker and "
                                        "the LRA directly under the module. Measured by sweeping solid clashes",
                                "bump_+0mm": "12 x 12 x 6 mm (11x11x6 with the LRA where it is now)",
                                "bump_+1mm": "16 x 16 x 6 mm", "bump_+2mm": "16 x 16 x 7 mm",
                                "bump_+3mm": "16 x 16 x 8 mm", "bump_+4mm": "16 x 16 x 9 mm",
                                "caveat": "anything past 12x12 needs the LRA moved off the camera footprint"},
               "target_envelope": {"what": "board-lens FPC module on any sensor in sensors_with_rv1106_isp_tuning",
                                   "board_max_mm": [12, 12], "height_max_mm": 6.0,
                                   "fov_target": "90-110 deg diagonal (a 150 deg F1.9 lens is what makes the Hampo "
                                   "module 18.6 mm tall)",
                                   "connector": "J4 is currently 20P on the Luckfox pinout. Many compact modules are "
                                   "24P - regenerating J4 for a 24P module is a small change to design.py, but the "
                                   "chosen module's drawing and pinout must come first",
                                   "sourcing": "module houses (Sincere, Hampo, CK Vision, Sinoseen) quote at MOQ 3-10"},
               "aperture_center": [0, 26, 16.8], "optical_axis": [0, 0.5, 0.8660254], "depth_along_axis": 6.0,
               "body_xy": [11.0, 11.0],
               "fpc": "FPC wraps over the PNM-MAIN top edge (y~44) into J4 on the bottom side; bench uses SC3336 (B)"},
    "touch_electrode": {"what": "copper-foil or FPC electrode on the front membrane inner face, ~10 mm below the "
                                "camera bump (bump lower edge is near y 8)",
                        "zone_xy": [-12.0, -12.0, 12.0, 4.0], "size_mm": [24, 16],
                        "contact": "PNM-MAIN TP11 spring pad at (11.0, 4.6), front side; front-end U6 is on PNM-MAIN "
                                   "so the electrode trace is short and TOUCH_OUT no longer crosses the FFC",
                        "note": "the battery pouch sits ~1-2 mm behind the lower part of this pad and the speaker is "
                                "just above it; both reduce sensitivity. Tune C25 (Cs) against the final electrode"},
    "lte_antenna": {"what": "FPC LTE antenna (698-2700 MHz) with MHF1 pigtail to PNM-PWR J3, part TBD",
                    "zones": [{"box_min": [-21.0, -50.5, 3.0], "box_max": [-7.5, -47.0, 10.0]},
                              {"box_min": [7.5, -50.5, 3.0], "box_max": [18.0, -47.0, 10.0]}],
                    "note": "pockets in the soft USB-end wall either side of the USB channel, just beyond the PNM-PWR "
                            "ground edge. Only viable because enclosure L has NO metal frame. Bench: external antenna on U.FL"},
}

# Enclosure L construction + thermal (see REV-A.md section 6)
ENCLOSURE = {
    "construction": "two-piece soft shell (front + rear), silicone or TPU, NO aluminum perimeter; rigid internal "
                    "carrier (PC/nylon/PA12) locates both boards, battery, speaker, LRA, camera and takes the M1.6 screws",
    "outward_face": "+z (front: camera, touch, LED). The rear (-z) face is the skin/clothing side and stays insulating",
    "wall": "front/rear skin 0.8-1.2 mm over the spreader; material k ~0.2 W/mK is fine once heat is spread",
}
THERMAL = {
    "strategy": "no spreader, no foil, no cutting. The PCB is the spreader (4-layer copper goes isothermal in "
                "milliseconds), and ONE compressible silicone gap pad per hot part carries the board-to-shell step. "
                "A soft shell cannot hold tolerance against a rigid post, which is why the earlier copper-foil + "
                "shim-post design was dropped; a squishy pad absorbs the same tolerance for free.",
    "numbers": {"source": "hardware/kicad/tools/thermal_estimate.py (lumped, first order)",
                "skin_area_cm2": 186, "to_air_K_per_W": 5.4,
                "ceiling": "43 C skin is reached at ~3.3 W CONTINUOUS regardless of internal material",
                "burst": "a 60 s session at 3 W lifts the whole device only ~2.3 K (device time constant ~6 min)",
                "modem_local_step": {"bare_1.5mm_air_gap": "+8 K at 60 s, +36 K at 10 min (26.8 K/W)",
                                     "one_gap_pad_3W_mK": "+0.5 K (0.3 K/W)"},
                "conclusion": "the burst interaction needs no thermal hardware at all; the gap pads exist for "
                              "sustained modes (nav, music, long calls), and firmware duty limiting is the real "
                              "control because the ceiling is skin area, not conduction"},
    "gap_pads": [
        {"name": "modem pad", "part": "generic silicone gap pad, >=3 W/mK, 3 mm uncompressed, pre-cut square",
         "over": "EG800Q-NA lid", "box_min": [-15.0, -42.5, 7.2], "box_max": [-3.0, -31.0, 10.4]},
        {"name": "SoC pad", "part": "same, 3 mm", "over": "Core1106 top, between the LRA and the camera",
         "box_min": [-5.0, 31.0, 8.42], "box_max": [2.0, 37.0, 11.5]},
    ],
    "routing_requirements": ["thermal via field under the EG800Q-NA ground pads into both inner planes",
                             "stitch the Core1106 GND stamp pads into the planes",
                             "do not neck the inner-layer copper around the modem"],
    "if_bench_says_not_enough": ["cast the FRONT shell in thermally conductive silicone (k 1-3 W/mK) - no extra "
                                 "parts, no assembly step, just a different material at mould time",
                                 "add pre-cut adhesive graphite pads inside the front shell (peel and stick)",
                                 "firmware: cap sustained-mode duty cycle"],
    "why_not_a_vapor_chamber": "ATS-VC-042 is 100 x 40 x 3 mm and 18 g: longer than the cavity, no 3 mm layer "
                               "spare, rated 124 W for a ~3 W problem, and it only spreads - the skin still does "
                               "the dissipating",
    "rf_note": "silicone pads are non-conductive, so unlike copper foil they impose no antenna or touch keep-outs",
}


def board_dump(name):
    brd = pcbnew.LoadBoard(os.path.join(ROOT, name, name + ".kicad_pcb"))
    zb = BOARD_Z[name]
    parts = {}
    for fp in brd.GetFootprints():
        ref = fp.GetReference()
        side = "bottom" if fp.IsFlipped() else "top"
        bb = enc_bbox(fp)
        ent = {"value": fp.GetValue(), "side": side, "pos": enc_xy(fp.GetPosition()),
               "rot_deg": round(fp.GetOrientationDegrees(), 1),
               "courtyard_xy": [round(v, 2) for v in bb]}
        nphs = [enc_xy(p.GetPosition()) for p in fp.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH]
        if nphs:
            ent["npth"] = nphs
        parts[ref] = ent
    return {"pcb_bottom_z": zb, "pcb_top_z": round(zb + T, 3), "thickness": T, "layers": 4,
            "outline": OUT["main" if name == "pneuma-main" else "pwr"], "parts": parts}


if __name__ == "__main__":
    main = board_dump("pneuma-main")
    pwr = board_dump("pneuma-pwr")
    feat = {
        "usb_c": {"mouth_center_xz": [0.0, round(pwr["pcb_top_z"] + 1.655, 2)], "mouth_y": -58.8,
                  "receptacle": "GCT USB4105-GF-A top-mount, shell 8.94 x 3.26 mm",
                  "note": "exterior wall at the port must be thin/counterbored for a full plug mate (overmold ~12.4 x 6.5)"},
        "mic_ports": {r: main["parts"][r]["npth"] for r in ("MK1", "MK2")},
        "mic_port_note": "bottom-port mics on the main-board underside; sound reaches them THROUGH the PCB hole from "
                         "the top side -> front-membrane port + gasket above each hole (top side is clear there)",
        "status_led": {"pos": main["parts"]["D1"]["pos"], "side": "top", "note": "needs light pipe/window in the front skin"},
        "mount_holes_M1_6": {"pneuma-main": [p["pos"] for r, p in main["parts"].items() if r.startswith("H")],
                             "pneuma-pwr": [p["pos"] for r, p in pwr["parts"].items() if r.startswith("H")]},
        "service_access": {"swd_tagconnect": main["parts"]["J1"]["pos"], "nano_sim": pwr["parts"]["J4"]["pos"],
                           "note": "both need the board out of the enclosure; SIM is not user-swappable in Rev A"},
    }
    out = {
        "revision": "Pneuma Rev A electronics for enclosure L",
        "status": "placement frozen for bench + enclosure modeling; PCBs NOT routed; not fabrication data",
        "units": "mm",
        "coordinates": "same axes as enclosure-k-interface.json; enclosure L = K with a 10 mm insert at y=-10 "
                       "(camera end unchanged, USB end moved -10 mm)",
        "cavity_L_section_z3_8": OUT["cavity_L"],
        "boards": {"pneuma-main": main, "pneuma-pwr": pwr},
        "offboard": OFFBOARD,
        "enclosure": ENCLOSURE,
        "thermal": THERMAL,
        "features": feat,
    }
    os.makedirs(MECH, exist_ok=True)
    path = os.path.join(MECH, "enclosure-L-electronics.json")
    json.dump(out, open(path, "w"), indent=1)
    print("wrote", path)
