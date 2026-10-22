"""Convert a PPTD project to an editable PPTX fully offline (no Kimi service, no browser).

Usage:
  python pptd2pptx.py deck.pptd --output deck.pptx [--force] [--transition fade|none]
  python pptd2pptx.py project_dir            # dir with exactly one .pptd; writes <name>.pptx beside it

Supported: text (rich text p/span/strong/em/br/a/ul/li, letterSpacing, gradient text),
shapes (all OOXML presets + custom M/L/H/V/C/Q/Z paths, rotation, gradient/alpha fills,
borders, shadows), lines (polyline, dash, arrow), images (local or http, cover/contain/crop),
charts (bar/column, stacked, pie/doughnut, data labels), tables (tableStyles, merges),
solid/gradient/image page backgrounds, speaker notes, slide fade transition.
Not supported: element animations, groups, smartart, video/audio, font embedding.
PPTD font families are mapped to locally installed fonts via FONT_MAP; East Asian families follow the
deck's script (--lang auto: Traditional Chinese → Microsoft JhengHei / PMingLiU, Simplified Chinese →
Microsoft YaHei / SimSun, Japanese → Yu Gothic / Yu Mincho, Korean → Malgun Gothic / Batang), so no glyph
falls back to another face.
"""
import argparse
import copy
import hashlib
import math
import re
import subprocess
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


def _ensure(mod, pkg):
    try:
        __import__(mod)
    except ImportError:
        print(f"installing {pkg} ...", file=sys.stderr)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "-q", pkg])


for _mod, _pkg in [("yaml", "PyYAML"), ("lxml", "lxml"), ("pptx", "python-pptx"), ("PIL", "Pillow")]:
    _ensure(_mod, _pkg)

import yaml  # noqa: E402
from lxml import etree  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svgpath  # noqa: E402

PX = 12700  # 1px = 1pt

FONT_MAP = {
    "MiSans": "Microsoft JhengHei",
    "阿里妈妈数黑体": "Microsoft JhengHei",
    "思源宋体": "PMingLiU",
    "Liter": "Segoe UI",
    "QuattrocentoSans": "Segoe UI",
    "Unna": "Georgia",
}
SHAPES = {
    "rect": MSO_SHAPE.RECTANGLE,
    "ellipse": MSO_SHAPE.OVAL,
    "rightArrow": MSO_SHAPE.RIGHT_ARROW,
    "rightBracket": MSO_SHAPE.RIGHT_BRACKET,
    "homePlate": MSO_SHAPE.PENTAGON,
    "chevron": MSO_SHAPE.CHEVRON,
    "roundRect": MSO_SHAPE.ROUNDED_RECTANGLE,
}
def _preset_map():
    from pptx.shapes.autoshape import AutoShapeType
    return {AutoShapeType(s).prst: s for s in MSO_SHAPE}


SHAPES.update({k: v for k, v in _preset_map().items() if k not in SHAPES})
ALIGN = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT,
         "justify": PP_ALIGN.JUSTIFY, "distributed": PP_ALIGN.DISTRIBUTE}
ANCHOR = {"top": MSO_ANCHOR.TOP, "middle": MSO_ANCHOR.MIDDLE, "bottom": MSO_ANCHOR.BOTTOM}


class Deck:
    def __init__(self, manifest):
        self.root = Path(manifest).parent
        self.data = yaml.safe_load(Path(manifest).read_text(encoding="utf-8"))
        theme = self.data.get("theme", {})
        self.colors = theme.get("colors", {})
        self.styles = theme.get("textStyles", {})

    def hex_alpha(self, value):
        """Resolve a PPTD color to (RRGGBB, alpha 0-1 or None)."""
        value = str(value).strip()
        if value.startswith("$"):
            # converter-internal defaults (chart text / axis) are used only when the theme lacks them
            value = self.colors.get(value[1:]) or {"ink": "#2B3A4F", "muted": "#5B6B7F", "rule": "#C9D8EA"}.get(value[1:], "#000000")
        value = value.lstrip("#").upper()
        alpha = int(value[6:8], 16) / 255 if len(value) == 8 else None
        return value[:6], alpha

    def color(self, value):
        if value is None:
            return None
        return RGBColor.from_string(self.hex_alpha(value)[0])

    def text_props(self, content):
        props = {"color": "#000000", "fontSize": 18, "fontFamily": "MiSans", "bold": False,
                 "italic": False, "lineHeight": 1.0}
        style = content.get("style")
        if style:
            props.update(self.styles[style.lstrip("$")])
        for key in ("color", "fontSize", "fontFamily", "bold", "italic", "lineHeight", "letterSpacing", "gradient"):
            if key in content:
                props[key] = content[key]
        return props


EA_FONTS = {                       # East Asian faces per script; FONT_MAP's entries are the zh-TW defaults
    "zh-TW": {},
    "zh-CN": {"MiSans": "Microsoft YaHei", "阿里妈妈数黑体": "Microsoft YaHei", "思源宋体": "SimSun"},
    "ja": {"MiSans": "Yu Gothic", "阿里妈妈数黑体": "Yu Gothic", "思源宋体": "Yu Mincho"},
    "ko": {"MiSans": "Malgun Gothic", "阿里妈妈数黑体": "Malgun Gothic", "思源宋体": "Batang"},
}
SIMPLIFIED = set("们这个来说为发会时对经过还进动产业关见长东车门问间实现应该数据电费区标准设计开报门营业图")
TRADITIONAL = set("們這個來說為發會時對經過還進動產業關見長東車門問間實現應該數據電費區標準設計開報門營業圖")
LANG = {"ea": "zh-TW"}


