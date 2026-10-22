# Decoration pass (圖形裝飾／美化)

Read this after the storyboard and before `build.py`, and again whenever feedback says 太素 / 不夠美 /
沒有圖塊 / 沒設計感. The storyboard decides *what* each page says and where the modules go; this pass
decides *which graphic blocks carry it*, so pages read as designed slides rather than typeset text.
A page made only of text and hairlines is a document, not a slide — `lint_pptd.py` flags it as `plain`.

Contents: 1 Boundaries · 2 Anchor + marks · 3 Vocabulary · 4 Budget · 5 Deck motifs ·
6 Cards vs. blocks, card craft · 7 Procedure · 8 QA · 9 Polish · 10 Material · 11 Art direction

## 1. Boundaries — who decides
Priority: the user's request > the design system (`reference/design_system/…`) > the scenario guide
(`reference/slides_categories/…`) > this file. This file adds a method, not permissions:
- **No cards by default** stays in force. Cards are used only when the design system uses them
  (e.g. `bright-blue-bento-briefing`) or the user asked for them — choosing 卡片式資訊塊 in the
  discovery round counts as asking (`design-workflow.md` §0). Otherwise use the block vocabulary
  below, which groups and decorates without containers.
- Scenarios that keep body pages minimal (e.g. `academic-research`) limit *atmosphere* decoration
  to the cover, dividers and closing page — body pages still need a visual anchor (§2).
- Decoration never carries a fact on its own: no decorative arrows without meaning, no rings for
  numbers that are not shares, no images unrelated to the claim.

## 2. Two layers on every content page
1. **Visual anchor (exactly one per content page)** — the element that carries the page's main
   evidence and is seen first after the title: a chart, photo, diagram, ring/bar group, pictogram,
   timeline, or one big extracted number on its own field. The storyboard's `role: main` module is
   normally the anchor; if that module is text, give the page another anchor or extract one (§3 of
   `design-workflow.md`).
2. **Supporting marks (2–6)** — small graphic elements that do structural work: grouping, ordering,
   emphasis, wayfinding. Each mark has a job you can name; remove any whose removal loses nothing.

Covers, section dividers and closing pages add a third layer, **atmosphere**: a photo, band or
motif that sets the tone. Atmosphere stays off body pages unless the design system uses it there.

## 3. Vocabulary (all in `scripts/pptd_kit.py`)
| Job | Element | Kit call | Rules |
|---|---|---|---|
| Group | open region: top rule + title | `region` | default module frame; 4px accent rule on the main module |
| Group | edge band (tint strip anchored to canvas edges) | `band` | square, no border/shadow, touches the left and right canvas edges (or spans the full body width); content sits on it |
| Group | card (card mode only) | `card` | see §6 |
| Order | number badge | `numdot` | steps, ranked lists, research questions |
| Order | step connector / timeline | `module` kind `diagram`, `line`, dots on a rule | every connector has a direction or meaning |
| Emphasis | big number + small unit + gray label | `stat`, `gtext` | one hero number per page at most; others 24–36 |
| Emphasis | tag / pill | `pill` | method names, roles, status; outline = label, filled = state |
| Emphasis | accent marker | `solid` (short thick bar), `takeaway` | marks the one sentence or item that matters |
| Wayfinding | chapter label + progress dots | `header` | fixed position on every body page |
| Wayfinding | ghost numeral / keyword | `watermark` | chapter number or year behind a divider or hero area; 12% alpha; never under paragraphs |
| Imagery | photo with base rule + caption | `photo`, `img` | evidence or scene, never filler; crop, don't stretch |
| Imagery | icon disc / bare glyph | `icon`, `icon_glyph` | library icons (`icons.md`); one icon family and fill per deck |
| Imagery | pictogram (unit chart) | `pictogram` | "1 in 10", "4 of 25" — counts the audience can see |
| Data | ring, progress bar with target, segment strip | `ring`, `bar`, `segments` | shares, goals, distributions; caption below the ring |
| Data | grouped ranking (bars colored by group) | module kind `rank`, `rank_bars` | categories the reader should tell apart (e.g. wafer fab vs. packaging); legend from `groups` |
| Data | before → after per row | module kind `dumbbell` | sensitivity, re-runs, policy effects; rows reaching `goal` turn green |
| Group | row chip: tick + name + value | `chip` | inputs / outputs, labelled quantities inside a card |
| Emphasis | soft tag (tinted pill, navy text) | `tag` | members of a set (company names); quieter than `pill` |
| Atmosphere | sweeping hairline arc | `arc` | cover / closing, under or across the cover photo |
| Atmosphere | corner motif: `dots`, `rings`, `leaf` | `motif` | cover, divider, closing; one corner, low contrast; on bare canvas — a motif over a band of the same tint disappears; on pages with a footer use a top corner, bottom corners run into the page number |
| Atmosphere | full-bleed photo with a wash | `img` + `solid` with alpha | cover / closing; text sits on the washed side |

