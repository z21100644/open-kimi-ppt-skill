#!/usr/bin/env python3
"""Storyboard stage: grid math, storyboard check, wireframe → lint → pptd2pptx (offline)."""
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURE = ROOT / "tests" / "fixtures" / "storyboard"
sys.path.insert(0, str(SCRIPTS))

from pptd_kit import LAYOUTS, grid_area, layout_areas  # noqa: E402


def run(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, encoding="utf-8")


class GridTest(unittest.TestCase):
    def test_full_grid_matches_body_box(self):
        self.assertEqual(grid_area(0, 0, 12, 6), (36, 124, 888, 322))
        self.assertEqual(grid_area(0, 0, 6, 3), (36, 124, 436, 153))

    def test_named_layouts_stay_in_body_with_exact_gutters(self):
        for name in [*LAYOUTS, "hero-top"]:
            boxes = [grid_area(*a) for a in layout_areas(name, 4)]
            for x, y, w, h in boxes:
                self.assertGreaterEqual(x, 36, name)
                self.assertLessEqual(x + w, 924, name)
                self.assertGreaterEqual(y, 124, name)
                self.assertLessEqual(y + h, 446, name)
            for x, y, w, h in boxes:  # neighbours on the same row band are exactly 16px apart
                for x2, y2, w2, h2 in boxes:
                    if y == y2 and x2 > x + w:
                        self.assertGreaterEqual(x2 - (x + w), 16, name)


