"""Electronics assembly for enclosure-L modeling (run with a CadQuery Python, not KiCad's).

Reads out/pneuma-*.step (kicad-cli export) + hardware/mechanical/enclosure-L-electronics.json,
places everything in enclosure coordinates, adds envelopes for off-board parts and for
on-board parts that have no stock 3D model, checks pairwise solid interference, and
writes:
  out/Pneuma-RevA-electronics-L.step   (one solid per item, named)
  out/interference-L.json
"""
import json, math, os, itertools
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IF = json.load(open(os.path.join(os.path.dirname(ROOT), "mechanical", "enclosure-L-electronics.json")))

# on-board parts without a stock KiCad 3D model: (board, ref, height above the PCB face)
NO_MODEL = [("pneuma-pwr", "J4", 1.6), ("pneuma-pwr", "U2", 1.0), ("pneuma-main", "U6", 0.6),
            ("pneuma-main", "D1", 0.3), ("pneuma-main", "MK1", 1.1), ("pneuma-main", "MK2", 1.3),
            ("pneuma-main", "U4", 0.8), ("pneuma-main", "Y1", 0.6)]


def board(name):
    b = IF["boards"][name]
    s = cq.importers.importStep(os.path.join(ROOT, "out", name + ".step"))
    # kicad-cli STEP: X = x+100, Y = y-100, Z=0 at PCB bottom
    return s.translate((-100, 100, b["pcb_bottom_z"])), b


def box(x0, y0, z0, x1, y1, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def main():
    items = {}
    for name in ("pneuma-main", "pneuma-pwr"):
        s, b = board(name)
        items[name] = s
    for bname, ref, h in NO_MODEL:
        b = IF["boards"][bname]
        p = b["parts"][ref]
        x0, y0, x1, y1 = p["courtyard_xy"]
        m = 0.25   # courtyard margin -> approximate body
        if p["side"] == "top":
            z0, z1 = b["pcb_top_z"], b["pcb_top_z"] + h
        else:
            z0, z1 = b["pcb_bottom_z"] - h, b["pcb_bottom_z"]
        items[f"{bname}:{ref}_envelope"] = box(x0 + m, y0 + m, z0, x1 - m, y1 - m, z1)
    ob = IF["offboard"]
    items["battery"] = box(*ob["battery"]["box_min"], *ob["battery"]["box_max"])
    items["ffc_under_battery"] = box(*ob["ffc"]["box_min"], *ob["ffc"]["box_max"])
    for k in ("speaker", "lra"):
        c = ob[k]
        items[k] = cq.Workplane("XY").circle(c["diameter"] / 2).extrude(c["height"]).translate(tuple(c["cyl_center"]))
    cam = ob["camera"]
    ax = cam["optical_axis"]
    tilt = math.degrees(math.atan2(ax[1], ax[2]))
    d = cam["depth_along_axis"]
    body = cq.Workplane("XY").box(cam["body_xy"][0], cam["body_xy"][1], d).translate((0, 0, -d / 2 - 0.4))
    body = body.rotate((0, 0, 0), (1, 0, 0), -tilt).translate(tuple(cam["aperture_center"]))
    items["camera_module"] = body
    for pad in IF["thermal"]["gap_pads"]:
        items[pad["name"].replace(" ", "_")] = box(*pad["box_min"], *pad["box_max"])
    for i, z in enumerate(ob["lte_antenna"]["zones"]):
        items[f"lte_antenna_zone_{i + 1}"] = box(*z["box_min"], *z["box_max"])

    # pairwise interference (solid intersection volume)
    names = list(items)
    solids = {n: items[n].val() if not isinstance(items[n].val(), cq.Compound) else items[n].val() for n in names}
    hits = []
    for a, b in itertools.combinations(names, 2):
        A, B = solids[a], solids[b]
        if not A.BoundingBox().overlaps(B.BoundingBox()) if hasattr(A.BoundingBox(), "overlaps") else False:
            continue
        try:
            v = A.intersect(B).Volume()
        except Exception as e:  # noqa
            v = -1
        if v > 0.01 or v < 0:
            hits.append({"a": a, "b": b, "overlap_mm3": round(v, 3)})
    extents = {n: [round(x, 2) for x in (lambda bb: (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))(solids[n].BoundingBox())]
               for n in names}
    json.dump({"method": "OCC solid intersection of every item pair (board STEPs are compounds)",
               "interferences": hits, "extents": extents},
              open(os.path.join(ROOT, "out", "interference-L.json"), "w"), indent=1)
    asm = cq.Assembly()
    for n in names:
        asm.add(items[n], name=n.replace(":", "_"))
    asm.save(os.path.join(ROOT, "out", "Pneuma-RevA-electronics-L.step"))
    print("items:", len(names), "| interferences:", hits)
    for n in names:
        print(f"  {n:34s}", extents[n])


if __name__ == "__main__":
    main()
