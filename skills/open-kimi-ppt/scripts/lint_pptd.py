"""Static layout lint for a PPTD project — run before every export / render.

Usage:
  python lint_pptd.py deck.pptd [--min-font 18] [--scale 18,20,26,30] [--strict]

Checks (per element, using the page coordinate system 1px = 1pt):
  bounds     element extends outside the canvas (full-bleed elements starting at 0 are allowed)
  font       any text / table / chart font smaller than --min-font
  overflow   estimated wrapped text height exceeds its box (CJK glyph = 1em, Latin ~0.55em)
  nowrap     wrap:false text whose single line is wider than its box
  orphan     a wrapped paragraph whose last line holds <= 2 characters, or a line starting with
             closing punctuation (，。、；：）」) — reword or resize instead of shrinking the font
  media      referenced local image missing
  container  the estimated glyphs of a text run past the card / panel / bar under the text's centre
  collision  the estimated text of two text boxes overlaps
  icon       `icon` elements (Font Awesome) are skipped by pptd2pptx — they vanish from the PPTX;
             use the SVG icon library instead (scripts/icons.py, reference/icons.md)
  scale      a font size outside the deck's type scale (--scale); the summary lists sizes in use
  table      columnWidths / rowHeights missing, mismatched, or not ratios summing to 1
  cell       table cell text that wraps past its row height
  contrast   text color vs. the fill behind it below WCAG 3:1 for large text (PPTD px = pt: ≥ 18, or bold
             ≥ 14), 4.5:1 below that;
             gradients use their average stop; text over photos and hollow shapes is not judged
  chart      series keys that are not PPTD (color -> fill, label -> dataLabels), unknown encode columns
  plain      a page with no visual element at all — only text and thin rules (no image, chart, table,
             icon or shape at least 12px on both sides); see reference/decoration.md
  sparse     a card (shape with shadow or border, ≥ 160×120, inside the canvas) whose content spans
             less than 70% of its body height (below the title band) — the card reads half empty;
             compose 2-3 element kinds in it (Page.module kind: stack) or shrink it
             (reference/decoration.md §6)
  deco       a decorative shape — hollow with a translucent outline, or a translucent solid fill
             (rings, faint icons, dot patterns) — that sits under text or hangs over a card's edge;
             patterns stay inside their card and clear of copy (reference/decoration.md §9)
Text drawn with a color alpha below 0.5 (watermarks, ghost numerals) is treated as decoration and
skipped by the contrast check.
Estimates are deliberately conservative; confirm flagged items on the rendered slide image.
Exit code 1 with --strict when any error-level issue is found.
"""
import argparse
import math
import re
import sys
from pathlib import Path

import yaml

CLOSE_PUNCT = "，。、；：）」』！？,.;:)!?％%"
PLAIN_MIN_SIDE = 12  # shapes thinner than this are rules / underlines, not visual anchors
CARD_MIN = (160, 120)  # smaller filled boxes are tags, chips and bars, not cards
SPARSE_SPAN = 0.7      # card content must span at least this share of the card body height
TITLE_BAND = 60        # a card title (text in its top 30px) takes the top 60px: band + underline
DECO_ALPHA = 0.6       # shapes fainter than this (outline or fill) are decoration, not content
DECO_MIN = 8           # smaller marks (pattern dots, hairlines) are ignored


def char_w(ch, size):
    if ch == " ":
        return 0.3 * size
    if ord(ch) > 0x2E80 or ch in "，。、；：（）「」『』！？—…":
        return size
    if ch.isupper() or ch.isdigit():
        return 0.62 * size
    return 0.52 * size


def paragraphs(html):
    html = re.sub(r"<br\s*/?>", "\n", html)
    html = re.sub(r"</p>|</li>", "\n", html)
    parts = []
    for raw in re.sub(r"<[^>]+>", "", html).split("\n"):
        t = raw.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        if t.strip():
            parts.append(t)
    return parts or [""]


def wrap(text, size, box_w):
    """Greedy character wrap -> list of lines (approximates PowerPoint CJK wrapping)."""
    lines, cur, w = [], "", 0.0
    for ch in text:
        cw = char_w(ch, size)
        if cur and w + cw > box_w:
            # keep closing punctuation on the previous line (kinsoku) like Office does, but flag it
            lines.append(cur)
            cur, w = ch, cw
        else:
            cur += ch
            w += cw
    lines.append(cur)
    return lines


