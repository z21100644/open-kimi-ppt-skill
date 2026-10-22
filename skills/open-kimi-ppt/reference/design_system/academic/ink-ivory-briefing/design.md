# Ink Ivory Briefing · academic STYLE DESIGN SYSTEM

> 墨藍象牙簡報 — the restrained member of the briefing family: ivory paper, ink-blue type, serif titles,
> hairline cards and a little gold. For thesis defences, formal reports, policy and board briefings —
> rooms where the bright-blue look would feel too promotional.
> Preview: `preview.jpg` · Reference implementation: `sample_build.py` (`Kit(..., theme="ink-ivory")`).

## PART A — Baseline
Same as `bright-blue-bento-briefing/design.md` PART A (audience, register, argument skeleton, reading
density with extraction, 18px floor, prohibitions). The two templates share the storyboard, the bento
grid (`reference/storyboard.md` §3) and the card craft rules (`reference/decoration.md` §6); a deck
switches between them with the `theme` argument alone.

## PART B — Signature System

One-line signature: ivory pages, white hairline cards with a gold dash under each serif title, ink-blue
solid numbers, one deep-navy feature card per page, and a gold-ticked 重點 line instead of a bar.

【Color Palette】 (tokens in `pptd_kit.INK_IVORY`)
- Canvas `#F5F1E8` ivory · Card `#FFFDF9` + border `#E0D8C8` 1px, no shadow · Hairlines `#D6CDBB`.
- Ink `#14213D` titles · Text `#2B2F36` · Gray `#696D74` labels/units/notes.
- Ink blue `#1F3A5F` — structure, primary numbers, primary series; partner `#3C6491`.
- Terracotta `#A8553A` — cost, emissions, the contrasting group. Pine `#4A7A5C` — improvement, targets.
- Gold `#A88748` — decoration only: header dash, card-title dash, 重點 tick, cover frame, progress dot.
  Never for text (too low contrast on ivory).
- Feature card: solid deep navy `#17294A`, ivory text `#EDE6D6`.
Color discipline as in the bright-blue system: one meaning per hue, declared in `brief.colors`.

【Typography】
Titles, card titles and the cover in a serif pair `{latin: Unna, ea: 思源宋体}` (PowerPoint: Georgia +
新細明體 via `FONT_MAP`), bold. Body, labels and numbers stay in the sans pair `{Liter, MiSans}` —
serif digits are hard to compare in charts. Sizes as bright-blue (cover 46 · page title 26 · card title
20 · key numbers 26–44 · body 18).

【Layout Skeleton】
Same grid and offsets as bright-blue. Header style `rule`: gold dash + spaced chapter label, serif
title, gray source line, a full-width hairline at y = 113, small dots for chapter progress (current =
gold). Cards: radius 1200, no title band, a hairline under the title with a 28px gold dash.
重點: hairline + gold tick + ink label, no tinted bar.

【Components】 (kit, template-aware)
`card` (hairline style) · `card(feature=True)` / module `feature: true` (navy, solid) · `gtext` and data
marks render solid (`gradients: False`) · `icon` as a bare glyph (`icon_style: glyph`) · `cover` recipe
`frame` · plus every bright-blue component (`stat`, `ring`, `bar`, `rank_bars`, `dumbbell`, `chip`,
`tag`, `pill`, `numdot`, module `stack`).

【Slide Types and Layouts】
Cover (`frame`) | photo in a panel on the right with an offset gold outline, gold dash + spaced kicker,
2-line serif title (second line ink blue), subtitle, meta as one line split by gold dots, hairline
above the byline | no header/footer. Body pages as bright-blue; prefer white space over a fourth card.

【Prohibited】
Gradients, glows and saturated fills; more than one gold element per card; serif type for numbers or
body copy; the bright-blue title band; photos as page backgrounds behind body copy.