class StoryboardTest(unittest.TestCase):
    def test_fixture_is_clean(self):
        r = run(SCRIPTS / "storyboard.py", "check", FIXTURE / "storyboard.yaml", "--stage", "layout")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("0 error(s), 0 warning(s)", r.stdout)

    def test_check_flags_outline_and_layout_errors(self):
        d = yaml.safe_load((FIXTURE / "storyboard.yaml").read_text(encoding="utf-8"))
        d["parts"][1]["claim"] = ""
        d["parts"][0]["pages"][0]["facts"] = ["F9"]
        pg = d["parts"][2]["pages"][0]
        pg["layout"] = "custom"
        for m, a in zip(pg["modules"], [[0, 0, 8, 6], [7, 0, 5, 3], [8, 3, 4, 3]]):
            m["area"] = a
        pg["modules"][2]["text"] = "超出卡片容量的文字" * 12
        with tempfile.TemporaryDirectory() as tmp:
            sb = Path(tmp) / "storyboard.yaml"
            sb.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
            (Path(tmp) / "facts.md").write_text((FIXTURE / "facts.md").read_text(encoding="utf-8"), encoding="utf-8")
            r = run(SCRIPTS / "storyboard.py", "check", sb)
        self.assertEqual(r.returncode, 1)
        for needle in ("missing part claim", "F9 not defined", "overlap", "copy needs"):
            self.assertIn(needle, r.stdout)

    def test_check_flags_weak_evidence_and_storyline_choice(self):
        d = yaml.safe_load((FIXTURE / "storyboard.yaml").read_text(encoding="utf-8"))
        d["storylines"][1]["chosen"] = True
        with tempfile.TemporaryDirectory() as tmp:
            sb = Path(tmp) / "storyboard.yaml"
            sb.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
            (Path(tmp) / "facts.md").write_text(
                "| ID | Fact | Value | Confidence |\n|---|---|---|---|\n"
                "| F1 | 比例 | 62 | 低（方向性） |\n| F2 | 時間 | 未提供 | — |\n| F3 | 文件 | 3,800 | 高 |\n",
                encoding="utf-8")
            r = run(SCRIPTS / "storyboard.py", "check", sb)
        self.assertEqual(r.returncode, 0, r.stdout)  # warnings only
        for needle in ("exactly one as chosen", "F1 is low-confidence", "F2 has no value"):
            self.assertIn(needle, r.stdout)

    def test_check_flags_even_split_rhythm_underfill_and_orphans(self):
        d = yaml.safe_load((FIXTURE / "storyboard.yaml").read_text(encoding="utf-8"))
        del d["parts"][1]["pages"][0]["layout_reason"]                     # hero-top without a reason
        pain = d["parts"][0]["pages"][0]
        clone = yaml.safe_load(yaml.safe_dump(pain))                        # same skeleton, next page
        clone["id"] = "pain-2"
        d["parts"][0]["pages"].append(clone)
        main = d["parts"][2]["pages"][0]["modules"][0]
        main["text"] = ["一行"]                                             # main module nearly empty
        d["parts"][2]["pages"][0]["modules"][1]["text"] = "首次回覆時間的每週平均值與中位數"  # orphan in a 4-col area
        d["brief"]["pages"] = 7
        with tempfile.TemporaryDirectory() as tmp:
            sb = Path(tmp) / "storyboard.yaml"
            sb.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
            (Path(tmp) / "facts.md").write_text((FIXTURE / "facts.md").read_text(encoding="utf-8"), encoding="utf-8")
            r = run(SCRIPTS / "storyboard.py", "check", sb, "--stage", "layout")
        for needle in ("evenly divided layout (hero-top)", "same skeleton as the previous page", "fills ~", "orphan last line"):
            self.assertIn(needle, r.stdout)

    def test_check_flags_visual_modules_without_data(self):
        d = yaml.safe_load((FIXTURE / "storyboard.yaml").read_text(encoding="utf-8"))
        del d["parts"][0]["pages"][0]["modules"][0]["data"]                 # chart with only a description
        with tempfile.TemporaryDirectory() as tmp:
            sb = Path(tmp) / "storyboard.yaml"
            sb.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
            r = run(SCRIPTS / "storyboard.py", "check", sb, "--stage", "layout")
        self.assertIn("chart has no data.rows", r.stdout)

    def test_kit_renders_every_module_kind_in_both_frames(self):
        from pptd_kit import Kit
        icon = "tabler-filled/bolt"
        pages = [
            ("mosaic", [
                {"kind": "chart", "role": "main", "title": "前後對照", "data": {"cols": ["公司", "原本", "排除後"],
                 "rows": [["甲", 0.41, 1.0], ["乙", 0.47, 1.0], ["丙", 0.56, 0.67]]}},
                {"kind": "stat", "title": "費率", "data": {"items": [{"value": "300", "unit": " 元", "label": "一般", "tone": "orange"},
                                                                     {"value": "50", "unit": " 元", "label": "優惠"}]}},
                {"kind": "pictogram", "title": "十分之一", "data": {"n": 10, "k": 2, "icon": icon, "label": "占車隊用電 20.4%"}},
                {"kind": "bar", "title": "分布", "data": {"items": [{"label": "等於 1", "value": 0.16, "display": "4 家"},
                                                                   {"label": "未滿 0.4", "value": 0.24, "display": "6 家", "tone": "orange"}]}},
            ]),
            ("hero-split", [
                {"kind": "ring", "role": "main", "title": "平均效率", "data": {"items": [{"value": 0.81, "center": "0.81", "label": "CCR"},
                                                                                     {"value": "64%", "label": "SBM", "tone": "orange"}]}},
                {"kind": "diagram", "title": "流程", "data": {"steps": [["投入", "車輛"], ["路線", "20 條"], ["產出", "載客量"]]}},
                {"kind": "quote", "title": "一句話", "text": "標竿會隨樣本改變"},
            ]),
            ("split-2-1", [
                {"kind": "chart", "role": "main", "title": "排名", "data": {"cols": ["公司", "強度"], "horizontal": True,
                 "rows": [["丁", 32.5], ["戊", 17.6], ["己", 4.0]]}},
                {"kind": "text", "title": "樣本", "text": ["12 條柴油路線", "8 條電動路線"]},
            ]),
        ]
        for frame in ("card", "region"):
            with self.subTest(frame=frame), tempfile.TemporaryDirectory() as tmp:
                kit = Kit(tmp, total=len(pages), chapters=["a"])
                for n, (layout, mods) in enumerate(pages, 1):
                    p = kit.page()
                    p.header(1, "標題", "副標")
                    p.modules({"layout": layout, "modules": mods}, frame=frame)
                    p.takeaway("一句話重點")
                    p.footer(n)
                    p.save(f"{n:02d}.page")
                kit.write_manifest("m.pptd", "m")
                lint = run(SCRIPTS / "lint_pptd.py", Path(tmp) / "m.pptd")
                if frame == "region":
                    self.assertIn("0 error(s), 0 warning(s)", lint.stdout, lint.stdout)
                else:  # two short lines alone in a 4×6 card read half empty — the sparse check's job
                    self.assertIn("0 error(s), 1 warning(s)", lint.stdout, lint.stdout)
                    self.assertRegex(lint.stdout, r"warn\s+03\s+\S+\s+sparse")
                self.assertEqual(run(SCRIPTS / "pptd2pptx.py", Path(tmp) / "m.pptd").returncode, 0)
                with zipfile.ZipFile(Path(tmp) / "m.pptx") as z:
                    chart = z.read("ppt/charts/chart1.xml").decode("utf-8")
                self.assertEqual(chart.count("<c:ser>"), 2)            # every data column is a series
                self.assertIn('formatCode="#,##0.00"', chart)          # 0.41 and 1.0 share two decimals

    def test_kit_card_craft_modules(self):
        """stack / feature / rank / dumbbell render through Page.modules, lint-clean and convertible."""
        from pptd_kit import Kit
        pages = [
            ("split-5-7", [
                {"kind": "stack", "role": "main", "title": "用電與綠電", "parts": [
                    {"kind": "stat", "data": {"items": [{"value": "261", "unit": " 萬度", "label": "年用電量"},
                                                        {"value": "+18.4%", "label": "比前一年", "tone": "orange"}]}},
                    {"kind": "bar", "title": "再生能源占比", "data": {"items": [{"label": "現在", "value": 0.2, "target": 0.6}]}}]},
                {"kind": "stack", "title": "每 10 度電", "parts": [
                    {"kind": "pictogram", "weight": 1.4, "data": {"n": 5, "k": 1, "icon": "tabler-filled/bolt", "tone": "orange"}},
                    {"kind": "stat", "data": {"value": "20.4%", "label": "占車隊用電", "tone": "orange"}}]}]),
            ("split-7-5", [
                {"kind": "rank", "role": "main", "title": "碳排強度", "data": {
                    "groups": {"柴油路線": "blue", "電動路線": "orange"},
                    "rows": [["12 路", 9.6, "柴油路線"], ["15 路", 5.8, "電動路線"], ["1 路", 2.1, "柴油路線"], ["3 路", 1.6, "電動路線"]]}},
                {"kind": "stack", "feature": True, "title": "算進碳排之後", "parts": [
                    {"kind": "stat", "data": {"value": "0.64", "label": "平均效率（原本 0.81）"}},
                    {"kind": "list", "text": ["4 家效率＝1<br/>是同業標竿", "6 家未滿 0.4<br/>仍有進步空間"]}]}]),
            ("split-2-1", [
                {"kind": "dumbbell", "role": "main", "title": "排除前後", "data": {
                    "labels": ["原本", "排除後"], "goal": 1,
                    "rows": [["2 路", 0.48, 1.0], ["5 路", 0.52, 1.0], ["12 路", 0.42, 0.63], ["18 路", 0.66, 0.81]]}},
                {"kind": "stack", "title": "標竿換人了", "parts": [
                    {"kind": "stat", "data": {"value": "+4", "unit": " 家", "label": "升到效率 1", "tone": "green"}},
                    {"kind": "ring", "data": {"items": [{"value": 0.16, "label": "原本占比"}]}}]}]),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            kit = Kit(tmp, total=len(pages), chapters=["a"])
            saved = []
            for n, (layout, mods) in enumerate(pages, 1):
                p = kit.page()
                p.header(1, "標題", "副標")
                p.modules({"layout": layout, "modules": mods}, frame="card")
                p.takeaway("一句話重點")
                p.footer(n)
                p.save(f"{n:02d}.page")
                saved.append(p)
            kit.write_manifest("m.pptd", "m")
            lint = run(SCRIPTS / "lint_pptd.py", Path(tmp) / "m.pptd")
            self.assertIn("0 error(s), 0 warning(s)", lint.stdout, lint.stdout)
            self.assertEqual(run(SCRIPTS / "pptd2pptx.py", Path(tmp) / "m.pptd").returncode, 0)
        texts = [e for e in saved[0].els if e["elementType"] == "text" and e["content"].get("gradient")]
        self.assertEqual(len({e["content"]["fontSize"] for e in texts if e["bounds"][1] < 300}), 1)  # one stat row, one size
        feat = next(e for e in saved[1].els if e["elementType"] == "shape" and e.get("shadow")
                    and (e.get("fill") or {}).get("type") == "gradient")           # the feature card
        x, y, w, h = feat["bounds"]
        on_card = [e for e in saved[1].els if e["elementType"] == "text" and x <= e["bounds"][0] < x + w and y + 60 < e["bounds"][1] < y + h]
        self.assertTrue(on_card)
        self.assertTrue(all(not e["content"].get("gradient") for e in on_card))   # light colors, no gradient text
        self.assertTrue(all(e["content"]["color"].upper() in ("#FFFFFF", kit.th["on_feature"].upper(), kit.th["blue"].upper())
                            for e in on_card))                                    # blue only inside the white number dots

    def test_templates_change_the_look_not_the_content(self):
        from pptd_kit import THEMES, Kit
        page = {"layout": "split-7-5", "modules": [
            {"kind": "stack", "role": "main", "title": "用電", "icon": "lightningBolt", "parts": [
                {"kind": "stat", "data": {"items": [{"value": "261", "unit": " 萬度", "label": "年用電量"}]}},
                {"kind": "bar", "data": {"items": [{"label": "綠電", "value": 0.2, "target": 0.6}]}}]},
            {"kind": "stack", "feature": True, "title": "算給你看", "parts": [
                {"kind": "stat", "data": {"value": "≈ 3", "unit": " 億元", "label": "一般費率"}},
                {"kind": "text", "text": "優惠費率 A：≈ 0.5 億元"}]}]}
        looks = {}
        for name in THEMES:
            with self.subTest(theme=name), tempfile.TemporaryDirectory() as tmp:
                kit = Kit(tmp, total=2, chapters=["a"], theme=name)
                p = kit.page()
                p.cover("公車跑得多，", "也排得多嗎？", "副標題一行", kicker="研究簡報", meta=["20 條", "2025"], byline="作者")
                p.save("01.page", "cover")
                p = kit.page()
                p.header(1, "標題", "副標")
                p.modules(page, frame="card")
                p.takeaway("一句話重點")
                p.footer(2)
                p.save("02.page")
                kit.write_manifest("m.pptd", "m")
                lint = run(SCRIPTS / "lint_pptd.py", Path(tmp) / "m.pptd")
                self.assertIn("0 error(s), 0 warning(s)", lint.stdout, lint.stdout)
                self.assertEqual(run(SCRIPTS / "pptd2pptx.py", Path(tmp) / "m.pptd").returncode, 0)
                card = next(e for e in p.els if e["elementType"] == "shape" and e["bounds"][1] == 124)
                texts = [e["content"] for e in p.els if e["elementType"] == "text"]
                looks[name] = {"radius": card["adjustments"][0], "border": bool(card.get("border")),
                               "shadow": bool(card.get("shadow")),
                               "gradient_numbers": any(c_.get("gradient") for c_ in texts),
                               "serif": any(c_.get("fontFamily") == {"latin": "Unna", "ea": "思源宋体"} for c_ in texts),
                               "hairline_header": any(e["bounds"][1] == 113 for e in p.els if e["elementType"] == "shape")}
        self.assertEqual(looks["bright-blue"], {"radius": 4000, "border": True, "shadow": True, "gradient_numbers": True,
                                                "serif": False, "hairline_header": False})
        self.assertEqual(looks["ink-ivory"], {"radius": 1200, "border": True, "shadow": False, "gradient_numbers": False,
                                              "serif": True, "hairline_header": True})
        self.assertEqual(looks["sage-mist"], {"radius": 9000, "border": False, "shadow": True, "gradient_numbers": True,
                                              "serif": False, "hairline_header": False})
        self.assertEqual(looks["ios-glass"], {"radius": 6500, "border": True, "shadow": True, "gradient_numbers": True,
                                              "serif": False, "hairline_header": False})
        with tempfile.TemporaryDirectory() as tmp:                   # a dict theme may start from a preset
            th = Kit(tmp, total=1, theme={"base": "ink-ivory", "blue": "#123456"}).th
        self.assertEqual((th["blue"], th["header"], th["bg"]), ("#123456", "rule", THEMES["ink-ivory"]["bg"]))

    def test_polish_components_in_every_template(self):
        """hero stat / hero band / breather / closing / semantic icons render lint-clean in all themes."""
        from pptd_kit import THEMES, Kit
        focus = {"layout": "split-7-5", "modules": [
            {"kind": "stack", "role": "main", "title": "算給你看", "icon": "calc", "parts": [
                {"kind": "stat", "hero": True, "weight": 1.6, "data": {"value": "≈ 3", "unit": " 億元", "label": "年排 100 萬噸"}},
                {"kind": "bar", "data": {"items": [{"label": "優惠後", "value": 0.17, "display": "≈ 0.5 億", "tone": "green"}]}}]},
            {"kind": "stack", "title": "費率", "icon": "money", "parts": [
                {"kind": "stat", "data": {"items": [{"value": "300", "label": "一般", "tone": "orange"},
                                                    {"value": "50", "label": "優惠", "tone": "green"}]}},
                {"kind": "text", "text": "減量計畫經核定可享優惠"}]}]}
        band = {"layout": "hero-split", "modules": [
            {"kind": "hero", "role": "main", "data": {"items": [{"label": "只看載客", "value": "0.81", "icon": "money"},
                                                                 {"label": "算進碳排", "value": "0.64", "icon": "carbon"}],
                                                      "delta": {"label": "平均下降", "value": "−0.17"}}},
            {"kind": "ring", "title": "平均效率", "icon": "efficiency", "data": {"items": [{"value": 0.81, "label": "CCR"},
                                                                                     {"value": 0.64, "label": "SBM", "tone": "orange"}]}},
            {"kind": "text", "title": "分布", "icon": "analysis", "text": ["4 家＝1", "6 家＜0.4"]}]}
        breather = {"lead": "1 路用掉車隊兩成的電", "value": "20.4%", "caption": "每 10 度電，就有 2 度",
                    "pictogram": {"n": 10, "k": 2, "icon": "power"}, "note": "給 1 路（2025 年）",
                    "stats": [{"value": "261", "unit": " 萬度", "label": "年用電量", "icon": "power"},
                              {"value": "+18.4%", "label": "比前一年", "icon": "growth"}],
                    "bar": {"label": "綠電占比", "value": 0.2, "target": 0.6, "display": "20% → 60%"}}
        for name in THEMES:
            with self.subTest(theme=name), tempfile.TemporaryDirectory() as tmp:
                kit = Kit(tmp, total=4, chapters=["a"], theme=name)
                pages = []
                for n, body in enumerate([focus, band, breather], 1):
                    p = kit.page()
                    p.header(1, "標題", "副標")
                    if "layout" in body:
                        p.modules(body, frame="card")
                    else:
                        p.breather(body)
                    p.takeaway("一句話重點")
                    p.footer(n)
                    p.save(f"{n:02d}.page")
                    pages.append(p)
                p = kit.page()
                p.closing(points=[("carbon", "orange", "碳費開徵"), ("benchmark", "green", "4 條新標竿")], byline="作者")
                p.save("04.page", "final")
                kit.write_manifest("m.pptd", "m")
                lint = run(SCRIPTS / "lint_pptd.py", Path(tmp) / "m.pptd")
                self.assertIn("0 error(s), 0 warning(s)", lint.stdout, lint.stdout)
                self.assertEqual(run(SCRIPTS / "pptd2pptx.py", Path(tmp) / "m.pptd").returncode, 0)
            sizes = sorted({e["content"]["fontSize"] for e in pages[0].els if e["elementType"] == "text"
                            and e["content"].get("bold") and e["bounds"][1] > 150})
            self.assertGreaterEqual(sizes[-1], 72)                # the hero number
            self.assertLessEqual(sizes[-2], 36)                   # every other number shrinks

    def test_check_flags_polish(self):
        d = yaml.safe_load((FIXTURE / "storyboard.yaml").read_text(encoding="utf-8"))
        content = d["parts"][0]["pages"]
        while sum(len(p_["pages"]) for p_ in d["parts"]) < 8:     # a long deck with no breather / hero band
            extra = yaml.safe_load(yaml.safe_dump(content[-1]))
            extra["id"] = f"{extra['id']}-{sum(len(p_['pages']) for p_ in d['parts'])}"
            content.append(extra)
        pg = content[0]
        pg["sub"] = "這是一段非常長的副標題，把好幾個想法塞在同一行裡面，讀者在現場根本來不及看完它"
        pg["modules"][1] = {"kind": "stat", "title": "數字", "data": {"items": [{"value": str(v), "label": "x"} for v in (1, 2, 3)]}}
        pg["modules"][0] = {"kind": "ring", "role": "main", "title": "環", "data": {"items": [{"value": 0.5, "label": "a"},
                                                                                             {"value": 0.6, "label": "b"}]}}
        del d["closing"]
        d["brief"]["mode"] = "live"

        def check(data):
            with tempfile.TemporaryDirectory() as tmp:
                (Path(tmp) / "facts.md").write_bytes((FIXTURE / "facts.md").read_bytes())
                sb = Path(tmp) / "storyboard.yaml"
                sb.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
                return run(SCRIPTS / "storyboard.py", "check", sb, "--stage", "layout").stdout
        out = check(d)
        for needle in ("numbers compete", "no closing page", "no breather page", "subtitle is more than one short clause"):
            self.assertIn(needle, out)
        pg["modules"][1]["hero"] = True
        pg["modules"][0]["hero"] = True
        self.assertIn("2 hero modules", check(d))
        pg["modules"][0].pop("hero")
        content[1]["breather"] = {"value": "20.4%", "photo": "media/x.jpg"}
        content[1].pop("layout", None)
        out = check(d)
        for needle in ("numbers compete", "hero modules", "no breather page"):
            self.assertNotIn(needle, out)

    def test_fit_size_never_splits_a_number(self):
        from pptd_kit import fit_size, wrap_lines
        item = "只看載客，平均 0.81–0.86<br/>擴大規模還能提升"
        size, _ = fit_size([item], 245, 88, 18, 1.4, (26, 22, 20))
        lines = wrap_lines(item, size, 245)
        self.assertFalse(any(a[-1:].isdigit() and b[:1] in "0123456789." for a, b in zip(lines, lines[1:])), (size, lines))

    def test_check_accepts_preset_shape_icons(self):
        d = yaml.safe_load((FIXTURE / "storyboard.yaml").read_text(encoding="utf-8"))
        d["parts"][0]["pages"][0]["modules"][0]["icon"] = "lightningBolt"
        d["parts"][0]["pages"][0]["modules"][1]["icon"] = "notAShapeOrIcon"
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "facts.md").write_bytes((FIXTURE / "facts.md").read_bytes())
            sb = Path(tmp) / "storyboard.yaml"
            sb.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
            out = run(SCRIPTS / "storyboard.py", "check", sb, "--stage", "layout").stdout
        self.assertNotIn("lightningBolt", out)
        self.assertIn("notAShapeOrIcon", out)

    def test_check_flags_card_craft(self):
        d = yaml.safe_load((FIXTURE / "storyboard.yaml").read_text(encoding="utf-8"))
        d["brief"]["frame"] = "card"
        mods = d["parts"][0]["pages"][0]["modules"]                  # split-2-1: chart (main) + stat in a 4×6 card
        (mods[1]["data"].get("items") or [mods[1]["data"]])[0]["tone"] = "orange"
        mods[0]["feature"] = mods[1]["feature"] = True

        def check(data):
            with tempfile.TemporaryDirectory() as tmp:
                (Path(tmp) / "facts.md").write_bytes((FIXTURE / "facts.md").read_bytes())
                sb = Path(tmp) / "storyboard.yaml"
                sb.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
                return run(SCRIPTS / "storyboard.py", "check", sb, "--stage", "layout").stdout
        out = check(d)
        for needle in ("card holding one stat", "one gradient feature card per page", "not chart", "brief.colors"):
            self.assertIn(needle, out)
        mods[0]["feature"] = False
        mods[1] = {"kind": "stack", "title": mods[1]["title"], "feature": True, "parts": [
            {"kind": "stat", "data": mods[1]["data"]}, {"kind": "text", "text": "8 週 PoC 驗證"}]}
        d["brief"]["colors"] = {"orange": "需要處理的工單"}
        out = check(d)
        for needle in ("card holding one", "feature card per page", "not chart", "brief.colors", "stack part"):
            self.assertNotIn(needle, out)

    def test_ring_bar_pictogram_with_data_pass_the_check(self):
        d = yaml.safe_load((FIXTURE / "storyboard.yaml").read_text(encoding="utf-8"))
        mods = d["parts"][0]["pages"][0]["modules"]
        mods[0] = {"kind": "ring", "role": "main", "title": "工單類型分布", "data": {"value": 0.62, "label": "可由文件回答"}}
        mods[1] = {"kind": "pictogram", "title": "首次回覆", "data": {"n": 10, "k": 6, "label": "十張有六張"}}
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "facts.md").write_bytes((FIXTURE / "facts.md").read_bytes())
            sb = Path(tmp) / "storyboard.yaml"
            sb.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
            r = run(SCRIPTS / "storyboard.py", "check", sb, "--stage", "layout")
        self.assertNotIn("has no data", r.stdout)
        self.assertNotIn("not rendered", r.stdout)

    def test_kit_modules_render_storyboard_pages(self):
        from pptd_kit import Kit
        d = yaml.safe_load((FIXTURE / "storyboard.yaml").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            kit = Kit(tmp, total=3, chapters=["a", "b", "c"])
            for n, part in enumerate(d["parts"], 1):
                pg = part["pages"][0]
                p = kit.page()
                p.header(n, pg["title"], part["claim"])
                p.modules(pg)
                p.takeaway(pg["takeaway"], style="rule")
                p.footer(n)
                p.save(f"{n:02d}_{pg['id']}.page")
            kit.write_manifest("m.pptd", "m")
            lint = run(SCRIPTS / "lint_pptd.py", Path(tmp) / "m.pptd")
            self.assertIn("0 error(s), 0 warning(s)", lint.stdout, lint.stdout)
            self.assertEqual(run(SCRIPTS / "pptd2pptx.py", Path(tmp) / "m.pptd").returncode, 0)

    def test_wireframe_is_lint_clean_and_converts(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "wf"
            r = run(SCRIPTS / "storyboard.py", "wireframe", FIXTURE / "storyboard.yaml", "--out", out)
            self.assertEqual(r.returncode, 0, r.stderr)
            manifest = out / "wireframe.pptd"
            lint = run(SCRIPTS / "lint_pptd.py", manifest, "--strict")
            self.assertEqual(lint.returncode, 0, lint.stdout)
            self.assertIn("0 error(s)", lint.stdout)
            r = run(SCRIPTS / "pptd2pptx.py", manifest, "--force")
            self.assertEqual(r.returncode, 0, r.stderr)
            with zipfile.ZipFile(out / "wireframe.pptx") as z:
                slides = [n for n in z.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
            self.assertEqual(len(slides), 7)                  # cover, toc, 3 content, end, closing

    def test_page_numbers_follow_the_deck_order_with_intro_pages(self):
        from storyboard import Storyboard
        d = yaml.safe_load((FIXTURE / "storyboard.yaml").read_text(encoding="utf-8"))
        d["intro"] = [{"id": "quiz", "title": "開始前，先猜三題"}]
        with tempfile.TemporaryDirectory() as tmp:
            sb_path = Path(tmp) / "storyboard.yaml"
            sb_path.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
            sb = Storyboard(sb_path)
            pno = sb.page_numbers()
            ids = [str(pg.get("id") or kind) for kind, pg, _ in sb.sequence()]
        self.assertEqual(pno["cover"], 1)
        self.assertEqual(pno["quiz"], ids.index("quiz") + 1)
        self.assertLess(pno["quiz"], pno[d["parts"][0]["pages"][0]["id"]])
        self.assertEqual(sorted(pno.values()), list(range(1, len(ids) + 1)))

    def test_wireframe_labels_intro_and_appendix_pages(self):
        d = yaml.safe_load((FIXTURE / "storyboard.yaml").read_text(encoding="utf-8"))
        d["intro"] = [{"id": "quiz", "title": "開始前，先猜三題", "takeaway": "答案藏在報告裡"}]
        d["appendix"] = [{"id": "glossary", "title": "名詞小卡"}]
        d["brief"].pop("pages", None)
        with tempfile.TemporaryDirectory() as tmp:
            sb = Path(tmp) / "storyboard.yaml"
            sb.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
            out = Path(tmp) / "wf"
            r = run(SCRIPTS / "storyboard.py", "wireframe", sb, "--out", out)
            self.assertEqual(r.returncode, 0, r.stderr)
            quiz = next((out / "pages").glob("*_quiz.page")).read_text(encoding="utf-8")
            gloss = next((out / "pages").glob("*_glossary.page")).read_text(encoding="utf-8")
            self.assertIn("開場", quiz)
            self.assertIn("附錄", gloss)
            lint = run(SCRIPTS / "lint_pptd.py", out / "wireframe.pptd").stdout
            self.assertIn("0 error(s)", lint)

    def test_check_reads_placeholders_notes_and_groups_repeats(self):
        d = yaml.safe_load((FIXTURE / "storyboard.yaml").read_text(encoding="utf-8"))
        pages = [pg for part in d["parts"] for pg in part["pages"]]
        # {placeholders} are filled from data by build.py: measured as short numbers, not as their names
        pages[0]["title"] = "從滿分到 {sbm}：技術扣 {tech}、規模扣 {scale}、碳排再扣 {carbon}"
        for pg in pages:                      # a deck-wide habit: no points anywhere
            pg.pop("points", None)

        def check():
            with tempfile.TemporaryDirectory() as tmp:
                sb = Path(tmp) / "storyboard.yaml"
                sb.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
                return run(SCRIPTS / "storyboard.py", "check", sb).stdout

        pages[2]["takeaway"] = "{wf_take}"                    # a whole sentence from the data: not measured
        out = check()
        self.assertNotIn("header line", out)
        self.assertNotIn("takeaway needs", out)
        self.assertNotIn("one short clause", out)
        lines = [ln for ln in out.splitlines() if "no supporting points" in ln]
        self.assertEqual(len(lines), 1, out)                 # one grouped line, counting every page
        self.assertIn(f"×{len(pages)}", lines[0])
        pages[1]["notes"] = "講稿：先說結論，再看圖"           # a speaker script carries the support too
        out = check()
        self.assertNotIn(pages[1]["id"], "".join(ln for ln in out.splitlines() if "no supporting points" in ln))

    def test_check_flags_big_appendix_and_typed_page_refs(self):
        d = yaml.safe_load((FIXTURE / "storyboard.yaml").read_text(encoding="utf-8"))
        d["parts"][0]["pages"][0]["takeaway"] = "答案在 P5，結尾再對一次"
        d["appendix"] = [{"id": f"a{i}", "title": f"附錄頁 {i}"} for i in range(6)]
        d["brief"].pop("pages", None)
        with tempfile.TemporaryDirectory() as tmp:
            sb = Path(tmp) / "storyboard.yaml"
            sb.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
            out = run(SCRIPTS / "storyboard.py", "check", sb).stdout
        self.assertIn("hard-codes page P5", out)
        self.assertIn("appendix is 6 of", out)

    def test_wireframe_refuses_nonempty_out_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "keep.txt").write_text("x", encoding="utf-8")
            r = run(SCRIPTS / "storyboard.py", "wireframe", FIXTURE / "storyboard.yaml", "--out", tmp)
            self.assertNotEqual(r.returncode, 0)
            self.assertTrue((Path(tmp) / "keep.txt").exists())


if __name__ == "__main__":
    unittest.main()
