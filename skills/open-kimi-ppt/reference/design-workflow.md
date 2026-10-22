# Deck design workflow (discovery → brief → content → extraction → storyboard → decoration → build → QA loop)

Read this for every *new* deck. It turns "make it look good" into checkable steps, in the order a
professional deck studio works: a 策劃師 researches, asks, outlines and plans every page; only then
does a designer style it. The planning artifacts live in `<project>/plan/` (`facts.md`,
`storyboard.yaml`; schema in `storyboard.md`). The feedback→fix table in §7 is the fastest way to
respond to a revision request.

## 0. Discovery (需求調研: research first, then ask)
A topic alone ("Dify 企業介紹") does not say who the deck is for or what it must achieve, and
generic questions get generic answers. So:
1. **Scan** — 3–6 quick searches on the topic: what it is, current state and recent changes,
   typical audiences and use cases, competitors/alternatives, credible sources. Start `plan/facts.md`
   with what you find.
2. **Ask once** — at most 3 questions in one round (use the ask/clarification tool with options),
   each grounded in the scan, each with a recommended default, in this priority:
   - audience + goal: who reads it and what they should decide/do (options from the use cases found);
   - scope/emphasis: which aspects matter (options from the scan, e.g. 產品功能 / 導入案例 / 價格與部署);
   - length/mode: duration or page count, live talk vs reading deck.
   When no design system or style is given, offer the visual style inside this round — replace a
   question the request already answers, or add it as options of the length/mode question:
   卡片式資訊塊 (bento cards) / 開放式版面 (blocks, rules, whitespace) / 圖像主導 (photo-led).
   Choosing 卡片式 is the explicit request the scenario guides require before cards are used. For cards,
   the runnable briefing templates are the concrete options: 亮藍 (bright-blue, lively) / 墨藍象牙
   (ink-ivory, formal and restrained) / 霧綠 (sage-mist, calm and soft) / 玻璃 (ios-glass, modern,
   iOS-style material) / 清透 (clear, premium and restrained — the recommended default for a public
   research talk); previews in their folders.
3. **Skip** the questions when the request already fixes audience, goal and length, or brings a full
   document/outline — infer the rest. If the user says not to ask, take the defaults.
   Either way record inferred values in `brief.assumptions` and report them at delivery.
4. After this single round run every later stage to delivery without approval stops. Stop after the
   wireframe (§4) only when the user asked to review the outline or layout first.

## 1. Design brief (decide before any page exists)
Fix these parameters from the request and the §0 answers, and write them to `storyboard.yaml`
`brief` (plus `topic`, `goal`, `language`, `design`):

| Parameter | Options | Drives |
|---|---|---|
| Audience | experts / informed public / general public | register, glossing, chart complexity |
| Mode | live talk / reading deck / hybrid (presented by someone who is not the author) | text density |
| Duration | minutes | page budget ≈ 1 page per minute (+ appendix), never more |
| Min font | default 18px for reading/hybrid decks, 24px for large rooms | every text box |
| Register | academic / professional-accessible / casual | wording, titles |
| Output | PPTD + PPTX (+ PDF) | export path |

"Hybrid" is common for thesis preliminary reports and team briefings: the presenter needs the full
reasoning on the slide, so pages must be *dense but refined* (see §3).

Deck language: the user's explicit choice > the source material's main language > the conversation
language. Don't spend a question on it unless sources are multilingual with no main language or
conflict with the user's instruction; record per-page or per-section exceptions in the brief.

## 2. Content pass (facts + pyramid outline)
1. Research first; complete the evidence table `plan/facts.md` (`storyboard.md` §1: type, value,
   unit, period, exact source location, confidence, caveat/conflict, implication) before writing
   pages. Every on-slide number must come from it; estimated values are labelled 推估; missing values
   are labelled, not filled; conflicting sources are both kept; facts the research marks as outdated
   or disputed are not used as support.
2. Draft 2–3 alternative storylines (SCR by default for analysis, decision and proposal decks),
   compare them on sharpness, evidence strength, visual potential, density and audience fit, and
   mark the chosen one (`storyboard.md` §2).
