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
    "strategy": "spread, don't sink, with commodity materials: 0.1 mm copper foil (C110 sheet or adhesive copper "
                "tape) on the INSIDE of the front shell, fed by two copper-shim thermal posts, generic silicone "
                "thermal pads at every interface. Total parts cost < ~$5. Step 0: measure on the bench first; short "
                "Q&A bursts may need no spreader at all. Upgrade path if hot spots persist: graphite sheet (~4x the "
                "spreading of copper at equal thickness). Rejected: ATS-VC-042 vapor chamber (100x40x3 mm, 18 g).",
    "no_cut_option": {"what": "4 off-the-shelf adhesive graphite pads, peel-and-stick, no cutting at all",
                      "pads": [{"size_mm": [30, 20], "center_xy": [-3.5, -32.0], "covers": "modem + modem post"},
                               {"size_mm": [15, 10], "center_xy": [-4.0, 37.0], "covers": "SoC post"},
                               {"size_mm": [10, 15], "center_xy": [3.5, 10.5], "covers": "main board, lower"},
                               {"size_mm": [10, 15], "center_xy": [11.5, 26.5], "covers": "main board, right"}],
                      "coverage": "1050 mm2 = ~52% of the custom-cut area; both posts still land on a pad",
                      "rest_of_chain": "copper shim kits (10x10/15x15, assorted thicknesses) for the posts; "
                                       "thermal putty from a syringe instead of cut TIM pads"},
    "materials": {"spreader": "copper foil/tape 0.07-0.1 mm, cut with a knife or vinyl cutter from the DXF of spreader_zones",
                  "posts": "stacked generic copper shims (laptop GPU shim type, 0.5/1.0/1.5 mm), cut to size",
                  "tim": "generic silicone thermal pad 0.5 mm, 3-6 W/mK (compressible, absorbs stack tolerance)",
                  "rf_note": "copper is conductive: honour spreader_keepouts; leave it floating first, try one GND "
                             "tie point only if EMI testing asks for it"},
    "budget": "whole-skin natural convection+radiation ~0.2 W/K -> ~+15 C over ambient at 3 W continuous even if "
              "perfectly spread; short Q&A bursts ride on thermal mass. Measure in Phase 0.",
    "spreader_zones": [
        {"name": "main", "box_xy": [-19.5, 16.0, 19.5, 44.5], "z_under_front_skin": True},
        {"name": "main_low_left", "box_xy": [-19.5, 2.5, 9.0, 16.0], "z_under_front_skin": True},
        {"name": "pwr", "box_xy": [-20.5, -46.0, 17.5, -21.0], "z_under_front_skin": True},
    ],
    "spreader_keepouts": [
        {"name": "nRF chip antenna + Core1106 WiFi/BT antenna", "box_xy": [9.0, 2.0, 23.5, 16.0]},
        {"name": "touch electrode (front face, below the bump)", "box_xy": [-13.5, -13.5, 13.5, 5.5]},
        {"name": "LTE antenna band", "box_xy": [-22.0, -59.0, 19.0, -46.0]},
        {"name": "camera aperture + optical cone", "circle_xy": [0.0, 26.0], "diameter": 12.0},
        {"name": "mic ports", "circles_xy": [[-15.9, 17.28], [-15.9, 22.08]], "diameter": 3.0},
        {"name": "speaker vents", "circle_xy": [-8.0, 10.2], "diameter": 12.0},
        {"name": "status LED window", "circle_xy": [0.7, 44.3], "diameter": 3.0},
    ],
    "thermal_posts": [
        {"name": "SoC post (RV1106 corner of Core1106)", "box_min": [-5.0, 31.0, 8.45], "box_max": [2.0, 37.0, 12.2],
         "note": "copper-shim stack + 0.5 mm silicone pad each end; bottom on the RV1106 package top, top on the "
                 "spreader. Height = local skin z - 8.42 - pads; confirm clearance to the camera FPC"},
        {"name": "modem post (EG800Q-NA lid)", "box_min": [-15.0, -42.5, 7.25], "box_max": [-2.0, -31.0, 10.3],
         "note": "same construction on the modem lid; the modem TX burst is the largest heat source (~1-2 W)"},
    ],
    "gap_filler_note": "a soft gap pad alone over 3-4 mm is too resistive (~10 K/W); use a metal post + thin TIMs",
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
