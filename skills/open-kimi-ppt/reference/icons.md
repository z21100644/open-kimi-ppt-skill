# Icons: library search, vector shapes, free adjustment

`assets/icons/tabler-filled/` holds 1,000+ filled icons (Tabler Icons, MIT, 24×24). `scripts/icons.py`
turns any of them — or any SVG you edit or draw — into PPTD custom shapes (`shapeName: custom`):
real vector shapes that stay editable, recolorable and sharp in the Kimi editor and in the PPTX
from `pptd2pptx.py`. Do not use Font Awesome `icon` elements when a PPTX is delivered: the offline
converter drops them (lint flags `icon`).

## When to use an icon
- Only when it carries meaning a reader would otherwise miss: a category marker in a list, a step
  in a process, a state (done / risk / blocked), a concept tile. Never as filler next to every heading.
- The scenario guide and design system decide first: some forbid colorful small icons or icon walls
  (`slides_categories/*.md`). They take precedence over this file.
- One visual language per deck: filled glyphs, one weight, one size per role on a page (e.g. 34px in
  card titles, 24px in list rows), colors from the palette — usually the primary color or white on
  a colored disc. Gradients are fine where the design system uses them.
- `brand-*` icons only for that real brand, product or service. Never draw or approximate a company
  logo; use the official image file if a logo is needed.

## Find
```bash
python <skill_dir>/scripts/icons.py search chart growth --limit 20
```
Names are English, so search with English words and pass synonyms together — any word counts and
icons matching more of them rank first (`search money coin cash wallet`). The filled set does not
cover everything (no robot or plug, for example): try neighbouring concepts (`sparkles`, `code-circle`).
Check the candidates' meaning before picking; an unknown id fails with close-match suggestions.

## Place
In `build.py` (preferred):
```python
p.icon(x, y, 40, "tabler-filled/bulb")                     # glyph on the kit's tinted disc
p.icon(x, y, 40, "tabler-filled/flame", light=True)         # white glyph for colored cards
els = p.svg(x, y, 48, 48, "tabler-filled/shield-check", fill="#1A73E8")   # bare glyph
p.svg(x, y, 48, 48, "tabler-filled/lock", fill=gfill(kit.ORANGE_G, 45))   # gradient fill
```
Hand-written pages: `python icons.py shape tabler-filled/bulb --bounds 120,80,48,48 --color '#1A73E8'`
prints the element YAML to paste. Each SVG drawable becomes its own shape (`icon-1`, `icon-2`… when
there are several) so overlapping parts don't cancel out. `fill` / `--color` tints every part;
leave it out to keep the SVG's own colors. The ratio is kept (centered in the bounds) unless
`keep_ratio=False` / `--stretch`.

## Adjust freely
The library is a starting point, not a limit. When no icon fits or one needs changing:
1. Copy it into the project: `cp <skill_dir>/assets/icons/tabler-filled/bulb.svg deck/media/icons/bulb-check.svg`
   (keep edited and self-drawn icons in `media/icons/` so the project stays self-contained).
2. Edit the SVG: combine two icons, drop or add parts, rotate/flip with `transform`, recolor parts
   with per-element `fill`, add a badge `<circle>`, or draw a new one on the same 24×24 grid with
   `<path>`, `<circle>`, `<ellipse>`, `<rect rx>`, `<polygon>` and `<g transform>`.
3. Use it like a library icon: `p.svg(x, y, 48, 48, "media/icons/bulb-check.svg")` (project-relative
   paths resolve against the kit's output folder) or `icons.py shape deck/media/icons/bulb-check.svg`.
After placing, the shapes are plain PPTD elements: rotation, flip, opacity, shadow and border apply
like on any shape.

Limits: fills only — stroke-only lines (`fill="none"` + `stroke`) are skipped with a warning, so
draw strokes as filled outlines (thin rects / closed paths). Holes come from opposite winding inside
one path (outer contour clockwise, inner counter-clockwise), as in the library icons; `fill-rule:
evenodd` gets a warning to check the render. No `<use>`, `<text>`, `<image>`, masks or gradients
defined inside the SVG — apply gradients through `fill`.

## Check
Lint and render as usual; icons show up in the overview at their real size. Look for icons whose
meaning is ambiguous at the rendered size, inconsistent sizes within a row, and glyphs touching
text or card edges.
