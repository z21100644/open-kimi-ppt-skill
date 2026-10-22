#!/usr/bin/env python3
"""Icon library: SVG path normalization, icon search/shapes, converter support for full PPTD path syntax."""
import math
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import svgpath  # noqa: E402
from icons import library_icons, load_svg, search, shape_elements  # noqa: E402


def run(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, encoding="utf-8")


def cubic(c, p0, t):
    x1, y1, x2, y2, x, y = c
    u = 1 - t
    return (u ** 3 * p0[0] + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t ** 3 * x,
            u ** 3 * p0[1] + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t ** 3 * y)


class SvgPathTest(unittest.TestCase):
    def test_relative_commands_become_absolute(self):
        segs = svgpath.normalize("M1 1l2 0h1v2z m3 3l1 1")
        self.assertEqual(svgpath.fmt(segs), "M 1 1 L 3 1 L 4 1 L 4 3 Z M 4 4 L 5 5")

    def test_arcs_stay_on_the_circle(self):
        segs = svgpath.normalize("M10 5 A5 5 0 1 0 0 5 A5 5 0 1 0 10 5Z")
        p0, err = (10, 5), 0
        for cmd, c in segs[1:]:
            if cmd == "C":
                for i in range(11):
                    x, y = cubic(c, p0, i / 10)
                    err = max(err, abs(math.hypot(x - 5, y - 5) - 5))
                p0 = c[4:]
        self.assertLess(err, 0.01)

    def test_compact_arc_flags(self):
        self.assertEqual(svgpath.normalize("M0 0a1 1 0 01.5.5")[-1][1][-2:], (0.5, 0.5))


class IconLibraryTest(unittest.TestCase):
    def test_every_library_icon_converts(self):
        ids = [i for i, _ in library_icons()]
        self.assertGreater(len(ids), 1000)
        for icon_id in ids:
            els = shape_elements(icon_id, 0, 0, 48, 48, "#000000")
            self.assertTrue(all(e["shapeName"] == "custom" and e["path"].startswith("M") for e in els), icon_id)

    def test_search_ranks_exact_names_first(self):
        self.assertEqual(search(["lock"], 1)[0][0], "tabler-filled/lock")

    def test_unknown_icon_suggests_matches(self):
        with self.assertRaises(FileNotFoundError) as cm:
            shape_elements("users", 0, 0, 48, 48)
        self.assertIn("tabler-filled/user", str(cm.exception))

    def test_custom_svg_with_transform_colors_and_stroke_warning(self):
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">'
               '<g transform="translate(24 24) rotate(45)"><rect x="-14" y="-14" width="28" height="28" rx="6" fill="#1A73E8"/></g>'
               '<circle cx="24" cy="24" r="7" fill="#FFFFFF"/><polygon points="24,2 28,10 20,10" fill="#F08C2E" opacity="0.5"/>'
               '<path d="M4 44 L44 44" stroke="#000" fill="none"/></svg>')
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "x.svg"
            f.write_text(svg, encoding="utf-8")
            _, items, warns = load_svg(f)
            els = shape_elements(str(f), 0, 0, 96, 96)
        self.assertEqual(len(items), 3)
        self.assertTrue(any("stroke-only" in w for w in warns))
        self.assertEqual([e["fill"]["color"] for e in els], ["#1A73E8", "#FFFFFF", "#F08C2E"])
        self.assertEqual(els[2]["opacity"], 0.5)
        x0, _, x1, _ = svgpath.bbox(svgpath.normalize(els[0]["path"]))
        # viewBox scaled ×100; the 45° rotation pushes the 28px square past its unrotated edges (x 10…38)
        self.assertTrue(400 < x0 < 900 and 3900 < x1 < 4400, (x0, x1))

    def test_svg_paint_values_and_missing_files(self):
        from icons import css_color
        self.assertEqual(css_color("white"), "#FFFFFF")
        self.assertEqual(css_color("#f00"), "#FF0000")
        self.assertEqual(css_color("rgb(0, 128, 0)"), "#008000")
        self.assertEqual(css_color("rgba(0,0,0,0.5)"), "#00000080")
        self.assertIsNone(css_color("url(#g)"))
        with self.assertRaises(FileNotFoundError) as cm:
            shape_elements("media/icons/typo.svg", 0, 0, 24, 24)
        self.assertIn("SVG file", str(cm.exception))

    def test_icons_survive_pptx_conversion_with_flip_and_relative_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pages").mkdir()
            els = shape_elements("tabler-filled/lock-square-rounded", 100, 100, 96, 96, "#1A73E8")
            els[0]["flip"] = [True, False]
            els.append({"elementId": "rel", "elementType": "shape", "shapeName": "custom", "bounds": [300, 100, 96, 96],
                        "viewBox": [24, 24], "path": "M12 2a10 10 0 1 1 0 20a10 10 0 1 1 0 -20z", "fill": {"type": "solid", "color": "#000000"}})
            (root / "pages" / "a.page").write_text(yaml.safe_dump({"elements": els}, allow_unicode=True), encoding="utf-8")
            (root / "d.pptd").write_text("version: v2\nsize: [960, 540]\npages: [pages/a.page]\n", encoding="utf-8")
            r = run(SCRIPTS / "pptd2pptx.py", root / "d.pptd")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertNotIn("skip", r.stdout)
            with zipfile.ZipFile(root / "d.pptx") as z:
                xml = z.read("ppt/slides/slide1.xml").decode("utf-8")
        self.assertEqual(xml.count("<a:custGeom>"), 2)
        self.assertIn('flipH="1"', xml)
        self.assertGreater(xml.count("<a:cubicBezTo>"), 8)  # arcs became curves, not straight lines


if __name__ == "__main__":
    unittest.main()
