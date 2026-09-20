"""Plan + side view of the Rev A electronics in enclosure L (reads mechanical/enclosure-L-electronics.json)."""
import json, os, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IF = json.load(open(os.path.join(os.path.dirname(ROOT), "mechanical", "enclosure-L-electronics.json")))
EXT = json.load(open(os.path.join(ROOT, "out", "interference-L.json")))["extents"]
BIG = {"U1": "Core1106", "U3": "nRF52840", "J5": "FFC", "J4": "CAM FPC", "U5": "EG800Q-NA", "J1": "USB-C", "J2": "BATT",
       "U2": "", "MK1": "mic", "MK2": "mic", "U4": "amp", "D1": "LED"}
fig, (ax, bx) = plt.subplots(1, 2, figsize=(13, 11), gridspec_kw={"width_ratios": [1, 1.05]})
for a in (ax,):
    cav = IF["cavity_L_section_z3_8"]
    a.add_patch(Polygon(cav, closed=True, fill=False, ec="0.35", lw=1.2, ls="--"))
    colors = {"pneuma-main": "#3b7dd8", "pneuma-pwr": "#d8843b"}
    for bn, b in IF["boards"].items():
        a.add_patch(Polygon(b["outline"], closed=True, fc=colors[bn], alpha=0.12, ec=colors[bn], lw=1.4))
        for ref, p in b["parts"].items():
            x0, y0, x1, y1 = p["courtyard_xy"]
            big = ref in ("U1", "U3", "J5", "J4", "U5", "J1", "J2") or (bn == "pneuma-pwr" and ref in ("J4",))
            ls = "-" if p["side"] == "top" else ":"
            a.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec=colors[bn], lw=1.3 if big else 0.4, ls=ls))
            if big:
                lab = {"pneuma-main": {"U1": "Core1106 (top)", "U3": "nRF52840 (btm)", "J5": "FFC 30P (btm)", "J4": "camera FPC (btm)"},
                       "pneuma-pwr": {"U5": "EG800Q-NA", "J4": "nano-SIM", "J1": "USB-C", "J5": "FFC 30P", "J2": "batt"}}[bn].get(ref, ref)
                a.text((x0 + x1) / 2, (y0 + y1) / 2, lab, ha="center", va="center", fontsize=7.5, color=colors[bn])
    ob = IF["offboard"]
    bmin, bmax = ob["battery"]["box_min"], ob["battery"]["box_max"]
    a.add_patch(Rectangle(bmin[:2], bmax[0] - bmin[0], bmax[1] - bmin[1], fc="#6a9f58", alpha=0.25, ec="#4d7a3e"))
    a.text((bmin[0] + bmax[0]) / 2, (bmin[1] + bmax[1]) / 2, "battery\n<=7.0 x 20 x 40\n~550-600 mAh", ha="center", va="center", fontsize=8)
    for k, c in (("speaker", "#9b59b6"), ("lra", "#c0392b")):
        o = ob[k]
        a.add_patch(Circle(o["cyl_center"][:2], o["diameter"] / 2, fill=False, ec=c, lw=1.2, ls="-."))
        a.text(o["cyl_center"][0], o["cyl_center"][1], k, ha="center", fontsize=7, color=c)
    th = IF["thermal"]
    for z in th["spreader_zones"]:
        x0, y0, x1, y1 = z["box_xy"]
        a.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="#f1c40f", alpha=0.10, ec="none"))
    for k in th["spreader_keepouts"]:
        if "box_xy" in k:
            x0, y0, x1, y1 = k["box_xy"]
            a.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec="#e74c3c", lw=0.9, hatch="//", alpha=0.5))
    for p in th["thermal_posts"]:
        (x0, y0, _), (x1, y1, _) = p["box_min"], p["box_max"]
        a.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="#e67e22", alpha=0.55, ec="#a04000"))
    a.text(9.5, 3.2, "RF keep-out", fontsize=6.5, color="#c0392b")
    for z in ob["lte_antenna"]["zones"]:
        (x0, y0, _), (x1, y1, _) = z["box_min"], z["box_max"]
        a.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="#e74c3c", alpha=0.25, ec="#c0392b"))
    a.text(-21, -53, "LTE antenna pockets", fontsize=6.5, color="#c0392b")
    a.add_patch(Rectangle((-5.5, 18.0), 11, 12.5, fill=False, ec="k", lw=1.0, ls="-."))
    a.text(0, 29, "camera", ha="center", fontsize=7)
    a.axhline(-10, color="0.6", lw=0.6, ls=":"); a.axhline(-20, color="0.6", lw=0.6, ls=":")
    a.text(21, -15, "+10 mm\ninsert\n(K->L)", fontsize=7, color="0.4")
    a.set_aspect("equal"); a.set_xlim(-26, 27); a.set_ylim(-62, 50); a.grid(True, lw=0.25)
    a.set_title("Plan view (enclosure L coords, mm)\nsolid = top side, dotted = bottom; yellow = copper-foil spreader, hatched = keep-out, orange = thermal posts", fontsize=10)
# side view: z vs y extents
for n, e in EXT.items():
    x0, x1, y0, y1, z0, z1 = e
    c = "#3b7dd8" if n.startswith("pneuma-main") else "#d8843b" if n.startswith("pneuma-pwr") else "#555"
    bx.add_patch(Rectangle((y0, z0), y1 - y0, z1 - z0, fill=False, ec=c, lw=1.0))
    if ":" not in n:
        bx.text((y0 + y1) / 2, z1 + 0.15, n.replace("pneuma-", "PNM-"), ha="center", fontsize=7, color=c)
bx.axhline(2.45, color="k", lw=0.8); bx.text(-60, 2.0, "rear floor z=2.45", fontsize=7)
bx.axhline(10.6, color="k", lw=0.8, ls="--"); bx.text(-60, 10.8, "front skin (inner) ~z=10.6 outside bump", fontsize=7)
bx.set_xlim(-62, 50); bx.set_ylim(0, 21); bx.set_aspect("equal"); bx.grid(True, lw=0.25)
bx.set_title("Side view (y vs z): stack heights", fontsize=10)
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "out", "layout-L.png")
plt.tight_layout(); plt.savefig(out, dpi=130)
print(out)
