"""Cut outline for the copper-foil spreader (run with the CadQuery Python). -> out/spreader-front-L.dxf/.svg"""
import json, os
import cadquery as cq
from shapely.geometry import Polygon, box, Point
from shapely.ops import unary_union
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IF = json.load(open(os.path.join(os.path.dirname(ROOT), "mechanical", "enclosure-L-electronics.json")))
th = IF["thermal"]
area = unary_union([box(*z["box_xy"]) for z in th["spreader_zones"]])
area = area.intersection(Polygon(IF["cavity_L_section_z3_8"]).buffer(-1.0))
cuts = []
for k in th["spreader_keepouts"]:
    if "box_xy" in k:
        cuts.append(box(*k["box_xy"]))
    for c in ([k["circle_xy"]] if "circle_xy" in k else k.get("circles_xy", [])):
        cuts.append(Point(c).buffer(k["diameter"] / 2, 32))
sheet = area.difference(unary_union(cuts)).buffer(-0.3).buffer(0.3)   # clean slivers
parts = [sheet] if sheet.geom_type == "Polygon" else list(sheet.geoms)
wp = cq.Workplane("XY")
faces = []
for p in parts:
    if p.area < 20:
        continue
    outer = cq.Wire.makePolygon([cq.Vector(x, y, 0) for x, y in p.exterior.coords], close=True)
    inner = [cq.Wire.makePolygon([cq.Vector(x, y, 0) for x, y in r.coords], close=True) for r in p.interiors]
    faces.append(cq.Face.makeFromWires(outer, inner))
shape = cq.Workplane("XY").add(cq.Compound.makeCompound(faces))
os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
cq.exporters.export(shape, os.path.join(ROOT, "out", "spreader-front-L.dxf"))
print("pieces:", len(faces), "| area mm2:", round(sum(f.Area() for f in faces)))
