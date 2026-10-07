"""Minimal S-expression reader/writer for KiCad files (no external deps)."""
import re

_TOK = re.compile(r'\s*(?:(\()|(\))|("(?:[^"\\]|\\.)*")|([^\s()"]+))', re.S)


class Sym(str):
    """Unquoted atom."""


def parse(text):
    stack, cur = [], []
    pos = 0
    while True:
        m = _TOK.match(text, pos)
        if not m or m.end() == pos:
            break
        pos = m.end()
        lp, rp, qs, atom = m.groups()
        if lp:
            stack.append(cur)
            cur = []
        elif rp:
            done, cur = cur, stack.pop()
            cur.append(done)
        elif qs is not None:
            cur.append(bytes(qs[1:-1], "utf-8").decode("unicode_escape") if "\\" in qs else qs[1:-1])
        else:
            cur.append(Sym(atom))
    return cur[0] if len(cur) == 1 else cur


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def dump(node, indent=0):
    if isinstance(node, list):
        if not node:
            return "()"
        simple = all(not isinstance(x, list) for x in node)
        head = " ".join(_atom(x) for x in node if not isinstance(x, list)) if simple else None
        if simple and len(head) < 100:
            return "(" + head + ")"
        parts, line = [], []
        for x in node:
            if isinstance(x, list):
                parts.append(dump(x, indent + 1))
            else:
                line.append(_atom(x))
        pad = "\n" + "  " * (indent + 1)
        return "(" + " ".join(line) + "".join(pad + p for p in parts) + "\n" + "  " * indent + ")"
    return _atom(node)


def _atom(x):
    if isinstance(x, Sym):
        return str(x)
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, (int,)):
        return str(x)
    if isinstance(x, float):
        s = f"{x:.4f}".rstrip("0").rstrip(".")
        return s if s not in ("-0", "") else "0"
    return q(x)


def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def find1(node, key):
    r = find(node, key)
    return r[0] if r else None
