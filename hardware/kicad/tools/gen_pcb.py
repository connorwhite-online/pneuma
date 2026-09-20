"""Build placed (unrouted) KiCad PCBs for both boards from design.py.

Run with KiCad's bundled Python (needs `pcbnew`).  Coordinates in PLACE are
ENCLOSURE coordinates (mm): x = width, y = long axis (+y = camera end), matching
hardware/mechanical/enclosure-k-interface.json.  KiCad board coords are
X = x + 100, Y = 100 - y.

Big parts are placed by hand below.  Everything else (passives, small ICs, test
points) is packed automatically as close as possible to the part it serves,
without courtyard collisions and inside the board outline.
"""
import json, math, os, sys, uuid
import pcbnew
import design

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SH = os.environ.get("KICAD_SHARE", "/Volumes/KiCad/KiCad/KiCad.app/Contents/SharedSupport")
OUT = json.load(open(os.path.join(HERE, "l_outlines.json")))
MM = pcbnew.FromMM


def U(*seed):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "pneuma/" + "/".join(map(str, seed))))


def K(x, y):
    return pcbnew.VECTOR2I(MM(x + 100), MM(100 - y))


# ------------------------------------------------------------------ placement
# ref: (x, y, side, rot)   side "F"/"B"; rot = KiCad degrees applied before flipping
BOARD_Z = {"pneuma-main": 4.7, "pneuma-pwr": 4.0}      # bottom-of-PCB height in the enclosure
MOUNT_HOLES = {"pneuma-main": [(-11.8, 41.5), (12.8, 41.35)],
               "pneuma-pwr": [(15.6, -21.6), (-19.8, -22.6)]}

PLACE = {
    "pneuma-main": {
        "U1": (0.7, 23.5, "F", 0),          # Core1106: centre of the camera-end bay
        "J5": (-8.9, 7.3, "B", 0),          # FFC to PNM-PWR, cable exits toward the battery
        "U3": (12.9, 8.2, "B", 90),         # nRF module, antenna end at the right edge after flip
        "J4": (0.7, 39.9, "B", 180),        # camera FPC, cable exits over the top edge toward the camera
        "MK1": (-15.9, 16.6, "B", 90),      # wake mic (port through board, faces the front skin)
        "MK2": (-15.9, 21.4, "B", 90),      # session mic
        "U4": (-15.9, 26.2, "B", 0),        # amp
        "U5": (17.5, 28.5, "B", 90),        # haptics (right strip)
        "J1": (19.0, 20.0, "B", 90),        # Tag-Connect SWD (right strip, clear of Core pads: its NPTHs go through)
        "U2": (12.6, 37.6, "B", 0),         # SoC load switch
        "Y1": (2.6, 12.6, "B", 0),          # 32 kHz crystal next to the nRF XL pins
        "D1": (0.7, 44.3, "F", 0),          # status LED at the top end, behind a light window
        "J2": (6.9, 41.4, "F", 0),          # speaker pads
        "J3": (-5.6, 41.4, "F", 0),         # LRA pads
    },
    "pneuma-pwr": {
        "J1": (0.0, -55.4, "F", 0),         # USB-C in the channel tongue, mouth toward -y
        "U5": (-8.3, -36.8, "F", 90),       # EG800Q-NA
        "J4": (9.9, -37.4, "F", 0),         # nano-SIM
        "J5": (-7.3, -24.1, "F", 180),      # FFC to PNM-MAIN, cable exits toward the battery
        "J2": (8.8, -24.1, "F", 180),       # battery JST-GH
    },
}
# which side auto-placed parts go on, per board (default), with per-ref overrides
AUTO_SIDE = {"pneuma-main": "B", "pneuma-pwr": "B"}
AUTO_SIDE_REF = {
    "pneuma-main": {**{f"TP{i}": "F" for i in range(1, 11)}, "C1": "F", "C2": "F", "C7": "F", "C8": "F",
                    "C3": "F", "C4": "F", "C23": "F", "R6": "F", "R7": "F", "R8": "F"},
    "pneuma-pwr": {"D1": "F", "C7": "F", "C8": "F", "U8": "F", "C9": "F", "C10": "F",
                   "C11": "F", "R14": "F", "C13": "F", "C14": "F", "R15": "F", "R16": "F", "R17": "F", "R18": "F",
                   "R19": "F", "C18": "F", "C19": "F", "C20": "F", "C21": "F", "R20": "F", "C23": "F",
                   "J3": "B", "TP13": "F"},
}
# optional explicit anchors (default: the non-passive part sharing the most signal nets)
ANCHOR = {"pneuma-main": {**{f"TP{i}": "U1" for i in range(1, 11)}},
          "pneuma-pwr": {}}
