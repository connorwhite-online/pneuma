"""Grouped BOM CSVs for both boards, straight from design.py (no KiCad needed)."""
import csv, os, re
from collections import OrderedDict
import design

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def natural(ref):
    m = re.match(r"([A-Z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def rows(board):
    groups = OrderedDict()
    for p in sorted(board.parts, key=lambda p: natural(p["ref"])):
        if p["lib_id"] == "Connector:TestPoint" and p["footprint"].startswith("TestPoint:"):
            key = ("TestPoint", "pad", p["footprint"], "", p["dnp"])
        else:
            f = p["fields"]
            key = (p["value"], f.get("MPN", ""), p["footprint"], f.get("Manufacturer", ""), p["dnp"])
        g = groups.setdefault(key, dict(refs=[], fields=p["fields"], lib=p["lib_id"]))
        g["refs"].append(p["ref"])
    out = []
    for (value, mpn, fp, mfr, dnp), g in groups.items():
        f = g["fields"]
        spec = ", ".join(x for x in (f.get("Voltage", ""), f.get("Note", "")) if x)
        out.append({"Refs": " ".join(g["refs"]), "Qty": 0 if dnp else len(g["refs"]), "Value": value,
                    "Manufacturer": mfr, "MPN": mpn, "Footprint": fp.split(":")[-1],
                    "Description": f.get("Description", ""), "Notes": ("DNP " if dnp else "") + spec})
    return out


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    for mk in design.BOARDS:
        b = mk()
        path = os.path.join(ROOT, "out", b.name + "-bom.csv")
        r = rows(b)
        with open(path, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(r[0]))
            w.writeheader()
            w.writerows(r)
        print(path, len(r), "lines,", sum(x["Qty"] for x in r), "placements")
