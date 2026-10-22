"""SVG path / shape normalizer — any SVG path data to absolute M/L/C/Q/Z segments.

Used by pptd2pptx.py (custom shapes may use the full PPTD path syntax: relative commands, H/V,
S/T, A arcs) and by icons.py (SVG files → PPTD custom shapes).

normalize(d)            -> [("M", (x, y)), ("L", (x, y)), ("C", (x1, y1, x2, y2, x, y)),
                            ("Q", (x1, y1, x, y)), ("Z", ())]
transform(segs, m)      -> segments with the affine matrix m = (a, b, c, d, e, f) applied
fmt(segs, scale, nd)    -> path string "M x y L … Z"
bbox(segs)              -> (minx, miny, maxx, maxy) of the control polygon (exact for M/L,
                           conservative for curves)
Arcs become cubic Béziers (≤ 90° per piece); winding direction is preserved, so holes drawn with
opposite winding keep working (PPTD custom-shape convention: outer clockwise, inner counter-clockwise).
"""
import math
import re

_TOKEN = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
_ARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}


def _arc_flags(tokens, i):
    """Arc flags may be written without separators ('a1 1 0 011 1'): split '011' into 0, 1, 1."""
    out = []
    for k in range(7):
        t = tokens[i]
        if k in (3, 4) and len(t) > 1 and t[0] in "01":  # a flag is always one character
            out.append(float(t[0]))
            tokens[i] = t[1:]
            continue
        out.append(float(t))
        i += 1
    return out, i


def _arc_to_cubic(x1, y1, rx, ry, phi, large, sweep, x2, y2):
    """SVG endpoint arc -> list of cubic segments (x1c, y1c, x2c, y2c, x, y)."""
    if (x1, y1) == (x2, y2):
        return []
    rx, ry = abs(rx), abs(ry)
    if rx == 0 or ry == 0:
        return [(x1, y1, x2, y2, x2, y2)]
    cphi, sphi = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    x1p, y1p = cphi * dx + sphi * dy, -sphi * dx + cphi * dy
    lam = (x1p / rx) ** 2 + (y1p / ry) ** 2
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    coef = math.sqrt(max(num / den, 0)) if den else 0
    if large == sweep:
        coef = -coef
    cxp, cyp = coef * rx * y1p / ry, -coef * ry * x1p / rx
    cx = cphi * cxp - sphi * cyp + (x1 + x2) / 2
    cy = sphi * cxp + cphi * cyp + (y1 + y2) / 2

    def ang(ux, uy, vx, vy):
        a = math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
        return a

    t1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dt = ang((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and dt > 0:
        dt -= 2 * math.pi
    elif sweep and dt < 0:
        dt += 2 * math.pi
    n = max(1, math.ceil(abs(dt) / (math.pi / 2) - 1e-9))
    step = dt / n
    k = 4 / 3 * math.tan(step / 4)
    out = []

    def pt(t):
        ct, st = math.cos(t), math.sin(t)
        return (cx + rx * ct * cphi - ry * st * sphi, cy + rx * ct * sphi + ry * st * cphi)

    def deriv(t):
        ct, st = math.cos(t), math.sin(t)
        return (-rx * st * cphi - ry * ct * sphi, -rx * st * sphi + ry * ct * cphi)

    for j in range(n):
        a, b = t1 + j * step, t1 + (j + 1) * step
        p0, p3 = pt(a), pt(b)
        d0, d3 = deriv(a), deriv(b)
        out.append((p0[0] + k * d0[0], p0[1] + k * d0[1], p3[0] - k * d3[0], p3[1] - k * d3[1], *p3))
    ex, ey = out[-1][4], out[-1][5]
    if abs(ex - x2) < 1e-6 and abs(ey - y2) < 1e-6:
        out[-1] = (*out[-1][:4], x2, y2)
    return out


def normalize(d):
    tokens = _TOKEN.findall(d or "")
    segs, i, cmd = [], 0, None
    cur = start = (0.0, 0.0)
    last_c = last_q = None  # reflection points for S / T
    while i < len(tokens):
        t = tokens[i]
        if t.isalpha():
            cmd = t
            i += 1
            if cmd in "Zz":
                segs.append(("Z", ()))
                cur = start
                last_c = last_q = None
                continue
        elif cmd is None:
            raise ValueError(f"path data must start with a command: {d[:40]!r}")
        up, rel = cmd.upper(), cmd.islower()
        n = _ARGS[up]
        if i + n > len(tokens) and up != "A":
            raise ValueError(f"truncated {cmd} command in path {d[:40]!r}")
        if up == "A":
            v, i = _arc_flags(tokens, i)
        else:
            v = [float(x) for x in tokens[i:i + n]]
            i += n
        ox, oy = cur if rel else (0.0, 0.0)
        if up == "M":
            cur = start = (v[0] + ox, v[1] + oy)
            segs.append(("M", cur))
            cmd = "l" if rel else "L"  # implicit lineto after the first pair
            last_c = last_q = None
        elif up in "LHV":
            if up == "H":
                cur = (v[0] + ox, cur[1])
            elif up == "V":
                cur = (cur[0], v[0] + oy)
            else:
                cur = (v[0] + ox, v[1] + oy)
            segs.append(("L", cur))
            last_c = last_q = None
        elif up in "CS":
            if up == "C":
                c1 = (v[0] + ox, v[1] + oy)
                c2, end = (v[2] + ox, v[3] + oy), (v[4] + ox, v[5] + oy)
            else:
                c1 = (2 * cur[0] - last_c[0], 2 * cur[1] - last_c[1]) if last_c else cur
                c2, end = (v[0] + ox, v[1] + oy), (v[2] + ox, v[3] + oy)
            segs.append(("C", (*c1, *c2, *end)))
            last_c, last_q, cur = c2, None, end
        elif up in "QT":
            if up == "Q":
                c, end = (v[0] + ox, v[1] + oy), (v[2] + ox, v[3] + oy)
            else:
                c = (2 * cur[0] - last_q[0], 2 * cur[1] - last_q[1]) if last_q else cur
                end = (v[0] + ox, v[1] + oy)
            segs.append(("Q", (*c, *end)))
            last_q, last_c, cur = c, None, end
        else:  # A
            end = (v[5] + ox, v[6] + oy)
            for c in _arc_to_cubic(cur[0], cur[1], v[0], v[1], v[2], int(v[3]), int(v[4]), *end):
                segs.append(("C", c))
            cur, last_c, last_q = end, None, None
    return segs


def transform(segs, m):
    a, b, c, d, e, f = m
    out = []
    for cmd, v in segs:
        pts = [(a * v[k] + c * v[k + 1] + e, b * v[k] + d * v[k + 1] + f) for k in range(0, len(v), 2)]
        out.append((cmd, tuple(x for p in pts for x in p)))
    return out


def bbox(segs):
    xs = [v[k] for _, v in segs for k in range(0, len(v), 2)]
    ys = [v[k] for _, v in segs for k in range(1, len(v), 2)]
    if not xs:
        return (0, 0, 0, 0)
    return min(xs), min(ys), max(xs), max(ys)


def fmt(segs, scale=1.0, nd=2):
    parts = []
    for cmd, v in segs:
        nums = " ".join(f"{round(x * scale, nd) + 0.0:g}" for x in v)
        parts.append(f"{cmd} {nums}".strip())
    return " ".join(parts)
