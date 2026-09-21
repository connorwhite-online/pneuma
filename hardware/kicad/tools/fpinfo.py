import os, sys, pcbnew
import design
SH=os.environ.get("KICAD_SHARE","/Volumes/KiCad/KiCad/KiCad.app/Contents/SharedSupport")
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load(fpid):
    lib,name=fpid.split(":")
    path=os.path.join(ROOT,"lib","Pneuma.pretty") if lib=="Pneuma" else os.path.join(SH,"footprints",lib+".pretty")
    return pcbnew.FootprintLoad(path,name)
if __name__=="__main__":
    seen={}
    for mk in design.BOARDS:
        b=mk()
        for p in b.parts:
            f=p["footprint"]
            if f in seen: continue
            fp=load(f); 
            cy=fp.GetCourtyard(pcbnew.F_CrtYd)
            bb=cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
            seen[f]=(pcbnew.ToMM(bb.GetWidth()),pcbnew.ToMM(bb.GetHeight()),pcbnew.ToMM(bb.GetX()),pcbnew.ToMM(bb.GetY()))
            print(f"{f:85s} {seen[f][0]:6.2f} x {seen[f][1]:6.2f}  at ({seen[f][2]:.2f},{seen[f][3]:.2f})")