CONTAINER_SHAPES = {"rect", "roundRect", "round2SameRect", "round1Rect", "snipRect", "snip2SameRect",
                    "flowChartAlternateProcess", "flowChartProcess"}


def _rgb(hexcolor):
    h = str(hexcolor).lstrip("#")
    if len(h) not in (6, 8) or any(c not in "0123456789abcdefABCDEF" for c in h):
        return None, None
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)), (int(h[6:8], 16) / 255 if len(h) == 8 else 1.0)


def _lum(rgb):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(c1, c2):
    a, b = sorted((_lum(c1), _lum(c2)), reverse=True)
    return (a + 0.05) / (b + 0.05)


HOLLOW = {"donut", "arc", "blockArc", "frame", "noSmoking", "line", "custom"}  # center is not covered by fill


def overlap(a, b):
    """Overlap (w, h) of two (x, y, w, h) rectangles."""
    return (min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]), min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))


def inline_sizes(html):
    return [float(m) for m in re.findall(r"font-size:\s*([\d.]+)px", html)]


class Linter:
    def __init__(self, manifest, min_font, scale=None):
        self.manifest = Path(manifest)
        self.root = self.manifest.parent
        self.deck = yaml.safe_load(self.manifest.read_text(encoding="utf-8"))
        self.W, self.H = self.deck.get("size", [960, 540])
        self.styles = (self.deck.get("theme") or {}).get("textStyles", {}) or {}
        self.tstyles = (self.deck.get("theme") or {}).get("tableStyles", {}) or {}
        self.min_font = min_font
        self.scale = set(scale or [])
        self.sizes = set()
        self.issues = []

    def add(self, level, page, el, kind, msg):
        self.issues.append((level, page, el.get("elementId", "?") if el else "-", kind, msg))

    def style_val(self, content, key, default=None):
        if key in content:
            return content[key]
        st = str(content.get("style", "")).lstrip("$")
        return (self.styles.get(st) or {}).get(key, default)

    def ink(self, el):
        """Estimated rectangle actually covered by the text of a text element."""
        c = el.get("content") or {}
        text = str(c.get("text", ""))
        size = float(self.style_val(c, "fontSize", 18))
        lh = float(self.style_val(c, "lineHeight", 1.2))
        x, y, w, h = el["bounds"]
        lines = []
        for p in paragraphs(text):
            lines += [p] if c.get("wrap") is False else wrap(p, size, w - 4)
        if not any(ln.strip() for ln in lines):
            return None
        iw = min(max(sum(char_w(ch, size) for ch in ln) for ln in lines) + 4, w if c.get("wrap") is not False else 10 ** 6)
        ih = len(lines) * size * lh
        ha, va = (list(c.get("align") or self.style_val(c, "align", None) or ["left", "top"]) + ["top"])[:2]
        ix = x + {"center": (w - iw) / 2, "right": w - iw}.get(ha, 0)
        iy = y + {"middle": (h - ih) / 2, "bottom": h - ih}.get(va, 0)
        return ix, iy, iw, ih

    def check_text(self, page, el):
        c = el.get("content") or {}
        text = str(c.get("text", ""))
        size = float(self.style_val(c, "fontSize", 18))
        lh = float(self.style_val(c, "lineHeight", 1.2))
        x, y, w, h = el["bounds"]
        for s in [size] + inline_sizes(text):
            self.sizes.add(s)
            if s < self.min_font:
                self.add("error", page, el, "font", f"{s:g}px < {self.min_font}px: {text[:30]!r}")
            elif self.scale and s not in self.scale:
                self.add("warn", page, el, "scale", f"{s:g}px not in type scale {sorted(self.scale)}: {text[:30]!r}")
        inner_w = w - 4  # PPTD text boxes have ~2px side insets
        if c.get("wrap") is False:
            for p in paragraphs(text):
                need = sum(char_w(ch, size) for ch in p)
                if need > inner_w * 1.04:
                    self.add("warn", page, el, "nowrap", f"line needs ~{need:.0f}px > box {w}px: {p[:30]!r}")
            return
        total = 0
        for p in paragraphs(text):
            lines = wrap(p, size, inner_w)
            total += len(lines)
            if len(lines) > 1:
                tail = lines[-1].strip()
                if len(tail) <= 2:
                    self.add("warn", page, el, "orphan", f"last line {tail!r} of {p[:24]!r}…")
                for ln in lines[1:]:
                    if ln and ln[0] in CLOSE_PUNCT:
                        self.add("warn", page, el, "orphan", f"line starts with {ln[0]!r}: {p[:24]!r}…")
        need_h = total * size * lh
        if need_h > h * 1.08 + 2:
            self.add("warn", page, el, "overflow", f"~{total} lines need {need_h:.0f}px > box {h}px: {text[:30]!r}")

    def check_bounds(self, page, el):
        b = el.get("bounds")
        if not b or len(b) != 4:
            return
        x, y, w, h = b
        tol = 1.5
        if x < -tol or y < -tol or x + w > self.W + tol or y + h > self.H + tol:
            self.add("error", page, el, "bounds", f"[{x}, {y}, {w}, {h}] outside {self.W}x{self.H}")

    def check_table(self, page, el):
        rows = el.get("rows") or []
        for key, n in (("columnWidths", max((len(r) for r in rows), default=0)), ("rowHeights", len(rows))):
            v = el.get(key)
            if not isinstance(v, list) or not v:
                self.add("error", page, el, "table", f"missing {key} (ratios of the bounds summing to 1)")
            elif len(v) != n:
                self.add("error", page, el, "table", f"{key} has {len(v)} items for {n} {'columns' if key == 'columnWidths' else 'rows'}")
            elif any(x < 0 or x > 1 for x in v) or abs(sum(v) - 1) > 0.02:
                self.add("error", page, el, "table", f"{key} must be ratios in [0, 1] summing to 1 (got sum {sum(v):g}) — not px")
        st = (self.tstyles.get(str(el.get("style", "")).lstrip("$")) or {}).get("cellStyle", {})
        size = st.get("fontSize")
        if size and size < self.min_font:
            self.add("error", page, el, "font", f"table cellStyle {size}px < {self.min_font}px")
        cw, rh = el.get("columnWidths"), el.get("rowHeights")
        if not (isinstance(cw, list) and isinstance(rh, list) and len(rh) == len(rows) and abs(sum(cw) - 1) <= 0.02):
            return
        x, y, w, h = el["bounds"]
        size, lh = float(size or 18), float(st.get("lineHeight", 1.2))
        for i, row in enumerate(rows):
            for j, cell in enumerate(row[:len(cw)]):
                text = str(cell.get("text", "") if isinstance(cell, dict) else cell)
                fs = float((cell.get("fontSize") if isinstance(cell, dict) else None) or size)
                lines = sum(len(wrap(p, fs * 1.06, w * cw[j] - 16)) for p in paragraphs(text))  # 6% margin: fallback CJK fonts run wide
                need = lines * fs * lh + 8  # cell margins 4 + 4
                if need > h * rh[i] + 2:
                    self.add("warn", page, el, "cell", f"row {i + 1} col {j + 1}: ~{lines} lines need {need:.0f}px > row {h * rh[i]:.0f}px: {text[:24]!r}")

    SERIES_KEYS = {
        "bar": {"type", "encode", "name", "xAxisIndex", "yAxisIndex", "stack", "symbol", "fill", "border", "dataLabels"},
        "line": {"type", "encode", "name", "xAxisIndex", "yAxisIndex", "dataLabels", "smooth", "lineStyle", "width",
                 "marker", "nullHandling", "lineColor"},
        "area": {"type", "encode", "name", "xAxisIndex", "yAxisIndex", "dataLabels", "smooth", "lineStyle", "width",
                 "marker", "nullHandling", "lineColor", "stack", "fill"},
        "pie": {"type", "encode", "innerRadius", "startAngle", "fill", "border", "dataLabels"},
    }
    SERIES_HINTS = {"color": "fill (bar/pie/area) or lineColor (line)", "label": "dataLabels: {show: true}",
                    "labels": "dataLabels: {show: true}", "data": "chart-level data: {cols, rows} + encode"}

    def check_chart_series(self, page, el):
        cols = set(((el.get("data") or {}).get("cols")) or [])
        for s in el.get("series") or []:
            allowed = self.SERIES_KEYS.get(s.get("type"))
            if allowed:
                for k in s:
                    if k not in allowed:
                        hint = self.SERIES_HINTS.get(k)
                        self.add("warn", page, el, "chart", f"{s['type']} series key {k!r} is not PPTD" + (f" — use {hint}" if hint else ""))
            for ch, col in (s.get("encode") or {}).items():
                if cols and col not in cols:
                    self.add("error", page, el, "chart", f"encode.{ch} = {col!r} is not a data column {sorted(cols)}")

    def check_chart(self, page, el):
        self.check_chart_series(page, el)
        def walk(o, path=""):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == "fontSize" and isinstance(v, (int, float)) and v < self.min_font:
                        self.add("error", page, el, "font", f"chart {path}.{k}={v}")
                    walk(v, f"{path}.{k}")
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    walk(v, f"{path}[{i}]")
        walk(el)
        rows = ((el.get("data") or {}).get("rows")) or []
        x, y, w, h = el["bounds"]
        horizontal = any((s.get("encode") or {}).get("y") == (el["data"]["cols"][0]) for s in el.get("series", []))
        span = h if horizontal else w
        if rows and span / len(rows) < self.min_font * 1.5:
            self.add("warn", page, el, "density", f"{len(rows)} categories in {span}px — Office will skip axis labels")

    def glyphs(self, el, ink):
        """The ink without the line's leading: half of (lineHeight − 1) × size above the first line and below the
        last is empty, so two boxes whose leading overlaps (axis ticks meeting at a chart's origin) do not collide."""
        c = el.get("content") or {}
        size = float(self.style_val(c, "fontSize", 18))
        lead = max(float(self.style_val(c, "lineHeight", 1.2)) - 1, 0) * size / 2
        x, y, w, h = ink
        return x, y + lead, w, max(h - 2 * lead, 1)

    @staticmethod
    def wash(el):
        """A gradient that fades to fully clear with no border is a sheen or wash laid over a surface — it
        holds nothing, so it is never a container (glass highlights, area fills)."""
        fill = el.get("fill") or {}
        return (fill.get("type") == "gradient" and not el.get("border")
                and any(len(s_.get("color", "")) == 9 and s_["color"].upper().endswith("00") for s_ in fill.get("stops", [])))

    def inset(self, b):
        """Cards and panels sit inside the canvas; full-bleed bands, washes and backgrounds are not containers."""
        x, y, w, h = b
        return x > 1 and y > 1 and x + w < self.W - 1 and y + h < self.H - 1

    def check_layout(self, page, els):
        """Text vs. the container it sits on, and text vs. text."""
        texts = [(i, el) for i, el in enumerate(els) if el.get("elementType") == "text" and el.get("bounds")]
        boxes = [(i, el) for i, el in enumerate(els)
                 if el.get("elementType") == "shape" and el.get("shapeName") in CONTAINER_SHAPES and el.get("bounds")
                 and (el.get("fill") or el.get("border")) and el["bounds"][2] >= 60 and el["bounds"][3] >= 30
                 and self.inset(el["bounds"]) and not self.wash(el)]
        inks = {}
        for i, el in texts:
            ink = self.ink(el)
            if ink is None:
                continue
            inks[i] = ink
            x, y, w, h = el["bounds"]
            # the container is the smallest box drawn *below* the text that holds the centre of its ink — a small
            # label straddling two adjacent fields (a number in a dot on a quadrant line) belongs to the field its
            # glyphs sit in; when no box holds the centre, fall back to the text box's top-left corner
            cx_, cy_ = ink[0] + ink[2] / 2, ink[1] + ink[3] / 2
            below = [b for j, b in boxes if j < i]
            holders = [b for b in below if b["bounds"][0] - 1 <= cx_ <= b["bounds"][0] + b["bounds"][2] + 1
                       and b["bounds"][1] - 1 <= cy_ <= b["bounds"][1] + b["bounds"][3] + 1] or                       [b for b in below if b["bounds"][0] - 1 <= x + 2 <= b["bounds"][0] + b["bounds"][2]
                       and b["bounds"][1] - 1 <= y + 2 <= b["bounds"][1] + b["bounds"][3]]
            if not holders:
                continue
            box = min(holders, key=lambda b: b["bounds"][2] * b["bounds"][3])
            bx, by, bw, bh = box["bounds"]
            # overflow is measured on the glyphs, not the text box: a box wider than its bar or cell with the
            # number centred inside is fine; wrapped text is estimated at the box width, so long lines still count
            ix, iy, iw, ih = self.glyphs(el, ink)
            over_x = ix + iw - (bx + bw)
            over_y = iy + ih - (by + bh)
            if over_x > 2 or over_y > 2:
                self.add("warn", page, el, "container",
                         f"text runs {max(over_x, over_y):.0f}px past container {box.get('elementId', '?')}: {str(el['content'].get('text', ''))[:30]!r}")
        keys = sorted(inks)
        glyphs = {k: self.glyphs(els[k], inks[k]) for k in keys}
        for a in range(len(keys)):
            for b in keys[a + 1:]:
                ow, oh = overlap(glyphs[keys[a]], glyphs[b])
                if ow > 4 and oh > 4:
                    ea, eb = els[keys[a]], els[b]
                    self.add("warn", page, eb, "collision",
                             f"text overlaps {ea.get('elementId', '?')} by {ow:.0f}×{oh:.0f}px: {str(eb['content'].get('text', ''))[:24]!r}")

    def color_of(self, value):
        """PPTD color -> (rgb, alpha); resolves $theme references."""
        if value is None:
            return None, None
        v = str(value)
        if v.startswith("$"):
            v = ((self.deck.get("theme") or {}).get("colors") or {}).get(v[1:], "")
        return _rgb(v)

    def fill_colors(self, fill):
        """Solid -> [rgb]; gradient -> the stop colors; with their alphas."""
        if not isinstance(fill, dict):
            return []
        if fill.get("type") == "solid":
            return [self.color_of(fill.get("color"))]
        if fill.get("type") == "gradient":  # text sits mid-gradient: judge against the average stop
            stops = [self.color_of(st.get("color")) for st in fill.get("stops") or []]
            stops = [(rgb, a) for rgb, a in stops if rgb]
            if not stops:
                return []
            avg = tuple(round(sum(rgb[k] for rgb, _ in stops) / len(stops)) for k in range(3))
            return [(avg, min(a for _, a in stops))]
        return []

    def check_contrast(self, page, page_bg, els):
        """Text color vs. the opaque fill drawn beneath the text's center (WCAG: 4.5:1, 3:1 for large text)."""
        img_bg = isinstance(page_bg, dict) and page_bg.get("type") == "image"
        base = None if img_bg else (self.fill_colors(page_bg) or [((255, 255, 255), 1.0)])  # unknown behind photos
        for i, el in enumerate(els):
            if el.get("elementType") != "text" or not el.get("bounds"):
                continue
            c = el.get("content") or {}
            fg, alpha = self.color_of(c.get("color"))
            if alpha is not None and alpha < 0.5:  # ghost / watermark text is decoration, not copy
                continue
            ink = self.ink(el) if fg else None
            if not ink:
                continue
            cx, cy = ink[0] + ink[2] / 2, ink[1] + ink[3] / 2
            under = base
            for j in range(i - 1, -1, -1):
                o = els[j]
                if not o.get("bounds") or o.get("elementType") not in ("shape", "image") or o.get("shapeName") in HOLLOW:
                    continue
                x, y, w, h = o["bounds"]
                if not (x <= cx <= x + w and y <= cy <= y + h):
                    continue
                if o["elementType"] == "image" or (o.get("fill") or {}).get("type") == "image":
                    under = None  # text over a photo: can't judge from the file
                    break
                cols = [(rgb, a) for rgb, a in self.fill_colors(o.get("fill")) if rgb]
                if cols and x <= cx <= x + w and y <= cy <= y + h and min(a for _, a in cols) * float(o.get("opacity", 1)) >= 0.6:
                    under = cols
                    break
            if not under:
                continue
            size = float(self.style_val(c, "fontSize", 18))
            bold = "<strong>" in str(c.get("text", "")) or c.get("bold")
            need = 3.0 if size >= 18 or (bold and size >= 14) else 4.5  # PPTD px = pt; WCAG large text = 18pt / 14pt bold
            worst = min(contrast(fg, rgb) for rgb, _ in under if rgb)
            if worst < need:
                self.add("warn", page, el, "contrast", f"{worst:.1f}:1 < {need:g}:1 against what is behind it: {str(c.get('text', ''))[:24]!r}")
        for el in els:  # table header row: style text color vs. style fill
            if el.get("elementType") != "table":
                continue
            st = self.tstyles.get(str(el.get("style", "")).lstrip("$")) or {}
            fr = dict(st.get("cellStyle") or {}, **(st.get("firstRowStyle") or {}))
            fg, _ = self.color_of(fr.get("color"))
            bgs = [rgb for rgb, _ in self.fill_colors(fr.get("fill")) if rgb]
            if fg and bgs and min(contrast(fg, b) for b in bgs) < 3.0:
                self.add("warn", page, el, "contrast", f"table header text {min(contrast(fg, b) for b in bgs):.1f}:1 < 3:1 on its fill")

    def check_plain(self, page, els):
        """A page built only from text and hairlines reads as a document, not a slide."""
        def visual(el):
            kind = el.get("elementType")
            if kind in ("image", "chart", "table"):
                return True
            if kind == "shape" and el.get("bounds"):
                w, h = el["bounds"][2:]
                return min(w, h) >= PLAIN_MIN_SIDE  # rules, underlines and arrows don't count
            return False
        if els and not any(visual(el) for el in els):
            self.add("warn", page, None, "plain", "only text and rules — add a visual anchor (chart, photo, icon, "
                     "big number on a shape, diagram) or block decoration; see reference/decoration.md")

    def check_cards(self, page, els):
        """Cards whose content leaves much of the card empty — the gap between a designed card and a
        box around one element."""
        for i, card in enumerate(els):
            if card.get("elementType") != "shape" or card.get("shapeName") not in CONTAINER_SHAPES:
                continue
            if not card.get("bounds") or not card.get("fill") or not (card.get("shadow") or card.get("border")):
                continue
            cx, cy, cw, ch = card["bounds"]
            if cw < CARD_MIN[0] or ch < CARD_MIN[1] or not self.inset(card["bounds"]):
                continue
            inside = [e for e in els[i + 1:] if e.get("bounds") and e.get("elementType") != "line"
                      and e["bounds"][0] >= cx - 2 and e["bounds"][1] >= cy - 2
                      and e["bounds"][0] + e["bounds"][2] <= cx + cw + 2 and e["bounds"][1] + e["bounds"][3] <= cy + ch + 2]
            titled = any(e["elementType"] == "text" and e["bounds"][1] < cy + 30 and e["bounds"][3] <= 44 for e in inside)
            top, bottom = (cy + TITLE_BAND if titled else cy + 12), cy + ch - 12
            if bottom - top < 100:
                continue
            spans = []
            for e in inside:
                box = self.ink(e) if e["elementType"] == "text" else e["bounds"]
                if not box or (e["elementType"] == "shape" and min(box[2:]) < 6):
                    continue
                y0, y1 = max(box[1], top), min(box[1] + box[3], bottom)
                # the title sits wholly inside the title band; anything reaching into the body counts —
                # a caption on the card's first line must not hide the hero number that starts under it
                if y1 > y0 and (not titled or box[1] >= top - 4 or box[1] + box[3] > top + 8):
                    spans.append((y0, y1))
            if not spans:
                self.add("warn", page, card, "sparse", "empty card — fill it or remove it")
                continue
            share = (max(b for _, b in spans) - min(a for a, _ in spans)) / (bottom - top)
            if share < SPARSE_SPAN:
                self.add("warn", page, card, "sparse",
                         f"content spans {share:.0%} of the card body — compose 2-3 element kinds in it "
                         "(Page.module kind: stack) or shrink the card; see reference/decoration.md §6")

    def deco_shapes(self, els):
        """Decorative shapes: hollow with a faint outline, or a faint solid fill; not full-bleed."""
        out = []
        for i, el in enumerate(els):
            if el.get("elementType") != "shape" or not el.get("bounds"):
                continue
            x, y, w, h = el["bounds"]
            if min(w, h) < DECO_MIN or w * h > 0.4 * self.W * self.H:
                continue
            fill, border = el.get("fill"), el.get("border") or {}
            if not fill:
                _, a = self.color_of(border.get("color"))
                if a is not None and a < DECO_ALPHA:
                    out.append((i, el))
            elif fill.get("type") == "solid":
                _, a = self.color_of(fill.get("color"))
                if a is not None and a < DECO_ALPHA:
                    out.append((i, el))
        return out

    def check_decoration(self, page, els):
        """Patterns stay inside their card and clear of copy."""
        decos = self.deco_shapes(els)
        if not decos:
            return
        inks = [(e, self.ink(e)) for e in els if e.get("elementType") == "text" and e.get("bounds")]
        cards = [e["bounds"] for e in els if e.get("elementType") == "shape" and e.get("shapeName") in CONTAINER_SHAPES
                 and e.get("bounds") and e.get("fill") and (e.get("shadow") or e.get("border"))
                 and e["bounds"][2] >= CARD_MIN[0] and e["bounds"][3] >= CARD_MIN[1] and self.inset(e["bounds"])]
        for _, d in decos:
            box = d["bounds"]
            for t_el, ink in inks:
                if not ink:
                    continue
                _, a = self.color_of((t_el.get("content") or {}).get("color"))
                if a is not None and a < 0.5:
                    continue                                    # ghost text is decoration too
                ow, oh = overlap(ink, box)
                if ow > 6 and oh > 6:
                    self.add("warn", page, d, "deco",
                             f"decorative shape sits under text {str(t_el['content'].get('text', ''))[:20]!r} — move the "
                             "pattern clear of copy (reference/decoration.md §9)")
                    break
            else:
                x, y, w, h = box
                for cx, cy, cw, ch in cards:
                    ow, oh = overlap(box, (cx, cy, cw, ch))
                    inside = x >= cx - 1 and y >= cy - 1 and x + w <= cx + cw + 1 and y + h <= cy + ch + 1
                    if ow > 2 and oh > 2 and not inside:
                        self.add("warn", page, d, "deco", "decorative shape hangs over a card edge — keep patterns inside their card")
                        break

    def check_media(self, page, el):
        src = el.get("src", "")
        if src and not re.match(r"https?://|data:", src) and not (self.root / src).exists():
            self.add("error", page, el, "media", f"missing {src}")

    def run(self):
        for rel in self.deck.get("pages", []):
            path = self.root / rel
            if not path.exists():
                self.add("error", rel, None, "page", "page file missing")
                continue
            page = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            name = Path(rel).stem
            els = page.get("elements", []) or []
            self.check_layout(name, els)
            self.check_contrast(name, page.get("background"), els)
            if (page.get("background") or {}).get("type") != "image":
                self.check_plain(name, els)
            self.check_cards(name, els)
            self.check_decoration(name, els)
            for el in els:
                self.check_bounds(name, el)
                kind = el.get("elementType")
                if kind == "text":
                    self.check_text(name, el)
                elif kind == "table":
                    self.check_table(name, el)
                elif kind == "chart":
                    self.check_chart(name, el)
                elif kind == "image":
                    self.check_media(name, el)
                elif kind == "icon":
                    self.add("warn", name, el, "icon", f"{el.get('iconName', '?')} is skipped by pptd2pptx — use icons.py / page.svg (reference/icons.md)")
        return self.issues


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest")
    ap.add_argument("--min-font", type=float, default=18)
    ap.add_argument("--scale", help="comma-separated font sizes allowed in this deck, e.g. 18,20,26,30,54")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    scale = [float(v) for v in a.scale.split(",")] if a.scale else None
    linter = Linter(a.manifest, a.min_font, scale)
    issues = linter.run()
    for level, page, eid, kind, msg in issues:
        print(f"{level:5} {page:<18} {eid:<8} {kind:<9} {msg}")
    print(f"\nfont sizes in use: {', '.join(f'{s:g}' for s in sorted(linter.sizes))}")
    errors = sum(1 for i in issues if i[0] == "error")
    print(f"\n{errors} error(s), {len(issues) - errors} warning(s)")
    sys.exit(1 if (a.strict and errors) else 0)


if __name__ == "__main__":
    # Emit UTF-8 regardless of the Windows code page (cp950, cp936…) so callers that capture the
    # output as UTF-8 — agents, tests, CI — can read CJK messages.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    main()
