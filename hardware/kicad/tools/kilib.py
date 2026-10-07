"""Read symbols (with `extends` resolved) and their pins from KiCad libraries."""
import copy, os
from sexp import parse, find, find1, Sym

KICAD_SHARE = os.environ.get("KICAD_SHARE", "/Volumes/KiCad/KiCad/KiCad.app/Contents/SharedSupport")
_cache = {}


def _lib(path):
    if path not in _cache:
        _cache[path] = parse(open(path, encoding="utf-8").read())
    return _cache[path]


def lib_path(libname, local_dirs=()):
    for d in local_dirs:
        p = os.path.join(d, libname + ".kicad_sym")
        if os.path.exists(p):
            return p
    return os.path.join(KICAD_SHARE, "symbols", libname + ".kicad_sym")


def get_symbol(lib_id, local_dirs=()):
    """Return a flattened symbol definition list named lib_id ('Lib:Name')."""
    libname, name = lib_id.split(":", 1)
    lib = _lib(lib_path(libname, local_dirs))
    syms = {s[1]: s for s in find(lib, "symbol")}
    s = copy.deepcopy(syms[name])
    ext = find1(s, "extends")
    if ext:
        parent = copy.deepcopy(syms[ext[1]])
        # child overrides properties; geometry/pins come from parent units
        props = {p[1]: p for p in find(s, "property")}
        out = [Sym("symbol"), name]
        for c in parent[2:]:
            if isinstance(c, list) and c[0] == "property" and c[1] in props:
                out.append(props.pop(c[1]))
            elif isinstance(c, list) and c[0] == "symbol":
                c = copy.deepcopy(c)
                c[1] = c[1].replace(ext[1], name, 1)
                out.append(c)
            else:
                out.append(c)
        out.extend(props.values())
        s = out
    s[1] = lib_id
    return s


def pins(symdef):
    """[(number, name, x, y, angle, length, etype, unit, hidden)] from a flattened symbol."""
    out = []
    for unit in find(symdef, "symbol"):
        uname = unit[1]
        try:
            u = int(uname.rsplit("_", 2)[-2])
        except ValueError:
            u = 0
        for p in find(unit, "pin"):
            at = find1(p, "at")
            ln = find1(p, "length")
            name = find1(p, "name")[1]
            num = find1(p, "number")[1]
            hidden = any((isinstance(c, list) and c and c[0] == "hide" and (len(c) == 1 or c[1] == "yes"))
                         or c == "hide" for c in p[1:])
            out.append((num, name, float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0,
                        float(ln[1]) if ln else 2.54, str(p[1]), u, hidden))
    return out


def prop(symdef, key):
    for p in find(symdef, "property"):
        if p[1] == key:
            return p[2]
    return None