TP_COLUMN = {"pneuma-main": [(-13.6 + 2.4 * i, 4.4) for i in range(10)]}   # row under the Core, top side

POWER_NETS = {"GND", "VSYS", "VBAT", "+VSOC", "+3V3_SOC", "+3V3_AON", "+1V8_SOC", "VBUS", "MDM_VDD_EXT"}


# ------------------------------------------------------------------ geometry helpers
def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def dist_to_poly_edge(x, y, poly):
    best = 1e9
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy or 1)))
        best = min(best, math.hypot(x - x1 - t * dx, y - y1 - t * dy))
    return best


def rect_in_poly(r, poly, margin=0.25):
    x0, y0, x1, y1 = r
    for x in (x0, x1, (x0 + x1) / 2):
        for y in (y0, y1, (y0 + y1) / 2):
            if not point_in_poly(x, y, poly) or dist_to_poly_edge(x, y, poly) < margin:
                return False
    return True


def overlap(a, b, gap=0.1):
    return not (a[2] + gap <= b[0] or b[2] + gap <= a[0] or a[3] + gap <= b[1] or b[3] + gap <= a[1])


def load_fp(fpid):
    lib, name = fpid.split(":")
    path = os.path.join(ROOT, "lib", "Pneuma.pretty") if lib == "Pneuma" else os.path.join(SH, "footprints", lib + ".pretty")
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise RuntimeError("footprint not found: " + fpid)
    return fp


def enc_bbox(fp):
    """Courtyard (or body) bbox of a placed footprint, in enclosure coords."""
    layer = pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd
    cy = fp.GetCourtyard(layer)
    bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
    x0 = pcbnew.ToMM(bb.GetX()) - 100
    x1 = x0 + pcbnew.ToMM(bb.GetWidth())
    y1 = 100 - pcbnew.ToMM(bb.GetY())
    y0 = y1 - pcbnew.ToMM(bb.GetHeight())
    return (x0, y0, x1, y1)


def place(fp, x, y, side, rot):
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(K(x, y))
    if side == "B" and not fp.IsFlipped():
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)


