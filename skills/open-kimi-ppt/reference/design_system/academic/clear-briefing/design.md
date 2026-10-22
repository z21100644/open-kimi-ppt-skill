# Clear Briefing · academic STYLE DESIGN SYSTEM

> 清透 — one art direction over the briefing family: bright-blue's data graphics, a calm glass material
> on a soft blurred ground, restraint (one solid surface per deck, non-focus data gray) and same-hue
> tonal transitions. For public talks and research sharing that should feel premium without noise.
> Preview: `preview.jpg` · Reference implementation: `sample_build.py` (`Kit(..., theme="clear")`).
> Origin: twenty-odd iterations on a research briefing — flat versions read cheap, gimmick versions read
> loud; this is the rule set the user approved (`reference/decoration.md` §10–11).

## PART A — Baseline
Same as `bright-blue-bento-briefing/design.md` PART A. Storyboard, bento grid, card craft (§6) and
polish (§9) are shared; a deck switches template with the `theme` argument alone.

## PART B — Signature System

One-line signature: white glass cards on a soft blurred ground, a rounded-rectangle language, colour
only where it means something, and every surface lit from the top-left.

【Colour — 60-30-10】
- Ground (60%): `#F6F8FC` + the wallpaper at 80% (cover 90%).
- Structure (30%): titles `#111827`, text `#374151`, notes `#6B7280`.
- Accent (10%): blue `#1A73E8` (analysis, key numbers, chapter, takeaway label).
- Meanings: orange `#F08C2E` carbon & cost · green `#2E9E5B` green power & benchmarks. Teal is mapped
  to gray (`#9CA3AF`) — a second group is not a focus colour. Non-focus data marks stay flat gray.

【Shape】 rounded rectangles only; circles are data (rings, chart dots). Radii: 16 px cards, photo frames
and the hero band (`radius_px`) · ~10 px tiles and chips · capsule for pills, takeaway and kicker.
Frames around photos are concentric (inner radius = outer − inset).

【Surfaces — three only】 white glass card (white 96 → 86%, 1.2 px white rim, shadow navy ~14%, blur 18,
offset 4) · pale feature card (`#F3F8FF` → `#E2EDFC`, dark copy, accent numbers; `feature_style: tint`) ·
the hero band (`kind: hero`) — the deck's one solid surface, `#3D8DF0` → `#1A5FD6` with a highlight.

【Transitions】 required, never decorative: same hue, a 10–18% lightness step, light from the top-left —
tiles, numbered tiles, key numbers, bars and rings (hue-light → hue), surfaces top to bottom. Flat
paint reads cheap; cross-hue (blue → purple) or high-contrast gradients read loud.

【Icons and markers】 one filled library; headings = solid gradient tile with a white glyph; numbered
markers (Q1–Q3, steps) are tiles too (`marker: tile`, contrast-guarded); list items = soft tiles.

【Typography】 two families (Latin + CJK). Page title 30 bold (large-title header), card title 20 bold,
body 18 regular gray; hero 60–96, key numbers 40–54, supporting 26–28; units 18 gray.

【Layout skeleton】 header in the safe area (caption at 24 px, title, subtitle; a gray page control with
the current chapter as a blue capsule) · body grid 12 × 6, 16 px gutters · takeaway glass capsule at
456 · footer at 502: the page's source / method note bottom-left (`Page.footer(n, source=…)`), page
number bottom-right. One divider: 1 px solid `#E3E9F2` (`divider: solid`).

【Slide types】 cover / closing `glass` (photo in a glass frame, gradient kicker, glass meta capsules,
grouped recap list) · breather (photo panel rounded with its wash baked in; numbers on a glass card)
· photo cards (photo tops follow the card corners).

【Prohibited】 flat-only fills; cross-hue or rainbow gradients; glow; borders thicker than 1.2 px; data
floating bare on the ground; square photos; circular number markers; dashed dividers; a second solid
accent surface; widgets, leaves, arcs and other ornaments without data meaning.