## 4. Budget per page type
| Page type | Anchor | Marks | Atmosphere |
|---|---|---|---|
| Cover | photo, band or large motif | kicker pill, meta numbers | ≤ 1 motif |
| Section divider | ghost numeral or photo | chapter label, one question | ≤ 1 motif |
| Content (medium density) | 1 | 2–6 | none (unless the design system uses it) |
| Content (dense: data, comparison) | 1 | 2–4 — density comes from evidence, not ornaments | none |
| Closing / summary | big numbers per answer, or photo with wash | number badges | ≤ 1 motif |
| Appendix | table | rules only | none |
Hard limits: one accent block (filled band, hero field or gradient feature card) per page; ≤ 3 hue
families per page; the anchor is the largest graphic on the page.

## 5. Deck motifs
Pick 2–3 recurring motifs for the whole deck before building and record them in the storyboard
(`brief.decor`, `storyboard.md` §4), e.g. "number badges for steps; photo + 4px rule for evidence;
dots motif on cover and closing". Keep each motif's shape, color and meaning fixed across pages —
a recurring motif reads as design, a different ornament per page reads as clip art.

## 6. Cards vs. blocks
A **card** is a container that floats inside the canvas with margins on all sides — rounded or
rectangular, usually with a border or shadow — holding one module. The scenario guides forbid it by
default. A **block** is not a container: an edge band, a strip spanning the full body width, a tint
field behind a whole section that touches a canvas edge, or a small graphic (disc, badge, pill,
marker). Blocks are allowed in every scenario that allows color fills.

Card mode (design system uses cards, or the user chose 卡片式): tinted canvas + white card + 1px
border + soft shadow + tinted title band + icon disc + short accent underline — `kit.card`; see
`bright-blue-bento-briefing/design.md`. White cards on a white page read as one flat sheet: always
tint the canvas.

### Card craft — what makes a card deck look designed
Learned by comparing a user's hand-designed deck with kit-default rebuilds of the same content: the
defaults used the same palette, cards and icons, yet read as plain because each card held one
element and every card looked alike. Four habits close the gap:

1. **Compose every card.** A card is a small layout of 2–3 element kinds, not a frame around one:
   ring + numbers over a progress bar with a target tick; thumbnails + counts over a ring; a ranking
   with a big "8×" callout beside it; big number + formula rows. Split the parts with a dashed rule
   (`hdash`) and fill the card edge to edge — no half-empty bodies. Storyboard: `kind: stack` with
   2–3 `parts` (`direction: column | row`, `weight`, part `title`); `build.py`: draw the parts
   yourself. A single stat, ring, bar or two lines of text in a card of 4×4 grid cells or more is
   too little — compose it or give it a smaller area.
2. **One feature card per page.** Exactly one module may sit on the gradient feature card
   (`feature: true` → `card(feature=True)`, deeper blue `FEATURE_G`, white text, light-colored
   content) against white cards — the page's light/dark hierarchy. Use it for the framing (research
   setup), the worked example ("算給你看"), the consequence or the next steps; never for a chart or
   table. Not every page needs one; never two.
3. **Color carries meaning.** Fix what each hue means for the whole deck in `brief.colors` (e.g.
   blue = main analysis / wafer fab, orange = carbon & cost / packaging, green = green power /
   comparison) and apply it everywhere: numbers (`tone`), bar and ranking groups (`groups`), pill
   outlines, photo rules. A ranking whose bars are all one color throws that meaning away — use
   `rank` with groups instead of a single-series chart.
4. **Finish with small details.** Outline pills for method names and roles (filled = the main
   one), soft `tag`s for members of a set, a target tick on progress bars, `chip`s for labelled
   quantities, gradient icons in title discs, a color rule under each photo, chevrons between
   timeline numbers; on the cover a photo washed into the canvas, an `arc` and one or two leaves.

Build card pages in `build.py` when a page needs a custom composition; `Page.module` covers the
common ones (`stack`, `feature`, `rank`, `dumbbell`). `lint_pptd.py` reports `sparse` when a card's
content spans less than 70% of its body height.

## 7. Procedure
1. From the brief and scenario, decide the mode: card mode or block mode (§1, §6).
2. Choose the deck motifs (§5) and write them to `brief.decor`.
3. For every page, name its anchor and marks in the storyboard (`decor: {anchor: …, marks: […]}`);
   pages whose main module is text get an extracted anchor.
