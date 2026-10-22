"""Icon library + SVG → PPTD custom shapes (editable vector shapes that survive pptd2pptx).

Library: assets/icons/tabler-filled (Tabler Icons, MIT, 1000+ filled icons, viewBox 24×24).
Any other SVG works too — a library icon you copied and edited, or one you drew yourself.

Usage:
  python icons.py search chart growth [--limit 20]     # keyword search over icon names
  python icons.py shape tabler-filled/bulb --bounds 100,80,48,48 --color '#1A73E8'
  python icons.py shape <project>/media/icons/my-icon.svg --bounds 100,80,48,48

shape prints PPTD element YAML (shapeName: custom). From Python / build.py:
  from icons import shape_elements          # -> list of PPTD element dicts
  page.svg(x, y, w, h, "tabler-filled/bulb", fill=...)   # pptd_kit helper, same thing

Supported SVG: <path>, <circle>, <ellipse>, <rect> (incl. rx/ry), <polygon>, filled <polyline>,
nested <g>, transform (matrix/translate/scale/rotate/skewX/skewY), fill / opacity / style="fill:…".
Stroke-only shapes (fill="none" + stroke) cannot become filled outlines automatically: they are
skipped with a warning — convert the stroke to a filled outline (or pick a filled icon) instead.
Each SVG drawable becomes its own shape (separate SVG paths are filled independently; merging
them would punch holes where they overlap). --color / fill tints all of them; without it every
shape keeps its SVG fill, so multi-color icons survive and parts can be recolored individually.
"""
import argparse
import difflib
import math
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svgpath  # noqa: E402

ICON_ROOT = Path(__file__).resolve().parents[1] / "assets" / "icons"
DEFAULT_LIB = "tabler-filled"
DEFAULT_COLOR = "#333333"
_NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
SKIP_TAGS = {"defs", "clipPath", "mask", "title", "desc", "metadata", "style", "linearGradient", "radialGradient", "symbol"}


# ---------------------------------------------------------------- library
def library_icons(lib=None):
    libs = [ICON_ROOT / lib] if lib else sorted(p for p in ICON_ROOT.iterdir() if p.is_dir())
    for d in libs:
        for f in sorted(d.glob("*.svg")):
            yield f"{d.name}/{f.stem}", f


def search(words, limit=20, lib=None):
    """Rank icon ids by query words matched (any word counts — pass synonyms freely), then match
    quality (exact name part > prefix > substring), then shorter names."""
    words = [w.lower() for w in words if w.strip()]
    scored = []
    for icon_id, f in library_icons(lib):
        parts = f.stem.lower().split("-")
        hits = score = 0
        for w in words:
            if w in parts:
                hits, score = hits + 1, score + 3
            elif any(p.startswith(w) for p in parts):
                hits, score = hits + 1, score + 2
            elif len(w) >= 3 and w in f.stem.lower():
                hits, score = hits + 1, score + 1
        if hits:
            scored.append((-hits, -score, len(parts), icon_id, f))
    return [(i, f) for *_, i, f in sorted(scored)[:limit]]


def resolve(ref):
    p = Path(ref)
    if p.suffix.lower() == ".svg":
        if p.exists():
            return p
        if "/" in ref and not ref.startswith(tuple(f"{d.name}/" for d in ICON_ROOT.iterdir() if d.is_dir())):
            raise FileNotFoundError(f"SVG file {ref!r} not found (relative paths resolve from the current folder)")
    rid = ref[:-4] if ref.endswith(".svg") else ref
    if "/" not in rid:
        rid = f"{DEFAULT_LIB}/{rid}"
    f = ICON_ROOT / f"{rid}.svg"
    if f.exists():
        return f
    lib, name = rid.split("/", 1)
    names = [f.stem for f in (ICON_ROOT / lib).glob("*.svg")] if (ICON_ROOT / lib).is_dir() else []
    close = difflib.get_close_matches(name, names, 6, 0.6) or [i.split("/")[1] for i, _ in search(re.split(r"[- ]", name), 6, lib if names else None)]
    hint = ", ".join(f"{lib}/{c}" for c in close)
    raise FileNotFoundError(f"icon {ref!r} not found" + (f"; close matches: {hint}" if hint else ""))


# ---------------------------------------------------------------- SVG parsing
def _matmul(m, n):
    a, b, c, d, e, f = m
    a2, b2, c2, d2, e2, f2 = n
    return (a * a2 + c * b2, b * a2 + d * b2, a * c2 + c * d2, b * c2 + d * d2, a * e2 + c * f2 + e, b * e2 + d * f2 + f)


