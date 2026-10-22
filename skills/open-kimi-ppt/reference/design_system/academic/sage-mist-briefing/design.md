# Sage Mist Briefing · academic STYLE DESIGN SYSTEM

> 霧綠簡報 — the calm member of the briefing family: a misty sage canvas, rounded borderless cards
> floating on soft shadows, sage-to-mint gradients and warm clay accents. For sustainability / ESG
> reports, education and training, health and community briefings.
> Preview: `preview.jpg` · Reference implementation: `sample_build.py` (`Kit(..., theme="sage-mist")`).

## PART A — Baseline
Same as `bright-blue-bento-briefing/design.md` PART A (audience, register, argument skeleton, reading
density with extraction, 18px floor, prohibitions). The briefing templates share the storyboard, the
bento grid (`reference/storyboard.md` §3) and the card craft rules (`reference/decoration.md` §6); a
deck switches between them with the `theme` argument alone.

## PART B — Signature System

One-line signature: soft rounded white cards without borders on a sage-gray canvas, sage gradient
numbers, one deep-sage feature card per page, a photo washed into the canvas on the cover.

【Color Palette】 (tokens in `pptd_kit.SAGE_MIST`)
- Canvas `#ECF1ED` · Card `#FFFFFF`, no border, shadow `blur 18, #1F3A2E24, offset 0/6`.
- Ink `#1F332C` titles · Text `#33443E` · Gray `#5F6F68` labels/units/notes.
- Sage `#4A846C` / mint `#86B9A2` (gradient pair) — structure, primary numbers, primary series.
- Clay `#C97A47` / `#E4A97C` — cost, emissions, the contrasting group.
- Teal `#2F7684` / `#7DB4BE` — comparison, targets, "green" tone (kept apart from the sage primary).
- Feature card: gradient `#5A977F` → `#3A6F5B`, text white / `#E4F1EA`.
- Sky `#DDEBE3` ring tracks and icon discs · insight bar `#DCEAE1`.

【Typography】
Sans throughout `{latin: Liter, ea: MiSans}`. Sizes as bright-blue (cover 52 · page title 26 · card
title 20 bold · key numbers 26–54 · body 18).

【Layout Skeleton】
Same grid, offsets and header (`bar`: gradient accent bar + numbered progress dots) as bright-blue.
Cards: radius 9000 (clearly rounded), no title band, a short sage bar under the title. 重點 bar in pale
sage with a filled sage label.

【Components】 (kit, template-aware)
`card` (rounded, borderless, shadowed) · `card(feature=True)` / module `feature: true` (sage gradient) ·
`icon` on a pale sage disc · `cover` recipe `wash` (full-bleed photo under a canvas-colored wash from
the left, rounded kicker, soft meta tags) · plus every bright-blue component.

【Slide Types and Layouts】
Cover (`wash`) | photo across the page, washed to the canvas color on the left 60%, rounded kicker,
2-line title (second line sage gradient), subtitle, soft meta tags, byline | no header/footer.
Body pages as bright-blue; favour rings, pictograms and photos over dense tables.

【Prohibited】
Hard 1px borders on cards; saturated greens (`#00A86B`-like) that read as "go" signals; clay and teal
on the same mark; more than one feature card per page.
