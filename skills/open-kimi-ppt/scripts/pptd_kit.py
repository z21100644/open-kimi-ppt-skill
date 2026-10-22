"""pptd_kit — Python component library for writing PPTD pages programmatically.

Why: hand-writing dozens of .page YAML files drifts (inconsistent offsets, colors, font sizes).
A small generator script built on these components keeps every page on one grid and one
palette, and makes a whole-deck redesign a one-line change. Default theme = "Bright Blue Bento"
(reference/design_system/academic/bright-blue-bento-briefing/design.md).

API index (signature + one line per helper, no need to read this file):
    python <skill>/scripts/pptd_kit.py            # everything, plus THEMES / LAYOUTS / SEMANTIC_ICONS
    python <skill>/scripts/pptd_kit.py takeaway   # only helpers whose name or doc mentions "takeaway"

Minimal use:
    import sys; sys.path.insert(0, r"<skill>/scripts")
    from pptd_kit import Kit, b, c, unit
    kit = Kit("deck_dir", total=11, footer="Deck title｜Report type",
              chapters=["研究背景", "文獻探討", "研究設計", "初步發現", "限制結論"])
    p = kit.page()
    p.header(1, "結論式標題：一句話說出本頁判斷", "對應論文第一章｜補充說明")
    p.card(kit.L, kit.T, 436, 322, "卡片標題", "star5")
    p.stat(56, 190, 250, "1,280", " 萬度", "年用電量")
    p.takeaway("本頁一句話重點")
    p.footer(2)
    p.save("02_purpose.page")
    kit.write_manifest("deck.pptd", "Deck title")   # pages = every page saved, in save order

Every helper takes absolute page coordinates (960×540, 1px = 1pt). Text helpers default to the
theme minimum font size (18) so reading decks never fall below it.

Bento planning grid (shared with scripts/storyboard.py): the body box is a 12-column × 6-row grid
with a 16px gutter. kit.area(col, row, colspan, rowspan) -> (x, y, w, h); kit.layout("split-2-1", n)
-> list of areas for a named bento layout (see LAYOUTS / reference/storyboard.md). Pass tall=True
for pages without the 重點 bar (body extends to y=494).

Templates: Kit(..., theme="bright-blue" | "ink-ivory" | "sage-mist" | "ios-glass" | "clear") picks a preset from THEMES —
colors plus the look beyond color (card radius / band / border / shadow, header and takeaway style,
gradients or solid marks, icon discs, title font, cover recipe). A dict theme overrides keys of
BRIGHT_BLUE, or of THEMES[theme["base"]] when it names a base. Build scripts that only use kit
components switch template with that one argument.

Material (reference/decoration.md §10): theme "ios-glass" swaps the material, not the layout — a
blurred-colour wallpaper (generated into media/ by Kit), top-lit white glass cards with a white rim,
a tinted-glass feature card with a specular highlight, app-icon tiles, tinted capsules, a large-title
header with a page control, a glass takeaway capsule, and a glass cover / closing (photo in a glass
frame with concentric corners via Kit.rounded, a floating widget, a grouped recap list).

Art direction "clear" (清透, reference/decoration.md §10–11): one rule set over every element — rounded
rectangles only (circles are data), radii in px (radius_px), solid-tile headings and numbered tiles
(marker "tile"), one solid divider, a pale-tint feature card with dark copy (feature_style "tint") and
the hero band as the one solid surface, same-hue tonal transitions on surfaces / tiles / numbers, a
safe-area header and a footer that names each page's source (Page.footer(n, source=…)).

Polish (reference/decoration.md §9): one focus per page — `hero: true` on a module makes its number
the page's largest and shrinks every other stat; module kind "hero" is a full-width focus band;
Page.breather draws a photo + giant-number breather page; Page.closing echoes the cover recipe;
icons may be named by meaning (SEMANTIC_ICONS: "carbon", "money", "power"…) so one icon keeps one
meaning across the deck.

Card craft (reference/decoration.md §6): a card holds a composed mini-layout, not one element —
Page.module kind "stack" splits a card into 2-3 parts (dashed rules between); feature=True turns one
module per page into the gradient feature card (content drawn in light colors); rank / dumbbell draw
grouped rankings and before→after comparisons from shapes; chip, tag and arc are finishing details.

Speaker notes: set page.notes = "…" before page.save(); it is written as the page's PPTD `notes` and
pptd2pptx.py carries it into the PowerPoint notes pane (live decks: one talk script per page).
Reveals: p.takeaway(text, reveal="第 1 題答案：B") adds a green check capsule at the band's right end, so quiz
answers appear in the same place on every page.

Readable charts (reference/decoration.md §12): free_spot(cx, cy, r, w, h, taken, bounds) returns the
first free box for a point label (centred above, nudged, right, left, below) so names never overlap dots,
other labels or captions; hit(a, b) tests two (x, y, w, h) boxes.

Decoration without cards (reference/decoration.md): band (edge-anchored tint strip), watermark (ghost
numeral at 12% alpha), photo (image + color rule + caption), motif (corner dots / rings / leaf) and
pictogram (unit chart), alongside icon, numdot, pill, stat, ring, bar and segments.
"""
import re
from pathlib import Path

import yaml

BRIGHT_BLUE = {
    "navy": "#0B1F3A", "text": "#2B3A4F", "gray": "#5B6B7F",
    "blue": "#1A73E8", "cyan": "#00B2FF", "sky": "#DCEAFB", "bg": "#E8EFF7", "white": "#FFFFFF", "on_accent": "#FFFFFF",
    "line": "#C9D8EA", "edge": "#CFDDEE", "band": "#EEF4FC", "insight": "#D3E4FA", "mist": "#DCEBFF",
    "green": "#2E9E5B", "green2": "#7BC96F", "orange": "#F08C2E", "orange2": "#FFB25B",
    "teal": "#14A39A", "teal2": "#4FD1C5",      # a fourth category (e.g. the second group), never carbon
    "feature": "#1A5FD6", "feature2": "#1E9BF0", "on_feature": "#E4F1FF",  # feature card: deeper than blue/cyan so white text reads
    "shadow": {"blur": 14, "color": "#1E3A6038", "offset": [0, 4]},
    "font": {"latin": "Liter", "ea": "MiSans"},
    "min_font": 18,
    # look beyond color — what turns a palette into a template (see THEMES)
    "title_font": None,        # {"latin", "ea"} for titles and card titles; None = the body font
    "accent": None,            # decorative rules and ticks; None = blue
    "card_radius": 4000,       # roundRect adjustment
    "card_band": True,         # tinted title band across the card top
    "card_border": 1,          # px; 0 = none
    "card_shadow": True,
    "card_rule": "short",      # under a card title: short accent bar | hairline (full width + accent dash)
    "icon_style": "disc",      # disc (glyph on a tinted disc) | glyph (bare glyph)
    "header": "bar",           # bar (gradient accent bar + numbered progress dots) | rule (hairline + small dots)
    "takeaway": "bar",         # bar (tinted bar + filled label) | rule (hairline + accent tick)
    "gradients": True,         # gradient key numbers and data marks; False = solid
    "cover": "photo-fade",     # photo-fade | frame | wash — the cover recipe of Page.cover / Page.closing
    "feature_pattern": "rings",  # rings (small concentric rings in the feature card's title corner) | highlight | None
    "material": "flat",        # flat | glass (top-lit translucent-white cards, white rim, tinted-glass feature card)
    "pill": "outline",         # outline (colored border) | tint (the tone at ~14% with deepened text, iOS tinted button)
    "wallpaper": None,         # glass: blurred colour blobs [(cx, cy, r, (r, g, b), alpha)] on a 1920×1080 ground
    "wallpaper_cover": None,   # the livelier variant behind the cover and closing
    "radius_px": None,         # card / feature corner radius in px (one radius at every card size); None = card_radius
    "feature_style": "solid",  # solid (light copy on the feature fill) | tint (pale gradient, dark copy; hero band stays solid)
    "feature_tint": None,      # tint stops, top to bottom
    "marker": "dot",           # numbered markers: dot (circle) | tile (rounded square, gradient, contrast-guarded)
    "divider": "dash",         # hdash: dash | solid (1 px in the line colour)
    "header_top": 18,          # large header: caption top; title +24, subtitle +66, page control +8
    "title_px": None,          # large header title size; None = title_size + 2
    "dot_off": None,           # large header: inactive page-control colour; None = white with a soft shadow
    "takeaway_y": 462,         # capsule takeaway top
    "footer_y": 508,           # footer line top
    "source_color": None,      # footer source line colour (Page.footer(n, source=…)); None = gray
}

# Elegant, restrained: ivory paper, ink-blue type, serif titles, hairline cards, gold rules, no
# gradients. Defences, formal reports, policy briefings.
INK_IVORY = dict(
    BRIGHT_BLUE,
    navy="#14213D", text="#2B2F36", gray="#696D74", blue="#1F3A5F", cyan="#3C6491", sky="#E8E2D4",
    bg="#F5F1E8", white="#FFFDF9", on_accent="#FFFFFF", line="#D6CDBB", edge="#E0D8C8", band="#F8F4EC",
    insight="#ECE5D6", mist="#EEE8DB", green="#4A7A5C", green2="#7FA48A", orange="#A8553A", orange2="#C58262",
    teal="#2F6F73", teal2="#6FA3A5",
    feature="#17294A", feature2="#24406A", on_feature="#EDE6D6",
    shadow={"blur": 10, "color": "#3B2F1A14", "offset": [0, 2]},
    title_font={"latin": "Unna", "ea": "思源宋体"}, accent="#A88748",
    card_radius=1200, card_band=False, card_border=1, card_shadow=False, card_rule="hairline",
    icon_style="glyph", header="rule", takeaway="rule", gradients=False, cover="frame", feature_pattern=None,
)

# Calm, soft: misty sage canvas, rounded borderless cards on soft shadows, sage primary with
# clay and teal tones. Sustainability, education, health, community reports.
SAGE_MIST = dict(
    BRIGHT_BLUE,
    navy="#1F332C", text="#33443E", gray="#5F6F68", blue="#4A846C", cyan="#86B9A2", sky="#DDEBE3",
    bg="#ECF1ED", white="#FFFFFF", on_accent="#FFFFFF", line="#C5D5CB", edge="#D6E2DA", band="#F2F7F4",
    insight="#DCEAE1", mist="#E2EDE7", green="#2F7684", green2="#7DB4BE", orange="#C97A47", orange2="#E4A97C",
    teal="#6B7FB0", teal2="#A3B3D9",
    feature="#3A6F5B", feature2="#5A977F", on_feature="#E4F1EA",
    shadow={"blur": 18, "color": "#1F3A2E24", "offset": [0, 6]},
    card_radius=9000, card_band=False, card_border=0, card_shadow=True, card_rule="short",
    icon_style="disc", header="bar", takeaway="bar", gradients=True, cover="wash",
)

# Calm glass after iOS 27's Liquid Glass (less transparency, more legibility): a soft blurred-colour
# wallpaper, near-opaque top-lit white glass cards with a white rim, app-icon tiles, tinted capsules,
# a large-title header with a page control, a glass photo frame on the cover. Public talks, product
# and tech briefings, modern research sharing. Same palette and layouts as bright-blue — only the
# material changes (reference/decoration.md §10).
WALL_BLOBS = [(1780, 40, 560, (110, 175, 255), 170), (80, 1060, 620, (130, 222, 206), 150),
              (1500, 1100, 560, (176, 190, 255), 150), (980, 1120, 360, (150, 214, 255), 110),
              (420, 40, 520, (246, 249, 255), 200)]          # light behind the large title
WALL_COVER_BLOBS = [(1900, 80, 760, (90, 160, 255), 200), (60, 1100, 700, (120, 220, 200), 180),
                    (1300, 1120, 600, (170, 180, 255), 170), (980, -80, 420, (160, 210, 255), 130),
                    (380, 120, 560, (248, 250, 255), 220)]
IOS_GLASS = dict(
    BRIGHT_BLUE,
    bg="#F0F4FB", edge="#FFFFFF",
    shadow={"blur": 26, "color": "#1E3A6026", "offset": [0, 8]},
    card_radius=6500, card_band=False, card_border=1.2, card_shadow=True, card_rule="none",
    icon_style="tile", header="large", takeaway="capsule", cover="glass", feature_pattern="highlight",
    material="glass", pill="tint", wallpaper=WALL_BLOBS, wallpaper_cover=WALL_COVER_BLOBS,
)

def faint(blobs, k):
    """The same wallpaper at k of its strength."""
    return [(cx, cy, r, col, round(a * k)) for cx, cy, r, col, a in blobs]


# 清透 Clear — one art direction over bright-blue's graphics: calm glass on a soft blurred ground,
# restraint (one solid surface per deck — the hero band; non-focus data gray) and same-hue tonal
# transitions (a 10–18% lightness step, light from the top-left). Flat paint reads cheap; cross-hue
# or high-contrast gradients read loud. Public talks and research sharing that should feel premium.
CLEAR = dict(
    IOS_GLASS,
    navy="#111827", text="#374151", gray="#6B7280", bg="#F6F8FC",
    blue="#1A73E8", cyan="#4D9BF2", green="#2E9E5B", green2="#4DB57A", orange="#F08C2E", orange2="#F6A85A",
    teal="#9CA3AF", teal2="#C3C9D2", feature="#1A5FD6", feature2="#3D8DF0", on_feature="#E4F1FF",
    sky="#EEF2F7", line="#E3E9F2", band="#F3F4F6", insight="#EFF4FF",
    shadow={"blur": 18, "color": "#0F2A4D24", "offset": [0, 4]},
    radius_px=16, feature_style="tint", feature_tint=[(0, "#F3F8FF"), (1, "#E2EDFC")], marker="tile",
    divider="solid", header_top=24, title_px=30, dot_off="#D1D5DB", takeaway_y=456, footer_y=502,
    source_color="#737D90", wallpaper=faint(WALL_BLOBS, 0.8), wallpaper_cover=faint(WALL_COVER_BLOBS, 0.9),
)

THEMES = {"bright-blue": BRIGHT_BLUE, "ink-ivory": INK_IVORY, "sage-mist": SAGE_MIST, "ios-glass": IOS_GLASS,
          "clear": CLEAR}