def parse_transform(s):
    m = (1, 0, 0, 1, 0, 0)
    for name, args in re.findall(r"(\w+)\s*\(([^)]*)\)", s or ""):
        v = [float(x) for x in _NUM.findall(args)]
        if name == "matrix":
            t = tuple(v[:6])
        elif name == "translate":
            t = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif name == "scale":
            t = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif name == "rotate":
            r = math.radians(v[0])
            t = (math.cos(r), math.sin(r), -math.sin(r), math.cos(r), 0, 0)
            if len(v) == 3:
                t = _matmul(_matmul((1, 0, 0, 1, v[1], v[2]), t), (1, 0, 0, 1, -v[1], -v[2]))
        elif name == "skewX":
            t = (1, 0, math.tan(math.radians(v[0])), 1, 0, 0)
        elif name == "skewY":
            t = (1, math.tan(math.radians(v[0])), 0, 1, 0, 0)
        else:
            raise ValueError(f"unsupported transform {name}")
        m = _matmul(m, t)
    return m


def _style(el, parent):
    st = dict(parent)
    for k in ("fill", "stroke", "opacity", "fill-opacity", "fill-rule"):
        if el.get(k) is not None:
            st[k] = el.get(k).strip()
    for decl in (el.get("style") or "").split(";"):
        if ":" in decl:
            k, v = (x.strip() for x in decl.split(":", 1))
            if k in ("fill", "stroke", "opacity", "fill-opacity", "fill-rule"):
                st[k] = v
    return st


def _f(el, k, default=0.0):
    v = el.get(k)
    return float(_NUM.findall(v)[0]) if v and _NUM.findall(v) else default


def _shape_d(tag, el):
    if tag == "path":
        return el.get("d", "")
    if tag == "circle":
        cx, cy, r = _f(el, "cx"), _f(el, "cy"), _f(el, "r")
        return f"M{cx + r} {cy}A{r} {r} 0 1 1 {cx - r} {cy}A{r} {r} 0 1 1 {cx + r} {cy}Z" if r > 0 else ""
    if tag == "ellipse":
        cx, cy, rx, ry = _f(el, "cx"), _f(el, "cy"), _f(el, "rx"), _f(el, "ry")
        return f"M{cx + rx} {cy}A{rx} {ry} 0 1 1 {cx - rx} {cy}A{rx} {ry} 0 1 1 {cx + rx} {cy}Z" if rx > 0 and ry > 0 else ""
    if tag == "rect":
        x, y, w, h = _f(el, "x"), _f(el, "y"), _f(el, "width"), _f(el, "height")
        rx = el.get("rx")
        ry = el.get("ry")
        rx = _f(el, "rx") if rx is not None else (_f(el, "ry") if ry is not None else 0)
        ry = _f(el, "ry") if ry is not None else rx
        rx, ry = min(rx, w / 2), min(ry, h / 2)
        if w <= 0 or h <= 0:
            return ""
        if not rx or not ry:
            return f"M{x} {y}H{x + w}V{y + h}H{x}Z"
        return (f"M{x + rx} {y}H{x + w - rx}A{rx} {ry} 0 0 1 {x + w} {y + ry}V{y + h - ry}"
                f"A{rx} {ry} 0 0 1 {x + w - rx} {y + h}H{x + rx}A{rx} {ry} 0 0 1 {x} {y + h - ry}"
                f"V{y + ry}A{rx} {ry} 0 0 1 {x + rx} {y}Z")
    if tag in ("polygon", "polyline"):
        nums = _NUM.findall(el.get("points", ""))
        if len(nums) < 4:
            return ""
        pts = " ".join(f"{nums[i]} {nums[i + 1]}" for i in range(0, len(nums) - 1, 2))
        return f"M{pts}" + ("Z" if tag == "polygon" else "")
    return None


def load_svg(path):
    """-> (viewBox (minx, miny, w, h), [(segments, fill, opacity)], warnings)."""
    root = ET.fromstring(Path(path).read_text(encoding="utf-8"))
    vb = root.get("viewBox")
    if vb:
        minx, miny, vw, vh = (float(v) for v in _NUM.findall(vb)[:4])
    else:
        minx, miny, vw, vh = 0.0, 0.0, _f(root, "width", 24), _f(root, "height", 24)
    out, warns = [], []

    def walk(el, m, st):
        tag = el.tag.split("}")[-1]
        if tag in SKIP_TAGS:
            return
        m = _matmul(m, parse_transform(el.get("transform"))) if el.get("transform") else m
        st = _style(el, st)
        d = _shape_d(tag, el)
        if d is None:
            if tag not in ("svg", "g"):
                warns.append(f"skipped <{tag}>")
            for ch in el:
                walk(ch, m, st)
            return
        if not d:
            return
        fill = st.get("fill", "black")
        if fill == "none":
            if st.get("stroke", "none") != "none":
                warns.append(f"skipped stroke-only <{tag}> — convert the stroke to a filled outline")
            return
        if st.get("fill-rule") == "evenodd":
            warns.append(f"<{tag}> uses fill-rule evenodd; PowerPoint fills by winding — check holes on the render")
        if fill not in ("currentColor",) and css_color(fill) is None:
            warns.append(f"<{tag}> fill {fill!r} not understood — drawn in {DEFAULT_COLOR}; use #RRGGBB")
        op = float(st.get("opacity", 1)) * float(st.get("fill-opacity", 1))
        out.append((svgpath.transform(svgpath.normalize(d), m), fill, op))

    walk(root, (1, 0, 0, 1, -minx, -miny), {})
    if not out:
        raise ValueError(f"{path}: nothing fillable found" + (f" ({'; '.join(warns)})" if warns else ""))
    return (0.0, 0.0, vw, vh), out, warns


