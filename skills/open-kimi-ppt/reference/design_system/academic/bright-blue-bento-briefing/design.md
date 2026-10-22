# Bright Blue Bento Briefing · academic STYLE DESIGN SYSTEM

> 亮藍資訊卡簡報 — a public-facing research briefing: dense enough to be *read* (the presenter may not
> know the material well), refined enough to *present*. Built for thesis preliminary reports, policy /
> ESG explainers, research-to-public briefings, and data-heavy internal reports.
> Preview: `preview.jpg` · Reference implementation: `sample_build.py` (uses `scripts/pptd_kit.py`).
> Briefing family: `ink-ivory-briefing` (restrained, serif), `sage-mist-briefing` (calm, rounded) and
> `ios-glass-briefing` (this layout in a glass material) and `clear-briefing` (one art direction, restrained
> glass with tonal transitions) share this PART A, the storyboard and the build —
> `Kit(..., theme="bright-blue" | "ink-ivory" | "sage-mist" | "ios-glass" | "clear")`.

## PART A — Baseline (Universal Floor)

Audience is the informed public: professional terminology is kept, but each term gets a short plain
gloss on first use — e.g. 「非期望產出（碳排）」「效率前緣（同業標竿）」「地區基準／市場基準」.
Register is formal written Chinese/English: no slang, no rhetorical questions in body copy, no
marketing tone. Every number carries a unit, a year and a scope.

Content and layout:
1. Argument skeleton: purpose → background/stakes → definitions → literature gap → design (variables,
   models) → sample → preliminary findings → limitations & next steps → conclusion → sources.
   A 10-minute talk = 10 body pages + 1 appendix. Never exceed ~1 page per minute.
2. **Reading density with extraction** (the "PPT 換頭術" principle): keep the full information of a
   wordy page, but *refine* it — pull every number out as `big number + small unit + gray label`,
   turn lists into numbered/pill rows, turn proportions into rings/bars, put definitions into cards.
   Target 120–220 CJK characters of body copy per page plus 3–8 extracted numbers.
3. Each body page states one claim in its title and seals it with one sentence in the 重點 bar.

Visual style:
1. Bright, clean, confident: light blue-gray canvas, white cards, one blue gradient hero card per page
   at most (FEATURE_G `#1E9BF0`→`#1A5FD6`, deeper than BLUE_G so white text reads), cyan→blue gradient
   on key numbers. Every card is composed of 2–3 element kinds split by dashed rules — never one
   element floating in a frame (`reference/decoration.md` §6 card craft).
2. **Minimum font size 18px (pt) everywhere** — including units, chart labels, table cells, footers.
3. Hierarchy by size + weight + color, never by shrinking below 18.

Global prohibitions: no text below 18px; no paragraphs longer than 2 lines inside a card (split with
`<p>` or extract); no orphan lines (a final line of 1–2 characters) — reword or resize the box; no full
stop at the end of slide copy; no decorative images unrelated to the claim; no rainbow categorical
charts; no evenly split 50/50 layouts when content is asymmetric.

## PART B — Signature System

One-line signature: a bento grid of high-contrast white cards on a pale blue-gray canvas, each card
with a tinted title band, numbers extracted as cyan→blue gradient figures, a chapter-progress header
and a blue 「重點」 takeaway bar sealing every page.

【Color Palette】 (tokens in `pptd_kit.BRIGHT_BLUE`)
- Canvas `#E8EFF7` — page background; never pure white (cards need the contrast).
- Card `#FFFFFF` + border `#CFDDEE` 1px + shadow `blur 14, #1E3A6038, offset 0/4` — the contrast fix:
  white-on-white cards without border/shadow read as one flat sheet.
- Card title band `#EEF4FC` with a 56×3 blue underline accent under the title.
- Navy `#0B1F3A` titles · Text `#2B3A4F` body · Gray `#5B6B7F` labels/units/notes.
- Primary blue `#1A73E8`, cyan `#00B2FF` (gradient pair BLUE_G) — structure, key numbers, active state.
- Sky `#DCEAFB` — ring tracks, icon discs, bar tracks. Insight bar `#D3E4FA`.
- Green `#2E9E5B`/`#7BC96F` — positive change, renewables, targets.
- Orange `#F08C2E`/`#FFB25B` — cost, emissions, warnings, the "other group" in comparisons.
Color discipline: blue = the main subject/primary series; orange = the contrasting group or a cost;
green = improvement. Max 3 hue families per page.

【Layout Skeleton】 (960×540, 1px = 1pt)
- Margins L=36, R=924 (888 wide). Header 20–110. Body T=124 → 446 (322 high). 重點 bar 456–498.
  Footer text y=508.