4. Build: draw atmosphere and bands first, then the anchor, then text, then marks — later elements
   sit on top, and `band` / `watermark` must come before what they sit behind.
5. QA (§8), then fix in the storyboard or `build.py`, never by shrinking type.

## 8. QA
- `lint_pptd.py` reports `plain` for pages with no visual element; fix every one (add the anchor).
- Card mode: `lint_pptd.py` reports `sparse` for half-empty cards; `storyboard.py check` warns about a
  large card holding one small element, more than one feature card on a page, and tones used without
  `brief.colors`. On the overview, every card should look composed (§6 card craft).
- On the rendered overview: every content page has one anchor seen first after the title; marks
  repeat the deck motifs; nothing decorative sits under body text; the same color means the same
  thing on every page; covers and dividers feel different from body pages.
- The final cut: for each mark ask "if I delete this, what does the reader lose?" — if nothing,
  delete it. For each page ask "what would make this look like a slide?" — if the answer is
  nothing, the page is missing its anchor.

## 9. Polish — the finish every deck gets
Learned from a user's review of a decorated deck ("more symbols, more polish") and the optimised
version that followed. Card craft (§6) makes each card composed; these rules make the deck read as
one designed object. They are defaults: the storyboard check and lint report the misses.

1. **One focus per page.** The page's single most important number is its hero — the largest thing on
   the page (≈ 60–96 px); every other number is supporting (24–32 px). Storyboard: `hero: true` on
   that module (or stack part); the kit shrinks the other stats on the page. A content page with five
   or more numbers and no hero, or with two heroes, is flagged. Parallel answers (a summary of Q1–Q3)
   may share one size; give the key one the feature card instead.
2. **One meaning per colour, one meaning per icon — deck-wide.** Declare the colours in
   `brief.colors` (blue = the analysis, orange = carbon & cost only, green = green power / discounts /
   benchmarks, teal = a second group such as packaging & testing, gray = neutral). Never let the
   carbon colour also mark a group. Name icons by meaning (`SEMANTIC_ICONS`: money, carbon, power,
   green, benchmark, compare, assets, people, time, analysis, limit, next, law, data, growth,
   efficiency, question, calc, check) so one icon cannot drift into two meanings.
3. **Rhythm.** Ten pages with the same header + two cards + takeaway skeleton tire the room. Give a
   deck of 8+ content pages at least one breather page (`breather:` — a photo panel with a caption
   and a pictogram, one giant number, two supporting stats, a bar) about every four pages, and/or a
   hero band (`kind: hero` — "0.81 → 0.64 ｜ −0.17" across the full width) on the key finding.
4. **Restraint.** Icons on headings and first-level items only; one pattern per feature card (small
   rings in the title corner, drawn only when the title leaves room); no dot grids or faint watermark
   icons behind copy. Patterns stay inside their card and clear of text — lint reports `deco`.