3. Write the outline into `storyboard.yaml` top-down with the pyramid principle (`storyboard.md` §2):
   `governing_claim` → part `claim`s → page `title`s → `takeaway`s → `points` → `facts`.
   Each title is a complete claim (「碳定價上路：排放成本化，柴油車隊首當其衝」), not a topic
   (「研究背景」); the topic goes into the short chapter label.
4. Each takeaway ≤ 40 CJK chars. If you cannot write it, the page has no point — merge or cut it.
   Low-confidence or partial evidence gets a page `caveat`.
5. Register for the informed public: keep the technical term, gloss it once in parentheses, cut filler.
   Too colloquial: 「到底誰比較會省電？」 → professional-accessible: 「能源效率：同業比較下的相對表現」.
6. Run `storyboard.py check … --stage outline` and fix every error.

## 3. Extraction pass (「PPT 換頭術」: keep the information, refine the form)
Never delete information to make a page pretty; convert it:

| Raw text | Becomes |
|---|---|
| sentence with a figure | `stat`: big gradient number + small unit + gray label |
| 3–5 parallel items | numbered rows (`numdot`, a `list` module) or an uneven grid with icons (`reference/icons.md`) |
| a share / rate | `ring` or `bar` with target tick |
| a distribution | `segments` strip |
| before vs after | grouped columns, gray → blue |
| ranking of many items | horizontal bar chart (show representatives, summarize the rest in a note) |
| definitions | photo cards with one-line gloss and a role `pill` |
| timeline / literature | year + subject + method pill + one-line finding |
| key conclusion | the 重點 takeaway bar |

## 4. Storyboard pass (策劃稿: layout + draft copy, no styling yet)
1. For every content page choose a bento `layout` and list its `modules` (`storyboard.md` §3):
   module count first, then the layout; main message on the largest area; vary adjacent pages.
2. Write the real draft copy into each module (`text`, or `data` for stats) — §3's extraction decides
   each module's `kind`. Size text to its box now: the checker fits copy at `min_font`; on failure cut
   words, split into 2-line `<p>` units, or change the layout.
3. Covers and section dividers stay low-density and title-led — no KPI cards or dashboards on a
   cover unless the user asks. Content density comes from the plan, never from smaller type.
4. Run `storyboard.py check … --stage layout`, then render the grayscale wireframe
   (`storyboard.md` §5) and review its overview: rhythm across pages, hierarchy within each page,
   density, empty or overcrowded cards. Fix the storyboard and re-render until clean.
5. **Decoration pass** (`decoration.md`): decide card mode or block mode, pick 2–3 deck motifs
   (`brief.decor`), and name each page's visual anchor and supporting marks (`decor`). A page whose
   main module is text gets an extracted anchor (big number, pictogram, photo, diagram).

## 5. Build (apply the design to the storyboard)
1. Pick the design system (user-named preset, or self-directed). For a data briefing the runnable
   templates fit — `bright-blue` (public, lively), `ink-ivory` (defence, formal report), `sage-mist`
   (ESG, education), `ios-glass` (modern public talk, tech briefing), `clear` (premium, restrained public talk) under
   `design_system/academic/*-briefing` — use one only when specified or when the
   user approves it; it is then one argument, `Kit(..., theme="ink-ivory")`.
2. For decks > 5 pages write `build.py` on `scripts/pptd_kit.py`. Load `plan/storyboard.yaml`; the
   standard content page is four calls, and only special pages (cover, dividers, custom visuals)
   need hand-placed elements:
   ```python
   p = kit.page(); p.header(part_no, pg["title"], sub)
   p.modules(pg, frame=brief.get("frame", "region"))   # every module in its area, storyboard copy/data
   p.takeaway(pg["takeaway"], style="rule")             # "rule" (no container) or "bar"
   p.footer(n); p.save(f"{n:02d}_{pg['id']}.page")
   ```
   Decisions change in the storyboard first, then in the build. One grid, one palette, consistent
   offsets; keep the script in the project folder so revisions stay reproducible.