# One icon, one meaning, deck-wide (reference/decoration.md §9). Name icons by meaning in storyboards
# and build scripts; the kit resolves them to library icons.
SEMANTIC_ICONS = {
    "money": "tabler-filled/coin", "carbon": "tabler-filled/flame", "power": "tabler-filled/bolt",
    "green": "tabler-filled/leaf", "benchmark": "tabler-filled/award", "compare": "tabler-filled/scale",
    "assets": "tabler-filled/stack-2", "people": "tabler-filled/user", "time": "tabler-filled/calendar",
    "analysis": "tabler-filled/chart-dots", "limit": "tabler-filled/alert-triangle", "next": "tabler-filled/flag",
    "law": "tabler-filled/file-text", "data": "tabler-filled/database", "growth": "tabler-filled/chart-area-line",
    "efficiency": "tabler-filled/gauge", "question": "tabler-filled/help-circle", "calc": "tabler-filled/calculator",
    "check": "tabler-filled/circle-check",
}
CANVAS = (960, 540)
GLASS_PHOTO = (488, 36, 436, 468, 10)   # glass cover / closing: the photo frame (x, y, w, h, inset)
WHITE = "#FFFFFF"


# Named bento layouts on the 12×6 body grid: area = (col, row, colspan, rowspan).
# Module order in a storyboard maps 1:1 to the areas listed here; the first area is the largest
# (or the visual center for center-main) — put the page's main module there.
# The scenario guides forbid evenly divided compositions unless nothing else works, so the
# asymmetric layouts are the default vocabulary; EVEN_LAYOUTS need a stated reason.
LAYOUTS = {
    "single":       [(0, 0, 12, 6)],
    "split-2-1":    [(0, 0, 8, 6), (8, 0, 4, 6)],
    "split-1-2":    [(4, 0, 8, 6), (0, 0, 4, 6)],
    "split-7-5":    [(0, 0, 7, 6), (7, 0, 5, 6)],
    "split-5-7":    [(5, 0, 7, 6), (0, 0, 5, 6)],
    "main-stack":   [(0, 0, 8, 6), (8, 0, 4, 3), (8, 3, 4, 3)],
    "stack-main":   [(4, 0, 8, 6), (0, 0, 4, 3), (0, 3, 4, 3)],
    "three-uneven": [(0, 0, 5, 6), (5, 0, 4, 6), (9, 0, 3, 6)],
    "center-main":  [(3, 0, 6, 6), (0, 0, 3, 6), (9, 0, 3, 6)],
    "hero-split":   [(0, 0, 12, 3), (0, 3, 7, 3), (7, 3, 5, 3)],
    "mixed":        [(0, 0, 6, 6), (6, 0, 6, 3), (6, 3, 3, 3), (9, 3, 3, 3)],
    "mosaic":       [(0, 0, 5, 6), (5, 0, 4, 3), (5, 3, 4, 3), (9, 0, 3, 6)],
    # evenly divided — only when the content is genuinely parallel and nothing else works
    "split":        [(0, 0, 6, 6), (6, 0, 6, 6)],
    "three":        [(0, 0, 4, 6), (4, 0, 4, 6), (8, 0, 4, 6)],
    "quad":         [(0, 0, 6, 3), (6, 0, 6, 3), (0, 3, 6, 3), (6, 3, 6, 3)],
}
EVEN_LAYOUTS = {"split", "three", "quad", "hero-top"}


def is_even(areas):
    """True when every module has the same size (an evenly divided composition)."""
    return len(areas) >= 2 and len({(a[2], a[3]) for a in areas}) == 1


def hero_top(n_below):
    """Wide hero on top (rows 0-2) + n_below (2-4) equal modules underneath (evenly divided below)."""
    if not 2 <= n_below <= 4:
        raise ValueError("hero-top needs 2-4 modules below the hero")
    span = 12 // n_below
    return [(0, 0, 12, 3)] + [(i * span, 3, span, 3) for i in range(n_below)]


def layout_areas(name, n=None):
    """Areas for a named layout; n = number of modules (needed for hero-top)."""
    if name == "hero-top":
        if n is None:
            raise ValueError("hero-top needs the module count")
        return hero_top(n - 1)
    if name not in LAYOUTS:
        raise KeyError(f"unknown layout {name!r}; known: {', '.join(sorted(LAYOUTS))}, hero-top, custom")
    return list(LAYOUTS[name])


GRID_COLS, GRID_ROWS, GRID_GUTTER, TALL_BOTTOM = 12, 6, 16, 494


def grid_area(col, row, colspan, rowspan, margins=(36, 924), body=(124, 446)):
    """Grid cell -> (x, y, w, h) on the body box. Edges are rounded independently so gutters stay exact."""
    (left, right), (top, bottom), g = margins, body, GRID_GUTTER
    cw = (right - left - (GRID_COLS - 1) * g) / GRID_COLS
    rh = (bottom - top - (GRID_ROWS - 1) * g) / GRID_ROWS
    x0, x1 = round(left + col * (cw + g)), round(left + (col + colspan) * (cw + g) - g)
    y0, y1 = round(top + row * (rh + g)), round(top + (row + rowspan) * (rh + g) - g)
    return x0, y0, x1 - x0, y1 - y0


def module_body(x, y, w, h, frame="region", has_title=True):
    """Body box of a module drawn by Page.region / Page.card — shared with storyboard.py so the
    planning checks measure copy exactly where Page.module will put it."""
    if frame == "card":
        return (x + 20, y + 72, w - 40, h - 92) if has_title else (x + 20, y + 20, w - 40, h - 40)
    return (x, y + 60, w, h - 60) if has_title else (x, y + 16, w, h - 16)


LIST_INDENT = 40  # Page.module list rows: number dot column


def b(s):
    """Rich text: bold."""
    return f"<strong>{s}</strong>"


def c(s, color):
    """Rich text: a coloured span."""
    return f'<span style="color:{color};">{s}</span>'


def unit(s, color="#5B6B7F", size=18):
    """Small unit suffix after a big number: f"{num}{unit(' 億元')}"."""
    return f'<span style="font-size:{size}px; color:{color};">{s}</span>'


TYPE_STEPS = (36, 30, 26, 22, 20)  # auto-fit sizes for short copy, largest first
OPEN_PUNCT = "（「『(［【《〈"         # never left at the end of a line
WORD_END, WORD_START = re.compile(r"[A-Za-z0-9.,%–-]$"), re.compile(r"[A-Za-z0-9.,%–-]")  # a word or number split


def _plain(s):
    return re.sub(r"<[^>]+>", "", re.sub(r"<br\s*/?>|</p>", "\n", str(s)))


def text_width(s, size):
    """Estimated single-line width in px at `size` (the estimate lint uses)."""
    from lint_pptd import char_w
    return sum(char_w(ch, size) for ch in _plain(s))


def wrap_lines(s, size, w):
    """Estimated wrapped lines of a copy string in a box w wide — the same estimate lint_pptd uses."""
    from lint_pptd import wrap
    return [ln for para in _plain(s).split("\n") if para.strip() for ln in wrap(para, size, w - 4)] or [""]


def fit_size(items, w, h, floor, lh=1.3, steps=TYPE_STEPS, keep_lines=False):
    """Largest size from `steps` (never below `floor`) whose wrapped copy fits w × h with clean
    breaks: no orphan last line of 1-2 characters, no line ending on an opening bracket, no line
    starting with closing punctuation and no number or Latin word split across lines (PowerPoint
    moves the whole word, so the estimate would be wrong there). keep_lines: only grow while no item wraps onto more lines
    than at `floor` (short parallel items stay one line each). Returns (size, line count)."""
    from lint_pptd import CLOSE_PUNCT
    base = [len(wrap_lines(it, floor, w)) for it in items]
    for s in steps:
        if s < floor:
            break
        paras = [wrap_lines(it, s, w) for it in items]
        n = sum(len(p_) for p_ in paras)
        bad = any((len(p_) > 1 and len(p_[-1].strip()) <= 2)
                  or any(ln.rstrip()[-1:] in OPEN_PUNCT for ln in p_[:-1])
                  or any(ln[:1] in CLOSE_PUNCT for ln in p_[1:])
                  or any(WORD_END.search(a_) and WORD_START.match(z_) for a_, z_ in zip(p_, p_[1:])) for p_ in paras)
        if keep_lines and any(len(p_) > n0 for p_, n0 in zip(paras, base)):
            continue
        if n * s * lh <= h and not bad:
            return s, n
    return floor, sum(len(wrap_lines(it, floor, w)) for it in items)


def number_format(nums):
    """One format for every label in a chart: thousands separators, and as many decimals as the most
    precise value (0.41 and 1.0 -> "0.41" / "1.00"; 32.5 and 15 -> "32.5" / "15.0")."""
    places = decimals(nums)
    return "#,##0" + ("." + "0" * places if places else "")


def decimals(nums):
    """Decimal places of the most precise value (max 3) — one count for every label in a set."""
    return min(max((len(f"{float(v):g}".partition(".")[2]) for v in nums if "e" not in f"{float(v):g}"), default=0), 3)


def light_theme(th):
    """Colors for content drawn on the gradient feature card: white ink, soft secondary text,
    translucent tracks and rules."""
    w = th["white"]
    return dict(th, navy=w, text=w, gray=th["on_feature"], blue=w, cyan=w, green=w, orange=w,
                sky="#FFFFFF40", line="#FFFFFF66", edge="#FFFFFF59", band="#FFFFFF1F")


def share(v):
    """0.72, "72%" or 72 -> 0.72."""
    v = float(str(v).rstrip("%"))
    return v / 100 if v > 1 else v


def _lum(hexcolor):
    h = str(hexcolor).lstrip("#")[:6]
    def ch(c):
        c = int(c, 16) / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(h[0:2]) + 0.7152 * ch(h[2:4]) + 0.0722 * ch(h[4:6])


def contrast_ratio(a, b):
    """WCAG contrast ratio of two hex colours."""
    la, lb = _lum(a), _lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def readable_on(bg, light="#FFFFFF", dark="#0B1F3A"):
    """Text color for a fill (hex, gradient stop list or Fill dict): whichever of light/dark contrasts more."""
    if isinstance(bg, dict):
        bg = [(0, st["color"]) for st in bg.get("stops", [])] or bg.get("color")
    if isinstance(bg, (list, tuple)):
        cols = [c for _, c in bg]
        avg = [round(sum(int(c.lstrip("#")[k:k + 2], 16) for c in cols) / len(cols)) for k in (0, 2, 4)]
        bg = "#" + "".join(f"{v:02X}" for v in avg)
    lb = _lum(bg)
    ratio = lambda c: (max(_lum(c), lb) + 0.05) / (min(_lum(c), lb) + 0.05)
    return light if ratio(light) >= ratio(dark) else dark


def tint(color, k):
    """color at strength k over white — an opaque tint (translucent fills read as decoration to lint)."""
    r, g, b_ = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{round(255 + (v - 255) * k):02X}" for v in (r, g, b_))


def deepen(color, bg, ratio=4.5):
    """Darken color until it reaches `ratio` contrast on bg (tinted-capsule text, filled capsules)."""
    r, g, b_ = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    out = color[:7]
    while contrast_ratio(out, bg) < ratio and max(r, g, b_) > 8:
        r, g, b_ = (int(v * 0.9) for v in (r, g, b_))
        out = f"#{r:02X}{g:02X}{b_:02X}"
    return out


def wallpaper(path, blobs, base, size=(1920, 1080), blur=200):
    """Soft blurred colour fields (the glass material's ground). Each blob is drawn on a layer that is
    transparent *in the blob's own hue*: blurring a layer of transparent black pulls every edge towards
    gray and dulls the whole ground."""
    from PIL import Image, ImageDraw, ImageFilter
    im = Image.new("RGB", size, base)
    for cx, cy, r, col, a in blobs:
        layer = Image.new("RGBA", size, tuple(col) + (0,))
        ImageDraw.Draw(layer).ellipse((cx - r, cy - r, cx + r, cy + r), fill=tuple(col) + (a,))
        im = Image.alpha_composite(im.convert("RGBA"), layer.filter(ImageFilter.GaussianBlur(blur))).convert("RGB")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    im.save(path, quality=92)


GLASS_G = [(0, "#FFFFFFF5"), (1, "#FFFFFFDC")]          # top-lit glass: 96% → 86% white


def gfill(stops, angle=0):
    """Gradient fill dict from [(position, colour), …] at `angle` degrees."""
    return {"type": "gradient", "gradientType": "linear", "angle": angle,
            "stops": [{"position": p, "color": col} for p, col in stops]}