def detect_lang(texts):
    """zh-TW / zh-CN / ja / ko from the deck's own characters: kana → ja, Hangul → ko; otherwise the side with more of the
    characters that differ between Simplified and Traditional Chinese (ties → zh-TW)."""
    blob = "".join(texts)
    # kana letters only: 「・」 (U+30FB) and 「ー」 (U+30FC) are common separators in Chinese copy too
    if sum(1 for ch in blob if "\u3041" <= ch <= "\u3096" or "\u30a1" <= ch <= "\u30fa") >= 5:
        return "ja"
    if sum(1 for ch in blob if "\uac00" <= ch <= "\ud7a3") >= 5:          # Hangul syllables
        return "ko"
    simp = sum(1 for ch in blob if ch in SIMPLIFIED - TRADITIONAL)
    trad = sum(1 for ch in blob if ch in TRADITIONAL - SIMPLIFIED)
    return "zh-CN" if simp > trad else "zh-TW"


def font_names(family):
    if isinstance(family, dict):
        latin, ea = family.get("latin"), family.get("ea")
    else:
        latin = ea = family
    return FONT_MAP.get(latin, latin), EA_FONTS[LANG["ea"]].get(ea) or FONT_MAP.get(ea, ea)


class RichText(HTMLParser):
    """Parses the PPTD rich-text subset into paragraphs of styled runs."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.paras = []
        self.stack = [{}]
        self.cur = None
        self.in_list = False

    def _new_para(self, pstyle):
        self.cur = {"runs": [], "style": pstyle, "bullet": False}
        self.paras.append(self.cur)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        css = parse_css(attrs.get("style", ""))
        top = dict(self.stack[-1])
        if tag == "p":
            self._new_para(css)
        elif tag == "li":
            self._new_para(css)
            self.cur["bullet"] = True
        elif tag in ("ul", "ol"):
            self.in_list = True
        elif tag == "br":
            if self.cur is None:
                self._new_para({})
            self.cur["runs"].append(("\v", top))
            return
        if tag == "span":
            top.update(css)
        elif tag == "strong":
            top["bold"] = True
        elif tag == "em":
            top["italic"] = True
        elif tag == "a":
            top["href"] = attrs.get("href")
        if tag not in ("br",):
            self.stack.append(top)

    def handle_endtag(self, tag):
        if tag in ("ul", "ol"):
            self.in_list = False
        if tag != "br" and len(self.stack) > 1:
            self.stack.pop()

    def handle_data(self, data):
        if not data.strip("\n"):
            return
        if self.cur is None:
            self._new_para({})
        self.cur["runs"].append((data.replace("\n", ""), dict(self.stack[-1])))


def parse_css(text):
    out = {}
    for part in text.split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip()] = v.strip().strip('"')
    return out


def parse_rich(text):
    text = str(text)
    if "<" not in text:
        lines = [ln for ln in text.split("\n") if ln.strip()] or [text]
        text = "".join(f"<p>{ln}</p>" for ln in lines)
    parser = RichText()
    parser.feed(text)
    return parser.paras


def apply_run_font(run, deck, base, ov):
    font = run.font
    size = ov.get("font-size")
    font.size = Pt(float(str(size).replace("px", "")) if size else float(base["fontSize"]))
    font.bold = bool(ov.get("bold", base.get("bold")))
    font.italic = bool(ov.get("italic", base.get("italic")))
    color = ov.get("color", base.get("color"))
    font.color.rgb = deck.color(color)
    family = ov.get("font-family")
    latin, ea = font_names(family if family else base.get("fontFamily", "MiSans"))
    rpr = run._r.get_or_add_rPr()
    solid = rpr.find(qn("a:solidFill"))
    grad = base.get("gradient")
    if grad and "color" not in ov and solid is not None:
        # text gradient (TextContent.gradient) replaces the solid run fill
        gf = etree.Element(qn("a:gradFill"))
        gs_lst = etree.SubElement(gf, qn("a:gsLst"))
        for stop in grad["stops"]:
            gs = etree.SubElement(gs_lst, qn("a:gs"))
            gs.set("pos", str(int(stop["position"] * 100000)))
            gs.append(color_xml(deck, stop["color"]))
        lin = etree.SubElement(gf, qn("a:lin"))
        lin.set("ang", str(int(grad.get("angle", 0) * 60000)))
        lin.set("scaled", "0")
        solid.addprevious(gf)
        rpr.remove(solid)
    elif solid is not None:
        alpha = deck.hex_alpha(color)[1]
        if alpha is not None and alpha < 0.999:
            etree.SubElement(solid.find(qn("a:srgbClr")), qn("a:alpha")).set("val", str(int(alpha * 100000)))
    spacing = ov.get("letter-spacing", base.get("letterSpacing"))
    if spacing:
        rpr.set("spc", str(int(float(str(spacing).replace("px", "")) * 100)))
    for tagname, face in (("a:latin", latin), ("a:ea", ea), ("a:cs", latin)):
        el = rpr.find(qn(tagname))
        if el is None:
            el = etree.SubElement(rpr, qn(tagname))
        el.set("typeface", face)
    if ov.get("href"):
        run.hyperlink.address = ov["href"]


def add_text(slide, deck, el):
    x, y, w, h = el["bounds"]
    content = el["content"]
    base = deck.text_props(content)
    box = slide.shapes.add_textbox(Emu(int(x * PX)), Emu(int(y * PX)), Emu(int(w * PX)), Emu(int(h * PX)))
    tf = box.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.word_wrap = content.get("wrap", True)
    halign, valign = content.get("align", ["left", "top"])
    tf.vertical_anchor = ANCHOR[valign]
    body = tf._txBody.find(qn("a:bodyPr"))
    for child in list(body):
        body.remove(child)
    if content.get("textDirection") == "vertical":
        body.set("vert", "eaVert")
    paras = parse_rich(content["text"])
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        css = para["style"]
        p.alignment = ALIGN[css.get("text-align", halign)]
        lh = css.get("line-height", base.get("lineHeight", 1.0))
        if isinstance(lh, str) and lh.endswith("px"):
            p.line_spacing = Pt(float(lh[:-2]))
        else:
            p.line_spacing = float(lh) * 0.92 if float(lh) > 1 else 1.0
        if css.get("margin-top"):
            p.space_before = Pt(float(css["margin-top"].replace("px", "")))
        if para["bullet"]:
            ppr = p._p.get_or_add_pPr()
            ppr.set("marL", str(int(18 * PX)))
            ppr.set("indent", str(int(-14 * PX)))
            bu = etree.SubElement(ppr, qn("a:buChar"))
            bu.set("char", "•")
        for txt, ov in para["runs"]:
            if txt == "\v":
                p.add_line_break()
                continue
            run = p.add_run()
            run.text = txt
            apply_run_font(run, deck, base, ov)
    return box


def fill_paragraphs(tf, deck, base, text, halign):
    """Write PPTD rich text into an existing text frame."""
    for i, para in enumerate(parse_rich(text)):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        css = para["style"]
        p.alignment = ALIGN[css.get("text-align", halign)]
        lh = css.get("line-height", base.get("lineHeight", 1.0))
        p.line_spacing = float(lh) * 0.92 if float(lh) > 1 else 1.0
        if css.get("margin-top"):
            p.space_before = Pt(float(css["margin-top"].replace("px", "")))
        if para["bullet"]:
            ppr = p._p.get_or_add_pPr()
            ppr.set("marL", str(int(18 * PX)))
            ppr.set("indent", str(int(-14 * PX)))
            etree.SubElement(ppr, qn("a:buChar")).set("char", "•")
        for txt, ov in para["runs"]:
            if txt == "\v":
                p.add_line_break()
                continue
            run = p.add_run()
            run.text = txt
            apply_run_font(run, deck, base, ov)


def border_sides(spec):
    """Normalize a PPTD BorderSpec into {side: Border|None} for T,R,B,L."""
    if spec is None:
        return {"T": None, "R": None, "B": None, "L": None}
    if isinstance(spec, dict):
        return {k: spec for k in "TRBL"}
    if len(spec) == 2:
        return {"T": spec[0], "B": spec[0], "L": spec[1], "R": spec[1]}
    return dict(zip("TRBL", spec))


def set_cell_border(cell, deck, sides):
    tcpr = cell._tc.get_or_add_tcPr()
    for pos, (side, tag) in enumerate((("L", "a:lnL"), ("R", "a:lnR"), ("T", "a:lnT"), ("B", "a:lnB"))):
        old = tcpr.find(qn(tag))
        if old is not None:
            tcpr.remove(old)
        ln = etree.Element(qn(tag))
        b = sides.get(side)
        if b:
            ln.set("w", str(int(b.get("width", 1) * PX)))
            sf = etree.SubElement(ln, qn("a:solidFill"))
            sf.append(color_xml(deck, b.get("color", "#000000")))
        else:
            ln.set("w", "0")
            etree.SubElement(ln, qn("a:noFill"))
        # schema order: lnL, lnR, lnT, lnB, then the cell fill
        tcpr.insert(pos, ln)


def add_table(slide, deck, el):
    x, y, w, h = el["bounds"]
    rows = el["rows"]
    n_rows, n_cols = len(el["rowHeights"]), len(el["columnWidths"])
    frame = slide.shapes.add_table(n_rows, n_cols, Emu(int(x * PX)), Emu(int(y * PX)),
                                   Emu(int(w * PX)), Emu(int(h * PX)))
    table = frame.table
    tbl_pr = frame._element.graphic.graphicData.tbl.tblPr
    for attr in ("firstRow", "bandRow", "firstCol", "lastRow", "lastCol", "bandCol"):
        tbl_pr.set(attr, "0")
    style_id = tbl_pr.find(qn("a:tableStyleId"))
    if style_id is not None:
        tbl_pr.remove(style_id)
    for j, cw in enumerate(el["columnWidths"]):
        table.columns[j].width = Emu(int(w * cw * PX))
    for i, rh in enumerate(el["rowHeights"]):
        table.rows[i].height = Emu(int(h * rh * PX))
    style = el.get("style") or {}
    if isinstance(style, str):
        style = deck.data.get("theme", {}).get("tableStyles", {}).get(style.lstrip("$"), {})
    occupied = set()
    for i, row in enumerate(rows):
        j = 0
        for cell_def in row:
            while (i, j) in occupied:
                j += 1
            rs, cs = cell_def.get("rowSpan", 1), cell_def.get("colSpan", 1)
            for di in range(rs):
                for dj in range(cs):
                    occupied.add((i + di, j + dj))
            merged = {}
            merged.update(style.get("cellStyle", {}))
            body = style.get("bodyStyles") or []
            if body and 0 < i < n_rows - 1:
                merged.update(body[(i - 1) % len(body)])
            if j == 0:
                merged.update(style.get("firstColumnStyle", {}))
            if j + cs == n_cols:
                merged.update(style.get("lastColumnStyle", {}))
            if i == 0:
                merged.update(style.get("firstRowStyle", {}))
            if i + rs == n_rows:
                merged.update(style.get("lastRowStyle", {}))
            merged.update({k: v for k, v in cell_def.items() if k not in ("text", "rowSpan", "colSpan")})
            cell = table.cell(i, j)
            if rs > 1 or cs > 1:
                cell.merge(table.cell(i + rs - 1, j + cs - 1))
            fill = merged.get("fill")
            if fill and fill.get("type") == "solid":
                cell.fill.solid()
                cell.fill.fore_color.rgb = deck.color(fill["color"])
            else:
                cell.fill.background()
            set_cell_border(cell, deck, border_sides(merged.get("border")))
            cell.margin_left = cell.margin_right = Emu(int(8 * PX))
            cell.margin_top = cell.margin_bottom = Emu(int(4 * PX))
            halign, valign = merged.get("align", ["left", "middle"])
            cell.vertical_anchor = ANCHOR[valign]
            base = deck.text_props({k: v for k, v in merged.items() if k in (
                "color", "fontSize", "fontFamily", "bold", "italic", "lineHeight", "letterSpacing")} | (
                {"style": merged["textStyle"]} if merged.get("textStyle") else {}))
            tf = cell.text_frame
            tf.word_wrap = True
            fill_paragraphs(tf, deck, base, cell_def.get("text", ""), halign)
            j += cs
    return frame


def style_line(line_fmt, deck, border):
    if not border:
        line_fmt.fill.background()
        return
    line_fmt.color.rgb = deck.color(border.get("color", "#000000"))
    line_fmt.width = Pt(border.get("width", 1))
    dash = {"dash": "dash", "dot": "sysDot"}.get(border.get("style"))
    if dash:
        ln = line_fmt._get_or_add_ln()
        prst = etree.SubElement(ln, qn("a:prstDash"))
        prst.set("val", dash)


def color_xml(deck, value, opacity=1.0):
    hex6, alpha = deck.hex_alpha(value)
    clr = etree.Element(qn("a:srgbClr"))
    clr.set("val", hex6)
    a = (alpha if alpha is not None else 1.0) * opacity
    if a < 0.999:
        etree.SubElement(clr, qn("a:alpha")).set("val", str(int(a * 100000)))
    return clr


def apply_fill(shape, deck, fill, opacity=1.0):
    """Write solid (with alpha) or linear/radial gradient fills into spPr."""
    if not fill:
        shape.fill.background()
        return
    shape.fill.solid()  # creates a fill node in the schema-correct position
    sppr = shape._element.spPr
    old = sppr.find(qn("a:solidFill"))
    if fill["type"] == "solid":
        new = etree.Element(qn("a:solidFill"))
        new.append(color_xml(deck, fill["color"], opacity))
    elif fill["type"] == "gradient":
        new = etree.Element(qn("a:gradFill"))
        new.set("rotWithShape", "1")
        gs_lst = etree.SubElement(new, qn("a:gsLst"))
        for stop in fill["stops"]:
            gs = etree.SubElement(gs_lst, qn("a:gs"))
            gs.set("pos", str(int(stop["position"] * 100000)))
            gs.append(color_xml(deck, stop["color"], opacity))
        if fill.get("gradientType") == "radial":
            path = etree.SubElement(new, qn("a:path"))
            path.set("path", "circle")
            rect = etree.SubElement(path, qn("a:fillToRect"))
            for k in ("l", "t", "r", "b"):
                rect.set(k, "50000")
        else:
            lin = etree.SubElement(new, qn("a:lin"))
            lin.set("ang", str(int(fill.get("angle", 0) * 60000)))
            lin.set("scaled", "0")
    else:
        print(f"unsupported fill type {fill['type']}; using no fill")
        shape.fill.background()
        return
    old.addprevious(new)
    sppr.remove(old)


def cover_crop(img_w, img_h, box_w, box_h, crop=None):
    """Return (l, t, r, b) crop fractions that make the image cover the box."""
    crop = crop or {}
    l, t = crop.get("left", 0.0), crop.get("top", 0.0)
    r, b = crop.get("right", 0.0), crop.get("bottom", 0.0)
    src_w, src_h = img_w * (1 - l - r), img_h * (1 - t - b)
    box_ratio, src_ratio = box_w / box_h, src_w / src_h
    if src_ratio > box_ratio:
        extra = (1 - box_ratio / src_ratio) * (1 - l - r)
        l, r = l + extra / 2, r + extra / 2
    else:
        extra = (1 - src_ratio / box_ratio) * (1 - t - b)
        t, b = t + extra / 2, b + extra / 2
    return l, t, r, b


def add_image(slide, deck, el):
    from PIL import Image as PILImage
    x, y, w, h = el["bounds"]
    path = resolve_media(deck, el["src"])
    if path is None:
        print(f"skip image {el['src']} (not found)")
        return None
    with PILImage.open(path) as im:
        iw, ih = im.size
    mode = (el.get("fit") or {}).get("mode", "cover")
    if mode == "contain":
        scale = min(w / iw, h / ih)
        dw, dh = iw * scale, ih * scale
        pic = slide.shapes.add_picture(str(path), Emu(int((x + (w - dw) / 2) * PX)),
                                       Emu(int((y + (h - dh) / 2) * PX)),
                                       Emu(int(dw * PX)), Emu(int(dh * PX)))
    else:
        pic = slide.shapes.add_picture(str(path), Emu(int(x * PX)), Emu(int(y * PX)),
                                       Emu(int(w * PX)), Emu(int(h * PX)))
        if mode == "cover":
            l, t, r, b = cover_crop(iw, ih, w, h, el.get("crop"))
            pic.crop_left, pic.crop_top, pic.crop_right, pic.crop_bottom = l, t, r, b
    if el.get("border"):
        style_line(pic.line, deck, el["border"])
    apply_shadow(pic, deck, el.get("shadow"))
    return pic


def apply_shadow(shape, deck, shadow):
    """Soft outer shadow (PPTD Shadow: blur, color, offset). Without one, also neutralize the theme
    effect reference python-pptx writes into <p:style>: PowerPoint honors the empty <a:effectLst/>,
    but LibreOffice falls back to effectRef idx=2 and draws a shadow the PowerPoint user never sees."""
    style = shape._element.find(qn("p:style"))
    if style is not None:
        ref = style.find(qn("a:effectRef"))
        if ref is not None:
            ref.set("idx", "0")
    if not shadow:
        return
    sppr = shape._element.spPr
    old = sppr.find(qn("a:effectLst"))
    if old is not None:
        sppr.remove(old)
    eff = etree.Element(qn("a:effectLst"))
    sh = etree.SubElement(eff, qn("a:outerShdw"))
    dx, dy = shadow.get("offset", [0, 0])
    sh.set("blurRad", str(int(shadow.get("blur", 8) * PX)))
    sh.set("dist", str(int((dx * dx + dy * dy) ** 0.5 * PX)))
    import math
    sh.set("dir", str(int((math.degrees(math.atan2(dy, dx)) % 360) * 60000)))
    sh.set("algn", "ctr")
    sh.set("rotWithShape", "0")
    sh.append(color_xml(deck, shadow["color"]))
    ln = sppr.find(qn("a:ln"))
    anchor = ln if ln is not None else sppr.find(qn("a:solidFill"))
    if anchor is None:
        anchor = sppr.find(qn("a:gradFill"))
    if anchor is not None:
        anchor.addnext(eff)
    else:
        sppr.append(eff)


def add_custom_shape(slide, deck, el):
    """Custom geometry from a PPTD path (full SVG path syntax: M/L/H/V/C/S/Q/T/A/Z, absolute or relative)
    in viewBox units. Arcs become cubic Béziers; small viewBoxes are scaled up so DrawingML's integer
    path coordinates keep their precision."""
    x, y, w, h = el["bounds"]
    vw, vh = el["viewBox"]
    k = max(1, math.ceil(21600 / max(vw, vh, 1e-9)))
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(int(x * PX)), Emu(int(y * PX)),
                                   Emu(max(int(w * PX), 1)), Emu(max(int(h * PX), 1)))
    sppr = shape._element.spPr
    prst = sppr.find(qn("a:prstGeom"))
    cust = etree.Element(qn("a:custGeom"))
    for tag in ("a:avLst", "a:gdLst", "a:ahLst", "a:cxnLst"):
        etree.SubElement(cust, qn(tag))
    rect = etree.SubElement(cust, qn("a:rect"))
    for kk, v in (("l", "l"), ("t", "t"), ("r", "r"), ("b", "b")):
        rect.set(kk, v)
    path_lst = etree.SubElement(cust, qn("a:pathLst"))
    path = etree.SubElement(path_lst, qn("a:path"))
    path.set("w", str(int(round(vw * k))))
    path.set("h", str(int(round(vh * k))))

    def pts(parent, vals):
        for i in range(0, len(vals), 2):
            p = etree.SubElement(parent, qn("a:pt"))
            p.set("x", str(int(round(vals[i] * k))))
            p.set("y", str(int(round(vals[i + 1] * k))))

    try:
        segs = svgpath.normalize(el["path"])
    except (ValueError, IndexError) as e:
        raise ValueError(f"bad path in {el.get('elementId')}: {e}") from e
    tag = {"M": "a:moveTo", "L": "a:lnTo", "C": "a:cubicBezTo", "Q": "a:quadBezTo"}
    for cmd, vals in segs:
        if cmd == "Z":
            etree.SubElement(path, qn("a:close"))
        else:
            pts(etree.SubElement(path, qn(tag[cmd])), vals)
    prst.addprevious(cust)
    sppr.remove(prst)
    apply_fill(shape, deck, el.get("fill"), el.get("opacity", 1.0))
    style_line(shape.line, deck, el.get("border"))
    shape.shadow.inherit = False
    apply_shadow(shape, deck, el.get("shadow"))
    if el.get("rotation"):
        shape.rotation = el["rotation"]
    apply_flip(shape, el)
    return shape


def apply_flip(shape, el):
    """PPTD flip: [horizontal, vertical] -> a:xfrm flipH / flipV."""
    flip = el.get("flip") or [False, False]
    xfrm = shape._element.spPr.find(qn("a:xfrm"))
    if xfrm is None:
        return
    for on, attr in zip(flip, ("flipH", "flipV")):
        if on:
            xfrm.set(attr, "1")


def add_shape(slide, deck, el):
    if el["shapeName"] == "custom":
        return add_custom_shape(slide, deck, el)
    x, y, w, h = el["bounds"]
    shape = slide.shapes.add_shape(SHAPES[el["shapeName"]], Emu(int(x * PX)), Emu(int(y * PX)),
                                   Emu(max(int(w * PX), 1)), Emu(max(int(h * PX), 1)))
    if el.get("adjustments"):
        for i, v in enumerate(el["adjustments"]):
            shape.adjustments[i] = v / 100000
    apply_fill(shape, deck, el.get("fill"), el.get("opacity", 1.0))
    style_line(shape.line, deck, el.get("border"))
    shape.shadow.inherit = False
    apply_shadow(shape, deck, el.get("shadow"))
    if el.get("rotation"):
        shape.rotation = el["rotation"]
    apply_flip(shape, el)
    return shape


def add_line(slide, deck, el):
    x, y, w, h = el["bounds"]
    vw, vh = el["viewBox"]
    pts = [tuple(map(float, p.split(","))) for p in el["points"].split()]
    sx, sy = w / vw, h / vh
    abs_pts = [((x + px * sx) * PX, (y + py * sy) * PX) for px, py in pts]
    fb = slide.shapes.build_freeform(abs_pts[0][0], abs_pts[0][1], scale=1.0)
    fb.add_line_segments(abs_pts[1:], close=False)
    shape = fb.convert_to_shape()
    shape.fill.background()
    style_line(shape.line, deck, el.get("border"))
    arrow = el.get("arrow") or [None, None]
    ln = shape.line._get_or_add_ln()
    for end, kind in (("a:headEnd", arrow[0]), ("a:tailEnd", arrow[1])):
        if kind:
            e = etree.SubElement(ln, qn(end))
            e.set("type", "triangle")
    shape.shadow.inherit = False
    return shape


CHART_TEXT = 18  # default chart text size = the skill's minimum font (PPTD leaves it to the renderer)
SERIES_CYCLE = ["#1A73E8", "#F08C2E", "#2E9E5B", "#7A5AF8", "#D64545", "#5B6B7F"]


def series_fill(deck, cfg, i):
    """Series color: explicit fill (solid or first gradient stop), else theme primary/blue, else a fixed cycle."""
    f = cfg.get("fill")
    if isinstance(f, dict):
        f = (f.get("stops") or [{}])[0].get("color") or f.get("color")
    if isinstance(f, list):
        f = f[0] if f else None
    if f:
        return deck.color(f)
    if i == 0 and (deck.colors.get("primary") or deck.colors.get("blue")):
        return deck.color(deck.colors.get("primary") or deck.colors.get("blue"))
    return deck.color(SERIES_CYCLE[i % len(SERIES_CYCLE)])


def font_size_of(cfg, default=CHART_TEXT):
    if isinstance(cfg, dict) and cfg.get("fontSize"):
        return cfg["fontSize"]
    return default


def bar_is_horizontal(el, cols, rows):
    """PPTD §5: bars run horizontally when the y axis is the category axis. An explicit axis.type wins;
    otherwise the type is inferred from the encoded column (string -> category, number -> value)."""
    def axis_type(axis):
        cfg = el.get(f"{axis}Axis")
        if isinstance(cfg, dict) and cfg.get("type") in ("category", "value"):
            return cfg["type"]
        key = el["series"][0]["encode"].get(axis)
        if key not in cols:
            return None
        ci = cols.index(key)
        return "category" if any(isinstance(r[ci], str) for r in rows) else "value"
    y_type = axis_type("y")
    return y_type == "category" and axis_type("x") != "category"


def add_chart(slide, deck, el):
    x, y, w, h = el["bounds"]
    cols, rows = el["data"]["cols"], el["data"]["rows"]
    series = el["series"]
    kind = series[0]["type"]
    pos = (Emu(int(x * PX)), Emu(int(y * PX)), Emu(int(w * PX)), Emu(int(h * PX)))
    latin, ea = font_names(el.get("fontFamily", "MiSans"))
    if kind == "pie":
        enc = series[0]["encode"]
        ci, vi = cols.index(enc["category"]), cols.index(enc["value"])
        cd = CategoryChartData()
        cd.categories = [r[ci] for r in rows]
        cd.add_series("s", [r[vi] for r in rows])
        ctype = XL_CHART_TYPE.DOUGHNUT if series[0].get("innerRadius") else XL_CHART_TYPE.PIE
        chart = slide.shapes.add_chart(ctype, *pos, cd).chart
        plot = chart.plots[0]
        for i, point in enumerate(plot.series[0].points):
            point.format.fill.solid()
            fills = series[0].get("fill")
            point.format.fill.fore_color.rgb = (deck.color(fills[i % len(fills)]) if isinstance(fills, list) and fills
                                                else deck.color(SERIES_CYCLE[i % len(SERIES_CYCLE)]))
            point.format.line.color.rgb = deck.color((series[0].get("border") or {}).get("color", "#FFFFFF"))
        if ctype == XL_CHART_TYPE.DOUGHNUT:
            hole = plot._element.find(qn("c:holeSize"))
            if hole is not None:
                hole.set("val", str(int(series[0]["innerRadius"] * 100)))
        legend = el.get("legend")
        chart.has_legend = bool(legend)
        if legend:
            chart.legend.position = XL_LEGEND_POSITION.BOTTOM
            chart.legend.include_in_layout = True
            chart.legend.font.size = Pt(font_size_of(legend))
            chart.legend.font.color.rgb = deck.color(legend.get("color", "$ink"))
            chart.legend.font.name = ea
    else:
        horizontal = bar_is_horizontal(el, cols, rows)
        cat_key = "y" if horizontal else "x"
        val_key = "x" if horizontal else "y"
        cat_col = cols.index(series[0]["encode"][cat_key])
        cd = CategoryChartData()
        cd.categories = [r[cat_col] for r in rows]
        for s in series:
            vc = cols.index(s["encode"][val_key])
            cd.add_series(s.get("name", s["encode"][val_key]), [r[vc] for r in rows])
        stacked = any((el.get("seriesDefaults") or {}).get("bar", {}).get("stack") for _ in [0])
        if horizontal:
            ctype = XL_CHART_TYPE.BAR_STACKED if stacked else XL_CHART_TYPE.BAR_CLUSTERED
        else:
            ctype = XL_CHART_TYPE.COLUMN_STACKED if stacked else XL_CHART_TYPE.COLUMN_CLUSTERED
        chart = slide.shapes.add_chart(ctype, *pos, cd).chart
        plot = chart.plots[0]
        plot.gap_width = int((1 - el.get("barWidth", 0.6)) / max(el.get("barWidth", 0.6), 0.05) * 100)
        if stacked:
            plot.overlap = 100
        elif el.get("barGap") is not None:
            plot.overlap = -int(el["barGap"] * 100)
        for si, (s_cfg, s) in enumerate(zip(series, plot.series)):
            s.format.fill.solid()
            s.format.fill.fore_color.rgb = series_fill(deck, s_cfg, si)
            dl = s_cfg.get("dataLabels")
            if dl and dl.get("show"):
                s.data_labels.show_value = True
                s.data_labels.font.size = Pt(dl.get("fontSize", CHART_TEXT))
                s.data_labels.font.color.rgb = deck.color(dl.get("color", "$ink"))
                s.data_labels.font.name = latin
                if dl.get("numberFormat"):
                    s.data_labels.number_format = dl["numberFormat"]
                    s.data_labels.number_format_is_linked = False
                s.data_labels.position = XL_LABEL_POSITION.INSIDE_END if not horizontal else XL_LABEL_POSITION.CENTER
        cat_cfg = el.get("yAxis" if horizontal else "xAxis") or {}
        val_cfg = el.get("xAxis" if horizontal else "yAxis") or {}
        ca, va = chart.category_axis, chart.value_axis
        ca.reverse_order = bool(cat_cfg.get("reverse"))
        if ca.reverse_order:
            # keep the value axis at the bottom when categories run top-down
            crosses = va._element.find(qn("c:crosses"))
            if crosses is not None:
                crosses.set("val", "max")
        ca.has_major_gridlines = False
        ca.tick_labels.font.size = Pt(font_size_of(cat_cfg.get("label")))
        ca.tick_labels.font.color.rgb = deck.color((cat_cfg.get("label") or {}).get("color", "$ink"))
        ca.tick_labels.font.name = ea
        ca.format.line.color.rgb = deck.color((cat_cfg.get("axisLine") or {}).get("color", "$rule"))
        if val_cfg.get("min") is not None:
            va.minimum_scale = val_cfg["min"]
        if val_cfg.get("max") is not None:
            va.maximum_scale = val_cfg["max"]
        va.visible = val_cfg.get("show", True)
        va.has_major_gridlines = bool(val_cfg.get("gridLine", True))
        if va.has_major_gridlines:
            va.major_gridlines.format.line.color.rgb = deck.color("#E2DCD1")
            va.major_gridlines.format.line.width = Pt(0.5)
        va.tick_labels.font.size = Pt(font_size_of(val_cfg.get("label")))
        va.tick_labels.font.color.rgb = deck.color((val_cfg.get("label") or {}).get("color", "$muted"))
        va.format.line.fill.background()
        chart.has_legend = False
    chart.has_title = False
    chart.font.name = latin
    # font.name only sets the Latin face; add East Asian faces so CJK labels match
    space = chart._chartSpace
    for rpr in space.iter(qn("a:defRPr"), qn("a:rPr")):
        for tag, face in (("a:latin", latin), ("a:ea", ea)):
            el = rpr.find(qn(tag))
            if el is None:
                el = etree.SubElement(rpr, qn(tag))
            el.set("typeface", face)
    return chart


def add_fade(slide):
    sld = slide._element
    trans = etree.SubElement(sld, qn("p:transition"))
    trans.set("spd", "med")
    etree.SubElement(trans, qn("p:fade"))
    # transition must follow clrMapOvr and precede timing/extLst
    sld.remove(trans)
    anchor = sld.find(qn("p:clrMapOvr"))
    if anchor is None:
        anchor = sld.find(qn("p:cSld"))
    anchor.addnext(trans)


def resolve_media(deck, src):
    """Local path for an image src; http(s) sources are cached under <project>/.cache/media."""
    if re.match(r"https?://", src):
        cache = deck.root / ".cache" / "media"
        cache.mkdir(parents=True, exist_ok=True)
        ext = Path(src.split("?")[0]).suffix or ".img"
        path = cache / (hashlib.sha1(src.encode()).hexdigest()[:16] + ext)
        if not path.exists():
            try:
                req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
                path.write_bytes(urllib.request.urlopen(req, timeout=30).read())
            except Exception as exc:  # noqa: BLE001
                print(f"download failed {src}: {exc}")
                return None
        return path
    path = deck.root / src
    return path if path.exists() else None


def add_background(slide, deck, bg, size):
    if not bg:
        return
    kind = bg.get("type")
    if kind == "solid":
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = deck.color(bg["color"])
    elif kind == "gradient":
        add_shape(slide, deck, {"elementType": "shape", "bounds": [0, 0, *size], "shapeName": "rect", "fill": bg})
    elif kind == "image" and bg.get("src"):
        add_image(slide, deck, {"elementType": "image", "bounds": [0, 0, *size], "src": bg["src"], "fit": {"mode": "cover"}})


def convert(manifest, output, transition="fade", lang="auto"):
    deck = Deck(manifest)
    texts = [(deck.root / pp).read_text(encoding="utf-8") for pp in deck.data["pages"]]
    LANG["ea"] = detect_lang(texts) if lang == "auto" else lang
    prs = Presentation()
    w, h = deck.data["size"]
    prs.slide_width, prs.slide_height = Emu(w * PX), Emu(h * PX)
    blank = prs.slide_layouts[6]
    for page_path in deck.data["pages"]:
        page = yaml.safe_load((deck.root / page_path).read_text(encoding="utf-8"))
        slide = prs.slides.add_slide(blank)
        add_background(slide, deck, page.get("background"), (w, h))
        if page.get("notes"):
            slide.notes_slide.notes_text_frame.text = re.sub(r"<[^>]+>", "", str(page["notes"]))
        for el in page["elements"]:
            kind = el["elementType"]
            if kind == "text":
                add_text(slide, deck, el)
            elif kind == "shape":
                add_shape(slide, deck, el)
            elif kind == "line":
                add_line(slide, deck, el)
            elif kind == "chart":
                add_chart(slide, deck, el)
            elif kind == "image":
                add_image(slide, deck, el)
            elif kind == "table":
                add_table(slide, deck, el)
            else:
                print(f"skip unsupported element {kind} on {page_path}")
        if transition == "fade":
            add_fade(slide)
    prs.save(output)
    print(f"saved {output} ({len(prs.slides)} slides, East Asian fonts for {LANG['ea']})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest", help=".pptd file, or a project dir containing exactly one .pptd")
    ap.add_argument("legacy_output", nargs="?", help=argparse.SUPPRESS)
    ap.add_argument("-o", "--output", help="output .pptx (default: <manifest stem>.pptx beside it)")
    ap.add_argument("--force", action="store_true", help="overwrite an existing output file")
    ap.add_argument("--transition", choices=["fade", "none"], default="fade")
    ap.add_argument("--lang", choices=["auto", "zh-TW", "zh-CN", "ja", "ko"], default="auto",
                    help="script for East Asian fonts (auto: detected from the deck's text)")
    a = ap.parse_args()
    src = Path(a.manifest)
    if src.is_dir():
        found = list(src.glob("*.pptd"))
        if len(found) != 1:
            sys.exit(f"expected exactly one .pptd in {src}, found {len(found)}")
        src = found[0]
    out = Path(a.output or a.legacy_output or src.with_suffix(".pptx"))
    # the legacy positional form (pptd2pptx.py deck.pptd out.pptx) keeps its old overwrite behaviour
    if out.exists() and not (a.force or a.legacy_output):
        sys.exit(f"{out} exists; pass --force to overwrite")
    convert(src, out, a.transition, a.lang)


if __name__ == "__main__":
    # Emit UTF-8 regardless of the Windows code page (cp950, cp936…) so callers that capture the
    # output as UTF-8 — agents, tests, CI — can read CJK messages.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    main()