5. **A closing page.** Live and hybrid decks end on a closing page in the cover's recipe
   (`closing:` → `Page.closing`: thank-you title, "Q & A", up to three recap points with icons, the
   byline, a photo that echoes the cover's). Sources move behind it as a backup slide.
6. **Distilled copy.** Subtitle and takeaway: one short clause each (≈ 30 字, checked). Lists:
   keywords, not sentences. Numbers come out of sentences into stats. Symbols replace connectives
   (→ ＝ × ≈ ▲ ▼ ≠ ✓). Break two-line subtitles between phrases with `<p>` — never inside a word.

## 10. Material — iterate the surface, keep the layout
Learned from iterating a deck the user already liked: a version with heavy colour blocks and
translucent shapes lost to the original; the version that kept every layout and changed only the
material (iOS 27-style glass) won. Material and layout are separate axes — change one at a time.

1. **When the user prefers an earlier version, keep its layout.** Ask (or take) a reference
   direction for the surface ("iOS 27", "Material You", "paper") and change only material tokens:
   ground, card fill / rim / radius / shadow, icon container, capsule style, header, takeaway.
   Theme `ios-glass` is the glass set; a dict theme over any preset changes single tokens.
2. **Calm glass, not transparency for its own sake.** Cards near-opaque (≈ 86–96% white, top-lit),
   a bright rim, a soft deep shadow; translucency only where no copy sits (lint `deco`); one tinted
   feature surface per page. Heavy colour blocks behind the content fight the glass.
3. **Concentric corners.** A frame around a photo or a card inside a card: inner radius = outer
   radius − inset (`Kit.rounded` bakes rounded photos; the converter has no picture radius).
4. **Every block in the same material.** A breather's numbers, a recap list, the takeaway — all sit
   on glass; nothing floats bare on the wallpaper except the header.
5. **Self-review before showing.** Each decoration must carry data or tie pages together (a 0→1 bar
   becomes a ruler with the averages; a lone ring becomes a share-of-emissions vs share-of-revenue
   pair; the summary cards carry the method pills of the questions they answer). Fix lint warnings
   at their cause — a false positive is a lint bug to fix, not a warning to leave.
6. **Keep the transitions.** De-noising removes ornaments, not light: surfaces, tiles and key numbers
   keep a same-hue tonal transition (a 10–18% lightness step, light from the top-left). Fully flat
   versions of an approved deck were judged cheap; cross-hue or high-contrast gradients read loud.

## 11. Art direction — one rule set, written down
A deck assembled from several looks (one version's graphics, another's material, a third's
restraint) still reads as a collage until every element passes one rule set. Write it down before
the next iteration (`plan/art-direction.md`) and check each element against it:
shape language (rounded rectangles; circles only for data) · a radius scale in px · one or two icon
treatments · one divider · a fixed number of surface types · one accent colour plus meanings ·
transitions · type scale · photo treatment · what is prohibited. Theme `clear`
(`design_system/academic/clear-briefing`) is such a rule set in kit form.

## 12. Main vs supporting (主次) — what the deck is for, and what only backs it up
Learned from a public classroom deck that grew to 34 pages while answering method questions: ten
appendix pages, side cards with three equal numbers, and a quadrant chart nobody could read. The
user's verdict was 「附錄頁數過多，請搞清主次」. These rules are defaults; `storyboard.py check` reports
a big appendix and typed page numbers.

1. **Appendix budget.** Keep supporting pages to about three — a glossary, the data table, and methods
   & sources on one page (one table: check · how · result; sources one line per category) — at most
   max(3, 15%) of the deck. Method and robustness pages that accreted during review collapse into one
   main-line page ("five checks, conclusions hold" with each result) plus that one appendix table;
   per-company detail stays in the analysis files.
2. **One point per side card.** The side card carries one lead number and one line; secondary numbers
   go small and gray or into the speaker notes. A side card that repeats the chart's numbers (a
   waterfall's steps listed again) is noise — replace it with the one point the chart implies.
3. **Fold pages that say one thing.** Two pages on one idea (a price ladder and the fee burden; the
   checks and "scores are relative") become one page with two cards.
4. **Close the findings and point back to them.** After the scorecard, one summary page states the
   N findings with their lead numbers; the finding pages carry 「・發現 1」… in their chapter label and
   the summary links them (「見 P14」).
5. **Reveal in one place.** Quiz answers and other reveals appear in the same spot on every page —
   `p.takeaway(text, reveal="第 1 題答案：B")` puts a green check capsule at the right end of the
   takeaway band (storyboard `reveal:`) — not in a different card each time.
6. **One vocabulary.** Once the deck names its measures (營運分數 / 低碳分數), every legend, axis, bar
   label, glossary card and appendix header uses those names; model codes appear once, in brackets.
7. **The takeaway is the main finding.** Not a side observation ("only one company is…"); titles
   state the headline, not a sensitivity check — those go to the notes.
8. **Never type a page number.** Fill every cross-reference from `Storyboard.page_numbers()`
   (`scripts/storyboard.py`) so pages can move; the check flags 「P12」 typed into copy.

### 12.1 Readable scatter and quadrant charts
- Ticks on both axes; each average or cut line dashed in its measure's hue and labelled with its value
  (below the axis or at the line's end) instead of a legend elsewhere.
- Quadrant names with counts in their own corners, clear of the dots.
- Points that coincide (several companies at 1.0 / 1.0) are one point with a label that says how many
  tie there; the names go in the side card. Never let one dot silently stand for four.
- Name sparse focus points directly — `pptd_kit.free_spot()` tries centred above, nudged, right, left,
  below and never touches a dot, a caption or another label; dense groups get numbered markers with a
  legend in the side card. Place labels left to right and append each box to `taken`.
- When a label has to sit on a reference line, break the line behind the label rather than striking
  through the text.
- Points outside the axis range get a note (「A 公司 0.10／0.04 在圖外」), never silent clipping.
- The side card next to such a chart is a roster (who is in each group), not "how to read" text.

### 12.2 Review pass before another iteration
When asked to 「重新審查」 or iterate the whole presentation, render the deck as 2×2 sheets and list,
per page: is there one lead number; is the takeaway the main finding; are names consistent; are
reveals in the same place; are page numbers computed; does a card repeat the chart. Fix the list in
one build, re-render the changed pages, and report the list in the reply.