class Kit:
    COLS, ROWS, GUTTER, TALL_BOTTOM = GRID_COLS, GRID_ROWS, GRID_GUTTER, TALL_BOTTOM

    def __init__(self, out_dir, total, footer="", chapters=(), theme=None, margins=(36, 924), body=(124, 446)):
        self.out = Path(out_dir)
        (self.out / "pages").mkdir(parents=True, exist_ok=True)
        if isinstance(theme, str):
            base, theme = THEMES[theme], None
        else:
            base = THEMES[theme["base"]] if theme and theme.get("base") else BRIGHT_BLUE
        self.th = dict(base, **{k: v for k, v in (theme or {}).items() if k != "base"})
        if theme and "blue" in theme and "feature" not in theme:  # custom palette: feature card follows its primary
            self.th["feature"], self.th["feature2"] = theme["blue"], theme.get("cyan", theme["blue"])
        self.total, self.footer_text, self.chapters = total, footer, list(chapters)
        self.L, self.R = margins
        self.T, self.B = body
        t = self.th
        self.BLUE_G = [(0, t["cyan"]), (1, t["blue"])]
        self.GREEN_G = [(0, t["green2"]), (1, t["green"])]
        self.ORANGE_G = [(0, t["orange2"]), (1, t["orange"])]
        self.FEATURE_G = [(0, t["feature2"]), (1, t["feature"])]
        self.GRAY_G = [(0, t["line"]), (1, t["gray"])]
        self.TEAL_G = [(0, t["teal2"]), (1, t["teal"])]
        self.saved = []
        if t["wallpaper"]:
            wallpaper(self.out / "media" / "wall.jpg", t["wallpaper"], t["bg"])
            wallpaper(self.out / "media" / "wall-cover.jpg", t["wallpaper_cover"] or t["wallpaper"], t["bg"])

    def page(self, bg=None):
        """A new Page on the theme's background (bg overrides it)."""
        p = Page(self, bg or self.th["bg"])
        if self.th["wallpaper"] and bg is None:
            p.img(0, 0, *CANVAS, "wall.jpg")
        return p

    def rounded(self, src, w, h, r, focus=(0.5, 0.5), corners="all", shade=None):
        """Bake media/<src> cover-cropped to w×h with corner radius r (px) into a PNG next to it and
        return its name — the converter has no picture corner radius. focus = the crop centre (0-1);
        corners="top" rounds only the top two (a photo heading a card); shade=[(pos, alpha)…] bakes a
        vertical navy wash (0 = top), so no square overlay pokes past the rounding."""
        from PIL import Image, ImageDraw
        media = self.out / "media"
        name = f"{Path(src).stem}-r{int(w)}x{int(h)}{'-top' if corners == 'top' else ''}{'-wash' if shade else ''}.png"
        im = Image.open(self.out / src if "/" in src else media / src).convert("RGB")   # "x.jpg" or "media/x.jpg"
        W, H = int(w * 2), int(h * 2)
        k = max(W / im.width, H / im.height)
        im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
        left, top = round((im.width - W) * focus[0]), round((im.height - H) * focus[1])
        im = im.crop((left, top, left + W, top + H))
        if shade:
            a = Image.new("L", (1, H))
            for yy in range(H):
                t_ = yy / max(H - 1, 1)
                for (p0, a0), (p1, a1) in zip(shade, shade[1:]):
                    if p0 <= t_ <= p1:
                        a.putpixel((0, yy), round(255 * (a0 + (a1 - a0) * (t_ - p0) / max(p1 - p0, 1e-6))))
            im = Image.composite(Image.new("RGB", (W, H), (11, 31, 58)), im, a.resize((W, H)))
        mask = Image.new("L", (W * 4, H * 4), 0)
        d_ = ImageDraw.Draw(mask)
        d_.rounded_rectangle((0, 0, W * 4 - 1, H * 4 - 1), r * 8, fill=255)
        if corners == "top":
            d_.rectangle((0, H * 2, W * 4 - 1, H * 4 - 1), fill=255)
        im.putalpha(mask.resize((W, H), Image.LANCZOS))
        im.save(media / name)
        return name
    def area(self, col, row, colspan, rowspan, tall=False):
        """(x, y, w, h) of a 12 × 6 bento-grid area; tall=True extends the body to y=494 (no takeaway bar)."""
        return grid_area(col, row, colspan, rowspan, (self.L, self.R), (self.T, self.TALL_BOTTOM if tall else self.B))

    def layout(self, name, n=None, tall=False):
        """Areas of a named bento layout (LAYOUTS) for n modules."""
        return [self.area(*a, tall=tall) for a in layout_areas(name, n)]

    def write_manifest(self, name, title, pages=None):
        """Write the .pptd manifest: theme, text styles and every saved page in save order."""
        t = self.th
        data = {
            "version": "v2", "title": title, "size": [960, 540],
            "theme": {
                "colors": {k: v for k, v in t.items() if isinstance(v, str)},
                "textStyles": {
                    "body": {"fontFamily": t["font"], "fontSize": t["min_font"], "color": t["text"], "lineHeight": 1.3},
                    "title": {"fontFamily": t["title_font"] or t["font"], "fontSize": 26, "bold": True, "color": t["navy"], "lineHeight": 1.15},
                },
                "tableStyles": {"data": {
                    "cellStyle": {"fontFamily": t["font"], "fontSize": t["min_font"], "color": t["text"], "lineHeight": 1.2,
                                  "align": ["left", "middle"],
                                  "border": [None, None, {"style": "solid", "width": 1, "color": t["edge"]}, None]},
                    "firstRowStyle": {"fill": {"type": "solid", "color": t["blue"]}, "color": t["on_accent"], "bold": True, "border": None},
                }},
            },
            "pages": [f"pages/{p}" for p in (pages or self.saved)],
        }
        (self.out / name).write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=10000), encoding="utf-8")


def hit(a, b):
    """True when two (x, y, w, h) boxes overlap."""
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def free_spot(cx, cy, r, w, h, taken, bounds, gap=4):
    """Where a w×h label for the point (cx, cy) of radius r can go without touching anything in `taken`
    (a list of boxes: dots, captions, labels already placed) and inside bounds (x0, y0, x1, y1).
    Tries centred above, nudged ±8, right, left, below; returns the box (x, y, w, h) or None.
    Append the returned box to `taken` before placing the next label (left to right works best)."""
    cands = [(-w / 2 + s, -r - gap - h) for s in (0, 8, -8)] + [(r + gap, -h / 2), (-w - r - gap, -h / 2), (-w / 2, r + gap)]
    x0, y0, x1, y1 = bounds
    for dx, dy in cands:
        box = (cx + dx, cy + dy, w, h)
        if box[0] >= x0 and box[1] >= y0 and box[0] + w <= x1 and box[1] + h <= y1 and not any(hit(box, t) for t in taken):
            return box
    return None