3. Theme: pass the palette as `Kit(..., theme={...})` — `bg`, `text`, `navy` (titles), `gray`, `blue`
   (primary accent), `cyan` (gradient partner; equal to `blue` for flat designs), `line`/`edge`,
   `white` (surface), `on_accent` (text on accent fills; dark for light accents such as lime),
   `feature` / `feature2` / `on_feature` (feature card; derived from `blue` / `cyan` when omitted).
   Number dots, segment and pill labels pick a readable color automatically.
4. Frame and decoration follow `decoration.md`: cards only when the design system uses them or the
   user chose them (§1, §6 — including card craft), otherwise `frame: region`; draw in the §7 order.

## 6. QA loop (repeat until clean)
```bash
python scripts/lint_pptd.py deck/deck.pptd --min-font 18      # static: bounds, font floor, overflow, orphans
python scripts/pptd2pptx.py deck/deck.pptd --force            # offline PPTX
python scripts/render_pptx.py deck/deck.pptx --cols 2         # PowerPoint (or LibreOffice) → PNG + overview + PDF
```
Read the `overview-<k>.jpg` sheets (6 slides each; `overview.jpg` for decks of 8 slides or fewer), then full-resolution `pages/<n>.png` for anything suspicious. Known defect list:
- orphan last line (1–2 chars) or a line starting with 。，、 → reword / widen / `<p>` split
- text inside ring holes clipping the ring → caption below the ring
- bar chart drops every other category label (rows < 1.5 × font size) → fewer rows
- chart-engine legends clipped → manual text legend with colored ■
- CJK chart labels in a serif fallback → converter sets the East-Asian typeface (already handled)
- glyphs like ≠ ≒ overlapping at 18px → use words
- low card contrast, crowded edges (content < 16px from a card edge), uneven gutters
- trailing 。 on slide copy (the kit strips it automatically)
- `container`: text running past the card / panel / bar it sits on (canvas bounds passing is not enough)
- `collision`: two text boxes whose text overlaps (labels on diagrams, timelines, matrices)
- `icon`: Font Awesome `icon` elements — the offline converter skips them; use the SVG library (`icons.md`)
- `table`: `columnWidths` / `rowHeights` are ratios of the bounds summing to 1, not px (`kit.table`
  converts px for you); `cell`: cell text wrapping past its row height
- `chart`: series keys that are not PPTD (`color` → `fill`, `label` → `dataLabels: {show: true}`) and
  `encode` columns missing from `data.cols` — the converter would silently ignore them
- `contrast`: text vs. the fill behind it below 3:1 (PPTD px = pt, so 18px+ is WCAG large text);
  text over photos is not judged — check those on the render
- `scale`: with `--scale 18,20,26,30,…` every size must belong to the deck's declared type scale; the
  summary line lists the sizes in use — more than ~6 distinct sizes usually means hierarchy drift
- `plain`: a page with only text and thin rules — add its visual anchor or block decoration
  (`decoration.md`); a deck where every page passes can still look sparse, so judge the overview too
- `sparse`: a card whose content spans < 70% of its body height — compose 2–3 element kinds in it
  (`kind: stack`, `decoration.md` §6 card craft) or shrink the card
- `deco`: a pattern (faint rings, watermark icons, dot grids) under text or over a card's edge — move
  it into the card corner or drop it (`decoration.md` §9)

Fix in this order, re-rendering affected pages after each layout change: (1) wrong or missing data →
(2) canvas, container, overflow and clipping → (3) overlaps and collisions → (4) image clarity,
crop and ratio → (5) missing interpretation / takeaway / caveat → (6) hierarchy and readability →
(7) chart labels and notes → (8) consistency and polish. Wrong data or a missing page blocks delivery;
overflow, collisions and unreadable text must be fixed before review.

