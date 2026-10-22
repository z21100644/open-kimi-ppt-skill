"""Storyboard (策劃稿) tools — check the plan, then render a grayscale wireframe deck.

The storyboard is the planning artifact between research and visual design: a deck brief, a
pyramid-structured outline (governing claim → part claims → page claims) and, per page, a bento
layout with the actual draft copy of every module. Schema: reference/storyboard.md.

Usage:
  python storyboard.py check plan/storyboard.yaml [--facts plan/facts.md] [--stage outline|layout]
  python storyboard.py wireframe plan/storyboard.yaml --out plan/wireframe [--force]

check      outline: brief fields, storyline alternatives, governing claim, part claims, page
           claims/takeaways, group sizes, fact references (F1, F2… defined in facts.md; default:
           facts.md next to the storyboard), caveats for low-confidence facts, missing-value facts
           layout:  known layout, module count = area count, areas inside the 12×6 grid and not
           overlapping, main module on the largest area, draft copy fits at min_font (and has no
           orphan last line), main module not mostly empty, evenly divided layouts, two
           consecutive pages with the same skeleton, icons exist; card craft: a large card holding
           one small element (compose it with kind: stack), more than one feature card per page,
           feature on a kind it cannot draw, tones used without brief.colors; polish: many numbers
           without one hero (or more than one), long decks without a breather page or hero band, live
           decks without a closing page, subtitles / takeaways longer than one short clause
           --stage outline skips layout checks; --stage layout makes a missing layout an error.
           Default: layout checks run on every content page that already has a layout.
wireframe  writes <out>/wireframe.pptd + pages/ — gray boxes on the same grid the final build uses.
           Convert and render it with pptd2pptx.py + render_pptx.py like any deck.
Exit code 1 when any error-level issue is found.
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from icons import resolve as resolve_icon  # noqa: E402
from lint_pptd import CLOSE_PUNCT, char_w, paragraphs, wrap  # noqa: E402
from pptd_kit import (EVEN_LAYOUTS, GRID_COLS, GRID_ROWS, LIST_INDENT, SEMANTIC_ICONS, TALL_BOTTOM, Kit, b,  # noqa: E402
                      grid_area, is_even, layout_areas, module_body)

REQUIRED_BRIEF = ("topic", "audience", "goal", "mode", "pages")
MODES = ("live", "reading", "hybrid")
TEXT_KINDS = ("text", "list", "quote")
VISUAL_KINDS = ("chart", "table", "image", "diagram", "ring", "bar", "pictogram", "rank", "dumbbell")
KINDS = TEXT_KINDS + VISUAL_KINDS + ("stat", "stack", "hero")
FEATURE_KINDS = TEXT_KINDS + ("stat", "ring", "bar", "pictogram", "stack")  # drawable on the feature card
SINGLE_KINDS = ("stat", "ring", "bar", "pictogram", "quote")  # one small element: thin in a large card
BIG_CARD = (4, 4)  # colspan, rowspan from which a single small element leaves a card half empty
SLUG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
# preset shape names (reference/shapes.md) are valid icons too: pptd_kit draws them on the icon disc
PRESET_SHAPES = frozenset(re.findall(r"^\| ([A-Za-z0-9]+) \|", (Path(__file__).resolve().parents[1] / "reference" / "shapes.md")
                                     .read_text(encoding="utf-8"), re.M))
FACT_BULLET = re.compile(r"^\s*[*-]\s*(?:\*\*)?(F\d+)\b")
CONF_COLS = ("confidence", "置信度", "可信度", "信心")
VALUE_COLS = ("value", "數值", "数值", "值")
LOW_CONF = ("低", "low", "方向", "directional")
MISSING = ("未提供", "無法推導", "无法推导", "需要外部驗證", "需要外部验证", "待填", "n/a")
TITLE_W, TAKEAWAY_W = 796, 796  # header title box (26px bold) / 重點 bar text box (18px bold)
CLAUSE_W = 540                  # a distilled subtitle / takeaway: one short clause, ≈ 30 CJK chars at 18px
FOCUS_NUMBERS = 5               # from this many numbers on a page, one must be marked hero
RHYTHM_PAGES = 8                # content pages from which the deck needs a breather page or hero band

GRAY_THEME = {
    "navy": "#2E2E2E", "text": "#404040", "gray": "#7A7A7A", "blue": "#8C8C8C", "cyan": "#B3B3B3",
    "sky": "#E3E3E3", "bg": "#F2F2F2", "white": "#FFFFFF", "line": "#BDBDBD", "edge": "#C8C8C8",
    "band": "#EDEDED", "insight": "#E3E3E3", "mist": "#E8E8E8",
    "green": "#8C8C8C", "green2": "#B3B3B3", "orange": "#8C8C8C", "orange2": "#B3B3B3",
    "feature": "#6B6B6B", "feature2": "#8C8C8C", "on_feature": "#EDEDED",
    "teal": "#9A9A9A", "teal2": "#C4C4C4",
}


def text_width(s, size):
    return sum(char_w(ch, size) for ch in str(s))


PLACEHOLDER = re.compile(r"\{[A-Za-z_]\w*(?:[:!][^{}]*)?\}")


def copy_width(s, size):
    """Width of slide copy whose {placeholders} are filled by build.py from the data: a placeholder inside a
    sentence counts as a short number ("0.00"), not as its own name; a field that is one placeholder only
    (a sentence chosen from the data) is not measured here — its width is known once it is filled."""
    s = str(s)
    if PLACEHOLDER.fullmatch(s.strip()):
        return 0
    return text_width(PLACEHOLDER.sub("0.00", s), size)


def parse_facts(text):
    """facts.md -> {ID: {column: cell}}. Markdown table rows whose first cell is F<n>; bullets '- F<n> …' also count."""
    facts, header = {}, None
    for line in text.splitlines():
        st = line.strip()
        if not st.startswith("|"):
            header = header if st == "" else None
            m = FACT_BULLET.match(line)
            if m:
                facts.setdefault(m.group(1), {})
            continue
        cells = [c.strip() for c in st.strip("|").split("|")]
        if header is None:
            if cells and cells[0].upper() == "ID":
                header = [c.lower() for c in cells]
            continue
        if cells and re.fullmatch(r"F\d+", cells[0]):
            facts[cells[0]] = dict(zip(header, cells))
    return facts


def col(row, names):
    for k, v in row.items():
        if any(n in k for n in names):
            return v
    return ""


def as_list(v):
    if v is None:
        return []
    return list(v) if isinstance(v, (list, tuple)) else [v]


APPENDIX_MIN, APPENDIX_SHARE = 3, 0.15        # appendix budget: max(3 pages, 15% of the deck)
PAGE_REF = re.compile(r"(?<![A-Za-z0-9])P\d{1,3}(?![0-9A-Za-z])")   # 「P12」 typed into copy


class Storyboard:
    def __init__(self, path):
        self.path = Path(path)
        self.data = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        self.brief = self.data.get("brief") or {}
        self.min_font = float(self.brief.get("min_font", 18))
        self.frame = self.brief.get("frame", "region")  # region (open, default) | card
        self.parts = self.data.get("parts") or []
        self.appendix = self.data.get("appendix") or []

    def icon_ref(self, ref):
        """Project-relative .svg paths (media/icons/x.svg) resolve against the project folder (plan/..)."""
        ref = str(ref)
        if ref.endswith(".svg") and not Path(ref).is_absolute():
            cand = self.path.resolve().parent.parent / ref
            if cand.exists():
                return str(cand)
        return ref

    def sequence(self):
        """Every page of the deck in order: (kind, page_dict, part_index or None)."""
        seq = [("cover", self.data.get("cover") or {}, None)]
        if self.data.get("toc"):
            seq.append(("toc", {}, None))
        for pg in self.data.get("intro") or []:       # opening pages before the first part (warm-up quiz, route map)
            seq.append(("intro", pg, None))
        for i, part in enumerate(self.parts):
            if self.data.get("section_dividers"):
                seq.append(("section", part, i))
            for pg in part.get("pages") or []:
                seq.append(("content", pg, i))
        if self.data.get("end"):
            seq.append(("end", self.data["end"], None))
        if self.data.get("closing"):
            seq.append(("closing", self.data["closing"], None))
        for pg in self.appendix:
            seq.append(("appendix", pg, None))
        return seq

    def page_numbers(self):
        """{page id (or kind for cover / toc / end / closing): 1-based page number} in deck order.
        Build scripts use it for every cross-reference (「答案在 P5」, 「見附錄 P26」) so a page added or
        moved never leaves a stale number:  PNO = Storyboard("plan/storyboard.yaml").page_numbers()"""
        return {str(pg.get("id") or kind): n for n, (kind, pg, _) in enumerate(self.sequence(), 1)}


# ---------------------------------------------------------------- check
class Checker:
    def __init__(self, sb, facts_path=None, stage=None):
        self.sb, self.stage, self.issues = sb, stage, []
        self.facts = None
        fp = Path(facts_path) if facts_path else sb.path.with_name("facts.md")
        if fp.exists():
            self.facts = parse_facts(fp.read_text(encoding="utf-8"))

    def add(self, level, where, msg):
        self.issues.append((level, where, msg))

    def run(self):
        sb, br = self.sb, self.sb.brief
        for k in REQUIRED_BRIEF:
            if not br.get(k):
                self.add("error", "brief", f"missing brief.{k}")
        if br.get("mode") and br["mode"] not in MODES:
            self.add("warn", "brief", f"mode {br['mode']!r} not in {MODES} — pick the main use: live = the author "
                                      "presents, reading = read without a presenter, hybrid = someone else presents")
        if sb.frame not in ("region", "card"):
            self.add("warn", "brief", f"frame {sb.frame!r} not in ('region', 'card') — treated as region")
        n_content = sum(len(p.get("pages") or []) for p in sb.parts)
        lines = sb.data.get("storylines") or []
        if n_content >= 5 and len(lines) < 2:
            self.add("warn", "deck", "fewer than 2 storylines compared — draft 2-3 alternatives before settling the outline")
        if lines and sum(1 for ln in lines if ln.get("chosen")) != 1:
            self.add("warn", "deck", "storylines: mark exactly one as chosen: true (with why)")
        if not sb.data.get("governing_claim"):
            self.add("error", "deck", "missing governing_claim (the one-sentence answer the whole deck supports)")
        if not sb.data.get("order"):
            self.add("warn", "deck", "missing order (the logic that sequences the parts: time / structure / importance / problem→solution)")
        if not (sb.data.get("cover") or {}).get("title"):
            self.add("error", "cover", "missing cover.title")
        if not sb.parts:
            self.add("error", "deck", "no parts")
        if len(sb.parts) == 1 and n_content > 6:
            self.add("warn", "deck", f"{n_content} pages in a single part — group them into 2-5 parts")
        if len(sb.parts) > 6:
            self.add("warn", "deck", f"{len(sb.parts)} parts — more than 5-6 top-level groups is hard to follow")

        if self.uses_tones() and not br.get("colors"):
            self.add("warn", "brief", "modules use tone / groups but brief.colors does not say what each color means "
                                      "(e.g. blue: 主要分析, orange: 碳排與成本, green: 對照) — reference/decoration.md §6")
        content_pages = [pg for p_ in sb.parts for pg in p_.get("pages") or []]
        if br.get("mode") in ("live", "hybrid") and not sb.data.get("closing"):
            self.add("warn", "deck", "no closing page — add closing: {title, subtitle, points, photo} (Page.closing echoes the cover)")
        if len(content_pages) >= RHYTHM_PAGES and not any(
                pg.get("breather") or any(m.get("kind") == "hero" for m in pg.get("modules") or []) for pg in content_pages):
            self.add("warn", "deck", f"{len(content_pages)} content pages and no breather page or hero band — give the deck a "
                                     "rhythm: breather: {…} on a page every ~4, or a kind: hero module (decoration.md §9)")
        total = len(sb.sequence())
        if isinstance(br.get("pages"), int) and br["pages"] != total:
            self.add("warn", "deck", f"brief.pages={br['pages']} but the storyboard has {total} pages")

        ids, prev_sig = set(), None
        for i, part in enumerate(sb.parts, 1):
            where = f"part{i}"
            if not part.get("title"):
                self.add("error", where, "missing part title")
            if not part.get("claim"):
                self.add("error", where, "missing part claim (summary of its pages — 以上統下)")
            pages = part.get("pages") or []
            if not pages:
                self.add("error", where, "part has no pages")
            if len(pages) > 5:
                self.add("warn", where, f"{len(pages)} pages in one part — split it or merge pages")
            if sb.data.get("section_dividers"):
                prev_sig = None  # a divider page sits between parts
            for pg in pages:
                self.check_page(pg, ids, content=True)
                sig = self.signature(pg)
                if sig and sig == prev_sig:
                    self.add("warn", pg.get("id", "?"), "same skeleton as the previous page — rotate layouts unless the pages are deliberately parallel")
                prev_sig = sig
        for pg in (sb.data.get("intro") or []) + sb.appendix:
            self.check_page(pg, ids, content=False)
        n_app = len(sb.appendix)
        if n_app > max(APPENDIX_MIN, round(total * APPENDIX_SHARE)):
            self.add("warn", "deck", f"appendix is {n_app} of {total} pages — supporting detail should stay small: "
                                     "glossary, data table, methods & sources on one page (decoration.md §12)")
        return self.issues

    def check_page(self, pg, ids, content):
        pid = str(pg.get("id", ""))
        where = pid or "?"
        if not SLUG.match(pid):
            self.add("error", where, "page id must be a slug (letters, digits, - _), used as the file name")
        elif pid in ids:
            self.add("error", where, "duplicate page id")
        ids.add(pid)
        title = str(pg.get("title", ""))
        if not title:
            self.add("error", where, "missing title")
        else:
            if content and len(title) <= 6:
                self.add("warn", where, f"title {title!r} reads like a topic label — write the page's claim")
            if copy_width(title, 26) > TITLE_W:
                self.add("warn", where, f"title needs ~{copy_width(title, 26):.0f}px at 26px — won't fit one header line (≈30 CJK chars)")
        for field in ("title", "takeaway", "sub", "notes"):
            ref = PAGE_REF.search(str(pg.get(field) or ""))
            if ref:
                self.add("warn", where, f"{field} hard-codes page {ref.group(0)} — fill it from Storyboard.page_numbers() "
                                        "so it follows when pages move")
        tk = pg.get("takeaway")
        if content and not tk:
            self.add("error", where, "missing takeaway (one sentence; if you cannot write it, the page has no point)")
        elif tk and copy_width(tk, self.sb.min_font) > TAKEAWAY_W:
            self.add("warn", where, f"takeaway needs ~{copy_width(tk, self.sb.min_font):.0f}px — keep it ≤ 40 CJK chars")
        elif content and tk and copy_width(tk, self.sb.min_font) > CLAUSE_W:
            self.add("warn", where, "takeaway is more than one short clause — distill it (≈ 30 字; → ＝ ≈ instead of connectives)")
        if content and pg.get("sub") and copy_width(pg["sub"], self.sb.min_font) > CLAUSE_W:
            self.add("warn", where, "subtitle is more than one short clause — distill it (≈ 30 字)")
        pts = as_list(pg.get("points"))
        if content and not pts and not pg.get("notes"):       # a speaker script carries the support too
            self.add("warn", where, "no supporting points")
        if len(pts) > 5:
            self.add("warn", where, f"{len(pts)} supporting points — group them (≤ 5)")
        refs = [str(r) for r in as_list(pg.get("facts"))]
        if self.facts is not None:
            for r in refs:
                if r not in self.facts:
                    self.add("error", where, f"fact {r} not defined in facts.md")
                    continue
                row = self.facts[r]
                value = col(row, VALUE_COLS)
                if any(m in value.lower() for m in MISSING):
                    self.add("warn", where, f"fact {r} has no value ({value}) — show 〔待填〕 on the slide or drop it")
                elif any(m in col(row, CONF_COLS).lower() for m in LOW_CONF) and not pg.get("caveat"):
                    self.add("warn", where, f"fact {r} is low-confidence/directional — add a caveat to the page")
        if content and "facts" not in pg and self.has_numbers(pg):
            self.add("warn", where, "copy contains numbers but no facts key — cite facts: [F…], or facts: [] when none are external")
        if self.stage != "outline":
            if pg.get("breather"):
                bd = pg["breather"]
                if not bd.get("value"):
                    self.add("error", where, "breather page needs breather.value (its one giant number)")
                if not bd.get("photo"):
                    self.add("warn", where, "breather page without breather.photo — the photo is what lets the page breathe")
            elif pg.get("layout"):
                self.check_layout(pg, where)
            elif content and self.stage == "layout":
                self.add("error", where, "missing layout")

    @staticmethod
    def signature(pg):
        mods = pg.get("modules") or []
        if not pg.get("layout") or not mods:
            return None
        try:
            areas = [tuple(m["area"]) for m in mods] if pg["layout"] == "custom" else layout_areas(pg["layout"], len(mods))
        except (KeyError, ValueError, TypeError):
            return None
        return tuple(sorted(areas)), bool(pg.get("tall"))

    def check_icons(self, where, j, m):
        refs = [m["icon"]] if m.get("icon") else []

        def walk(o):
            if isinstance(o, dict):
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
            elif isinstance(o, str) and (re.fullmatch(r"[a-z0-9-]+/[a-z0-9-]+", o) and (Path(__file__).resolve().parents[1] / "assets" / "icons" / o.split("/")[0]).is_dir()
                                         or o.endswith(".svg")):
                refs.append(o)
        walk(m.get("data"))
        for r in refs:
            if str(r) in PRESET_SHAPES or str(r) in SEMANTIC_ICONS:
                continue
            try:
                resolve_icon(self.sb.icon_ref(r))
            except FileNotFoundError as e:
                self.add("error", where, f"module {j}: {e}")

    def uses_tones(self):
        found = []

        def walk(o):
            if isinstance(o, dict):
                if o.get("tone") or o.get("groups"):
                    found.append(o)
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        sb = self.sb
        walk([sb.data.get("intro"), sb.data.get("end"), sb.parts, sb.appendix])
        return bool(found)

    @staticmethod
    def has_numbers(pg):
        blobs = [*map(str, as_list(pg.get("points")))]
        for m in pg.get("modules") or []:
            blobs += [str(x) for x in as_list(m.get("text"))]
            blobs.append(str(m.get("data", "")) if m.get("data") else "")
        return any(re.search(r"\d", s) for s in blobs)

    def check_layout(self, pg, where):
        name, mods = pg["layout"], pg.get("modules") or []
        if not mods:
            self.add("error", where, "layout given but no modules")
            return
        if len(mods) > 6:
            self.add("warn", where, f"{len(mods)} modules on one page — too dense for one reader task")
        if name == "custom":
            areas = []
            for j, m in enumerate(mods, 1):
                a = m.get("area")
                if not (isinstance(a, (list, tuple)) and len(a) == 4 and all(isinstance(v, int) for v in a)):
                    self.add("error", where, f"module {j}: custom layout needs area: [col, row, colspan, rowspan]")
                    return
                areas.append(tuple(a))
        else:
            try:
                areas = layout_areas(name, len(mods))
            except (KeyError, ValueError) as e:
                self.add("error", where, str(e).strip("'\""))
                return
            if len(areas) != len(mods):
                self.add("error", where, f"layout {name} has {len(areas)} areas but the page has {len(mods)} modules")
                return
        for j, (c, r, cs, rs) in enumerate(areas, 1):
            if c < 0 or r < 0 or cs < 1 or rs < 1 or c + cs > GRID_COLS or r + rs > GRID_ROWS:
                self.add("error", where, f"module {j}: area {[c, r, cs, rs]} outside the 12×6 grid")
        cells = {}
        for j, (c, r, cs, rs) in enumerate(areas, 1):
            for x in range(c, c + cs):
                for y in range(r, r + rs):
                    if (x, y) in cells:
                        self.add("error", where, f"modules {cells[(x, y)]} and {j} overlap")
                        break
                    cells[(x, y)] = j
                else:
                    continue
                break
        if (name in EVEN_LAYOUTS or (name == "custom" and is_even(areas))) and not pg.get("layout_reason"):
            self.add("warn", where, f"evenly divided layout ({name}) — the scenario guides forbid it unless nothing else works; "
                                    "use an asymmetric layout or state layout_reason")
        sizes = [cs * rs for _, _, cs, rs in areas]
        mains = [j for j, m in enumerate(mods) if m.get("role") == "main"]
        if len(mains) > 1:
            self.add("warn", where, "more than one module has role: main")
        if mains and sizes[mains[0]] < max(sizes):
            self.add("warn", where, "the main module is not on the largest area (size encodes importance)")
        if not mains and len(mods) > 1 and len(set(sizes)) > 1:
            self.add("warn", where, "areas differ in size but no module is role: main")
        def numbers(m):
            d = m.get("data") if isinstance(m.get("data"), dict) else {}
            if m.get("kind") in ("stat", "ring"):
                return len(d.get("items") or []) or (1 if d.get("value") is not None else 0)
            return len(d.get("items") or []) if m.get("kind") == "hero" else 0
        units = [m for m in mods] + [p_ for m in mods for p_ in m.get("parts") or []]
        heroes = [u for u in units if u.get("hero") or u.get("kind") == "hero"]
        if len(heroes) > 1:
            self.add("warn", where, f"{len(heroes)} hero modules — one focus per page")
        elif not heroes and sum(numbers(u) for u in units) >= FOCUS_NUMBERS:
            self.add("warn", where, f"{sum(numbers(u) for u in units)} numbers compete on the page — mark the one that matters "
                                    "hero: true (it grows, the rest shrink) or move some to the notes (decoration.md §9)")
        features = [j for j, m in enumerate(mods, 1) if m.get("feature")]
        if len(features) > 1:
            self.add("warn", where, f"modules {features} are all feature: true — one gradient feature card per page")
        for j, (m, a) in enumerate(zip(mods, areas), 1):
            kind = m.get("kind", "text")
            if kind not in KINDS:
                self.add("warn", where, f"module {j}: unknown kind {kind!r}")
            label = m.get("title") or kind
            if m.get("feature"):
                inner = [str(p_.get("kind", "text")) for p_ in m.get("parts") or []] if kind == "stack" else [kind]
                if self.sb.frame != "card":
                    self.add("warn", where, f"module {j} ({label}): feature: true needs brief.frame: card — ignored in region frame")
                elif any(k not in FEATURE_KINDS for k in inner):
                    self.add("warn", where, f"module {j} ({label}): the feature card draws {', '.join(FEATURE_KINDS)} — "
                                            f"not {', '.join(k for k in inner if k not in FEATURE_KINDS)}")
            if kind == "stack":
                parts = m.get("parts") or []
                if not 2 <= len(parts) <= 3:
                    self.add("warn", where, f"module {j} ({label}): stack needs 2-3 parts, has {len(parts)}")
                for p_ in parts:
                    if str(p_.get("kind", "text")) not in KINDS or p_.get("kind") == "stack":
                        self.add("warn", where, f"module {j} ({label}): stack part kind {p_.get('kind')!r} not allowed")
            single = kind in SINGLE_KINDS or (kind == "text" and len(as_list(m.get("text"))) <= 2)
            if self.sb.frame == "card" and single and a[2] >= BIG_CARD[0] and a[3] >= BIG_CARD[1]:
                self.add("warn", where, f"module {j} ({label}): a {a[2]}×{a[3]} card holding one {kind} reads half empty — "
                                        "compose 2-3 element kinds with kind: stack, or give it a smaller area (decoration.md §6)")
            self.check_icons(where, j, m)
            need = Wireframe.RENDERABLE.get(kind)
            if kind == "stack" and m.get("parts") and not renderable(m):
                self.add("warn", where, f"module {j} ({label}): a stack part has no data — Page.module would render only its text")
            elif kind != "stack" and need and not renderable(m):
                self.add("warn", where, f"module {j} ({m.get('title') or kind}): {kind} has no data.{' / data.'.join(need)} — "
                                        "Page.module would render only its text; add the data or draw it in build.py")
            if kind in TEXT_KINDS:
                x, y, w, h = grid_area(*a, body=(124, TALL_BOTTOM if pg.get("tall") else 446))
                need, avail = self.text_need(m, w, h)
                label = m.get("title") or kind
                if need > avail:
                    self.add("error", where, f"module {j} ({label}): copy needs ~{need:.0f}px, module body has {avail:.0f}px at {self.sb.min_font:g}px — cut copy or enlarge the area")
                elif m.get("role") == "main" and avail > 120 and need / avail < 0.3:
                    self.add("warn", where, f"main module ({label}) fills ~{need / avail:.0%} of its body — add substance (extracted numbers, evidence) or give it a smaller area")
                tw = self.text_width_of(m, w, h)
                for item in as_list(m.get("text")):
                    for para in paragraphs(str(item)):
                        lines = wrap(para, self.sb.min_font, tw)
                        if len(lines) > 1 and len(lines[-1].strip()) <= 2:
                            self.add("warn", where, f"module {j} ({label}): orphan last line {lines[-1].strip()!r} in {para[:20]!r}… — reword")
                        elif any(ln and ln[0] in CLOSE_PUNCT for ln in lines[1:]):
                            self.add("warn", where, f"module {j} ({label}): a line would start with punctuation in {para[:20]!r}… — reword")

    def text_width_of(self, m, w, h):
        _, _, bw, _ = module_body(0, 0, w, h, self.sb.frame, bool(m.get("title")))
        return bw - (LIST_INDENT if m.get("kind") == "list" else 0) - 4  # 4 = text box inset (lint)

    def text_need(self, m, w, h):
        size, lh = self.sb.min_font, 1.3
        _, _, _, avail = module_body(0, 0, w, h, self.sb.frame, bool(m.get("title")))
        tw = self.text_width_of(m, w, h)
        lines = 0
        for item in as_list(m.get("text")):
            for para in paragraphs(str(item)):  # tags don't take space
                lines += len(wrap(para, size, tw))
        return lines * size * lh, avail


def renderable(m):
    """True when Page.module can draw this module from its data (otherwise only its text shows)."""
    if m.get("kind") == "stack":
        parts = m.get("parts") or []
        return bool(parts) and all(str(p_.get("kind", "text")) in TEXT_KINDS or renderable(p_) for p_ in parts)
    d = m.get("data") if isinstance(m.get("data"), dict) else {}
    need = Wireframe.RENDERABLE.get(str(m.get("kind", "text")))
    return bool(need) and any(d.get(k) is not None and d.get(k) != [] for k in need)


# ---------------------------------------------------------------- wireframe
class Wireframe:
    def __init__(self, sb, out):
        self.sb, self.out = sb, Path(out)
        seq = sb.sequence()
        chapters = [str(p.get("short") or p.get("title", ""))[:10] for p in sb.parts]
        self.kit = Kit(self.out, total=len(seq), footer=f"WIREFRAME｜{sb.brief.get('topic', '')}",
                       chapters=chapters, theme=dict(GRAY_THEME, min_font=int(sb.min_font)))
        self.seq = seq

    def build(self):
        for n, (kind, pg, part) in enumerate(self.seq, 1):
            p = self.kit.page()
            getattr(self, f"page_{kind}")(p, n, pg, part)
            stem = {"cover": "cover", "toc": "toc", "end": "end", "closing": "closing", "section": f"section-{(part or 0) + 1}"}.get(kind, pg.get("id", f"p{n}"))
            p.save(f"{n:02d}_{stem}.page", {"cover": "cover", "toc": "table_of_contents", "section": "chapter", "end": "final", "closing": "final"}.get(kind, "content"))
        self.kit.write_manifest("wireframe.pptd", f"WIREFRAME｜{self.sb.brief.get('topic', '')}")
        return self.out / "wireframe.pptd"

    def tag(self, p, text):
        k = self.kit
        p.pill(k.R - 150, 22, 150, text, filled=True)

    def page_cover(self, p, n, pg, part):
        k, t = self.kit, self.kit.th
        self.tag(p, "WIREFRAME")
        p.text(k.L + 24, 170, 820, 130, b(pg.get("title", "")), 40, t["navy"], lineHeight=1.2)
        p.text(k.L + 24, 310, 820, 60, pg.get("subtitle", ""), 22, t["gray"])
        p.text(k.L + 24, 430, 820, 52, f"{self.sb.brief.get('audience', '')}｜{self.sb.brief.get('goal', '')}", 18, t["gray"])

    def page_toc(self, p, n, pg, part):
        k, t = self.kit, self.kit.th
        p.text(k.L + 24, 40, 600, 50, b("目錄"), 30, t["navy"], wrap=False)
        step = min(64, 380 / max(len(self.sb.parts), 1))
        for i, pt in enumerate(self.sb.parts):
            y = 120 + i * step
            p.numdot(k.L + 46, y + 22, 40, str(i + 1))
            p.text(k.L + 84, y + 4, 780, 36, b(pt.get("title", "")), 22, t["navy"], wrap=False, align=["left", "middle"])
        p.footer(n)

    def page_section(self, p, n, pg, part):
        k, t = self.kit, self.kit.th
        p.text(k.L + 24, 150, 300, 90, b(f"{part + 1:02d}"), 64, t["gray"], wrap=False)
        p.text(k.L + 24, 250, 820, 50, b(pg.get("title", "")), 30, t["navy"], wrap=False)
        p.text(k.L + 24, 310, 820, 80, pg.get("claim", ""), 20, t["text"])
        p.footer(n)

    def page_end(self, p, n, pg, part):
        k, t = self.kit, self.kit.th
        p.text(k.L + 24, 60, 820, 50, b(pg.get("title", "")), 30, t["navy"], wrap=False)
        if pg.get("takeaway"):
            p.text(k.L + 24, 120, 820, 60, pg["takeaway"], 20, t["text"])
        for i, pt in enumerate(as_list(pg.get("points"))[:5]):
            y = 200 + i * 56
            p.numdot(k.L + 44, y + 20, 36, str(i + 1))
            p.text(k.L + 80, y, 780, 44, pt, 18, t["text"], align=["left", "middle"])
        p.footer(n)

    def page_closing(self, p, n, pg, part):
        p.closing(pg.get("title", "謝謝聆聽"), pg.get("subtitle", "Q & A"),
                  [(it.get("icon", "check"), it.get("tone"), it.get("text", "")) for it in pg.get("points") or []],
                  pg.get("byline", ""))

    def page_appendix(self, p, n, pg, part):
        self.page_content(p, n, pg, None, label="附錄")

    def page_intro(self, p, n, pg, part):
        self.page_content(p, n, pg, None, label="開場")

    def page_content(self, p, n, pg, part, label=None):
        k = self.kit
        tall = bool(pg.get("tall"))
        refs = ",".join(map(str, as_list(pg.get("facts")))) or "—"
        p.header(None if label else (part or 0) + 1 if self.sb.parts and part is not None else 1, pg.get("title", ""),
                 f"P{n}｜{pg.get('layout', 'no layout')}｜facts {refs}", label=label)
        mods = pg.get("modules") or []
        if pg.get("breather"):
            p.breather(dict(pg["breather"], photo=None))
        elif pg.get("layout") and mods:
            if pg["layout"] == "custom":
                areas = [k.area(*m["area"], tall=tall) for m in mods]
            else:
                areas = k.layout(pg["layout"], len(mods), tall=tall)
            for m, a in zip(mods, areas):
                self.module(p, m, *a)
        else:
            bottom = k.TALL_BOTTOM if tall else k.B
            p.text(k.L, k.T, k.R - k.L, bottom - k.T, "".join(f"<p>• {x}</p>" for x in as_list(pg.get("points"))) or "（尚未規劃版面）", lineHeight=1.4)
        if pg.get("takeaway") and not tall:
            p.takeaway(pg["takeaway"], reveal=pg.get("reveal"))
        p.footer(n)

    RENDERABLE = {"chart": ("rows",), "table": ("rows",), "diagram": ("steps",), "image": ("src",),
                  "stat": ("value", "items"), "ring": ("value", "items"), "bar": ("value", "items"), "pictogram": ("n",),
                  "rank": ("rows",), "dumbbell": ("rows",), "stack": ("parts",), "hero": ("items",)}

    def module(self, p, m, x, y, w, h):
        """Same renderer and frame as the final build (Page.module); visuals without data become a
        crossed placeholder carrying their description, inside the same frame."""
        t, size = self.kit.th, self.kit.th["min_font"]
        kind = str(m.get("kind", "text"))
        m = dict(m)
        if m.get("icon"):
            m["icon"] = self.sb.icon_ref(m["icon"])
        if kind == "diagram" and (m.get("data") or {}).get("steps"):
            m["data"] = dict(m["data"], steps=[[*st[:2], self.sb.icon_ref(st[2])] if len(st) > 2 and st[2] else st
                                               for st in m["data"]["steps"]])
        if kind in TEXT_KINDS or renderable(m):
            p.module(m, x, y, w, h, frame=self.sb.frame)
            return
        if self.sb.frame == "card":
            p.card(x, y, w, h, m.get("title"), m.get("icon"))
        else:
            p.region(x, y, w, h, m.get("title"), m.get("icon"), main=m.get("role") == "main")
        bx, by, bw, bh = module_body(x, y, w, h, self.sb.frame, bool(m.get("title")))
        if bh < 10:
            return
        p.solid(bx, by, bw, bh, t["sky"])
        p.line(bx, by, bw, bh, f"0,0 {bw},{bh}", color=t["line"], width=1)
        p.line(bx, by, bw, bh, f"0,{bh} {bw},0", color=t["line"], width=1)
        desc = " ".join(map(str, as_list(m.get("text")))) or str(m.get("data", "") or "")
        lw = min(bw - 16, 420)
        lh = min(bh - 8, (2 if desc else 1) * size * 1.3 + 8)
        p.solid(bx + (bw - lw) / 2, by + (bh - lh) / 2, lw, lh, t["white"])
        if desc:
            cap = int((lw - 8) / size) - 1
            desc = desc if len(desc) <= cap else desc[:max(cap - 1, 1)] + "…"
        p.text(bx + (bw - lw) / 2 + 4, by + (bh - lh) / 2 + 4, lw - 8, lh - 8,
               f"<p>{b(kind.upper())}</p>" + (f"<p>{desc}</p>" if desc else ""), size, t["text"],
               align=["center", "middle"], lineHeight=1.3)


def grouped(issues, at=3):
    """One line for a message repeated in `at` or more places ("×19 no supporting points — journey, …"),
    so a deck-wide habit does not bury the one-off problems; counts stay per page."""
    seen = {}
    for level, where, msg in issues:
        seen.setdefault((level, msg), []).append(where)
    out = []
    for level, where, msg in issues:
        ws = seen.get((level, msg))
        if ws is None:
            continue
        if len(ws) >= at:
            out.append((level, f"×{len(ws)}", f"{msg} — {', '.join(ws[:8])}{' …' if len(ws) > 8 else ''}"))
        else:
            out += [(level, w, msg) for w in ws]
        seen[(level, msg)] = None
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("storyboard")
    c.add_argument("--facts")
    c.add_argument("--stage", choices=["outline", "layout"])
    w = sub.add_parser("wireframe")
    w.add_argument("storyboard")
    w.add_argument("--out", required=True)
    w.add_argument("--force", action="store_true")
    a = ap.parse_args()

    sb = Storyboard(a.storyboard)
    if a.cmd == "check":
        issues = Checker(sb, a.facts, a.stage).run()
        for level, where, msg in grouped(issues):
            print(f"{level:5} {where:<20} {msg}")
        errors = sum(1 for i in issues if i[0] == "error")
        print(f"\n{len(sb.sequence())} pages · {errors} error(s), {len(issues) - errors} warning(s)")
        sys.exit(1 if errors else 0)

    out = Path(a.out)
    if out.exists() and any(out.iterdir()):
        if not a.force:
            sys.exit(f"{out} is not empty; pass --force to replace it")
        shutil.rmtree(out)
    print(Wireframe(sb, out).build())


if __name__ == "__main__":
    # Emit UTF-8 regardless of the Windows code page (cp950, cp936…) so callers that capture the
    # output as UTF-8 — agents, tests, CI — can read CJK messages.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    main()