class Page:
    def __init__(self, kit, bg):
        self.k, self.th, self.els, self.bg, self.n = kit, kit.th, [], bg, 0
        self.light = False  # True while drawing inside a feature card (light_theme colors, no gradients)
        self.focus = False  # True when a module on this page is the hero: other stats shrink
        self.notes = None   # speaker notes (plain text) — saved as the page's PPTD `notes`

    # ---------- primitives ----------
    def _id(self, p):
        self.n += 1
        return f"{p}{self.n}"

    def add(self, el):
        """Append a raw PPTD element dict and return it (for anything the helpers do not cover)."""
        self.els.append(el)
        return el

    def text(self, x, y, w, h, text, size=None, color=None, **kw):
        """Text box; size defaults to the theme's min font; rich text via b() / c() / <p>; **kw adds PPTD content keys (align, wrap, lineHeight, bold, letterSpacing…); a trailing 。 is dropped."""
        if text.endswith("。"):  # no full stop on slide copy
            text = text[:-1]
        content = {"style": "$body", "text": text, "fontSize": size or self.th["min_font"], "color": color or self.th["text"]}
        content.update(kw)
        return self.add({"elementId": self._id("t"), "elementType": "text", "bounds": [x, y, w, h], "content": content})

    def gtext(self, x, y, w, h, text, size, stops=None, **kw):
        """Bold gradient text — for key numbers only (plain white on a feature card)."""
        if self.light:
            return self.text(x, y, w, h, text, size, color=self.th["navy"], bold=True, **kw)
        stops = stops or self.k.BLUE_G
        if not self.th["gradients"]:
            return self.text(x, y, w, h, text, size, color=stops[-1][1], bold=True, **kw)
        return self.text(x, y, w, h, text, size, color=self.th["blue"], bold=True, gradient=gfill(stops), **kw)

    def grad(self, stops=None, angle=0):
        """Gradient fill for data marks; solid white on a feature card, solid (the deeper stop) in
        templates without gradients."""
        if self.light:
            return {"type": "solid", "color": self.th["white"]}
        stops = stops or self.k.BLUE_G
        return gfill(stops, angle) if self.th["gradients"] else {"type": "solid", "color": stops[-1][1]}

    def accent(self):
        """The template's accent colour (its blue when no accent is set)."""
        return self.th["accent"] or self.th["blue"]

    def title_text(self, x, y, w, h, text, size, color, **kw):
        """Bold title text in the template's title font."""
        if self.th["title_font"]:
            kw["fontFamily"] = self.th["title_font"]
        return self.text(x, y, w, h, b(text), size, color, **kw)

    def shape(self, x, y, w, h, fill, shape="rect", **kw):
        """Preset shape with a PPTD fill dict (gfill(...) for gradients); **kw: adjustments, border, shadow, rotation…"""
        el = {"elementId": self._id("s"), "elementType": "shape", "bounds": [x, y, w, h], "shapeName": shape, "fill": fill}
        el.update(kw)
        return self.add(el)

    def solid(self, x, y, w, h, color, shape="rect", **kw):
        """shape() with a solid colour fill ('#RRGGBB' or '#RRGGBBAA')."""
        return self.shape(x, y, w, h, {"type": "solid", "color": color}, shape, **kw)

    def img(self, x, y, w, h, src, crop=None, **kw):
        """Image from media/ (bare file name) or a path / URL, cover-fit; crop and **kw pass through."""
        el = {"elementId": self._id("i"), "elementType": "image", "bounds": [x, y, w, h], "src": f"media/{src}" if "/" not in src else src,
              "fit": {"mode": "cover"}}
        if crop:
            el["crop"] = crop
        el.update(kw)
        return self.add(el)

    def line(self, x, y, w, h, points, color=None, width=1.5, dash=False, arrow=False):
        """Polyline in its own box: points 'x,y x,y…' in local coordinates; dash and an end arrow optional."""
        el = {"elementId": self._id("l"), "elementType": "line", "bounds": [x, y, max(w, 1), max(h, 1)],
              "viewBox": [max(w, 1), max(h, 1)], "points": points, "curve": "sharp",
              "border": {"style": "dash" if dash else "solid", "width": width, "color": color or self.th["line"]}}
        if arrow:
            el["arrow"] = [None, "arrow"]
        return self.add(el)

    def svg(self, x, y, w, h, ref, fill=None, keep_ratio=True):
        """Library icon ("tabler-filled/bulb") or any .svg file -> editable custom shapes.

        fill: color string or Fill dict (e.g. gfill(kit.BLUE_G, 45)); None keeps the SVG's own colors.
        Returns the added elements so callers can tweak them (rotation, opacity, shadow…)."""
        from icons import shape_elements
        ref = SEMANTIC_ICONS.get(ref, ref)
        if ref.endswith(".svg") and not Path(ref).is_absolute() and (self.k.out / ref).exists():
            ref = str(self.k.out / ref)  # project-relative, e.g. "media/icons/edited.svg"
        els = shape_elements(ref, x, y, w, h, fill, keep_ratio, element_id=self._id("v"))
        for el in els:
            self.add(el)
        return els

    def hdash(self, x, y, w, color=None):
        """The template's divider: a dashed hairline (a 1 px solid rule in "clear")."""
        if self.th["divider"] == "solid":            # clear: one divider, 1 px solid
            self.solid(x, y, w, 1, color or self.th["line"])
            return
        self.line(x, y, w, 1, f"0,0.5 {w},0.5", color=color, dash=True)
    def header(self, chap, title, sub, title_size=26, label=None):
        """Chapter label + conclusion title + source line on the left, chapter progress on the right.
        chap=None (with label="開始之前" / "結論" / "附錄"…): same anchor, no progress.
        Template style "bar": gradient accent bar + numbered dots; "rule": accent dash, hairline under
        the header, small dots."""
        t, k = self.th, self.k
        label = label or (f"{chap:02d}｜{k.chapters[chap - 1]}" if chap and k.chapters else f"{chap:02d}" if chap else "")
        if t["header"] == "large":                    # iOS large title: caption, title, subtitle; page control
            y0 = t["header_top"]
            self.text(k.L, y0, 520, 26, b(label.replace("｜", "　")), 18, t["blue"], wrap=False, letterSpacing=1)
            self.title_text(k.L, y0 + 24, 860, 42, title, t["title_px"] or title_size + 2, t["navy"], wrap=False,
                            align=["left", "middle"])
            self.text(k.L, y0 + 66, 820, 24, sub, 18, t["gray"], wrap=False)
            off = t["dot_off"] or t["white"]
            x = k.R
            for i in reversed(range(len(k.chapters) if chap else 0)):
                wd = 26 if i + 1 == chap else 9
                x -= wd
                kw = {} if t["dot_off"] else {"shadow": {"blur": 4, "color": "#1E3A6033", "offset": [0, 1]}}
                self.solid(x, y0 + 8, wd, 9, t["blue"] if i + 1 == chap else off, "roundRect", adjustments=[50000], **kw)
                x -= 8
            return
        if t["header"] == "rule":
            self.solid(k.L, 31, 22, 3, self.accent())
            self.text(k.L + 32, 20, 500, 26, b(label), 18, t["blue"], wrap=False, letterSpacing=2)
            self.title_text(k.L, 46, 820, 38, title, title_size, t["navy"], wrap=False, align=["left", "middle"])
            self.text(k.L, 84, 820, 26, sub, 18, t["gray"], wrap=False)
            self.solid(k.L, 113, k.R - k.L, 1, t["line"])
            n = len(k.chapters) if chap else 0
            for i in range(n):
                cx = k.R - (n - 1) * 22 - 5 + i * 22
                if i + 1 == chap:
                    self.solid(cx - 6, 27, 12, 12, self.accent(), "ellipse")
                else:
                    self.solid(cx - 5, 28, 10, 10, t["bg"], "ellipse", border={"style": "solid", "width": 1, "color": t["line"]})
            return
        self.shape(k.L, 22, 5, 86, self.grad(k.BLUE_G, 90), "roundRect", adjustments=[50000])
        self.text(k.L + 18, 20, 500, 26, b(label), 18, t["blue"], wrap=False, letterSpacing=1)
        self.title_text(k.L + 18, 46, 800, 38, title, title_size, t["navy"], wrap=False, align=["left", "middle"])
        self.text(k.L + 18, 84, 800, 26, sub, 18, t["gray"], wrap=False)
        n = len(k.chapters) if chap else 0
        for i in range(n):
            cx = k.R - (n - 1) * 36 - 13 + i * 36
            if i + 1 == chap:
                self.shape(cx - 13, 22, 26, 26, self.grad(k.BLUE_G, 45), "ellipse")
                self.text(cx - 13, 22, 26, 26, b(str(i + 1)), 18, readable_on(k.BLUE_G, t["on_accent"], t["navy"]),
                          align=["center", "middle"], wrap=False)
            else:
                self.solid(cx - 13, 22, 26, 26, t["white"], "ellipse", border={"style": "solid", "width": 1, "color": t["edge"]})
                self.text(cx - 13, 22, 26, 26, str(i + 1), 18, t["gray"], align=["center", "middle"], wrap=False)

    def takeaway(self, text, label="重點", style=None, accent=None, reveal=None):
        """Full-width line sealing the page with one sentence; style defaults to the template's.
        style="bar": tinted rounded bar + filled label (bento look); style="rule": hairline + accent tick +
        colored label, no container (for scenarios / designs that forbid cards).
        reveal="第 1 題答案：B": a green check capsule at the right end — quiz answers and other reveals then
        appear in the same place on every page (decoration.md §12)."""
        t, k = self.th, self.k
        w = k.R - k.L
        rw = text_width(reveal, 18) + 46 if reveal else 0      # the reveal capsule's width; the sentence yields it
        st = style or t["takeaway"]
        if st == "capsule":                                # glass capsule, 16 px below the body like the gutters
            y0 = t["takeaway_y"]
            self.shape(k.L, y0, w, 38, self.glass_fill(), "roundRect", adjustments=[50000], shadow=t["shadow"],
                       border={"style": "solid", "width": 1.2, "color": t["edge"]})
            self.shape(k.L + 5, y0 + 4, 66, 30, self.grad(k.BLUE_G, 0), "roundRect", adjustments=[50000])
            self.text(k.L + 5, y0 + 4, 66, 30, b(label), 18, t["on_accent"], align=["center", "middle"], wrap=False)
            self.text(k.L + 86, y0, w - 100 - rw, 38, b(text), 18, t["navy"], align=["left", "middle"], wrap=False)
            ry = y0 + 4
        elif st == "rule":
            self.solid(k.L, 456, w, 1, t["line"])
            self.solid(k.L, 468, 6, 30, accent or self.accent())
            self.text(k.L + 18, 466, 64, 34, b(label), 18, t["blue"], wrap=False, align=["left", "middle"])
            self.text(k.L + 84, 466, w - 92 - rw, 34, b(text), 18, t["navy"], wrap=False, align=["left", "middle"])
            ry = 468
        else:
            self.solid(k.L, 456, w, 42, t["insight"], "roundRect", adjustments=[22000])
            self.solid(k.L + 8, 461, 64, 32, t["blue"], "roundRect", adjustments=[50000])
            self.text(k.L + 8, 461, 64, 32, b(label), 18, t["on_accent"], align=["center", "middle"], wrap=False)
            self.text(k.L + 84, 456, w - 92 - rw, 42, b(text), 18, t["navy"], align=["left", "middle"], wrap=False)
            ry = 462
        if reveal:
            rx, ink = k.R - rw - 6, deepen(t["green"], tint(t["green"], 0.16))
            self.solid(rx, ry, rw, 30, tint(t["green"], 0.16), "roundRect", adjustments=[50000])
            self.svg(rx + 10, ry + 6, 18, 18, "check", ink)
            self.text(rx + 32, ry, rw - 38, 30, b(reveal), 18, ink, align=["left", "middle"], wrap=False)

    def footer(self, n, color=None, source=None):
        """Footer: the deck line (or, with source=, the page's source / method note) and the page number."""
        k, t = self.k, self.th
        y = t["footer_y"]
        left, lc = (source, t["source_color"] or t["gray"]) if source else (k.footer_text, color or t["gray"])
        self.text(k.L, y, 760 if source else 560, 26, left, 18, lc, wrap=False)
        self.text(k.R - 100, y, 100, 26, f"{n:02d} / {k.total:02d}", 18, color or t["gray"], align=["right", "top"], wrap=False)
    def region(self, x, y, w, h, title=None, icon=None, main=False, rule_color=None, icon_fill=None):
        """Open module without a container — the default when cards are not allowed: a top rule
        (4px primary for the main module, 2px ink otherwise), optional icon + title. Returns the body
        box (x, y, w, h) below the title so content stays aligned across regions."""
        t = self.th
        self.solid(x, y, w, 4 if main else 2, rule_color or (t["blue"] if main else t["navy"]))
        if not title:
            return module_body(x, y, w, h, "region", False)
        tx = x
        if icon:
            self.icon_glyph(x, y + 16, 28, icon, icon_fill or t["blue"])
            tx = x + 40
        self.text(tx, y + 12, w - (tx - x), 36, b(title), 20, t["navy"], wrap=False, align=["left", "middle"])
        return module_body(x, y, w, h, "region", True)

    def icon_glyph(self, x, y, s, kind, fill=None):
        """Bare glyph without the disc: a library icon / SVG file, or a preset shape name."""
        fill = fill or self.th["blue"]
        kind = SEMANTIC_ICONS.get(kind, kind)
        if "/" in kind or kind.endswith(".svg"):
            return self.svg(x, y, s, s, kind, fill)
        return [self.shape(x, y, s, s, fill if isinstance(fill, dict) else {"type": "solid", "color": fill}, kind)]

    def module(self, m, x, y, w, h, frame="region"):
        """Render one storyboard module into its area — the same content contract as
        plan/storyboard.yaml (reference/storyboard.md §4), so build.py only customizes special pages.

        frame: "region" (open, no container — default, the scenario guides forbid cards) or "card".
        kinds: hero (data.items: [{label, value, icon}] joined by arrows, data.delta: {label, value} —
        a full-width focus band, the page's one hero) / stack (parts: 2-3 sub-modules in one frame, split by dashed rules; direction column /
        row; each part may have weight and a small title) / rank (data.rows: [label, value, group],
        data.groups: {group: tone}) / dumbbell (data.rows: [label, before, after], labels, goal) /
        text / quote / list (items may be "head<br/>sub") / stat (data: value, unit, label —
        or data.items: up to 3 of them) / ring (data: value 0-1 or %, label — or data.items, up to 4)
        / bar (data: value, target, label — or data.items) / pictogram (data: n, k, icon, label) /
        table (data.rows, first row = header) / chart (data: cols, rows — every column after the
        first is a series; horizontal, format, colors) / diagram (data.steps: [[name, sub, icon]…]) /
        image (data.src; a photo card in card frame). Items may carry tone: orange / green.
        feature: true (card frame) draws the module on the gradient feature card in light colors —
        one per page, for text / list / stat / ring / bar / pictogram / stack of those.
        Short copy grows to the largest size that fits and every block is centred vertically in its
        body, so a module never leaves its card half empty. Anything else falls back to text.
        Returns the body box."""
        kind, d = m.get("kind", "text"), m.get("data") or {}
        if kind == "hero" and d.get("items"):
            self.hero_band(x, y, w, h, d)
            return x + 20, y + 20, w - 40, h - 40
        feature = frame == "card" and bool(m.get("feature"))
        if frame == "card" and kind == "image" and d.get("src"):
            return self.photo_card(x, y, w, h, d["src"], m.get("title"), d.get("caption"))
        if frame == "card":
            self.card(x, y, w, h, m.get("title"), m.get("icon"), feature=feature)
        else:
            self.region(x, y, w, h, m.get("title"), m.get("icon"), main=m.get("role") == "main")
        bx, by, bw, bh = module_body(x, y, w, h, frame, bool(m.get("title")))
        saved = self.th
        if feature and saved["feature_style"] != "tint":   # tint feature cards keep dark copy
            self.light, self.th = True, light_theme(saved)
        try:
            self.content(m, bx, by, bw, bh)
        finally:
            self.light, self.th = False, saved
        return bx, by, bw, bh

    def content(self, m, bx, by, bw, bh):
        """Draw a module's content (no frame) into a box — also each part of a kind: stack module."""
        t, kind, main = self.th, m.get("kind", "text"), m.get("role") == "main"
        d = m.get("data") or {}
        items = m.get("text") if isinstance(m.get("text"), list) else ([m["text"]] if m.get("text") else [])
        series = d.get("items") or ([d] if d.get("value") is not None else [])
        if kind == "stack" and m.get("parts"):
            self.stack(bx, by, bw, bh, m["parts"], m.get("direction", "column"))
        elif kind == "rank" and d.get("rows"):
            self.rank_bars(bx, by, bw, bh, d)
        elif kind == "dumbbell" and d.get("rows"):
            self.dumbbell(bx, by, bw, bh, d)
        elif kind == "list":
            self.numbered_rows(bx, by, bw, bh, items)
        elif kind == "quote" and items:
            size, n = fit_size([items[0]], bw, bh, t["min_font"], 1.3, (36, 30, 26, 22, 20))  # same width as the box drawn
            hh = n * size * 1.3 + 4
            self.text(bx, by + (bh - hh) / 2, bw, hh, b(items[0]), size, t["blue"], lineHeight=1.3)
        elif kind == "stat" and series:
            cap = (96 if len(series) == 1 else 72) if m.get("hero") else (32 if self.focus else None)
            self.stats(bx, by, bw, bh, series, main, cap)
        elif kind == "ring" and series:
            self.rings(bx, by, bw, bh, series)
        elif kind == "bar" and series:
            self.bars(bx, by, bw, bh, series)
        elif kind == "pictogram" and d.get("n"):
            self.pictogram_block(bx, by, bw, bh, d)
        elif kind == "table" and d.get("rows"):
            self.fitted_table(bx, by, bw, bh, d["rows"], d.get("col_widths"))
        elif kind == "chart" and d.get("rows"):
            self.bar_chart(bx, by, bw, bh, d)
        elif kind == "diagram" and d.get("steps"):
            self.steps(bx, by, bw, bh, d["steps"])
        elif kind == "image" and d.get("src"):
            self.img(bx, by, bw, bh, d["src"])
        else:
            self.text_block(bx, by, bw, bh, items)

    # ---------- module renderers (Page.module uses them; build.py may call them directly) ----------
    def _stops(self, it):
        return self.tone_stops(it.get("tone"), None)

    def tone_stops(self, tone, default="blue"):
        """Gradient stops for a semantic tone (blue / orange / green / gray / teal) — brief.colors says what
        each tone means in this deck."""
        k = self.k
        return {"blue": k.BLUE_G, "orange": k.ORANGE_G, "green": k.GREEN_G, "gray": k.GRAY_G, "teal": k.TEAL_G}.get(tone or default)

    def tone_color(self, tone):
        """Colour of a module tone: blue (default) / orange / green / gray / teal."""
        return {"orange": self.th["orange"], "green": self.th["green"], "gray": self.th["gray"],
                "teal": self.th["teal"]}.get(tone, self.th["blue"])

    def stack(self, x, y, w, h, parts, direction="column", gap=28):
        """Two or three element kinds in one card: e.g. ring + numbers over a progress bar, thumbnails
        + counts over a ring. Parts split the box top to bottom (column) or side by side (row) by
        `weight`, with a dashed rule in each gap; a part's `title` is a small bold label above it."""
        weights = [float(p_.get("weight", 1)) for p_ in parts]
        col = direction != "row"
        span = (h if col else w) - gap * (len(parts) - 1)
        pos = y if col else x
        for i, (part, wt) in enumerate(zip(parts, weights)):
            size = span * wt / sum(weights)
            if i:
                if col:
                    self.hdash(x, pos - gap / 2, w, self.th["line"])
                else:
                    self.line(pos - gap / 2, y, 1, h, f"0.5,0 0.5,{h}", color=self.th["line"], dash=True)
            sx, sy, sw, sh = (x, pos, w, size) if col else (pos, y, size, h)
            if part.get("title"):
                self.text(sx, sy, sw, 28, b(part["title"]), 18, self.th["navy"], wrap=False)
                sy, sh = sy + 32, sh - 32
            self.content(part, sx, sy, sw, sh)
            pos += size + gap

    def rank_bars(self, x, y, w, h, d):
        """Ranking drawn from shapes (not a chart object): one gradient bar per row colored by its
        group, the value after the bar, a text legend when rows carry groups. data.rows: [[label,
        value, group?], …] in display order; data.groups: {group: tone}."""
        t = self.th
        rows, groups = d["rows"], d.get("groups") or {}
        if groups:
            self.text(x, y, w, 28, "　".join(f"{c('■', self.tone_color(tn))} {g}" for g, tn in groups.items()),
                      18, t["gray"], wrap=False)
            y, h = y + 34, h - 34
        nums = [float(r[1]) for r in rows]
        dec = decimals(nums)
        shown = [f"{v:,.{dec}f}" for v in nums]
        lab_w = max(text_width(str(r[0]), 18) for r in rows) + 8
        val_w = max(text_width(v, 18) for v in shown) + 10
        step = h / len(rows)
        bh = max(10, min(22, step - 10))
        bx = x + lab_w + 10
        max_w, top = max(w - lab_w - 10 - val_w, 40), max(nums) or 1
        self.solid(bx - 1, y + 2, 1.5, step * len(rows) - 4, t["line"])
        for i, (r, v, sv) in enumerate(zip(rows, nums, shown)):
            yy = y + i * step
            tone = groups.get(r[2]) if len(r) > 2 else None
            bw = max(max_w * v / top, 4)
            self.text(x, yy, lab_w, step, str(r[0]), 18, t["text"], wrap=False, align=["right", "middle"])
            self.shape(bx, yy + (step - bh) / 2, bw, bh, self.grad(self.tone_stops(tone)), "roundRect", adjustments=[20000])
            self.text(bx + bw + 6, yy, val_w, step, sv, 18, t["navy"], wrap=False, align=["left", "middle"])

    def dumbbell(self, x, y, w, h, d):
        """Before -> after per row on a 0..max track: gray dot, gradient connector, colored dot, and
        "before → after" on the right; rows that reach data.goal turn green and bold, with a dashed
        goal line. data.rows: [[label, before, after], …]; data.labels: [before, after]."""
        t = self.th
        rows = d["rows"]
        goal = d.get("goal")
        labels = d.get("labels") or ["before", "after"]
        legend = [(t["line"], labels[0]), (t["blue"], labels[1])] + ([(t["green"], f"= {goal:g}")] if goal is not None else [])
        self.text(x, y, w, 28, "　".join(f"{c('●', col)} {lab}" for col, lab in legend), 18, t["gray"], wrap=False)
        y, h = y + 34, h - 34 - (30 if goal is not None else 0)
        nums = [float(v) for r in rows for v in r[1:3]]
        dec = decimals(nums)
        top = float(d.get("max") or goal or max(nums))
        lab_w = max(text_width(str(r[0]), 18) for r in rows) + 8
        val_w = max(text_width(f"{float(r[1]):.{dec}f} → {float(r[2]):.{dec}f}", 18) for r in rows) + 12
        tx = x + lab_w + 14
        tw = w - lab_w - 14 - val_w - 24
        step = h / len(rows)
        for i, (nm, a, z) in enumerate(rows):
            a, z = float(a), float(z)
            cy = y + i * step + step / 2
            hit = goal is not None and z >= goal
            xa, xz = tx + tw * a / top, tx + tw * z / top
            self.text(x, cy - 14, lab_w, 28, b(nm) if hit else str(nm), 18, t["navy"] if hit else t["text"],
                      wrap=False, align=["right", "middle"])
            self.solid(tx, cy - 1, tw, 2, t["band"])
            if abs(xz - xa) > 1:
                lo, hi = sorted((xa, xz))
                ramp = [(0, t["line"]), (1, t["blue"])] if z >= a else [(0, t["blue"]), (1, t["line"])]
                self.shape(lo, cy - 3, hi - lo, 6, self.grad(ramp))
            self.solid(xa - 7, cy - 7, 14, 14, t["line"], "ellipse")
            self.shape(xz - 8, cy - 8, 16, 16, self.grad(self.k.GREEN_G if hit else self.k.BLUE_G, 45), "ellipse")
            after = f"{z:.{dec}f}"
            self.text(tx + tw + 24, cy - 14, val_w, 28, f"{a:.{dec}f} → " + (b(c(after, t["green"])) if hit else after),
                      18, t["gray"], wrap=False, align=["left", "middle"])
        if goal is not None:
            gx = tx + tw * goal / top
            self.line(gx, y - 2, 1, step * len(rows) + 4, f"0.5,0 0.5,{step * len(rows) + 4}", color=t["green"], dash=True)
            self.text(tx - 10, y + step * len(rows) + 4, 40, 26, "0", 18, t["gray"], wrap=False)
            self.text(gx - 60, y + step * len(rows) + 4, 120, 26, b(f"{goal:g}"), 18, t["green"], wrap=False, align=["center", "top"])

    def text_block(self, x, y, w, h, items):
        """One item: a paragraph sized up to fill the box. Several: rows with an accent marker."""
        t = self.th
        if not items:
            return
        if len(items) == 1:
            size, n = fit_size([items[0]], w, h, t["min_font"], 1.4, (26, 22, 20))  # same width as the box drawn
            hh = n * size * 1.4 + 4
            self.text(x, y + (h - hh) / 2, w, hh, str(items[0]), size, t["text"], lineHeight=1.4)
            return
        size, _ = fit_size(items, w - 18, h - 12 * len(items), t["min_font"], 1.3, (22, 20), keep_lines=True)
        heights = [len(wrap_lines(it, size, w - 18)) * size * 1.3 + 4 for it in items]
        gap = min(18, max(8, (h - sum(heights)) / len(items)))
        yy = y + (h - sum(heights) - gap * (len(items) - 1)) / 2
        for it, hh in zip(items, heights):
            self.solid(x, yy + 4, 4, size, t["blue"])
            self.text(x + 18, yy, w - 18, hh, str(it), size, t["text"], lineHeight=1.3)
            yy += hh + gap

    def fitted_table(self, x, y, w, h, rows, col_widths=None):
        """Table whose row heights follow the wrapped cell text (lint's `cell` estimate: 6% wider
        glyphs, 16 px side padding, line height 1.2 + 8). Rows get breathing room when the box allows
        it; in a short box the room shrinks first, the text height last."""
        size = self.th["min_font"]
        ratios = list(col_widths) if col_widths else [1] * len(rows[0])
        cols = [w * r / sum(ratios) for r in ratios]
        base = [max(len(wrap_lines(str(cell), size * 1.06, cw - 12)) for cell, cw in zip(r, cols)) * size * 1.2 + 10
                for r in rows]
        pad = [max(40 - v, 0) + 10 for v in base]           # at least 40 px per row, plus 10 px of air
        room = (h - sum(base)) / sum(pad) if sum(pad) else 0
        heights = ([v + p_ * min(1, room) for v, p_ in zip(base, pad)] if room >= 0
                   else [v * h / sum(base) for v in base])
        return self.table([x, y, w, sum(heights)], rows, ratios, heights)

    def numbered_rows(self, x, y, w, h, items):
        """Number badge + bold head + gray sub-line ("head<br/>sub"), rows centred in the box."""
        t = self.th
        if not items:
            return
        has_sub = any("<br/>" in str(it) for it in items)
        step = min(h / len(items), 84 if has_sub else 56)
        yy = y + (h - step * len(items)) / 2
        for i, it in enumerate(items):
            head, _, sub = str(it).partition("<br/>")
            self.numdot(x + 14, yy + 17, 28, str(i + 1))
            self.text(x + LIST_INDENT, yy, w - LIST_INDENT, 34, b(head) if sub else head, None, t["text"], align=["left", "middle"])
            if sub:
                self.text(x + LIST_INDENT, yy + 32, w - LIST_INDENT, max(step - 36, 28), sub, None, t["gray"], lineHeight=1.25)
            yy += step

    def stats(self, x, y, w, h, items, main=False, cap=None):
        """Up to 3 big numbers side by side, each with a small unit and a gray label below. Numbers in
        one row share a size (the largest every one of them fits), so none looks more important."""
        t = self.th
        items = items[:3]
        if cap and cap >= 72 and len(items) == 1:
            return self.hero_stat(x, y, w, h, items[0], cap)
        cw = w / len(items)
        cap = cap or (72 if main and len(items) == 1 else 54)
        lab_hs = [len(wrap_lines(str(it.get("label", "")), t["min_font"], cw - 12)) * t["min_font"] * 1.25
                  if it.get("label") else 0 for it in items]

        def fits(s_, it, lab_h):  # lint measures the unit span at the full size too
            return s_ * 1.3 + 6 + lab_h <= h and text_width(str(it.get("value", "?")) + str(it.get("unit", "")), s_) <= cw - 16
        size = next((s_ for s_ in (96, 84, 72, 60, 54, 44, 36, 30, 26) if s_ <= cap
                     and all(fits(s_, it, lh) for it, lh in zip(items, lab_hs))), 26)
        for i, (it, lab_h) in enumerate(zip(items, lab_hs)):
            num, u = str(it.get("value", "?")), str(it.get("unit", ""))
            label = str(it.get("label", ""))
            hh = size * 1.3 + 6 + lab_h
            yy = y + (h - hh) / 2
            self.gtext(x + i * cw, yy, cw - 8, size * 1.3, f"{num}{unit(u, t['gray'], 20)}" if u else num, size,
                       self._stops(it), wrap=False)
            if label:
                self.text(x + i * cw, yy + size * 1.3 + 6, cw - 12, lab_h + 4, label, None, t["gray"], lineHeight=1.25)

    def hero_stat(self, x, y, w, h, it, cap=96):
        """The page's one hero number, as large as the box allows: the value alone at full size, its unit
        moved into the gray label; label below when there is height, beside the number when the box is
        short (a 3-row card)."""
        t = self.th
        num = str(it.get("value", "?"))
        label = "　".join(p_ for p_ in (str(it.get("unit", "")).strip(), str(it.get("label", ""))) if p_)
        lab_h = len(wrap_lines(label, t["min_font"], w - 12)) * t["min_font"] * 1.25 if label else 0
        steps = [s_ for s_ in (96, 84, 72, 60, 54, 44, 36, 30) if s_ <= cap]
        stacked = next((s_ for s_ in steps if s_ * 1.3 + 6 + lab_h <= h and text_width(num, s_) <= w - 16), 30)
        lab_w = min(text_width(label, t["min_font"]) + 8, w * 0.45) if label else 0
        inline = next((s_ for s_ in steps if s_ * 1.3 <= h and text_width(num, s_) + 20 + lab_w <= w), 30)
        stops = self._stops(it)
        if inline >= stacked + 12:
            nw = text_width(num, inline) + 8
            self.gtext(x, y + (h - inline * 1.3) / 2, nw, inline * 1.3, num, inline, stops, wrap=False)
            if label:
                lines = len(wrap_lines(label, t["min_font"], w - nw - 16))
                lh = lines * t["min_font"] * 1.3 + 4
                self.text(x + nw + 12, y + (h - lh) / 2, w - nw - 12, lh, label, None, t["gray"], lineHeight=1.3)
            return
        hh = stacked * 1.3 + 6 + lab_h
        yy = y + (h - hh) / 2
        self.gtext(x, yy, w - 8, stacked * 1.3, num, stacked, stops, wrap=False)
        if label:
            self.text(x, yy + stacked * 1.3 + 6, w - 12, lab_h + 4, label, None, t["gray"], lineHeight=1.25)

    def rings(self, x, y, w, h, items):
        """Up to 4 progress rings in a row (value 0-1 or a percentage), captions below the rings — or,
        in a box too short for that, each caption beside its ring."""
        t = self.th
        items = items[:4]
        slot = w / len(items)
        has_sub = any(it.get("sub") for it in items)
        if h - 40 - (26 if has_sub else 0) < 56:          # short box: ring + label side by side
            dd = max(36, min(64, h))
            cy = y + h / 2
            for i, it in enumerate(items):
                v = share(it.get("value", 0))
                x0 = x + slot * i
                self.ring(x0 + dd / 2, cy, dd, v, str(it.get("center") or f"{v:.0%}"), None, self._stops(it), 14000, 18)
                self.text(x0 + dd + 10, cy - 14, slot - dd - 14, 28, str(it.get("label", "")), 18, t["text"], wrap=False,
                          align=["left", "middle"])
            return
        dd = min(150, slot - 28, h - 40 - (26 if has_sub else 0))
        block = dd + 36 + (26 if has_sub else 0)
        top = y + (h - block) / 2
        for i, it in enumerate(items):
            v = share(it.get("value", 0))
            cx = x + slot * i + slot / 2
            self.ring(cx, top + dd / 2, dd, v, str(it.get("center") or f"{v:.0%}"), None, self._stops(it), 14000)
            self.text(cx - slot / 2, top + dd + 8, slot, 28, b(str(it.get("label", ""))), 18, t["navy"], wrap=False, align=["center", "top"])
            if it.get("sub"):
                self.text(cx - slot / 2, top + dd + 34, slot, 26, str(it["sub"]), 18, t["gray"], wrap=False, align=["center", "top"])

    def bars(self, x, y, w, h, items):
        """Progress bars (value 0-1 or %, optional target tick). With room: label and value above each
        bar; in a short box: label, bar and value on one line. In a tall box the rows spread to cover
        most of it (85%), so a strip of two bars doesn't huddle in the middle of its card."""
        t = self.th
        shown = [str(it.get("display") or f"{share(it.get('value', 0)):.0%}") for it in items]
        val_w = max(text_width(s_, 18) for s_ in shown) + 10
        stacked = h / len(items) >= 56
        tight = stacked and any(text_width(str(it.get("label", "")), 18) + val_w + 8 > w for it in items)
        def spread(cap, item_h):                 # row pitch and top of the centred block
            n = len(items)
            step = min((h - item_h) / (n - 1), max(cap, (0.85 * h - item_h) / (n - 1))) if n > 1 else cap
            return step, y + (h - step * (n - 1) - item_h) / 2
        if tight and h / len(items) >= 84:      # label and value don't share a line: value goes under the bar
            step, yy = spread(96, 84)
            for it, s_ in zip(items, shown):
                target = it.get("target")
                self.text(x, yy, w, 28, b(str(it.get("label", ""))), 18, t["navy"], wrap=False)
                self.bar(x, yy + 34, w, share(it.get("value", 0)), 14, self._stops(it), share(target) if target is not None else None)
                self.text(x, yy + 56, w, 28, s_, 18, t["blue"], wrap=False, align=["right", "top"])
                yy += step
            return
        if stacked:
            step, yy = spread(72, 48)
        else:
            step = max(min(h / len(items), 44), 30)
            yy = y + (h - step * len(items)) / 2
        lab_w = 0 if stacked else min(max(text_width(str(it.get("label", "")), 18) for it in items) + 12, w * 0.4)
        for it, s_ in zip(items, shown):
            v = share(it.get("value", 0))
            target = it.get("target")
            tick = share(target) if target is not None else None
            if stacked:
                self.text(x, yy, w - val_w - 8, 28, b(str(it.get("label", ""))), 18, t["navy"], wrap=False)
                self.text(x + w - val_w, yy, val_w, 28, s_, 18, t["blue"], wrap=False, align=["right", "top"])
                self.bar(x, yy + 34, w, v, 14, self._stops(it), tick)
            else:
                self.text(x, yy, lab_w, 28, b(str(it.get("label", ""))), 18, t["navy"], wrap=False, align=["left", "middle"])
                self.bar(x + lab_w, yy + 7, w - lab_w - val_w - 8, v, 14, self._stops(it), tick)
                self.text(x + w - val_w, yy, val_w, 28, s_, 18, t["blue"], wrap=False, align=["right", "middle"])
            yy += step

    def pictogram_block(self, x, y, w, h, d):
        """Unit chart sized to the box (n icons, first k highlighted) with a one-line label below."""
        t = self.th
        n, k = int(d["n"]), int(d.get("k", 0))
        label = str(d.get("label", ""))
        size = max(20, min(48, (w - (n - 1) * 10) / n, h - (44 if label else 0)))
        gap = min(16, (w - n * size) / max(n - 1, 1))
        top = y + (h - size - (40 if label else 0)) / 2
        on = self.grad(self.tone_stops(d.get("tone")), 90) if d.get("tone") else None
        self.pictogram(x, top, n, k, d.get("icon", "tabler-filled/user"), size, gap, on=on)
        if label:
            self.text(x, top + size + 10, w, 30, label, 18, t["text"], wrap=False)

    def bar_chart(self, x, y, w, h, d):
        """Bar chart from storyboard data: every column after the first is a series with its own color
        (a text legend when there are several); numbers keep their decimals; horizontal charts rank
        top-down in data order."""
        t = self.th
        cols, rows = d.get("cols", ["category", "value"]), d["rows"]
        names = cols[1:]
        palette = d.get("colors") or [t["blue"], t["orange"], t["cyan"], t["gray"]]
        nums = [v for r in rows for v in r[1:] if isinstance(v, (int, float))]
        fmt = d.get("format") or number_format(nums)
        if len(names) > 1:
            self.text(x, y, w, 28, "　".join(f"{c('■', palette[i % len(palette)])} {nm}" for i, nm in enumerate(names)),
                      18, t["gray"], wrap=False)
            y, h = y + 32, h - 32
        horizontal = d.get("horizontal", False)
        series = []
        for i, nm in enumerate(names):
            col = palette[i % len(palette)]
            enc = {"x": nm, "y": cols[0]} if horizontal else {"x": cols[0], "y": nm}
            series.append({"type": "bar", "encode": enc, "fill": col,
                           "dataLabels": {"show": True, "numberFormat": fmt, "color": readable_on(col, t["white"], t["navy"])}})
        label = {"label": {"fontSize": 18, "color": t["text"]}, "gridLine": False}
        if horizontal:
            axes = {"yAxis": dict(label, type="category", reverse=True), "xAxis": {"show": False, "min": 0, "gridLine": False}}
        else:
            axes = {"xAxis": dict(label, axisLine={"color": t["line"]}), "yAxis": {"show": False, "min": 0, "gridLine": False}}
        extra = {"barGap": 0.06} if len(names) > 1 else {}
        self.chart([x, y, w, h], cols, rows, series, barWidth=0.6 if len(names) == 1 else 0.78, **extra, **axes)

    def steps(self, x, y, w, h, steps):
        """Connected step nodes (icon, or the step number when there is none) with name and sub-line."""
        t = self.th
        sw = w / len(steps)
        dd = max(36, min(64, h - 74))              # node size adapts to the body height
        has_sub = any(len(st) > 1 and st[1] for st in steps)
        sub_h = min(52, max(h - (dd + 40), 0)) if has_sub else 0
        top = y + max(0, (h - (dd + 40 + (sub_h if sub_h >= 24 else 0))) / 2)
        cy, name_y = top + dd / 2, top + dd + 8
        self.line(x + sw / 2, cy, max(w - sw, 1), 2, f"0,1 {max(w - sw, 1)},1", color=t["line"], width=2)
        for i, st in enumerate(steps):
            name, sub, icon = (list(st) + [None, None])[:3]
            cx = x + sw * i + sw / 2
            self.solid(cx - dd / 2, cy - dd / 2, dd, dd, t["white"], "ellipse", border={"style": "solid", "width": 2, "color": t["blue"]})
            if icon:
                self.icon_glyph(cx - dd * 0.28, cy - dd * 0.28, dd * 0.56, icon, t["blue"])
            else:
                self.text(cx - dd / 2, cy - dd / 2, dd, dd, b(str(i + 1)), 20, t["blue"], wrap=False, align=["center", "middle"])
            self.text(cx - sw / 2, name_y, sw, 30, b(name), 20, t["navy"], wrap=False, align=["center", "top"])
            if sub and sub_h >= 24:
                self.text(cx - sw / 2 + 4, name_y + 32, sw - 8, sub_h, sub, None, t["gray"], align=["center", "top"])

    def photo_card(self, x, y, w, h, src, title=None, caption=None):
        """Card-mode image module: the photo fills the top of the card, then a colored rule, the title
        and an optional one-line caption — the photo card of the bento-briefing system."""
        t = self.th
        self.card_fill(x, y, w, h)
        foot = (48 if title else 0) + (28 if caption else 0)
        ih = h - 2 - foot - (8 if foot else 0)
        if t["material"] == "glass":                  # the photo top follows the card corners
            r = t["radius_px"] or t["card_radius"] / 100000 * min(w, h)
            self.img(x + 1, y + 1, w - 2, ih, self.k.rounded(src, w - 2, ih, max(r - 1, 0), corners="top"),
                     fit={"mode": "stretch"})
        else:
            self.img(x + 1, y + 1, w - 2, ih, src)
        self.solid(x + 1, y + 1 + ih, w - 2, 4 if t["gradients"] else 2, self.accent())
        if title:
            self.title_text(x + 18, y + ih + 12, w - 36, 30, title, 20, t["navy"], wrap=False, align=["left", "middle"])
        if caption:
            self.text(x + 18, y + ih + (44 if title else 12), w - 36, 28, caption, 18, t["gray"], wrap=False)
        return x + 18, y + ih + 8, w - 36, foot

    def modules(self, page, frame="region"):
        """Render every module of a storyboard page on the kit grid (named layout or custom areas)."""
        mods = page.get("modules") or []
        tall = bool(page.get("tall"))
        self.focus = any(m.get("hero") or m.get("kind") == "hero" or any(p_.get("hero") for p_ in m.get("parts") or [])
                         for m in mods)
        boxes = ([self.k.area(*m["area"], tall=tall) for m in mods] if page.get("layout") == "custom"
                 else self.k.layout(page["layout"], len(mods), tall=tall))
        return [self.module(m, *box, frame=frame) for m, box in zip(mods, boxes)]

    def card_frame(self, feature=False, w=None, h=None):
        """Radius, border and shadow keywords of the template's card (radius_px: one px radius at every size)."""
        t = self.th
        kw = {"adjustments": self.radius(w, h)}
        if t["card_shadow"] or feature:
            kw["shadow"] = t["shadow"]
        if t["card_border"] and not feature:
            kw["border"] = {"style": "solid", "width": t["card_border"], "color": t["edge"]}
        return kw

    def radius(self, w=None, h=None):
        """roundRect adjustments for the template's card radius (a px radius when the theme sets radius_px)."""
        t = self.th
        if t["radius_px"] and w and h:
            return [int(min(t["radius_px"] / min(w, h), 0.5) * 100000)]
        return [t["card_radius"]]
    def glass_fill(self):
        """Card fill: top-lit translucent white in glass material, solid white otherwise."""
        return gfill(GLASS_G, 90) if self.th["material"] == "glass" else {"type": "solid", "color": self.th["white"]}

    def card_fill(self, x, y, w, h):
        """The template's white card (glass: top-lit translucent white under a white rim)."""
        self.shape(x, y, w, h, self.glass_fill(), "roundRect", **self.card_frame(w=w, h=h))

    def feature_frame(self, x, y, w, h, solid=False):
        """The page's one feature surface: gradient or solid; glass — tinted glass, a white rim, a coloured
        shadow and a specular highlight across the top (feature_pattern "highlight")."""
        t, k = self.th, self.k
        if t["feature_style"] == "tint" and not solid:   # pale tint, white rim — the page's one feature card
            self.shape(x, y, w, h, gfill(t["feature_tint"], 90), "roundRect", adjustments=self.radius(w, h),
                       shadow=t["shadow"], border={"style": "solid", "width": 1.2, "color": t["edge"]})
            return
        if t["material"] == "glass":
            self.shape(x, y, w, h, gfill([(0, t["feature2"] + "F0"), (1, t["feature"] + "F5")], 60), "roundRect",
                       adjustments=self.radius(w, h), shadow={"blur": 28, "color": t["feature"] + "55", "offset": [0, 10]},
                       border={"style": "solid", "width": 1.2, "color": "#FFFFFFB3"})
        else:
            fill = gfill(k.FEATURE_G, 60) if t["gradients"] else {"type": "solid", "color": t["feature"]}
            self.shape(x, y, w, h, fill, "roundRect", **self.card_frame(True, w, h))
        if t["feature_pattern"] == "highlight":
            self.shape(x + 1.5, y + 1.5, w - 3, h - 3, gfill([(0, "#FFFFFF45"), (0.42, "#FFFFFF00"), (1, "#FFFFFF00")], 90),
                       "roundRect", adjustments=self.radius(w, h))
    def card(self, x, y, w, h, title=None, icon=None, feature=False):
        """White card in the template's style — radius, border, shadow, tinted title band, the rule
        under the title (feature=True: the page's one feature card, gradient or solid)."""
        t = self.th
        if feature:
            self.feature_frame(x, y, w, h)
        else:
            self.card_fill(x, y, w, h)
            if title and t["card_band"]:
                r = t["card_radius"] / 100000 * min(w, h)
                self.solid(x + 1, y + 1, w - 2, 55, t["band"], "round2SameRect", adjustments=[int(r / 55 * 100000), 0])
                self.solid(x + 1, y + 56, w - 2, 1, t["edge"])
        if title:
            tx = x + 20
            light = feature and t["feature_style"] != "tint"
            if icon:
                self.icon(x + 20, y + 14, 34, icon, light=light)
                tx = x + 62
            self.title_text(tx, y + 14, w - (tx - x) - 16, 34, title, 20, t["on_accent"] if light else t["navy"],
                            wrap=False, align=["left", "middle"])
            if t["card_rule"] == "none":                # glass: the icon tile and spacing do the separating
                pass
            elif feature:
                self.solid(x + 20, y + 56, w - 40, 1.5, "#FFFFFF59")
                if t["feature_pattern"] == "rings" and (tx - x) + text_width(title, 20) + 8 < w - 78:
                    # the one pattern, kept in the title corner — only when the title leaves it room
                    for r_ in (12, 21, 30):
                        self.shape(x + w - 44 - r_, y + 30 - r_, 2 * r_, 2 * r_, None, "ellipse",
                                   border={"style": "solid", "width": 1, "color": "#FFFFFF2E"})
            elif t["card_rule"] == "hairline":
                self.solid(x + 20, y + 56, w - 40, 1, t["line"])
                self.solid(x + 20, y + 55, 28, 3, self.accent())
            else:
                self.solid(x + 20, y + 54, 56, 3, t["blue"], "roundRect", adjustments=[50000])

    def icon(self, x, y, s, kind, stops=None, light=False):
        """Glyph on a tinted disc (template icon_style "glyph": the bare glyph, larger). kind = a preset
        shape (star5, cube, cloud, lightningBolt, pie, gear9…) or a library icon / SVG file
        ("tabler-filled/bulb", "media/icons/x.svg") or a SEMANTIC_ICONS name ("carbon", "money"…)."""
        t = self.th
        kind = SEMANTIC_ICONS.get(kind, kind)
        if t["icon_style"] == "tile":                 # iOS app-icon tile: the meaning's gradient, white glyph
            if light:
                self.solid(x, y, s, s, "#FFFFFF38", "roundRect", adjustments=[30000])
            else:
                self.shape(x, y, s, s, self.grad(stops, 45), "roundRect", adjustments=[30000],
                           shadow={"blur": 6, "color": "#1A3A6A33", "offset": [0, 2]})
            k = s * 0.58
            if "/" in kind or kind.endswith(".svg"):
                self.svg(x + (s - k) / 2, y + (s - k) / 2, k, k, kind, WHITE)
            else:
                self.solid(x + (s - k) / 2, y + (s - k) / 2, k, k, WHITE, kind)
            return
        if t["icon_style"] == "glyph":
            k = s * 0.72
            fill = t["on_accent"] if light else self.grad(stops, 45)
            if "/" in kind or kind.endswith(".svg"):
                self.svg(x + (s - k) / 2, y + (s - k) / 2, k, k, kind, fill if isinstance(fill, str) else fill)
            else:
                self.shape(x + (s - k) / 2, y + (s - k) / 2, k, k, {"type": "solid", "color": fill} if isinstance(fill, str) else fill, kind)
            return
        self.solid(x, y, s, s, "#FFFFFF33" if light else t["sky"], "ellipse")
        k = s * 0.56
        if "/" in kind or kind.endswith(".svg"):
            self.svg(x + (s - k) / 2, y + (s - k) / 2, k, k, kind, t["on_accent"] if light else self.grad(stops, 45))
        elif light:
            self.solid(x + (s - k) / 2, y + (s - k) / 2, k, k, t["white"], kind)
        else:
            self.shape(x + (s - k) / 2, y + (s - k) / 2, k, k, self.grad(stops, 45), kind)

    def pill(self, x, y, w, label, color=None, filled=False, h=32, text_color=None):
        """Capsule label — filled or tinted per template — for tags, statuses, short names."""
        t = self.th
        color = color or t["blue"]
        if t["pill"] == "tint" and not text_color:      # iOS tinted capsule: soft fill, deepened text
            if filled:
                fill = color if contrast_ratio(color, WHITE) >= 3 else deepen(color, WHITE, 3.2)
                self.solid(x, y, w, h, fill, "roundRect", adjustments=[50000])
                self.text(x, y, w, h, b(label), 18, WHITE, align=["center", "middle"], wrap=False)
            else:
                fill = tint(color, 0.14)
                self.solid(x, y, w, h, fill, "roundRect", adjustments=[50000])
                self.text(x, y, w, h, b(label), 18, deepen(color, fill), align=["center", "middle"], wrap=False)
            return
        if filled:
            self.solid(x, y, w, h, color, "roundRect", adjustments=[50000])
        else:
            self.solid(x, y, w, h, t["white"], "roundRect", adjustments=[50000], border={"style": "solid", "width": 1.5, "color": color})
        if not text_color:  # keep the label readable: outline pills fall back to navy on a pale tint
            text_color = (readable_on(color, t["on_accent"], t["navy"]) if filled
                          else (color if contrast_ratio(color, t["white"]) >= 3 else t["navy"]))
        self.text(x, y, w, h, label, 18, text_color, align=["center", "middle"], wrap=False)

    def tag(self, x, y, w, label, fill=None, h=30, text_color=None):
        """Soft filled tag: navy text on a pale tint (names, members of a set) — quieter than pill."""
        self.solid(x, y, w, h, fill or self.th["sky"], "roundRect", adjustments=[50000])
        self.text(x, y, w, h, label, 18, text_color or self.th["navy"], align=["center", "middle"], wrap=False)

    def chip(self, x, y, w, h, name, value, color=None):
        """Row chip: tinted box, colored tick, bold name on the left, value on the right — inputs,
        outputs, labelled quantities."""
        t = self.th
        self.solid(x, y, w, h, t["band"], "roundRect", adjustments=[18000], border={"style": "solid", "width": 1, "color": t["edge"]})
        self.solid(x + 8, y + 10, 4, h - 20, color or t["blue"], "roundRect", adjustments=[50000])
        nw = text_width(name, 18) + 6
        self.text(x + 20, y, nw, h, b(name), 18, t["navy"], wrap=False, align=["left", "middle"])
        self.text(x + 20 + nw, y, w - 32 - nw, h, value, 18, t["text"], wrap=False, align=["right", "middle"])

    def arc(self, x, y, w, h, color=None, width=2.5, path=None):
        """Sweeping hairline curve (no fill) for covers and closing pages, e.g. under a cover photo.
        Default path dips through the box's lower middle and rises to its top-right corner."""
        self.shape(x, y, w, h, None, "custom", viewBox=[w, h],
                   path=path or f"M0,{h * 0.6:.0f} C{w * 0.24:.0f},{h:.0f} {w * 0.67:.0f},{h * 1.1:.0f} {w},{h * 0.06:.0f}",
                   border={"style": "solid", "width": width, "color": color or self.th["blue"]})

    def stat(self, x, y, w, num, u, label, icon=None, stops=None, size=30, label_h=52):
        """Number + small unit + gray label (the core 'data extraction' block)."""
        stops = stops or self.k.BLUE_G
        tx = x
        if icon:
            self.icon(x, y + 4, 40, icon, stops)
            tx = x + 52
        self.gtext(tx, y, w - (tx - x), 42, f"{num}{unit(u, self.th['gray']) if u else ''}", size, stops, wrap=False)
        self.text(tx, y + 42, w - (tx - x), label_h, label, 18, self.th["gray"], lineHeight=1.2)

    def ring(self, cx, cy, d, p, center, sub=None, stops=None, thick=12000, csize=None):
        """Progress ring (0..1). Put long captions *below* the ring, not inside: sub must fit the hole."""
        stops = stops or self.k.BLUE_G
        self.solid(cx - d / 2, cy - d / 2, d, d, self.th["sky"], "donut", adjustments=[thick])
        if p >= 0.999:
            self.shape(cx - d / 2, cy - d / 2, d, d, self.grad(stops, 90), "donut", adjustments=[thick])
        elif p > 0:
            end = (270 + 360 * p) % 360
            self.shape(cx - d / 2, cy - d / 2, d, d, self.grad(stops, 90), "blockArc", adjustments=[16200000, int(end * 60000), thick])
        size = csize or max(20, int(d * 0.2))
        self.gtext(cx - d / 2, cy - (size * 0.75 if sub else size * 0.65), d, size * 1.3, center, size, stops,
                   align=["center", "middle"], wrap=False)
        if sub:
            self.text(cx - d / 2 + 6, cy + size * 0.5, d - 12, 26, sub, 18, self.th["gray"], align=["center", "top"], wrap=False)

    def bar(self, x, y, w, p, h=16, stops=None, target=None):
        """Horizontal progress bar with optional target tick (0..1)."""
        self.solid(x, y, w, h, self.th["sky"], "roundRect", adjustments=[50000])
        if p > 0:
            self.shape(x, y, max(w * p, h), h, self.grad(stops or self.k.GREEN_G), "roundRect", adjustments=[50000])
        if target is not None:
            self.solid(x + w * target - 1, y - 6, 3, h + 12, self.th["green"])

    def segments(self, x, y, w, parts, h=30, labels=True):
        """100% stacked strip: parts = [(count, label, color), ...]."""
        total = sum(p[0] for p in parts)
        for k, lab, col in parts:
            sw = w * k / total
            self.solid(x, y, sw - 2, h, col)
            self.text(x, y, sw - 2, h, b(str(k)), 18, readable_on(col, self.th["on_accent"], self.th["navy"]), align=["center", "middle"], wrap=False)
            if labels:
                self.text(x, y + h + 4, sw, 26, lab, 18, self.th["gray"], align=["center", "top"], wrap=False)
            x += sw

    def numdot(self, cx, cy, d, label, stops=None, light=False):
        """Numbered marker centred on (cx, cy): a disc, or a rounded tile in "clear"; light=True on feature cards."""
        t = self.th
        if t["marker"] == "tile":                     # clear: a rounded square, never a circle
            adj = [int(min(10 * d / 34 / d, 0.5) * 100000)]
            if light or self.light:
                self.solid(cx - d / 2, cy - d / 2, d, d, WHITE, "roundRect", adjustments=adj)
                self.text(cx - d / 2, cy - d / 2, d, d, b(label), 18, self.k.th["blue"], align=["center", "middle"], wrap=False)
                return
            end = (stops or self.k.BLUE_G)[-1][1]
            if contrast_ratio(tint(end, 0.8), WHITE) < 3.2:   # the light corner must still carry white
                end = deepen(end, WHITE, 4.2)
            self.shape(cx - d / 2, cy - d / 2, d, d, gfill([(0, tint(end, 0.8)), (1, end)], 45), "roundRect",
                       adjustments=adj, shadow={"blur": 6, "color": "#0F2A4D29", "offset": [0, 2]})
            self.text(cx - d / 2, cy - d / 2, d, d, b(label), 18, WHITE, align=["center", "middle"], wrap=False)
            return
        if light or self.light:
            self.solid(cx - d / 2, cy - d / 2, d, d, self.th["white"], "ellipse")
            self.text(cx - d / 2, cy - d / 2, d, d, b(label), 18, self.k.th["blue"], align=["center", "middle"], wrap=False)
        else:
            g = stops or self.k.BLUE_G
            self.shape(cx - d / 2, cy - d / 2, d, d, self.grad(g, 45), "ellipse")
            self.text(cx - d / 2, cy - d / 2, d, d, b(label), 18, readable_on(g, self.th["on_accent"], self.th["navy"]),
                      align=["center", "middle"], wrap=False)
    def cover(self, title, title2, subtitle, kicker="", meta=(), byline="", photo=None, widget=None):
        """Cover page in the template's recipe (call on a page from kit.page(), then save as "cover"):
        photo-fade — white page, photo on the right washed into it, sweeping arc, leaves, filled kicker
                     pill, 2-line title (second line gradient), outline meta pills;
        frame      — ivory page, photo in a framed panel on the right with an offset accent outline,
                     accent dash + spaced kicker, serif title, meta as one line split by accent dots,
                     hairline above the byline;
        wash       — full-bleed photo under a canvas-colored wash from the left, rounded kicker,
                     soft meta tags;
        glass      — the livelier wallpaper, the photo in a glass frame on the right (concentric
                     corners), gradient kicker capsule, glass meta capsules (meta items may be
                     (icon, text)), an optional floating widget (icon, tone, title, line) over the frame.
        meta: strings, or (icon, text) pairs (glass)."""
        t = self.th
        style = self._backdrop(photo)
        if style == "glass":
            k = self.k
            kw_ = text_width(kicker, 18) + 48
            self.shape(56, 66, kw_, 34, self.grad(k.BLUE_G, 0), "roundRect", adjustments=[50000])
            self.text(56, 66, kw_, 34, b(kicker), 18, t["on_accent"], wrap=False, align=["center", "middle"], letterSpacing=1)
            self.title_text(56, 124, 420, 74, title, 54, t["navy"], wrap=False)
            self.gtext(56, 196, 420, 74, title2, 54, k.BLUE_G, wrap=False)
            self.text(56, 286, 420, 60, subtitle, 20, t["gray"], lineHeight=1.4)
            x, y = 56, 362
            for m_ in meta:                           # glass capsules; a second row when the first is full
                icon, txt = m_ if isinstance(m_, (list, tuple)) else (None, m_)
                pad = 34 if icon else 18
                w_ = text_width(txt, 18) + pad + 22
                if x + w_ > GLASS_PHOTO[0] - 12 and x > 56:
                    x, y = 56, y + 44
                self.shape(x, y, w_, 36, self.glass_fill(), "roundRect", adjustments=[50000], shadow=t["shadow"],
                           border={"style": "solid", "width": 1.2, "color": t["edge"]})
                if icon:
                    self.svg(x + 12, y + 9, 18, 18, SEMANTIC_ICONS.get(icon, icon), t["blue"])
                self.text(x + pad, y, w_ - pad - 8, 36, b(txt), 18, t["navy"], wrap=False,
                          align=["left", "middle"])
                x += w_ + 8
            self.text(56, 470, 420, 28, byline, 18, t["gray"], wrap=False)
            if widget:
                icon, tone, head, line = widget
                wx, wy, ww, wh = GLASS_PHOTO[0] - 36, 418, 236, 80
                self.shape(wx, wy, ww, wh, self.glass_fill(), "roundRect", adjustments=[22000],
                           shadow={"blur": 30, "color": "#1E3A6040", "offset": [0, 10]},
                           border={"style": "solid", "width": 1.2, "color": t["edge"]})
                self.icon(wx + 16, wy + 18, 44, icon, self.tone_stops(tone))
                self.text(wx + 72, wy + 12, ww - 84, 30, b(head), 20, t["navy"], wrap=False, align=["left", "middle"])
                self.text(wx + 72, wy + 42, ww - 84, 26, line, 18, t["gray"], wrap=False, align=["left", "middle"])
            return
        if style == "frame":
            self.solid(56, 98, 36, 3, self.accent())
            self.text(104, 86, 440, 28, b(kicker), 18, t["blue"], wrap=False, letterSpacing=3)
            self.title_text(56, 132, 480, 70, title, 46, t["navy"], wrap=False)
            self.title_text(56, 198, 480, 70, title2, 46, t["blue"], wrap=False)
            self.text(56, 286, 460, 60, subtitle, 20, t["gray"], lineHeight=1.4)
            if meta:
                dot = f"　{c('●', self.accent())}　"
                self.text(56, 372, 480, 30, dot.join(meta), 18, t["text"], wrap=False)
            self.solid(56, 452, 480, 1, t["line"])
            self.text(56, 464, 480, 28, byline, 18, t["gray"], wrap=False)
            return
        if style == "wash":
            self.solid(56, 76, 220, 36, t["blue"], "roundRect", adjustments=[50000])
            self.text(56, 76, 220, 36, kicker, 18, t["on_accent"], wrap=False, align=["center", "middle"])
            self.title_text(56, 132, 560, 74, title, 52, t["navy"], wrap=False)
            self.gtext(56, 204, 560, 74, title2, 52, self.k.BLUE_G, wrap=False,
                       **({"fontFamily": t["title_font"]} if t["title_font"] else {}))
            self.text(56, 296, 440, 60, subtitle, 20, t["text"], lineHeight=1.4)
            x = 56
            for m_ in meta:
                w_ = text_width(m_, 18) + 36
                self.tag(x, 380, w_, m_, t["white"])
                x += w_ + 12
            self.text(56, 470, 520, 28, byline, 18, t["gray"], wrap=False)
            return
        kw_ = text_width(kicker, 18) + 48
        self.solid(56, 70, kw_, 34, t["blue"], "roundRect", adjustments=[50000])
        self.text(56, 70, kw_, 34, kicker, 18, t["on_accent"], wrap=False, align=["center", "middle"], letterSpacing=1)
        self.title_text(56, 126, 560, 74, title, 54, t["navy"], wrap=False)
        self.gtext(56, 198, 560, 74, title2, 54, self.k.BLUE_G, wrap=False)
        self.text(56, 290, 420, 60, subtitle, 20, t["gray"], lineHeight=1.4)
        x = 56
        for m_ in meta:
            w_ = text_width(m_, 18) + 36
            self.pill(x, 372, w_, m_, t["blue"], h=34)
            x += w_ + 12
        self.text(56, 474, 460, 28, byline, 18, t["gray"], wrap=False)

    def hero_band(self, x, y, w, h, d):
        """Focus band on the feature fill: 1-3 big numbers (icon + label above each) joined by arrows,
        and an optional delta on the right — "只看載客 0.81 → 算進碳排 0.64 ｜ 下降 −0.17"."""
        t = self.th
        self.feature_frame(x, y, w, h, solid=True)       # the hero band is the deck's one solid surface
        items, delta = d["items"][:3], d.get("delta")
        right = 250 if delta else 0
        if t["feature_pattern"] == "rings":
            for r_ in (22, 36, 50):
                self.shape(x + w - 64 - r_, y + h / 2 - r_, 2 * r_, 2 * r_, None, "ellipse",
                           border={"style": "solid", "width": 1, "color": "#FFFFFF2E"})
        slot = (w - 64 - right - (64 if t["feature_pattern"] == "rings" and not delta else 0)) / len(items)
        size = max(36, min(60, h - 92))
        for i, it in enumerate(items):
            xx = x + 32 + i * slot
            tx = xx
            if it.get("icon"):
                self.solid(xx, y + 18, 36, 36, "#FFFFFF33", "ellipse")
                self.svg(xx + 8, y + 26, 20, 20, it["icon"], WHITE)
                tx = xx + 46
            self.text(tx, y + 22, slot - (tx - xx) - 8, 28, b(str(it.get("label", ""))), 18, WHITE, wrap=False,
                      align=["left", "middle"])
            self.text(xx, y + 62, slot - 70, size * 1.25, b(str(it.get("value", ""))), size, WHITE, wrap=False)
            if i < len(items) - 1:
                self.shape(xx + slot - 62, y + 62 + size * 0.3, 44, 38, {"type": "solid", "color": "#FFFFFFB3"}, "rightArrow")
        if delta:
            dx = x + w - right - (64 if t["feature_pattern"] == "rings" else 0) + 40
            self.text(dx, y + 22, right - 40, 28, str(delta.get("label", "")), 18, t["on_feature"], wrap=False)
            self.text(dx, y + 62, right - 40, 56, b(str(delta.get("value", ""))), 40, WHITE, wrap=False)

    def breather(self, d):
        """Breather page body (use it every ~4 content pages): a photo panel on the left 5/12 with a dark
        wash, a caption and an optional pictogram row; on the right one giant hero number with a lead
        line, up to two supporting stats and an optional progress bar.
        d: photo, caption, note, pictogram {n, k, icon}, lead, value, unit, tone,
           stats [{value, unit, label, icon, tone}], bar {label, value, target, display, tone}."""
        t, k = self.th, self.k
        px, py, pw, ph = k.area(0, 0, 5, 6)
        if d.get("photo") and t["material"] == "glass":   # rounded, the wash baked in (no square overlay)
            r = t["radius_px"] or t["card_radius"] / 100000 * min(pw, ph)
            self.img(px, py, pw, ph, k.rounded(d["photo"], pw, ph, r, shade=[(0, 0.10), (0.45, 0.45), (0.6, 0.8), (1, 0.87)]),
                     fit={"mode": "stretch"})
        else:
            if d.get("photo"):
                self.img(px, py, pw, ph, d["photo"])
            else:
                self.solid(px, py, pw, ph, t["sky"])
            plate = 150                             # copy sits on a solid plate; the wash fades into it
            self.shape(px, py, pw, ph - plate, gfill([(0, t["navy"] + "14"), (1, t["navy"] + "CC")], 90))
            self.solid(px, py + ph - plate, pw, plate, t["navy"] + "CC")
        pic = d.get("pictogram")
        cap_y = py + ph - (136 if pic else 96)
        if d.get("caption"):
            self.text(px + 24, cap_y, pw - 48, 30, b(d["caption"]), 20, WHITE, wrap=False)
        if pic:
            n, lit = int(pic.get("n", 10)), int(pic.get("k", 1))
            step = min(30, (pw - 48) / n)
            for i in range(n):
                self.svg(px + 24 + i * step, py + ph - 92, step - 6, step - 6, pic.get("icon", "power"),
                         WHITE if i < lit else "#FFFFFF59")
        if d.get("note"):
            self.text(px + 24, py + ph - 54, pw - 48, 26, d["note"], 18, "#E4ECF7", wrap=False)
        rx = px + pw + 40
        rw = k.R - rx
        top = py
        if t["material"] == "glass":                  # every block sits in the same material
            self.card_fill(px + pw + 16, py, k.R - px - pw - 16, ph)
            rw, top = rw - 24, py + 4
        stops = self.tone_stops(d.get("tone"))
        if d.get("lead"):
            self.text(rx, top + 6, rw, 28, d["lead"], 20, t["gray"], wrap=False)
        val = str(d.get("value", ""))
        size = next(s_ for s_ in (96, 84, 72, 60, 54) if text_width(val + str(d.get("unit", "")), s_) <= rw - 8 or s_ == 54)
        self.gtext(rx - 4, top + 34, rw, size * 1.25, val + (unit(d["unit"], t["gray"], 22) if d.get("unit") else ""),
                   size, stops, wrap=False)
        y0 = top + 34 + size * 1.25 + 12
        stats = d.get("stats") or []
        if stats:
            self.hdash(rx, y0, rw)
            sw = rw / len(stats[:2])
            for i, it in enumerate(stats[:2]):
                xx = rx + i * sw
                g = self.tone_stops(it.get("tone"))
                self.icon(xx, y0 + 20, 34, it.get("icon", "analysis"), g)
                self.gtext(xx + 44, y0 + 14, sw - 52, 34, f"{it.get('value', '')}" + (unit(it["unit"], t["gray"], 18) if it.get("unit") else ""),
                           26, g, wrap=False)
                self.text(xx + 44, y0 + 50, sw - 52, 26, str(it.get("label", "")), 18, t["gray"], wrap=False)
            y0 += 92 if top == py else 84            # glass: the card's inset comes out of this gap
        bar = d.get("bar")
        if bar and y0 + 52 <= py + ph - 6:           # label row + 12 px bar must clear the panel bottom
            self.icon(rx, y0, 30, bar.get("icon", "green"), self.tone_stops(bar.get("tone") or "green"))
            self.text(rx + 40, y0, rw / 2, 30, b(str(bar.get("label", ""))), 18, t["navy"], wrap=False, align=["left", "middle"])
            if bar.get("display"):
                self.text(rx + rw / 2, y0, rw / 2, 30, str(bar["display"]), 18, t["gray"], wrap=False, align=["right", "middle"])
            tgt = bar.get("target")
            self.bar(rx, y0 + 40, rw, share(bar.get("value", 0)), 12, self.tone_stops(bar.get("tone") or "green"),
                     share(tgt) if tgt is not None else None)

    def _backdrop(self, photo, ornaments=True):
        """The cover recipe's background, shared by Page.cover and Page.closing."""
        t = self.th
        style = t["cover"]
        if style == "glass":
            self.bg = t["bg"]
            self.els = [e for e in self.els if e.get("src") != "media/wall.jpg"]
            self.img(0, 0, *CANVAS, "wall-cover.jpg")
            x, y, w, h, inset = GLASS_PHOTO
            self.card_fill(x, y, w, h)
            r = t["card_radius"] / 100000 * min(w, h) - inset      # concentric: frame radius − inset
            if photo:
                self.img(x + inset, y + inset, w - 2 * inset, h - 2 * inset,
                         self.k.rounded(photo, w - 2 * inset, h - 2 * inset, r), fit={"mode": "stretch"})
            else:
                self.solid(x + inset, y + inset, w - 2 * inset, h - 2 * inset, t["sky"], "roundRect",
                           adjustments=[int(r / min(w - 2 * inset, h - 2 * inset) * 100000)])
            return style
        if style == "frame":
            self.bg = t["bg"]
            self.shape(578, 66, 346, 430, None, "rect", border={"style": "solid", "width": 1.5, "color": self.accent()})
            if photo:
                self.img(564, 52, 346, 430, photo)
            else:                                   # no photo: a tinted panel keeps the framed anchor
                self.solid(564, 52, 346, 430, t["sky"])
        elif style == "wash":
            self.bg = t["bg"]
            if photo:
                self.img(0, 0, 960, 540, photo)
            self.shape(0, 0, 720, 540, gfill([(0, t["bg"]), (0.55, t["bg"] + "F2"), (1, t["bg"] + "00")], 0))
        else:
            self.bg = t["white"]
            if photo:
                self.img(330, 0, 630, 440, photo)
                self.shape(330, 0, 330, 440, gfill([(0, t["white"]), (1, t["white"] + "00")], 0))
            self.arc(330, 330, 630, 160)
            if ornaments:
                self.leaf(570, 92, 66, -25)
            self.leaf(866, 468, 54, 18)
        return style

    def closing(self, title="謝謝聆聽", title2="Q & A", points=(), byline="", photo=None):
        """Closing page in the cover's recipe (same backdrop, another photo): a thank-you title, a
        second line, up to three recap points [(icon, tone, text)] and the byline. Save as "final"."""
        t = self.th
        style = self._backdrop(photo, ornaments=False)
        if style == "glass":                          # the recap as an iOS grouped list
            self.title_text(56, 56, 400, 74, title, 54, t["navy"], wrap=False)
            self.gtext(56, 128, 400, 60, title2, 44, self.k.BLUE_G, wrap=False)
            pts = list(points)[:3]
            lx, ly, lw, rh = 56, 216, 400, 64
            if pts:
                self.card_fill(lx, ly, lw, rh * len(pts))
            for i, (icon, tone, txt) in enumerate(pts):
                yy = ly + i * rh
                if i:
                    self.solid(lx + 68, yy, lw - 68, 1, "#D5DFEC")
                self.icon(lx + 18, yy + 14, 36, icon, self.tone_stops(tone))
                self.text(lx + 68, yy, lw - 84, rh, b(txt), 20, t["navy"], wrap=False, align=["left", "middle"])
            self.text(56, 470, 420, 28, byline, 18, t["gray"], wrap=False)
            return
        big = 46 if style == "frame" else 54
        if style == "frame":
            self.solid(56, 98, 36, 3, self.accent())
        self.title_text(56, 108, 480, big * 1.3, title, big, t["navy"], wrap=False)
        if t["gradients"]:
            self.gtext(56, 108 + big * 1.3, 480, 60, title2, 44, self.k.BLUE_G, wrap=False,
                       **({"fontFamily": t["title_font"]} if t["title_font"] else {}))
        else:
            self.title_text(56, 108 + big * 1.3, 480, 60, title2, 44, t["blue"], wrap=False)
        for i, (icon, tone, txt) in enumerate(list(points)[:3]):
            yy = 270 + i * 52
            self.icon(56, yy, 36, icon, self.tone_stops(tone))
            self.text(104, yy + 2, 400, 32, b(txt), 20, t["navy"], wrap=False, align=["left", "middle"])
        self.text(56, 474, 460, 28, byline, 18, t["gray"], wrap=False)

    def coins(self, cx, base_y, n, stops=None, w=34):
        """Coin stack (n coins, bottom at base_y) — amounts the audience can count, e.g. 1 coin = 50 元."""
        for k_ in range(n):
            self.shape(cx - w / 2, base_y - 11 - k_ * 7, w, 11, self.grad(stops or self.k.ORANGE_G, 90), "ellipse",
                       border={"style": "solid", "width": 1, "color": self.th["white"]})

    def leaf(self, x, y, w, rot=-25):
        """Small decorative leaf (custom bezier) — covers / closing pages only."""
        self.shape(x, y, w, w / 2, gfill(self.k.GREEN_G), "custom", viewBox=[120, 60],
                   path="M0,30 C30,0 90,0 120,30 C90,60 30,60 0,30 Z", rotation=rot)

    # ---------- decoration without cards (reference/decoration.md) ----------
    def band(self, y, h, color=None, x=0, w=None):
        """Tint strip anchored to the canvas edges (full width by default): groups a header, hero or
        section behind its content without becoming a card — square, no border, no shadow.
        Draw it before the content it sits behind."""
        return self.solid(x, y, (CANVAS[0] - x) if w is None else w, h, color or self.th["mist"])

    def watermark(self, x, y, text, size=160, color=None, w=None, align="left"):
        """Oversized ghost text (chapter number, year, keyword) behind a section, drawn at ~12% alpha
        so it never competes with body text (lint skips contrast for alpha < 0.5).
        Draw it before the content it sits behind and keep it off paragraphs."""
        col = (color or self.th["blue"])[:7] + "1F"
        w = w or round(sum(size if ord(ch) > 0x2E80 else size * 0.62 for ch in text)) + 8  # CJK 1em, Latin/digits ~0.6em
        return self.text(x, y, w, size * 1.2, b(text), size, col, wrap=False,
                         align=[align, "top"], lineHeight=1)

    def photo(self, x, y, w, h, src, caption=None, rule=None, crop=None):
        """Photo with a colored base rule and an optional one-line caption below (+36 px)."""
        self.img(x, y, w, h, src, crop)
        self.solid(x, y + h, w, 4, rule or self.th["blue"])
        if caption:
            self.text(x, y + h + 8, w, 28, caption, 18, self.th["gray"], wrap=False)

    def motif(self, kind, corner="tr", color=None, size=120):
        """Corner motif for covers, dividers and closing pages, inside the canvas edge:
        "dots" (4×4 dot grid), "rings" (three concentric quarter rings hugging the corner) or "leaf".
        corner = tl / tr / bl / br."""
        col = color or self.th["sky"]
        cw, ch = CANVAS
        left, top = corner[1] == "l", corner[0] == "t"
        if kind == "rings":
            # quarter annuli drawn for the top-left corner, mirrored with flip for the others
            x0, y0 = (0 if left else cw - size), (0 if top else ch - size)
            for r in (1.0, 0.72, 0.44):
                ro, ri = 100 * r, 100 * r - 8
                path = f"M{ro},0 A{ro},{ro} 0 0 1 0,{ro} L0,{ri} A{ri},{ri} 0 0 0 {ri},0 Z"
                self.shape(x0, y0, size, size, {"type": "solid", "color": col}, "custom", viewBox=[100, 100],
                           path=path, flip=[not left, not top])
            return
        x0 = 24 if left else cw - 24 - size
        y0 = 24 if top else ch - 24 - size
        if kind == "dots":
            step = size / 4
            for i in range(4):
                for j in range(4):
                    self.solid(x0 + i * step + step / 2 - 4, y0 + j * step + step / 2 - 4, 8, 8, col, "ellipse")
        elif kind == "leaf":
            self.leaf(x0 + size * 0.2, y0 + size * 0.3, size * 0.6)
        else:
            raise ValueError(f"unknown motif {kind!r}: dots / rings / leaf")

    def pictogram(self, x, y, n, k, icon="tabler-filled/user", size=36, gap=10, on=None, off=None):
        """Unit chart: n icons in a row with the first k highlighted ("1 in 10"). icon = library id or
        preset shape name; keep n ≤ 12 per row."""
        for i in range(n):
            fill = (on or self.th["blue"]) if i < k else (off or self.th["line"])
            self.icon_glyph(x + i * (size + gap), y, size, icon, fill)

    def chart(self, bounds, cols, rows, series, **kw):
        """Native PPTD chart from cols / rows / series (reference/pptd.md §5 Chart); **kw: type, axis, labels…"""
        el = {"elementId": self._id("c"), "elementType": "chart", "bounds": bounds, "fontFamily": self.th["font"],
              "data": {"cols": cols, "rows": rows}, "legend": False, "series": series}
        el.update(kw)
        return self.add(el)

    def table(self, bounds, rows, col_widths=None, row_heights=None, style="$data"):
        """col_widths / row_heights may be px or ratios; PPTD stores ratios of the bounds that sum to 1.
        Omitted -> equal columns / rows."""
        def ratios(vals, n):
            vals = list(vals) if vals else [1] * n
            if len(vals) != n or min(vals) <= 0:
                raise ValueError(f"table: expected {n} positive widths/heights, got {vals}")
            out = [round(v / sum(vals), 4) for v in vals]  # px or uneven ratios -> ratios summing to 1
            out[-1] = round(1 - sum(out[:-1]), 4)
            return out
        el = {"elementId": self._id("tb"), "elementType": "table", "bounds": bounds,
              "columnWidths": ratios(col_widths, len(rows[0])), "rowHeights": ratios(row_heights, len(rows)),
              "style": style, "rows": [[{"text": str(cell)} for cell in r] for r in rows]}
        return self.add(el)

    def save(self, name, ptype="content"):
        """Write pages/<name> (with the speaker notes when set) and append it to the manifest order."""
        data = {"pageType": ptype, "background": {"type": "solid", "color": self.bg}}
        if self.notes:
            data["notes"] = str(self.notes)
        data["elements"] = self.els
        (self.k.out / "pages" / name).write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=10000), encoding="utf-8")
        if name not in self.k.saved:
            self.k.saved.append(name)