## 7. Responding to feedback (observed requests → concrete fix)
| Feedback | Fix |
|---|---|
| 字太小 / font too small | raise the floor (18+) in kit + lint; recompute box capacities; cut words, never shrink |
| 單調 / 沒設計感 / 沒有圖文並茂 | run §3 extraction on every page, then the decoration pass (`decoration.md`): one visual anchor per page, rings/stats/pictograms, relevant photos, deck motifs; vary archetypes; hero cards only in card mode |
| 太素 / 不夠美 / 沒有圖塊 | decoration pass (`decoration.md`): fix every `plain` page, add 2–6 supporting marks per content page, bands and motifs on cover / dividers / closing; offer card mode if the user wants cards |
| 不夠精緻 / 數字太多看不出重點 / 每頁長得一樣 / 沒有收尾 | polish (`decoration.md` §9): one hero number per page (`hero: true`), one colour and one icon per meaning (`brief.colors`, semantic icon names), a breather page or hero band every ~4 pages, icons on headings and first-level items only, a closing page, subtitles and takeaways cut to one clause |
| 沒有 vN 好 / 質感不對 / 想要更現代（給了參考，如 iOS 27） | material pass (`decoration.md` §10): keep vN's layout and graphics, change the material only — `theme="ios-glass"` or single tokens (ground, card fill / rim / radius / shadow, icon tiles, tinted capsules, large-title header); never answer with heavier colour blocks; build each iteration as a new folder so versions can be compared |
| 風格不統一 / 質感廉價 / 太平 | art direction (`decoration.md` §11): write the rule set down and pass every element through it; restore same-hue tonal transitions (§10.6) — never "flat only"; or start from `theme="clear"` |
| 自我迭代 / 再最佳化 | self-review (`decoration.md` §10.5): every decoration carries data or links pages; then UI/UX — header and progress, title-to-body separation, one gutter for cards and takeaway, every block in the same material; render and lint each round to 0 warnings |
| 沒有原稿（或範例）有設計感 / 卡片很空 | card craft (`decoration.md` §6): compose each card from 2–3 element kinds with dashed rules (`kind: stack`), one gradient feature card per page, a deck-wide color legend (`brief.colors`) applied to numbers, groups and pills, finishing details (pills, tags, target ticks, photo rules, cover arc); compare against the reference page by page and fix every `sparse` card |
| 附錄太多 / 搞清主次 / 重點被淹沒 | main vs supporting (`decoration.md` §12): appendix ≈ 3 pages (glossary, data, methods & sources on one page), method pages folded into one "checks hold" page, one point per side card, a findings summary page with 「發現 N」 markers, reveals in one place, one vocabulary |
| 重新審查 / 整體呈現再迭代 | review pass (`decoration.md` §12.2): 2×2 sheets of every page, a per-page list (lead number, takeaway, vocabulary, reveals, typed page numbers, repeated numbers), fixed in one build |
| 圖看不懂 / 點疊在一起 / 標籤擠成一團 | readable charts (`decoration.md` §12.1): ticks, labelled average lines, corner quadrant names, coinciding points as one labelled point, `free_spot` labels or numbered markers + roster card, lines broken behind labels |
| 需要講稿 / 現場報告 | speaker notes: `notes:` per page in the storyboard, `page.notes` in `build.py` (SKILL.md Step 5.9); one paragraph per page with the page's own numbers |
| 要密集閱讀文字 | keep full sentences in 2-line units under each extracted number; add 重點 bar |
| 頁數太多 | merge in `storyboard.yaml` to the §1 page budget; combine adjacent small topics into a `split` page |
| 邏輯不清 / 重點不明 | revisit §2: governing claim, part claims, claim titles; re-run the outline check |
| 卡片對比不好 | tinted canvas, border, shadow, title band, underline accent |
| 太白話 / too colloquial | §2.4 register: technical term + gloss, claim titles, remove questions/exclamations |
| 整體布局 | header with chapter progress, fixed body box, takeaway bar, consistent card grid |

## 8. Delivery
Deliver the PPTD project folder (+ `build.py` and `plan/` with `facts.md` and `storyboard.yaml`), the
PPTX and the PDF — after the final `render_pptx.py deck.pptx --embed-fonts --pdf-to deck.pdf` pass, so the
PPTX carries its fonts (PowerPoint) and the PDF sits next to it; then delete `.qa-images/`. Mention `brief.assumptions`, placeholders left for the user
(〔待填〕) and any approximate facts that need confirmation.