- Header: 5px gradient accent bar at x=36 (y 22–108) · chapter label `01｜研究背景` 18 bold blue ·
  conclusion title 26 bold navy (one line, ≤ 32 CJK chars) · source line 18 gray (`對應報告第一章｜…`) ·
  chapter progress dots (26px circles, active = gradient fill with white number) at top-right.
- Body grids: the bento layouts of `reference/storyboard.md` §3 (gutter 16). Typical picks:
  `split-1-2` (hero card + list: purpose, frameworks), `split-7-5` / `mosaic` (data pages; a column
  may hold two stacked cards), `custom` three photo cards over a full-width strip (definitions),
  `single` + `tall` for appendix tables.
- Card internals: title band 56 high; content box = `module_body` (card.x + 20, card.y + 72,
  w − 40, h − 92).

【Typography】
Font {latin: Liter, ea: MiSans}. Sizes: cover title 56 · page title 26 · card title 20 bold ·
key numbers 24–30 bold gradient (hero 54) · body/labels/units 18. Line height 1.2–1.35.
Before writing a text box, compute capacity: chars per line ≈ (width − 4) / fontSize for CJK
(Latin/digits ≈ 0.55em). Design copy to the box, not the box to the copy.

【Chart Language】
- Horizontal bar ranking (category axis reversed, value axis hidden, white data labels inside bars,
  two series stacked so each bar takes its group color). Keep ≥ 1.5 × font size per category row —
  otherwise Office silently drops every other axis label; show representatives and summarize the rest.
- Grouped column before/after (gray `#B9C7D8` = before, blue = after), legend written manually as text.
  When the bars get too narrow for their value labels, use a dumbbell (`dumbbell`) instead.
- Ranking colored by group (`rank` with `groups`), with a big ratio callout ("8×") beside it.
- Rings (donut track + blockArc gradient) for single percentages; caption *below*, not inside.
- 100% segment strip for distributions; progress bar with target tick for goals.
- Tables: blue header row, horizontal hairlines only, 18px cells.

【Signature Components】 (all in `scripts/pptd_kit.py`)
`header` (chapter label + conclusion title + source line + progress dots) · `card` (white + border +
title band + icon; `feature=True` blue gradient hero) · `stat` (number + unit + label, optional icon) ·
`ring` · `bar` · `segments` · `pill` (outlined tag / filled role) · `numdot` (Q1/1/2/3 markers) ·
`icon` (preset shape on sky disc) · `takeaway` (重點 bar) · `footer` (deck name + n / total) ·
`leaf` (cover/closing decoration only) · `chip` (tick + name + value rows) · `tag` (soft tinted name
pill) · `arc` (cover curve) · `rank_bars` · `dumbbell` · `Page.module` kind `stack` (composed card)
and `feature: true` (hero card from the storyboard).

【Slide Types and Layouts】
Cover | photo right 2/3 with white fade + bezier wave, kicker pill, 2-line title (2nd line gradient),
subtitle, 3 meta pills, author line | no header/footer.
Purpose | 316 hero card (framework rows) + three 100-high question cards (numdot, title, pill, 2 lines).
Background | 2 stacked stat cards + 1 tall card with ring + 2 stats + target bar.
Definition | 3 photo cards (84px photo, colored 4px rule, title, one-line gloss, role pill) + example strip.
Literature | timeline card (year gradient + sample + method pill + finding) + gaps list + hero contributions.
Design | variable rows (icon, number+unit, name, role pill) + schematic card + 3 model tiles.
Sample | group rows with photos + share ring | ranking bar chart + big multiplier + notes.
Findings | ring row + distribution strip | before/after columns + delta stat.
Limits | 2×2 limitation grid + estimate rings | hero card numbered next-steps.
Summary | 3 answer cards (Q, answer 2 lines, key number); the key answer on the feature card.
Breather | photo panel (left 5/12) with caption + pictogram, one giant number, 2 stats, a bar — every ~4 pages.
Closing | `Page.closing`: the cover recipe with another photo, 謝謝聆聽 / Q & A, 3 recap lines with icons.
Appendix | full-width table of sources (links), image credits.

【Density Baseline】
Body page: 2–4 cards, 25–45 elements, 3–8 extracted numbers, 1 chart or 1 ring group, 1 takeaway
sentence ≤ 40 CJK chars (must fit one line at 18 bold in 796px).

【Prohibited】
Header photos competing with the title; text inside ring holes longer than 4 characters; legends
generated by the chart engine (clipped in PowerPoint) — write them as text; 1–2-character last lines;
glyphs that collide at 18px in some fonts (≠, ≒) — use words.