def api(pattern=""):
    """Compact API index — signature and first doc line of every public helper (python pptd_kit.py [filter])."""
    import inspect
    rows = []

    for name, o in globals().items():
        if not name.startswith("_") and inspect.isfunction(o) and o.__module__ == __name__ and name != "api":
            rows.append((name, str(inspect.signature(o)), inspect.getdoc(o) or ""))
    for cls in (Kit, Page):
        for name, o in vars(cls).items():
            if not name.startswith("_") and inspect.isfunction(o):
                sig = str(inspect.signature(o)).replace("(self, ", "(").replace("(self)", "()")
                rows.append((f"{cls.__name__}.{name}", sig, inspect.getdoc(o) or ""))
    pat = pattern.lower()
    # the filter searches the whole doc; the index prints its first line
    out = [f"{n}{sig}\n    {d.splitlines()[0] if d else ''}" for n, sig, d in rows if pat in n.lower() or pat in d.lower()]
    if not pat:
        out += [f"THEMES: {', '.join(THEMES)}", f"LAYOUTS: {', '.join(LAYOUTS)}",
                f"SEMANTIC_ICONS: {', '.join(SEMANTIC_ICONS)}"]
    return "\n".join(out)


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):          # UTF-8 on any Windows code page
        sys.stdout.reconfigure(encoding="utf-8")
    print(api(sys.argv[1] if len(sys.argv) > 1 else ""))
