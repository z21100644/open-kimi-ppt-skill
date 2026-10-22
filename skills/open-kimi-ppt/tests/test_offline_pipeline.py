#!/usr/bin/env python3
"""Offline pipeline: pptd_kit → lint_pptd → pptd2pptx (no browser, no network)."""
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURE = ROOT / "tests" / "fixtures" / "minimal" / "minimal.pptd"
SAMPLE = ROOT / "reference" / "design_system" / "academic" / "bright-blue-bento-briefing" / "sample_build.py"
sys.path.insert(0, str(SCRIPTS))


def run(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, encoding="utf-8")


class OfflinePipelineTest(unittest.TestCase):
    def test_minimal_fixture_converts_with_root_level_fade(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "minimal.pptx"
            r = run(SCRIPTS / "pptd2pptx.py", FIXTURE, "--output", out)
            self.assertEqual(r.returncode, 0, r.stderr)
            with zipfile.ZipFile(out) as z:
                self.assertIsNone(z.testzip())
                xml = z.read("ppt/slides/slide1.xml").decode("utf-8")
            # transition must be a direct child of p:sld, after cSld (Office ignores it elsewhere)
            self.assertEqual(xml.count("<p:transition"), 1)
            self.assertLess(xml.index("</p:cSld>"), xml.index("<p:transition"))

    def test_refuses_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "x.pptx"
            out.write_bytes(b"keep")
            r = run(SCRIPTS / "pptd2pptx.py", FIXTURE, "--output", out)
            self.assertNotEqual(r.returncode, 0)
            self.assertEqual(out.read_bytes(), b"keep")

    def test_transition_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "x.pptx"
            self.assertEqual(run(SCRIPTS / "pptd2pptx.py", FIXTURE, "-o", out, "--transition", "none").returncode, 0)
            with zipfile.ZipFile(out) as z:
                self.assertNotIn("<p:transition", z.read("ppt/slides/slide1.xml").decode("utf-8"))

    def test_kit_sample_is_lint_clean_and_converts(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(run(SAMPLE, tmp).returncode, 0)
            manifest = Path(tmp) / "sample.pptd"
            lint = run(SCRIPTS / "lint_pptd.py", manifest, "--strict")
            self.assertEqual(lint.returncode, 0, lint.stdout)
            self.assertIn("0 error(s), 0 warning(s)", lint.stdout)
            r = run(SCRIPTS / "pptd2pptx.py", manifest, "--force")
            self.assertEqual(r.returncode, 0, r.stderr)
            with zipfile.ZipFile(Path(tmp) / "sample.pptx") as z:
                self.assertEqual(len([n for n in z.namelist() if n.startswith("ppt/slides/slide")]), 3)

    def test_template_samples_are_lint_clean_and_convert(self):
        """The briefing templates' samples (cover recipe + module pages) in every kit theme."""
        ink = SAMPLE.parents[1] / "ink-ivory-briefing" / "sample_build.py"
        sage = SAMPLE.parents[1] / "sage-mist-briefing" / "sample_build.py"
        glass = SAMPLE.parents[1] / "ios-glass-briefing" / "sample_build.py"
        clear = SAMPLE.parents[1] / "clear-briefing" / "sample_build.py"
        for args in ((ink,), (sage,), (glass,), (clear,), (ink, "bright-blue")):
            with self.subTest(args=[Path(a).parent.name if isinstance(a, Path) else a for a in args]), \
                    tempfile.TemporaryDirectory() as tmp:
                r = run(args[0], tmp, *args[1:])
                self.assertEqual(r.returncode, 0, r.stderr)
                manifest = Path(tmp) / "sample.pptd"
                lint = run(SCRIPTS / "lint_pptd.py", manifest, "--strict")
                self.assertIn("0 error(s), 0 warning(s)", lint.stdout, lint.stdout)
                self.assertEqual(run(SCRIPTS / "pptd2pptx.py", manifest, "--force").returncode, 0)
                with zipfile.ZipFile(Path(tmp) / "sample.pptx") as z:
                    self.assertEqual(len([n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)]), 4)

    def test_lint_flags_small_font_orphan_and_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pages").mkdir()
            (root / "d.pptd").write_text("version: v2\nsize: [960, 540]\npages: [pages/a.page]\n", encoding="utf-8")
            (root / "pages" / "a.page").write_text(
                "elements:\n"
                "- {elementId: t1, elementType: text, bounds: [444, 200, 466, 50], content: {text: 柴油與電動路線的效率差距，以及結果是否受最大路線影響, fontSize: 18}}\n"
                "- {elementId: t2, elementType: text, bounds: [10, 10, 300, 30], content: {text: 小字, fontSize: 14}}\n"
                "- {elementId: t3, elementType: text, bounds: [900, 500, 100, 60], content: {text: x, fontSize: 18}}\n",
                encoding="utf-8")
            r = run(SCRIPTS / "lint_pptd.py", root / "d.pptd", "--strict")
            self.assertNotEqual(r.returncode, 0)
            for kind in ("orphan", "font", "bounds"):
                self.assertIn(kind, r.stdout)

    def test_lint_flags_container_collision_icon_and_scale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pages").mkdir()
            (root / "d.pptd").write_text("version: v2\nsize: [960, 540]\npages: [pages/a.page]\n", encoding="utf-8")
            (root / "pages" / "a.page").write_text(
                "elements:\n"
                "- {elementId: card, elementType: shape, shapeName: roundRect, bounds: [100, 100, 300, 120], fill: {type: solid, color: '#FFFFFF'}}\n"
                "- {elementId: t1, elementType: text, bounds: [120, 120, 260, 120], content: {text: " + "超出卡片的說明文字" * 9 + ", fontSize: 18}}\n"
                "- {elementId: t2, elementType: text, bounds: [500, 100, 300, 30], content: {text: 標題文字, fontSize: 20}}\n"
                "- {elementId: t3, elementType: text, bounds: [520, 110, 300, 30], content: {text: 重疊文字, fontSize: 18}}\n"
                "- {elementId: i1, elementType: icon, bounds: [700, 300, 40, 40], iconName: 'fas:lightbulb'}\n",
                encoding="utf-8")
            r = run(SCRIPTS / "lint_pptd.py", root / "d.pptd", "--scale", "18")
            for kind in ("container", "collision", "icon", "scale"):
                self.assertIn(kind, r.stdout)
            self.assertIn("font sizes in use: 18, 20", r.stdout)

    def test_lint_ignores_a_fading_sheen_as_container(self):
        # a glass highlight over the top of a card fades to clear: text crossing it is not "past" it
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pages").mkdir()
            (root / "d.pptd").write_text("version: v2\nsize: [960, 540]\npages: [pages/a.page]\n", encoding="utf-8")
            sheen = ("{type: gradient, angle: 90, stops: [{position: 0, color: '#FFFFFF8C'}, "
                     "{position: 1, color: '#FFFFFF00'}]}")
            (root / "pages" / "a.page").write_text(
                "elements:\n"
                "- {elementId: card, elementType: shape, shapeName: roundRect, bounds: [100, 100, 400, 300], fill: {type: solid, color: '#FFFFFF'}}\n"
                "- {elementId: sheen, elementType: shape, shapeName: roundRect, bounds: [101, 101, 398, 100], fill: " + sheen + "}\n"
                "- {elementId: t1, elementType: text, bounds: [120, 180, 300, 60], content: {text: 跨過高光的文字, fontSize: 18}}\n",
                encoding="utf-8")
            out = run(SCRIPTS / "lint_pptd.py", root / "d.pptd").stdout
        self.assertNotIn("container", out)

    def test_kit_table_ratios_and_lint_table_cell_chart_checks(self):
        sys.path.insert(0, str(SCRIPTS))
        from pptd_kit import Kit
        with tempfile.TemporaryDirectory() as tmp:
            kit = Kit(tmp, total=1)
            p = kit.page()
            el = p.table([36, 124, 600, 120], [["a", "b"], ["c", "很長很長很長很長很長很長很長很長很長很長的儲存格文字"]], [450, 150])
            self.assertEqual(el["columnWidths"], [0.75, 0.25])                 # px -> ratios
            self.assertAlmostEqual(sum(el["rowHeights"]), 1)
            bad = dict(el, elementId="tbad", columnWidths=[450, 150])
            p.add(bad)
            p.chart([36, 300, 400, 150], ["k", "v"], [["x", 1]], [{"type": "bar", "encode": {"x": "k", "y": "w"}, "color": "#000000"}])
            p.save("01.page")
            kit.write_manifest("d.pptd", "d")
            out = run(SCRIPTS / "lint_pptd.py", Path(tmp) / "d.pptd").stdout
        self.assertIn("must be ratios", out)
        self.assertIn("cell", out)
        self.assertIn("'color' is not PPTD", out)
        self.assertIn("encode.y = 'w'", out)

    def test_horizontal_bar_infers_category_axis_from_data(self):
        # Page.module(horizontal: true) encodes y = category column without yAxis.type; the converter
        # must infer the axis type from the data (PPTD §5), or it writes names as numbers and
        # PowerPoint refuses to open the file.
        from pptd_kit import Kit
        with tempfile.TemporaryDirectory() as tmp:
            kit = Kit(tmp, total=1)
            p = kit.page()
            p.module({"kind": "chart", "title": "排名", "data": {"cols": ["公司", "值"], "horizontal": True,
                      "rows": [["甲", 4.0], ["乙", 32.5]]}}, 36, 124, 600, 300)
            p.save("01.page")
            kit.write_manifest("d.pptd", "d")
            r = run(SCRIPTS / "pptd2pptx.py", Path(tmp) / "d.pptd", "--force")
            self.assertEqual(r.returncode, 0, r.stderr)
            with zipfile.ZipFile(Path(tmp) / "d.pptx") as z:
                xml = z.read("ppt/charts/chart1.xml").decode("utf-8")
        self.assertIn('<c:barDir val="bar"/>', xml)
        cat = xml[xml.index("<c:cat>"):xml.index("</c:cat>")]
        self.assertIn("<c:strRef>", cat)
        self.assertIn("甲", cat)

    def test_lint_flags_plain_pages_and_decoration_clears_it(self):
        from pptd_kit import Kit
        with tempfile.TemporaryDirectory() as tmp:
            kit = Kit(tmp, total=2)
            p = kit.page()                               # text + hairlines only
            p.text(36, 124, 600, 40, "只有文字的頁面", 26)
            p.solid(36, 170, 888, 2, "#0B1F3A")
            p.save("01_plain.page")
            p = kit.page()                               # same copy, decorated without cards
            p.band(0, 110, kit.th["sky"])
            p.watermark(700, 140, "01", 160)
            p.text(36, 124, 600, 40, "只有文字的頁面", 26)
            p.motif("rings", "br")
            p.save("02_decorated.page")
            kit.write_manifest("d.pptd", "d")
            out = run(SCRIPTS / "lint_pptd.py", Path(tmp) / "d.pptd").stdout
            self.assertEqual(run(SCRIPTS / "pptd2pptx.py", Path(tmp) / "d.pptd", "--force").returncode, 0)
        plain = [ln for ln in out.splitlines() if " plain " in ln]
        self.assertEqual(len(plain), 1, out)
        self.assertIn("01_plain", plain[0])
        self.assertNotIn("contrast", out)                # 12%-alpha watermark is decoration, not copy
        self.assertNotIn("bounds", out)                  # corner motifs stay inside the canvas

    def test_lint_flags_half_empty_cards(self):
        from pptd_kit import Kit
        with tempfile.TemporaryDirectory() as tmp:
            kit = Kit(tmp, total=2)
            p = kit.page()                               # one number floating in a tall card
            p.card(36, 124, 360, 322, "算給你看", "star5")
            p.stat(56, 200, 300, "≈ 3", " 億元", "年排 100 萬噸")
            p.save("01_sparse.page")
            p = kit.page()                               # same card, composed: number, rule, bar, captions
            p.card(36, 124, 360, 322, "算給你看", "star5")
            p.stat(56, 200, 300, "≈ 3", " 億元", "年排 100 萬噸")
            p.hdash(56, 300, 320)
            p.text(56, 316, 320, 28, "再生能源占比", 18)
            p.bar(56, 356, 320, 0.2, 18, target=0.6)
            p.text(56, 390, 320, 28, "20%（目標 60%）", 18)
            p.save("02_composed.page")
            kit.write_manifest("d.pptd", "d")
            out = run(SCRIPTS / "lint_pptd.py", Path(tmp) / "d.pptd").stdout
        sparse = [ln for ln in out.splitlines() if " sparse " in ln]
        self.assertEqual(len(sparse), 1, out)
        self.assertIn("01_sparse", sparse[0])

    def test_lint_sparse_counts_a_hero_number_under_a_first_line_caption(self):
        """A caption on a card's first line reads as its title; the hero number that starts inside the
        title band and runs into the body still counts (no sparse warning on a full breather card)."""
        from pptd_kit import Kit
        with tempfile.TemporaryDirectory() as tmp:
            kit = Kit(tmp, total=1)
            p = kit.page()
            p.card(400, 124, 524, 322)
            p.text(424, 140, 460, 28, "1 路用掉車隊兩成的電", 20)
            p.gtext(420, 166, 470, 120, "20.4%", 96)
            p.hdash(424, 300, 476)
            p.stat(424, 316, 220, "261", " 萬度", "年用電量")
            p.bar(424, 410, 476, 0.2, 12, target=0.6)
            p.save("01.page")
            kit.write_manifest("d.pptd", "d")
            out = run(SCRIPTS / "lint_pptd.py", Path(tmp) / "d.pptd").stdout
        self.assertNotIn(" sparse ", out, out)

    def test_clear_art_direction(self):
        """theme "clear": px radius on every card, pale feature card with dark copy, the hero band solid,
        numbered tiles (no circles), a solid divider, a source footer — and lint-clean."""
        from pptd_kit import THEMES, Kit
        th = THEMES["clear"]
        with tempfile.TemporaryDirectory() as tmp:
            kit = Kit(tmp, total=2, chapters=["a", "b"], theme="clear")
            p = kit.page()
            p.header(1, "結論句標題", "副標")
            p.modules({"layout": "split-2-1", "modules": [
                {"kind": "stack", "title": "費率", "icon": "money", "parts": [
                    {"kind": "stat", "data": {"items": [{"value": "300", "label": "一般", "tone": "orange"},
                                                        {"value": "50", "label": "優惠", "tone": "green"}]}},
                    {"kind": "list", "text": ["減量計畫經核定", "可享優惠費率"]}]},
                {"kind": "stack", "feature": True, "title": "算給你看", "icon": "calc", "parts": [
                    {"kind": "stat", "data": {"value": "≈ 3", "unit": " 億元", "label": "年排 100 萬噸"}},
                    {"kind": "bar", "data": {"items": [{"label": "優惠後", "value": 0.17, "display": "≈ 0.5 億"}]}}]}]},
                      frame="card")
            p.takeaway("一句話重點")
            p.footer(1, source="資料：本研究整理")
            p.save("01.page")
            q = kit.page()
            q.header(2, "結論橫幅", "副標")
            q.modules({"layout": "hero-split", "modules": [
                {"kind": "hero", "data": {"items": [{"label": "前", "value": "0.81"}, {"label": "後", "value": "0.64"}]}},
                {"kind": "text", "title": "說明", "text": "算進碳排後下降"}, {"kind": "text", "title": "分布", "text": "4 家＝1"}]},
                      frame="card")
            q.footer(2)
            q.save("02.page")
            r = kit.page()                               # markers and dividers on their own (not linted)
            r.numdot(60, 300, 32, "1")
            r.hdash(100, 300, 200)
            r.save("03.page")
            kit.write_manifest("m.pptd", "m", pages=["01.page", "02.page"])
            lint = run(SCRIPTS / "lint_pptd.py", Path(tmp) / "m.pptd")
        self.assertIn("0 error(s), 0 warning(s)", lint.stdout, lint.stdout)
        shapes = [e for e in p.els if e["elementType"] == "shape"]
        cards = [e for e in shapes if e.get("shapeName") == "roundRect" and e["bounds"][1] == 124]
        self.assertEqual(len(cards), 2)
        for c_ in cards:
            w, h = c_["bounds"][2:]
            self.assertEqual(c_["adjustments"], [int(min(16 / min(w, h), 0.5) * 100000)])
        feat = next(c_ for c_ in cards if c_["fill"].get("stops") and c_["fill"]["stops"][0]["color"] == th["feature_tint"][0][1])
        fx, fy, fw, fh = feat["bounds"]
        inside = [e for e in p.els if e["elementType"] == "text" and fx <= e["bounds"][0] < fx + fw and fy <= e["bounds"][1] < fy + fh]
        self.assertTrue(inside and all((e["content"].get("color") or "").upper() != "#FFFFFF" for e in inside))
        marks = [e for e in r.els if e["elementType"] == "shape"]
        self.assertEqual(marks[0]["shapeName"], "roundRect")                                            # tile, not dot
        self.assertTrue(any(e["bounds"] == [100, 300, 200, 1] for e in marks))                           # solid divider
        self.assertFalse(any(e["elementType"] == "line" for e in p.els + r.els))
        src = next(e for e in p.els if e["elementType"] == "text" and e["content"]["text"] == "資料：本研究整理")
        self.assertEqual((src["bounds"][1], src["content"]["color"]), (th["footer_y"], th["source_color"]))
        band = next(e for e in q.els if e["elementType"] == "shape" and e["bounds"][1] == 124)
        self.assertEqual(band["fill"]["stops"][-1]["color"][:7], th["feature"])                     # the one solid surface

    def test_glass_material_helpers(self):
        """Wallpaper blobs blur on a layer of their own hue (no gray fringe); tinted capsules keep 4.5:1."""
        from PIL import Image
        from pptd_kit import contrast_ratio, deepen, tint, wallpaper
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "w.jpg"
            wallpaper(path, [(200, 100, 120, (255, 255, 255), 255)], "#FFFFFF", size=(400, 200), blur=60)
            lo = min(lo_ for lo_, _ in Image.open(path).convert("RGB").getextrema())
        self.assertGreaterEqual(lo, 250)                 # blurring transparent black would drop to gray
        for color in ("#F08C2E", "#2E9E5B", "#1A73E8", "#14A39A"):
            fill = tint(color, 0.14)
            self.assertGreaterEqual(contrast_ratio(deepen(color, fill), fill), 4.5, color)

    def test_lint_flags_decoration_under_text_or_over_card_edges(self):
        from pptd_kit import Kit
        with tempfile.TemporaryDirectory() as tmp:
            kit = Kit(tmp, total=3)
            for name, (rx, ry) in [("01_under_text", (120, 240)), ("02_over_edge", (390, 140)), ("03_clear", (330, 170))]:
                p = kit.page()
                p.card(36, 124, 360, 322, "卡片", "star5", feature=True)
                p.text(56, 230, 300, 40, "0.81 → 0.64", 30, "#FFFFFF", bold=True)
                for r in (20, 34):
                    p.shape(rx - r, ry - r, 2 * r, 2 * r, None, "ellipse", border={"style": "solid", "width": 1, "color": "#FFFFFF2E"})
                p.save(f"{name}.page")
            kit.write_manifest("d.pptd", "d")
            out = run(SCRIPTS / "lint_pptd.py", Path(tmp) / "d.pptd").stdout
        deco = [ln for ln in out.splitlines() if " deco " in ln]
        self.assertTrue(any("01_under_text" in ln and "under text" in ln for ln in deco), out)
        self.assertTrue(any("02_over_edge" in ln and "card edge" in ln for ln in deco), out)
        self.assertFalse(any("03_clear" in ln for ln in deco), out)

    def test_kit_decoration_components(self):
        from pptd_kit import Kit
        with tempfile.TemporaryDirectory() as tmp:
            kit = Kit(tmp, total=1)
            p = kit.page()
            band = p.band(0, 100)
            self.assertEqual(band["bounds"], [0, 0, 960, 100])
            self.assertTrue(p.watermark(0, 0, "02")["content"]["color"].endswith("1F"))
            n = len(p.els)
            p.pictogram(36, 200, 10, 1, "ellipse")
            self.assertEqual(len(p.els) - n, 10)
            for corner in ("tl", "tr", "bl", "br"):
                for kind in ("dots", "rings", "leaf"):
                    p.motif(kind, corner)
            for el in p.els:
                x, y, w, h = el["bounds"]
                self.assertTrue(-0.5 <= x and -0.5 <= y and x + w <= 960.5 and y + h <= 540.5, el["bounds"])
            with self.assertRaises(ValueError):
                p.motif("stars")

    def test_lint_contrast_and_readable_labels(self):
        sys.path.insert(0, str(SCRIPTS))
        from pptd_kit import Kit, readable_on
        self.assertEqual(readable_on("#C6F24E", "#FFFFFF", "#141414"), "#141414")   # dark text on lime
        self.assertEqual(readable_on("#1A73E8", "#FFFFFF", "#141414"), "#FFFFFF")   # white on blue
        with tempfile.TemporaryDirectory() as tmp:
            kit = Kit(tmp, total=1, theme={"blue": "#C6F24E", "cyan": "#C6F24E"})
            p = kit.page()
            p.numdot(100, 100, 28, "1")                                     # label color picked automatically
            p.pill(200, 100, 120, "標籤", "#FFB25B")                         # pale outline pill -> navy label
            p.text(200, 300, 300, 40, "淺色字在淺底上", 18, "#EEEEEE")         # explicit low contrast
            p.save("01.page")
            kit.write_manifest("d.pptd", "d")
            out = run(SCRIPTS / "lint_pptd.py", Path(tmp) / "d.pptd").stdout
        self.assertEqual(out.count("contrast"), 1, out)
        self.assertIn("淺色字在淺底上", out)

    def test_lint_label_on_a_field_border_and_ticks_at_the_origin(self):
        # a number in a dot that straddles two quadrant fields belongs to the field its glyphs sit in; two axis
        # ticks whose line leading touches at a chart's origin are not a collision; real overlaps still are
        els = [
            "{elementId: top, elementType: shape, shapeName: rect, bounds: [300, 100, 300, 150], fill: {type: solid, color: '#E6EDEA'}}",
            "{elementId: bot, elementType: shape, shapeName: rect, bounds: [300, 250, 300, 150], fill: {type: solid, color: '#F4EAE5'}}",
            "{elementId: num, elementType: text, bounds: [400, 248, 22, 22], content: {text: '3', fontSize: 18, wrap: false, align: [center, middle]}}",
            "{elementId: y0, elementType: text, bounds: [50, 388, 42, 24], content: {text: '0.0', fontSize: 18, wrap: false, align: [right, middle]}}",
            "{elementId: x0, elementType: text, bounds: [76, 406, 48, 22], content: {text: '0.4', fontSize: 18, wrap: false, align: [center, top]}}",
            "{elementId: a, elementType: text, bounds: [600, 450, 200, 24], content: {text: 重疊的文字, fontSize: 18}}",
            "{elementId: b, elementType: text, bounds: [610, 455, 200, 24], content: {text: 重疊的文字, fontSize: 18}}",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pages").mkdir()
            (root / "d.pptd").write_text("version: v2\nsize: [960, 540]\npages: [pages/a.page]\n", encoding="utf-8")
            (root / "pages" / "a.page").write_text("elements:\n" + "".join(f"- {e}\n" for e in els), encoding="utf-8")
            out = run(SCRIPTS / "lint_pptd.py", root / "d.pptd").stdout
        self.assertNotIn("container", out)
        hits = [ln for ln in out.split("\n") if "collision" in ln]
        self.assertEqual(len(hits), 1, out)
        self.assertIn(" b ", f" {hits[0].split()[2]} ")

    def test_kit_notes_reach_the_pptx_notes_pane(self):
        from pptd_kit import Kit
        with tempfile.TemporaryDirectory() as tmp:
            kit = Kit(tmp, total=1, footer="t", chapters=["一"])
            p = kit.page()
            p.text(100, 100, 400, 40, "本頁內容", 18)
            p.notes = "講稿：先說結論，再看圖"
            p.save("01_a.page")
            kit.write_manifest("d.pptd", "t")
            self.assertIn("notes:", (Path(tmp) / "pages" / "01_a.page").read_text(encoding="utf-8"))
            r = run(SCRIPTS / "pptd2pptx.py", Path(tmp) / "d.pptd", "--force")
            self.assertEqual(r.returncode, 0, r.stderr)
            with zipfile.ZipFile(Path(tmp) / "d.pptx") as z:
                notes = [n for n in z.namelist() if n.startswith("ppt/notesSlides/") and n.endswith(".xml")]
                self.assertTrue(notes)
                self.assertIn("先說結論", z.read(notes[0]).decode("utf-8"))

    def test_takeaway_reveal_capsule_in_every_style(self):
        from pptd_kit import Kit
        for theme in ("bright-blue", "ink-ivory", "ios-glass", "clear"):
            with tempfile.TemporaryDirectory() as tmp:
                kit = Kit(tmp, total=1, footer="t", chapters=["一"], theme=theme)
                p = kit.page()
                p.takeaway("算進碳排後平均分數下降", reveal="第 3 題答案：C")
                p.save("01_a.page")
                kit.write_manifest("d.pptd", "t")
                page = (Path(tmp) / "pages" / "01_a.page").read_text(encoding="utf-8")
                self.assertIn("第 3 題答案：C", page, theme)
                out = run(SCRIPTS / "lint_pptd.py", Path(tmp) / "d.pptd").stdout
                for kind in ("collision", "container", "contrast", "nowrap"):
                    self.assertNotIn(kind, out, f"{theme}: {out}")

    def test_east_asian_fonts_follow_the_decks_script(self):
        from pptd_kit import Kit
        for text, lang, face in (("这个数据说明了产业的变化", None, "Microsoft YaHei"),
                                 ("這個數據說明了產業的變化", None, "Microsoft JhengHei"),
                                 ("甲客運・乙客運・丙客運・丁客運・戊客運・己客運", None, "Microsoft JhengHei"),
                                 ("これはテストのページです", None, "Yu Gothic"),
                                 ("이 페이지는 시험용입니다", None, "Malgun Gothic"),
                                 ("這個數據說明了產業的變化", "zh-CN", "Microsoft YaHei")):
            with tempfile.TemporaryDirectory() as tmp:
                kit = Kit(tmp, total=1, footer="t", chapters=["一"])
                p = kit.page()
                p.text(100, 100, 600, 40, text, 18)
                p.save("01_a.page")
                kit.write_manifest("d.pptd", "t")
                args = [SCRIPTS / "pptd2pptx.py", Path(tmp) / "d.pptd", "--force"] + (["--lang", lang] if lang else [])
                r = run(*args)
                self.assertEqual(r.returncode, 0, r.stderr)
                with zipfile.ZipFile(Path(tmp) / "d.pptx") as z:
                    xml = z.read("ppt/slides/slide1.xml").decode("utf-8")
                self.assertIn(f'typeface="{face}"', xml, text)

    def test_kit_api_index_documents_every_helper(self):
        out = run(SCRIPTS / "pptd_kit.py").stdout
        for name in ("Page.takeaway(", "Page.text(", "Kit.area(", "free_spot(", "THEMES: ", "LAYOUTS: "):
            self.assertIn(name, out)
        lines = out.splitlines()
        sigs = [i for i, ln in enumerate(lines) if "(" in ln and not ln.startswith(" ")
                and not ln.startswith(("THEMES", "LAYOUTS", "SEMANTIC"))]
        self.assertGreater(len(sigs), 80)
        self.assertTrue(all(lines[i + 1].strip() for i in sigs), "a public helper without a doc line")
        narrowed = run(SCRIPTS / "pptd_kit.py", "reveal").stdout
        self.assertIn("Page.takeaway(", narrowed)
        self.assertNotIn("Page.ring(", narrowed)

    def test_free_spot_avoids_dots_labels_and_bounds(self):
        from pptd_kit import free_spot, hit
        taken = [(95, 95, 10, 10)]                                   # the dot itself
        a = free_spot(100, 100, 5, 40, 20, taken, (0, 0, 300, 300))
        self.assertIsNotNone(a)
        self.assertFalse(any(hit(a, t) for t in taken))
        taken.append(a)
        b = free_spot(110, 100, 5, 40, 20, taken + [(105, 95, 10, 10)], (0, 0, 300, 300))
        self.assertIsNotNone(b)
        self.assertFalse(hit(a, b))
        self.assertIsNone(free_spot(10, 10, 5, 40, 20, [(5, 5, 10, 10)], (0, 0, 20, 20)))

    def test_render_writes_readable_sheets_for_long_decks(self):
        from PIL import Image
        from render_pptx import write_sheets
        with tempfile.TemporaryDirectory() as tmp:
            pages = Path(tmp) / "pages"
            pages.mkdir()
            for i in range(1, 11):
                Image.new("RGB", (192, 108), "#DDE3EA").save(pages / f"{i}.png")
            (Path(tmp) / "overview-9.jpg").write_bytes(b"stale")
            sheets = write_sheets(pages, list(range(1, 11)), Path(tmp), 2, 6)
            self.assertEqual([p.name for p in sheets], ["overview-1.jpg", "overview-2.jpg"])
            self.assertFalse((Path(tmp) / "overview-9.jpg").exists())
            self.assertEqual(write_sheets(pages, [1, 2], Path(tmp), 2, 0), [])

    def test_render_offers_font_embedding_and_pdf_copy(self):
        out = run(SCRIPTS / "render_pptx.py", "--help").stdout
        self.assertIn("--embed-fonts", out)
        self.assertIn("--pdf-to", out)

    def test_lint_layout_checks_quiet_on_kit_sample(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(run(SAMPLE, tmp).returncode, 0)
            out = run(SCRIPTS / "lint_pptd.py", Path(tmp) / "sample.pptd").stdout
            for kind in ("container", "collision"):
                self.assertNotIn(kind, out)


if __name__ == "__main__":
    unittest.main()
