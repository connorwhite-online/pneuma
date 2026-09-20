"""Which off-the-shelf rectangular thermal pads fit the spreader zones without cutting?"""
import json, os
from shapely.geometry import box, Point, Polygon
from shapely.ops import unary_union
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IF = json.load(open(os.path.join(os.path.dirname(ROOT), "mechanical", "enclosure-L-electronics.json")))
th = IF["thermal"]
area = unary_union([box(*z["box_xy"]) for z in th["spreader_zones"]]).intersection(
    Polygon(IF["cavity_L_section_z3_8"]).buffer(-1.0))
cuts = []
for k in th["spreader_keepouts"]:
    if "box_xy" in k: cuts.append(box(*k["box_xy"]))
    for c in ([k["circle_xy"]] if "circle_xy" in k else k.get("circles_xy", [])):
        cuts.append(Point(c).buffer(k["diameter"] / 2, 32))
free = area.difference(unary_union(cuts))
print("custom-cut coverage:", round(free.area), "mm2")
STOCK = [(40,40),(40,20),(30,30),(30,20),(25,25),(25,15),(20,20),(20,15),(15,15),(15,10),(10,10)]
placed, remaining = [], free
for _ in range(6):
    best = None
    for (w, h) in STOCK:
        for (ww, hh) in {(w, h), (h, w)}:
            x = remaining.bounds[0]
            while x + ww <= remaining.bounds[2]:
                y = remaining.bounds[1]
                while y + hh <= remaining.bounds[3]:
                    r = box(x, y, x + ww, y + hh)
                    if remaining.contains(r) and (best is None or ww * hh > best[0]):
                        best = (ww * hh, ww, hh, x, y)
                    y += 1.0
                x += 1.0
    if not best or best[0] < 100:
        break
    a, ww, hh, x, y = best
    placed.append((ww, hh, round(x + ww / 2, 1), round(y + hh / 2, 1)))
    remaining = remaining.difference(box(x, y, x + ww, y + hh).buffer(0.5))
tot = sum(p[0] * p[1] for p in placed)
for w, h, cx, cy in placed:
    print(f"  {w:.0f} x {h:.0f} mm  centre ({cx}, {cy})")
print("stock coverage:", tot, "mm2 =", round(100 * tot / free.area), "% of the custom-cut area")
json.dump([{"size_mm": [w, h], "center_xy": [cx, cy]} for w, h, cx, cy in placed],
          open(os.path.join(ROOT, "out", "spreader-stock-pads.json"), "w"), indent=1)