NAMED = {"black": "#000000", "white": "#FFFFFF", "red": "#FF0000", "green": "#008000", "blue": "#0000FF",
         "yellow": "#FFFF00", "orange": "#FFA500", "purple": "#800080", "gray": "#808080", "grey": "#808080",
         "silver": "#C0C0C0", "navy": "#000080", "teal": "#008080", "maroon": "#800000", "lime": "#00FF00"}


def css_color(value):
    """SVG paint -> PPTD #RRGGBB / #RRGGBBAA, or None when it can't be read (currentColor, url(), unknown names)."""
    v = str(value).strip()
    if v.lower() in NAMED:
        return NAMED[v.lower()]
    if re.fullmatch(r"#[0-9a-fA-F]{3,4}", v):
        return "#" + "".join(c * 2 for c in v[1:]).upper()
    if re.fullmatch(r"#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?", v):
        return v.upper()
    m = re.fullmatch(r"rgba?\(\s*([\d.]+)%?\s*[, ]\s*([\d.]+)%?\s*[, ]\s*([\d.]+)%?\s*(?:[,/]\s*([\d.]+%?))?\s*\)", v)
    if m:
        pct = "%" in v.split(")")[0].split("/")[0].split(",")[0]
        rgb = [round(float(c) * (2.55 if pct else 1)) for c in m.groups()[:3]]
        out = "#" + "".join(f"{max(0, min(255, c)):02X}" for c in rgb)
        if m.group(4):
            a = m.group(4)
            alpha = float(a[:-1]) / 100 if a.endswith("%") else float(a)
            out += f"{round(alpha * 255):02X}"
        return out
    return None


def _color(svg_fill, override):
    if override is not None:
        return override if isinstance(override, dict) else {"type": "solid", "color": override}
    return {"type": "solid", "color": css_color(svg_fill) or DEFAULT_COLOR}


def shape_elements(ref, x, y, w, h, fill=None, keep_ratio=True, element_id="icon"):
    """PPTD custom-shape element dicts for an icon id or SVG file, fitted into [x, y, w, h].

    fill: '#RRGGBB' / '#RRGGBBAA' or a PPTD Fill dict (gradients work); None keeps the SVG's own
    colors (currentColor → #333333). keep_ratio centers the icon instead of stretching it."""
    (_, _, vw, vh), items, _warns = load_svg(resolve(ref))
    if keep_ratio:
        s = min(w / vw, h / vh)
        x, y, w, h = x + (w - vw * s) / 2, y + (h - vh * s) / 2, vw * s, vh * s
    k = 100 if max(vw, vh) < 100 else 1  # integer-friendly coordinates for editors
    els = []
    for n, (segs, svg_fill, opacity) in enumerate(items, 1):
        el = {"elementId": element_id if len(items) == 1 else f"{element_id}-{n}", "elementType": "shape",
              "bounds": [round(x, 2), round(y, 2), round(w, 2), round(h, 2)], "shapeName": "custom",
              "viewBox": [round(vw * k, 2), round(vh * k, 2)], "path": svgpath.fmt(segs, k, 1),
              "fill": _color(svg_fill, fill)}
        if opacity < 1:
            el["opacity"] = round(opacity, 3)
        els.append(el)
    return els


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("words", nargs="+")
    s.add_argument("--limit", type=int, default=20)
    s.add_argument("--lib")
    sh = sub.add_parser("shape")
    sh.add_argument("ref", help="icon id (tabler-filled/bulb, or bulb) or path to an .svg file")
    sh.add_argument("--bounds", default="0,0,48,48")
    sh.add_argument("--color")
    sh.add_argument("--stretch", action="store_true", help="fill bounds exactly instead of keeping the ratio")
    sh.add_argument("--id", default="icon")
    a = ap.parse_args()
    if a.cmd == "search":
        hits = search(a.words, a.limit, a.lib)
        for icon_id, f in hits:
            print(f"{icon_id:<48} {f}")
        if not hits:
            print("no match — try English synonyms (e.g. money → coin, cash, currency)")
        return
    import yaml
    x, y, w, h = (float(v) for v in a.bounds.split(","))
    _, _, warns = load_svg(resolve(a.ref))
    for wmsg in warns:
        print(f"# warning: {wmsg}", file=sys.stderr)
    els = shape_elements(a.ref, x, y, w, h, a.color, not a.stretch, a.id)
    print(yaml.safe_dump(els, allow_unicode=True, sort_keys=False, width=10000, default_flow_style=None), end="")


if __name__ == "__main__":
    # Emit UTF-8 regardless of the Windows code page (cp950, cp936…) so callers that capture the
    # output as UTF-8 — agents, tests, CI — can read CJK messages.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    main()
