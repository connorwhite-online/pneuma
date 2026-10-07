"""Generate the project library: lib/Pneuma.kicad_sym, lib/Pneuma.pretty, lib/3d.

Inputs that are vendor files (Luckfox Core1106 KiCad symbol/footprint/STEP) are read
from hardware/kicad/vendor/.  Everything else is derived from datasheet numbers that
are cited next to the code.
"""
import os, shutil, uuid
from sexp import parse, dump, find, find1, Sym as S
import eg800q

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LIB = os.path.join(ROOT, "lib")
VENDOR = os.path.join(ROOT, "vendor")


def U(seed):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "pneuma/lib/" + seed))


def eff(size=1.27, hide=False, justify=None):
    e = [S("effects"), [S("font"), [S("size"), size, size]]]
    if justify:
        e.append([S("justify")] + [S(j) for j in justify.split()])
    if hide:
        e.append([S("hide"), S("yes")])
    return e


def prop(k, v, x=0.0, y=0.0, hide=False, size=1.27):
    return [S("property"), k, v, [S("at"), x, y, 0], eff(size, hide)]


# ---------------------------------------------------------------- symbols
def box_symbol(name, left, right, bottom, ref="U", value=None, footprint="", desc="", hidden=()):
    """Rectangular symbol. left/right/bottom: [(number, name, etype)]."""
    pitch = 2.54
    h = max(len(left), len(right), 1) * pitch + pitch
    w = max(len(bottom) * pitch + pitch * 2, 30.48)
    x0, y0 = -w / 2, h / 2
    pins = []

    def pin(num, pname, et, x, y, ang, hide=False):
        p = [S("pin"), S(et), S("line"), [S("at"), x, y, ang], [S("length"), 2.54],
             [S("name"), pname, eff()], [S("number"), str(num), eff()]]
        if hide:
            p.insert(3, [S("hide"), S("yes")])
        pins.append(p)

    for i, (n, nm, et) in enumerate(left):
        pin(n, nm, et, x0 - 2.54, y0 - pitch * (i + 1), 0)
    for i, (n, nm, et) in enumerate(right):
        pin(n, nm, et, -x0 + 2.54, y0 - pitch * (i + 1), 180)
    for i, (n, nm, et) in enumerate(bottom):
        pin(n, nm, et, x0 + pitch * (i + 1), -y0 - 2.54, 90)
    for i, (n, nm, et) in enumerate(hidden):
        pin(n, nm, et, 0, 0, 0, hide=True)
    body = [S("symbol"), f"{name}_0_1",
            [S("rectangle"), [S("start"), x0, y0], [S("end"), -x0, -y0],
             [S("stroke"), [S("width"), 0.254], [S("type"), S("default")]], [S("fill"), [S("type"), S("background")]]]]
    unit = [S("symbol"), f"{name}_1_1"] + pins
    return [S("symbol"), name, [S("pin_names"), [S("offset"), 1.016]],
            [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")], [S("on_board"), S("yes")],
            prop("Reference", ref, x0, y0 + 1.5), prop("Value", value or name, x0, -y0 - 6),
            prop("Footprint", footprint, 0, 0, hide=True), prop("Datasheet", "", 0, 0, hide=True),
            prop("Description", desc, 0, 0, hide=True), body, unit]


def eg800q_symbol():
    tbl = eg800q.pin_table()
    sig = [r for r in tbl if r[1] not in ("GND", "RESERVED")]
    order_left = ["VBAT", "PWRKEY", "RESET_N", "STATUS", "NET_STATUS", "VDD_EXT", "USB_VBUS", "USB_DP", "USB_DM",
                  "USB_BOOT", "ANT_MAIN", "USIM_VDD", "USIM_DATA", "USIM_CLK", "USIM_RST", "USIM_DET", "PSM_IND",
                  "PSM_INT", "ADC0", "ADC1"]
    left = sorted([r for r in sig if r[1] in order_left], key=lambda r: (order_left.index(r[1]), r[0]))
    right = sorted([r for r in sig if r[1] not in order_left], key=lambda r: r[1])
    gnd = [r for r in tbl if r[1] == "GND"]
    res = [r for r in tbl if r[1] == "RESERVED"]
    return box_symbol("EG800Q-NA", left, right, gnd, value="EG800Q-NA",
                      footprint="Pneuma:Quectel_EG800Q_LGA-109",
                      desc="Quectel LTE Cat-1 bis module, North America (B2/4/5/12/13/66)", hidden=res)


def led_symbol():
    name = "LED_RGB_CA_0404"
    pins = []
    for num, nm, x, y, ang in [(1, "A", -7.62, 0, 0), (2, "RK", 7.62, 2.54, 180), (3, "BK", 7.62, -2.54, 180),
                               (4, "GK", 7.62, 0, 180)]:
        pins.append([S("pin"), S("passive"), S("line"), [S("at"), x, y, ang], [S("length"), 2.54],
                     [S("name"), nm, eff()], [S("number"), str(num), eff()]])
    body = [S("symbol"), f"{name}_0_1",
            [S("rectangle"), [S("start"), -5.08, 3.81], [S("end"), 5.08, -3.81],
             [S("stroke"), [S("width"), 0.254], [S("type"), S("default")]], [S("fill"), [S("type"), S("background")]]]]
    return [S("symbol"), name, [S("pin_names"), [S("offset"), 1.016]], [S("exclude_from_sim"), S("no")],
            [S("in_bom"), S("yes")], [S("on_board"), S("yes")],
            prop("Reference", "D", -5.08, 5.5), prop("Value", name, -5.08, -5.5),
            prop("Footprint", "LED_SMD:LED_Lumex_SML-LX0404SIUPGUSB", 0, 0, hide=True),
            prop("Datasheet", "https://www.lumex.com/spec/SML-LX0404SIUPGUSB.pdf", 0, 0, hide=True),
            prop("Description", "RGB LED, common anode; pad 1=A 2=R 3=B 4=G (Lumex SML-LX0404)", 0, 0, hide=True),
            body, [S("symbol"), f"{name}_1_1"] + pins]


def core_symbol():
    src = parse(open(os.path.join(VENDOR, "luckfox-core1106", "Core1106.kicad_sym"), encoding="utf-8").read())
    sym = find1(src, "symbol")
    for p in find(sym, "property"):
        if p[1] == "Footprint":
            p[2] = "Pneuma:Core1106-SMT-Cutout"
        if p[1] == "Reference":
            p[2] = "U"
        if p[1] == "Description":
            p[2] = "Luckfox Core1106 RV1106 stamp-hole SoM (vendor symbol)"
    return sym


def write_symbols():
    lib = [S("kicad_symbol_lib"), [S("version"), 20241209], [S("generator"), "pneuma_lib_gen"],
           [S("generator_version"), "1.0"], core_symbol(), eg800q_symbol(), led_symbol()]
    open(os.path.join(LIB, "Pneuma.kicad_sym"), "w").write(dump(lib) + "\n")


# ---------------------------------------------------------------- footprints
def fp_line(a, b, layer, w=0.12, seed=""):
    return [S("fp_line"), [S("start"), *a], [S("end"), *b], [S("stroke"), [S("width"), w], [S("type"), S("solid")]],
            [S("layer"), layer], [S("uuid"), U(seed + layer + str(a) + str(b))]]


def rect(x0, y0, x1, y1, layer, w=0.12, seed=""):
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return [fp_line(pts[i], pts[(i + 1) % 4], layer, w, seed) for i in range(4)]


def fp_text(kind, text, x, y, layer, hide=False, seed=""):
    e = [S("effects"), [S("font"), [S("size"), 1, 1], [S("thickness"), 0.15]]]
    p = [S("property"), kind, text, [S("at"), x, y, 0], [S("layer"), layer]]
    if hide:
        p.append([S("hide"), S("yes")])
    p += [[S("uuid"), U(seed + kind)], e]
    return p


def smd_pad(num, x, y, w, h, seed, shape="rect", paste=True):
    layers = ["F.Cu", "F.Mask"] + (["F.Paste"] if paste else [])
    return [S("pad"), str(num), S("smd"), S(shape), [S("at"), x, y], [S("size"), w, h],
            [S("layers")] + layers, [S("uuid"), U(seed + "pad" + str(num) + str(x) + str(y))]]


def footprint(name, descr, items, model=None, attr="smd"):
    fp = [S("footprint"), name, [S("version"), 20241229], [S("generator"), "pneuma_lib_gen"],
          [S("generator_version"), "1.0"], [S("layer"), "F.Cu"], [S("descr"), descr],
          [S("attr")] + [S(a) for a in attr.split()]] + items
    if model:
        fp.append(model)
    open(os.path.join(LIB, "Pneuma.pretty", name + ".kicad_mod"), "w").write(dump(fp) + "\n")


def model(path, offset=(0, 0, 0), rot=(0, 0, 0)):
    return [S("model"), path, [S("offset"), [S("xyz"), *offset]], [S("scale"), [S("xyz"), 1, 1, 1]],
            [S("rotate"), [S("xyz"), *rot]]]


def eg800q_fp():
    name = "Quectel_EG800Q_LGA-109"
    W, H = eg800q.BODY
    items = [fp_text("Reference", "REF**", 0, -H / 2 - 1.2, "F.SilkS", seed=name),
             fp_text("Value", "EG800Q-NA", 0, H / 2 + 1.2, "F.Fab", seed=name)]
    items += rect(-W / 2, -H / 2, W / 2, H / 2, "F.Fab", 0.1, name)
    items += rect(-W / 2 - 0.12, -H / 2 - 0.12, W / 2 + 0.12, H / 2 + 0.12, "F.SilkS", 0.12, name + "s")
    items += rect(-W / 2 - 0.5, -H / 2 - 0.5, W / 2 + 0.5, H / 2 + 0.5, "F.CrtYd", 0.05, name)
    items.append(fp_line((-W / 2 - 0.12, -H / 2 + 1.2), (-W / 2 + 1.2, -H / 2 - 0.12), "F.SilkS", 0.12, name + "p1"))
    for n, x, y, w, h in eg800q.pads():
        # large centre GND pads: segmented paste is left to the stencil step; keep full paste here
        items.append(smd_pad(n, round(x, 3), round(y, 3), w, h, name))
    footprint(name, "Quectel EG800Q series LGA-109, 15.8x17.7x2.4 mm, per EG800Q Hardware Design V1.1 Fig.37",
              items, model("${KIPRJMOD}/../lib/3d/EG800Q-NA_body.step"))


def pads2_fp():
    name = "Pads_2x_1.2x1.6mm_P2.5mm"
    items = [fp_text("Reference", "REF**", 0, -2, "F.SilkS", seed=name),
             fp_text("Value", name, 0, 2, "F.Fab", seed=name),
             smd_pad(1, -1.25, 0, 1.2, 1.6, name, paste=False), smd_pad(2, 1.25, 0, 1.2, 1.6, name, paste=False)]
    items += rect(-2.1, -1.05, 2.1, 1.05, "F.CrtYd", 0.05, name)
    items.append(fp_line((-2.3, -1.0), (-2.3, 1.0), "F.SilkS", 0.12, name))
    footprint(name, "Two solder pads for wire leads (LRA)", items)


def springpad_fp():
    name = "SpringPad_3.0x2.0mm"
    items = [fp_text("Reference", "REF**", 0, -2, "F.SilkS", seed=name),
             fp_text("Value", name, 0, 2, "F.Fab", seed=name),
             smd_pad(1, 0, 0, 3.0, 2.0, name, shape="rect", paste=False)]
    items += rect(-1.75, -1.25, 1.75, 1.25, "F.CrtYd", 0.05, name)
    footprint(name, "ENIG pad for a spring finger / pogo contact (touch electrode)", items)


def hole_fp():
    name = "MountingHole_1.7mm_M1.6"
    items = [fp_text("Reference", "REF**", 0, -2.4, "F.SilkS", hide=True, seed=name),
             fp_text("Value", name, 0, 2.4, "F.Fab", seed=name),
             [S("pad"), "", S("np_thru_hole"), S("circle"), [S("at"), 0, 0], [S("size"), 1.7, 1.7], [S("drill"), 1.7],
              [S("layers"), "*.Cu", "*.Mask"], [S("uuid"), U(name + "pad")]],
             [S("fp_circle"), [S("center"), 0, 0], [S("end"), 1.6, 0], [S("stroke"), [S("width"), 0.12], [S("type"), S("solid")]],
              [S("fill"), S("no")], [S("layer"), "Cmts.User"], [S("uuid"), U(name + "c")]]]
    items += rect(-1.7, -1.7, 1.7, 1.7, "F.CrtYd", 0.05, name)
    footprint(name, "NPTH 1.7 mm for M1.6 self-tapper / heat-set insert in the rigid carrier; 3.2 mm head clearance",
              items, attr="exclude_from_pos_files exclude_from_bom")


def core_fp():
    """Luckfox footprint + routed cutout for the module's underside parts + courtyard + 3D."""
    src = parse(open(os.path.join(VENDOR, "luckfox-core1106", "Core1106-SMT.kicad_mod"), encoding="utf-8").read())
    name = "Core1106-SMT-Cutout"
    src[1] = name
    src[:] = [c for c in src if not (isinstance(c, list) and c and c[0] in ("zone", "model"))]
    # underside-parts keepout from the vendor footprint: x -12.15..11.40, y -11.65..9.02
    cx0, cy0, cx1, cy1 = -12.45, -11.95, 11.70, 9.32
    src += rect(cx0, cy0, cx1, cy1, "Edge.Cuts", 0.05, name + "cut")
    src += rect(-15.95, -15.95, 15.95, 15.95, "F.CrtYd", 0.05, name)
    src += rect(-15, -15, 15, 15, "F.Fab", 0.1, name)
    # STEP spans x,y 0..30 with the module PCB at z -1.6..0: lift onto the carrier, centre on origin
    src.append(model("${KIPRJMOD}/../lib/3d/Core1106-3D.step", offset=(-15, -15, 1.6)))
    for c in src:
        if isinstance(c, list) and c and c[0] == "descr":
            c[1] = "Luckfox Core1106 (vendor pads) + carrier cutout 24.15x21.27 mm for underside parts"
    if not find1(src, "descr"):
        src.insert(2, [S("descr"), "Luckfox Core1106 + carrier cutout"])
    open(os.path.join(LIB, "Pneuma.pretty", name + ".kicad_mod"), "w").write(dump(src) + "\n")


def body_step(path, w, h, t, chamfer_pin1=True):
    import cadquery as cq  # noqa: only needed when (re)generating 3D bodies
    s = cq.Workplane("XY").box(w, h, t, centered=(True, True, False))
    cq.exporters.export(s, path)


def write_footprints():
    os.makedirs(os.path.join(LIB, "Pneuma.pretty"), exist_ok=True)
    eg800q_fp()
    pads2_fp()
    springpad_fp()
    hole_fp()
    core_fp()


def copy_vendor_3d():
    os.makedirs(os.path.join(LIB, "3d"), exist_ok=True)
    shutil.copy(os.path.join(VENDOR, "luckfox-core1106", "Core1106-3D.stp"), os.path.join(LIB, "3d", "Core1106-3D.step"))


if __name__ == "__main__":
    os.makedirs(LIB, exist_ok=True)
    write_symbols()
    write_footprints()
    copy_vendor_3d()
    print("library written to", LIB)