# ------------------------------------------------------------------ board build
def build(board_def):
    name = board_def.name
    outline = OUT["main" if name == "pneuma-main" else "pwr"]
    brd = pcbnew.BOARD()
    brd.SetCopperLayerCount(4)
    ds = brd.GetDesignSettings()
    ds.SetBoardThickness(MM(0.8))
    ds.m_TrackMinWidth = MM(0.1)
    ds.m_MinClearance = MM(0.1)
    ds.m_ViasMinSize = MM(0.4)
    ds.m_MinThroughDrill = MM(0.2)
    ds.m_CopperEdgeClearance = MM(0.25)
    ds.m_HoleClearance = MM(0.17)   # stock USB4105 / Infineon mic footprints sit at 0.18-0.21 mm (vendor land patterns)
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(MM(0.1))
    nc.SetTrackWidth(MM(0.12))
    nc.SetViaDiameter(MM(0.45))
    nc.SetViaDrill(MM(0.2))
    tb = brd.GetTitleBlock()
    tb.SetTitle(board_def.title)
    tb.SetRevision("A")
    tb.SetCompany("Pneuma")
    tb.SetComment(0, "Generated by hardware/kicad/tools/gen_pcb.py - placement only, NOT routed")
    tb.SetComment(1, f"Enclosure L coords: KiCad (X,Y) = (x+100, 100-y); PCB bottom at z={BOARD_Z[name]} mm")

    # outline
    pts = outline[:-1] if outline[0] == outline[-1] else outline
    for i in range(len(pts)):
        s = pcbnew.PCB_SHAPE(brd)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(MM(0.05))
        s.SetStart(K(*pts[i]))
        s.SetEnd(K(*pts[(i + 1) % len(pts)]))
        brd.Add(s)

    nets = {}
    for n in board_def.nets():
        ni = pcbnew.NETINFO_ITEM(brd, n)
        brd.Add(ni)
        nets[n] = ni

    root_uuid = U(name, "root")
    sheet_of = {ref: sh for sh, refs in board_def.sheets for ref in refs}
    fps = {}
    for part in board_def.parts:
        fp = load_fp(part["footprint"])
        fp.SetReference(part["ref"])
        fp.SetValue(part["value"])
        sheet_uuid = U(name, "sheet", sheet_of[part["ref"]])
        fp.SetPath(pcbnew.KIID_PATH(f"/{sheet_uuid}/{U(name, 'sym', part['ref'])}"))
        if part["dnp"]:
            fp.SetDNP(True)
        for pad in fp.Pads():
            net = part["pins"].get(pad.GetNumber())
            if net:
                pad.SetNet(nets[net])
        fps[part["ref"]] = fp
        brd.Add(fp)

    # manual placements
    occupied = {"F": [], "B": []}
    placed = set()
    for ref, (x, y, side, rot) in PLACE.get(name, {}).items():
        place(fps[ref], x, y, side, rot)
        placed.add(ref)
        occupied[side].append((enc_bbox(fps[ref]), ref))
        if any(p.GetAttribute() in (pcbnew.PAD_ATTRIB_NPTH, pcbnew.PAD_ATTRIB_PTH) for p in fps[ref].Pads()):
            occupied["F" if side == "B" else "B"].append((enc_bbox(fps[ref]), ref))   # holes go through
    for i, (ref, pos) in enumerate(zip([f"TP{j}" for j in range(1, 11)], TP_COLUMN.get(name, []))):
        place(fps[ref], pos[0], pos[1], "F", 0)
        placed.add(ref)
        occupied["F"].append((enc_bbox(fps[ref]), ref))

    # keep-outs: Core cutout (both sides) and Core body (top)
    if name == "pneuma-main":
        cx, cy = PLACE[name]["U1"][:2]
        cut = (cx - 12.45, cy - 9.32, cx + 11.70, cy + 11.95)
        occupied["B"].append((cut, "CUTOUT"))
    holes = []
    for (hx, hy) in MOUNT_HOLES.get(name, []):
        h = load_fp("Pneuma:MountingHole_1.7mm_M1.6")
        h.SetReference(f"H{len(holes) + 1}")
        h.SetPosition(K(hx, hy))
        brd.Add(h)
        holes.append(h)
        r = (hx - 1.7, hy - 1.7, hx + 1.7, hy + 1.7)
        occupied["F"].append((r, h.GetReference()))
        occupied["B"].append((r, h.GetReference()))

    # nRF chip-antenna keep-out: no parts and no copper on any layer
    ant_ka = None
    if name == "pneuma-main":
        x0, y0, x1, y1 = enc_bbox(fps["U3"])
        ant_ka = (x1 - 3.4, y0 - 1.0, x1 + 4.0, y1 + 1.5)
        occupied["F"].append((ant_ka, "ANT_KEEPOUT"))
        occupied["B"].append((ant_ka, "ANT_KEEPOUT"))

    # auto placement
    by_ref = {p["ref"]: p for p in board_def.parts}

    def anchor_for(ref):
        if ref in ANCHOR.get(name, {}):
            return ANCHOR[name][ref]
        mynets = {n for n in by_ref[ref]["pins"].values() if n and n not in POWER_NETS}
        if not mynets:
            mynets = {n for n in by_ref[ref]["pins"].values() if n and n != "GND"}
        best, score = None, 0
        for r in sorted(placed):   # sorted: set iteration order is not stable across runs
            if r not in by_ref:
                continue
            s = len(mynets & {n for n in by_ref[r]["pins"].values() if n})
            if s > score:
                best, score = r, s
        return best

    order = sorted([p["ref"] for p in board_def.parts if p["ref"] not in placed],
                   key=lambda r: (not r.startswith("U"), not r.startswith(("Q", "D", "Y")), r))
    failures = []
    for ref in order:
        fp = fps[ref]
        side = AUTO_SIDE_REF.get(name, {}).get(ref, AUTO_SIDE[name])
        anc = anchor_for(ref)
        if anc:
            ax, ay = pcbnew.ToMM(fps[anc].GetPosition().x) - 100, 100 - pcbnew.ToMM(fps[anc].GetPosition().y)
        else:
            ax, ay = 0.0, sum(p[1] for p in pts) / len(pts)
        best = None
        cands = []
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        step = 0.5
        x = min(xs)
        while x <= max(xs):
            y = min(ys)
            while y <= max(ys):
                cands.append((math.hypot(x - ax, y - ay), x, y))
                y += step
            x += step
        cands.sort()
        for d, x, y in cands:
            for rot in (0, 90):
                place(fp, x, y, side, rot)
                bb = enc_bbox(fp)
                if not rect_in_poly(bb, pts):
                    continue
                if any(overlap(bb, o) for o, _ in occupied[side]):
                    continue
                best = (x, y, rot, bb)
                break
            if best:
                break
        if not best:
            failures.append(ref)
            continue
        placed.add(ref)
        occupied[side].append((best[3], ref))

    # GND planes on In1 (both boards) and In2 (main)
    for layer in (pcbnew.In1_Cu, pcbnew.In2_Cu):
        z = pcbnew.ZONE(brd)
        z.SetLayer(layer)
        z.SetNet(nets["GND"])
        z.SetLocalClearance(MM(0.2))
        z.SetMinThickness(MM(0.2))
        ol = z.Outline()
        ol.NewOutline()
        for p in pts:
            ol.Append(MM(p[0] + 100), MM(100 - p[1]))
        brd.Add(z)
    # no copper under the nRF chip antenna (both inner layers + bottom) — MDBT50Q keep-out
    if name == "pneuma-main":
        x0, y0, x1, y1 = enc_bbox(fps["U3"])
        ka = (x1 - 3.4, y0, x1, y1)   # antenna end after rotation/flip is +x
        z = pcbnew.ZONE(brd)
        z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowZoneFills(True)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        ls = pcbnew.LSET()
        for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
            ls.AddLayer(l)
        z.SetLayerSet(ls)
        ol = z.Outline()
        ol.NewOutline()
        for (px, py) in [(ka[0], ka[1]), (ka[2], ka[1]), (ka[2], ka[3]), (ka[0], ka[3])]:
            ol.Append(MM(px + 100), MM(100 - py))
        z.SetZoneName("nRF antenna keep-out")
        brd.Add(z)
    filler = pcbnew.ZONE_FILLER(brd)
    filler.Fill(brd.Zones())

    out_dir = os.path.join(ROOT, name)
    path = os.path.join(out_dir, name + ".kicad_pcb")
    brd.Save(path)
    report = {ref: dict(zip(("x0", "y0", "x1", "y1"), [round(v, 2) for v in enc_bbox(fps[ref])]),
                        side="B" if fps[ref].IsFlipped() else "F") for ref in fps}
    return path, failures, report


if __name__ == "__main__":
    allrep = {}
    for mk in design.BOARDS:
        b = mk()
        path, fails, rep = build(b)
        allrep[b.name] = {"z_bottom": BOARD_Z[b.name], "parts": rep, "unplaced": fails}
        print(b.name, "->", path, "| unplaced:", fails or "none")
    json.dump(allrep, open(os.path.join(HERE, "placement_report.json"), "w"), indent=1)
