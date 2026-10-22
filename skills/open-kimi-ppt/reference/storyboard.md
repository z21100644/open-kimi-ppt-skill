# Storyboard (策劃稿): outline → page plan → wireframe

The storyboard is the planning artifact a professional deck studio's 策劃師 hands to the designer:
every page's claim, its supporting points, which facts back it, which layout it uses, and the
actual draft copy of every block — decided *before* any color, font or decoration. It lives at
`<project>/plan/storyboard.yaml` next to `plan/facts.md`, and `build.py` reads its decisions
instead of re-deciding them.

Why a separate stage: content mistakes (no point, wrong order, unsupported number, text that cannot
fit) are cheap to fix in YAML and expensive to fix after styling. The bento grid is the planning
vocabulary because modules hold a lot of information per page, recombine freely, and are the layout
language a model plans most reliably. A module is a layout region, not necessarily a drawn card.

Contents: 1 Facts · 2 Outline (pyramid) · 3 Page plan (bento) · 4 Schema · 5 Commands

## 1. Fact sheet — `plan/facts.md`
An auditable evidence table: one row per fact, number, judgement or recommendation, each with a
stable ID that pages cite. Every on-slide number traces to an ID.

```markdown
| ID | Type | Fact | Value | Unit | Period | Source | Confidence | Caveat / conflict | Implication |
|---|---|---|---|---|---|---|---|---|---|
| F1 | fact | 客服工單中可由文件回答的比例 | 62 | % | 2025 | <url>・p.12 表 3 | 中 | 抽樣 500 張，非全量 | 多數問題答案已存在 |
```
- **Type**: `fact` (measured), `interpretation` (someone's reading of facts), `recommendation`.
  Never present an interpretation as a fact.
- **Source**: URL or file plus the exact location (page, sheet, section, table). Keep the original
  unit and period; normalize for comparison in a separate row, never by overwriting.
- **Confidence**: 高 / 中 / 低; 低 or 方向性 (directional only) facts need a `caveat` on the page.
- **Missing values** use an explicit label in Value — 未提供 / 無法推導 / 需要外部驗證 — and appear on
  the slide as 〔待填〕; never fill gaps with general knowledge. Estimates say 推估.
- **Conflicts**: when sources disagree keep both rows with their sources and periods, note the likely
  reason (rounding, period, scope, denominator, forecast vs actual) — never silently "correct" a
  number. If the difference changes the conclusion, ask the user.
- **Derived metrics** (shares, CAGR, deltas) only when inputs and formula are explicit; cite the input IDs.
- **Implication**: why the fact matters — the raw material for takeaways.
- If research shows something is outdated, superseded or disputed, record that too — the outline must
  not build on it.
`storyboard.py check` warns when a page cites a low-confidence fact without a caveat, or a fact
whose value is missing. Simpler tables (ID, Fact, Value, Unit, Year, Scope, Source) still parse.

## 2. Outline — pyramid principle (金字塔原理)
Write the outline before any layout. Four rules, each checked by `storyboard.py check`:

| Rule | In the storyboard |
|---|---|
| 結論先行 Answer first | `governing_claim`: one sentence the whole deck proves. Every page `title` is a claim (「六成工單可由既有文件回答，回覆卻平均等 4.5 小時」), not a topic (「現況分析」) |
| 以上統下 Summary above | every part has a `claim` that summarizes its pages; every page has a `takeaway` its modules support |
| 歸類分組 Group by kind | 2–5 parts; ≤ 5 pages per part; ≤ 5 `points` per page. Items in one group are the same kind of thing (MECE) |
| 邏輯遞進 Ordered | `order` names the sequencing logic of the parts: time / structure / importance / problem → solution → plan |

**Compare storylines first.** Before settling the outline, draft 2–3 alternative `storylines`
(decks with ≥ 5 content pages; the checker warns otherwise), each with its governing claim, structure,
key fact IDs and biggest risk or data gap. Compare them on sharpness (a judgement, not a pile of
material), evidence strength, visual potential, density and audience fit; mark one `chosen: true`
with `why`. This is internal work — record it, don't stop for approval unless the user asked to
review the outline.

**SCR** (Situation → Complication → Resolution) is the default structure for analysis, decision and
proposal decks: Situation = what the audience already accepts; Complication = the change, gap, risk
or opportunity that forces a decision; Resolution = the evidence-backed choice and actions. Give
pages a `role` (situation / complication / resolution / bridge / close) when SCR is used.

Work top-down: governing claim → part claims → page titles → takeaways → points → facts. A page
whose takeaway you cannot write has no point: merge or cut it. A page with two unrelated conclusions
splits; pages whose evidence repeats without advancing the argument merge. Each page:
- is built in evidence order: claim title → main evidence → secondary evidence → interpretation →
  implication/action (takeaway) → source line; never a chart without a sentence saying what it proves;
- carries its strongest `caveat` when the evidence is partial, directional or estimated;
- may name its `bridge`: the question the next page answers — if consecutive bridges don't connect,
  the order is wrong.
A strong title can be challenged by the page's evidence and still hold: 「市場增長正在修復，但價值
正在向結構性優勢賽道轉移」, not 「市場概覽」.

Topic-only requests usually follow one of these skeletons — adapt, don't copy:
- Introduction / pitch: problem → what it is → how it works → proof → how to start
- Analysis / decision: question → criteria → options compared → recommendation → risks → next steps
- Report: result vs target → drivers → issues → actions → asks

## 3. Page plan — bento grid (便當網格)
Each content page picks a layout on the body grid and lists its modules (layout regions) in area order.
The grid is the planning grid shared with `pptd_kit` (`kit.area`, `kit.layout`):

- Canvas 960×540; body box x 36→924, y 124→446 (y 124→494 with `tall: true`, i.e. no 重點 bar).
- 12 columns × 6 rows, 16px gutter. 6 columns = 436px, 3 rows = 153px.
- The gutter is the bento rule "≥ 20px between cards" at this scale: 16pt on a 960 canvas = 21px on
  1280. Never place modules closer than one gutter; let whitespace, not borders, separate them.
- Module count is free (1–6): one big module for one strong message, more for a dashboard — the
  checker warns above 6. Count the messages first, then pick the layout.

Asymmetric layouts are the default vocabulary — every scenario guide forbids evenly divided
compositions unless nothing else works:

| Layout | Areas (first = main) | Use for |
|---|---|---|
| `single` | 12×6 | one strong message, a detailed chart or table (單一焦點) |
| `split-2-1` / `split-1-2` | 8+4 / 4+8 | main content + supporting data, quote or image (非對稱) |
| `split-7-5` / `split-5-7` | 7+5 / 5+7 | two related blocks of unequal weight |
| `main-stack` / `stack-main` | 8 + two stacked 4×3 (mirrored) | main block + two small facts |
| `three-uneven` | 5+4+3 | three items of decreasing weight |
| `center-main` | 6 center + 3 + 3 | one central object with context on both sides (主次結合) |
| `hero-split` | 12×3 hero + 7/5 below | a headline visual/number, then two unequal follow-ups (頂部英雄式) |
| `mixed` | 6×6 + 6×3 + 3×3 + 3×3 | asymmetric mix (混合網格) |
| `mosaic` | 5×6 + 4×3 + 4×3 + 3×6 | a medium square, two small horizontal blocks and a tall strip (混合網格: e.g. chart + two stats + photo or ranking) |
| `custom` | `area: [col, row, colspan, rowspan]` per module | anything else; no overlaps |

Evenly divided — `split` (6+6), `three` (4+4+4), `quad` (2×2), `hero-top` (hero + 2–4 equal):
only for genuinely parallel content, with `layout_reason` on the page; the checker warns otherwise
(custom areas of identical size count as even too).

Principles:
1. Content drives the layout: count the modules first, then pick. Rotate skeletons — the checker
   warns when two consecutive pages share one, unless they are deliberately parallel pages.
2. Size encodes importance: the module with `role: main` sits on the largest area, and is not
   mostly empty (the checker warns below ~30% fill: add extracted evidence or shrink the area).
3. A module is a self-contained region with its own title and one job. How it is drawn is
   `brief.frame`: `region` (default — open block with a top rule, no container; the scenario guides
   forbid cards by default) or `card` (only when the design system uses cards, e.g.
   `bright-blue-bento-briefing`, or the user asks). Checks, wireframe and `Page.module` all use the
   frame's real body box, so copy that fits the plan fits the build.
4. Draft the real copy in `text` now, and the real data in `data` (table rows, chart values,
   diagram steps) — the build renders them, it does not re-decide them. The checker fits text at
   `brief.min_font` and flags orphan last lines; a failure means cut words or change the layout,
   never shrink type. List items may carry a sub-line: `"head<br/>sub"`.
5. Pick `kind` from the extraction table in `design-workflow.md` §3: numbers → `stat`, shares →
   `chart`, sequences → `list`/`diagram`, comparisons → `table`/`chart`, evidence → `image`.
6. Every content page needs one visual anchor (`decoration.md` §2). When the main module is text,
   plan the anchor in `decor` (big number, pictogram, photo, diagram) before building.

Design systems with their own grid numbers (e.g. `bright-blue-bento-briefing`: 316 + 556) may
refine the areas at build time; keep the same modules, order and hierarchy.

### Module kinds rendered by `Page.module`
| kind | fields |
|---|---|
| `text` / `quote` | `text` (string or list) |
| `list` | `text`: items, each `"head"` or `"head<br/>sub"`; numbered rows |
| `stat` | `data: {value, unit, label, tone}` or `data: {items: [up to 3 of those]}` → big numbers side by side |
| `ring` | `data: {value, center, label, sub, tone}` or `items` (≤ 4); value 0–1, `"72%"` or 72 → progress rings |
| `bar` | `data: {value, target, label, display, tone}` or `items` → progress bars with an optional target tick |
| `pictogram` | `data: {n, k, icon, label}` → n icons, first k highlighted ("1 in 10") |
| `table` | `data: {rows: [[header…], [row…]…], col_widths: [ratios]}` |
| `chart` | `data: {cols: [category, series…], rows: [[…]…], horizontal, format, colors}` → bar chart; every column after the first is a series with a text legend; decimals kept unless `format` is set; horizontal charts rank top-down in data order |
| `diagram` | `data: {steps: [[name, sub, icon], …]}` → connected steps (step numbers when there is no icon) |
| `image` | `data: {src: media/…, caption}` → photo; in card frame a photo card (photo on top, color rule, title, caption) |
| `rank` | `data: {rows: [[label, value, group], …], groups: {group: tone}}` → ranking bars colored by group, value after each bar, legend |
| `dumbbell` | `data: {rows: [[label, before, after], …], labels: [before, after], goal, max}` → before → after dots per row; rows reaching `goal` turn green |
| `hero` | `data: {items: [{label, value, icon}], delta: {label, value}}` → full-width focus band on the feature fill: big numbers joined by arrows, the delta on the right (the page's one hero) |
| `stack` | `parts: [2-3 sub-modules]`, `direction: column \| row` → one card holding several element kinds split by dashed rules; each part takes `kind`, `data` / `text`, optional `weight` and a small `title` |
Common: `title`, `icon` (a meaning from `SEMANTIC_ICONS` — carbon, money, power, green, benchmark…
— a library id or a project `.svg`), `role: main`; `hero: true` (one per page) makes that module's
number the page's largest and shrinks every other stat (`decoration.md` §9); `tone: blue | orange |
green | gray | teal` on stat / ring / bar / pictogram items picks the semantic color (declare the
meanings in `brief.colors`); `feature: true` (card frame, one per page) puts the module on the gradient feature
card in light colors — for text / list / quote / stat / ring / bar / pictogram or a stack of those.
In card frame, compose large cards (`decoration.md` §6 card craft): the check warns when a card of
4×4 grid cells or more holds a single stat / ring / bar / pictogram / quote or ≤ 2 lines of text. The renderer grows short copy to the largest size that
fits (up to 36 for quotes, 26 for text) and centres every block vertically in its body, so give it
the real data rather than a description — a visual kind without its data falls back to text, and
the wireframe shows a crossed placeholder. Segments and custom diagrams are still drawn in `build.py`.

## 4. Schema — `plan/storyboard.yaml`

```yaml
brief:
  topic: 客服知識庫 AI 助理導入提案
  audience: 客服部主管與 IT 主管          # who reads/listens
  goal: 同意以 8 週 PoC 驗證 AI 助理       # what they should understand / believe / decide / do
  mode: hybrid                          # live | reading | hybrid
  duration_min: 10
  pages: 6                              # total incl. cover, toc, intro, dividers, end, closing, appendix
  min_font: 18
  register: professional-accessible
  design: self-directed                 # or a preset path, template:<file>, style:<ref>
  scenario: business-plan               # the slides_categories guide in force
  frame: region                         # region (default, no containers) | card
  decor: [數字徽章標步驟, 照片＋4px 色條當證據, 封面與結尾 dots 角落圖形]   # 2-3 deck motifs (decoration.md §5)
  colors: {blue: 主要分析, orange: 成本與風險, green: 對照與目標}   # what each tone means, deck-wide (decoration.md §6, §9)
  language: zh-TW                       # user-specified > source material > conversation; never a separate question
  assumptions: [未指定設計系統，採自主設計]   # defaults taken without asking — report them
storylines:                             # 2-3 alternatives, exactly one chosen
  - {name: 效率缺口, structure: SCR, claim: 六成工單可由既有文件回答…, facts: [F1, F2, F3], risk: F1 為抽樣數據, chosen: true, why: 證據最直接}
  - {name: 成本節省, structure: problem → solution → plan, claim: AI 助理可降低客服人力成本, facts: [F2], risk: 缺人力成本數據, chosen: false, why: 證據不足}
governing_claim: 六成工單可由既有文件回答，先以 8 週 PoC 驗證 AI 助理能縮短回覆時間
order: problem → solution → plan
cover: {title: 客服知識庫 AI 助理導入提案, subtitle: 以 8 週 PoC 驗證回覆效率}
toc: true
section_dividers: false                 # true adds one divider page per part
intro:                                  # optional pages after the cover / toc, before part 1
  - {id: quiz, title: 開始前，先猜三題, takeaway: 答案藏在報告裡，結尾一起對答案}
parts:
  - title: 現況問題
    short: 現況                         # optional ≤ 4 chars, header chapter label
    claim: 多數工單可由文件回答，但回覆仍仰賴人工搜尋
    pages:
      - id: pain                        # slug, becomes the .page file stem
        title: 六成工單可由既有文件回答，回覆卻平均等 4.5 小時
        takeaway: 瓶頸在找文件，不在缺文件
        role: complication              # optional: situation | complication | resolution | bridge | close
        facts: [F1, F2]                 # [] when the page has no external facts
        points: [可由文件回答的工單占 62%, 首次回覆平均 4.5 小時]
        caveat: 工單比例為 500 張抽樣      # optional; required when a cited fact is low-confidence
        bridge: 要怎麼讓客服更快找到答案？   # optional: the question the next page answers
        layout: split-2-1               # added in the page-plan stage; even layouts need layout_reason
        tall: false                     # true: no 重點 bar, body extends to y=494
        decor: {anchor: 工單類型分布長條圖, marks: [圖示, 重點細線]}   # optional: decoration.md §2
        notes: 先說結論：六成工單可由文件回答，卻平均要等 4.5 小時   # optional speaker notes → page.notes
        reveal: 第 1 題答案：B             # optional: a quiz answer shown at the right end of the takeaway band
        modules:
          - role: main
            kind: chart                 # text|list|quote|stat|ring|bar|pictogram|chart|table|image|diagram|rank|dumbbell|stack
            title: 工單類型分布
            icon: tabler-filled/chart-pie   # optional: library id or project .svg (reference/icons.md)
            text: 可由文件回答 62% vs 需人工判斷 38%
          - kind: stat
            title: 首次回覆
            data: {value: "4.5", unit: " 小時", label: 2025 年平均首次回覆時間}
end: {title: 決議事項, takeaway: 請核准 8 週 PoC 與試行人力, points: [核准 PoC 時程, 指派試行人員]}
closing:                                # live / hybrid decks: Page.closing in the cover's recipe (decoration.md §9)
  title: 謝謝聆聽
  subtitle: Q & A
  photo: closing.jpg                    # media/… — echoes the cover photo
  points: [{icon: check, tone: green, text: 8 週 PoC 驗證 AI 助理}]   # ≤ 3 recap lines
# a content page may be a breather instead of a layout (about one every four content pages):
#   breather: {photo, caption, note, pictogram: {n, k, icon}, lead, value, unit, tone,
#              stats: [{value, unit, label, icon, tone}], bar: {label, value, target, display, tone}}
appendix: []                            # optional pages, same schema, takeaway optional — keep it to ≈ 3 (decoration.md §12)
```
A complete example: `tests/fixtures/storyboard/`.

## 5. Commands
```bash
python <skill_dir>/scripts/storyboard.py check  deck/plan/storyboard.yaml --stage outline   # after §2
python <skill_dir>/scripts/storyboard.py check  deck/plan/storyboard.yaml --stage layout    # after §3
python <skill_dir>/scripts/storyboard.py wireframe deck/plan/storyboard.yaml --out deck/plan/wireframe --force
python <skill_dir>/scripts/pptd2pptx.py deck/plan/wireframe/wireframe.pptd --force
python <skill_dir>/scripts/render_pptx.py deck/plan/wireframe/wireframe.pptx --cols 3
```
`check` reads `facts.md` next to the storyboard and exits 1 on errors; fix every error and every
plausible warning. Copy may hold `{placeholders}` that `build.py` fills from the data
(`title.format(**FMT)`): inside a sentence each is measured as a short number; a field that is one
placeholder only is not measured — check its filled width on the render. A message repeated in 3 or
more places prints once with a count (`×19`). It also flags an appendix larger than max(3 pages, 15% of the deck) and page numbers
typed into copy (「P12」): fill cross-references in `build.py` from the deck order instead —

```python
sys.path.insert(0, r"<skill_dir>/scripts")
from storyboard import Storyboard
PNO = Storyboard(HERE / "plan/storyboard.yaml").page_numbers()   # {"quiz": 2, "waffle": 5, …, "closing": 23}
p.text(…, f"答案在 P{PNO['waffle']}", …)
```
 Layout-stage checks: known layout, area count, grid bounds, overlaps, main on the
largest area, text fit and orphans at `min_font`, main-module fill, even layouts without
`layout_reason`, repeated skeletons, icon ids (also inside `data`). The wireframe is a grayscale deck on the final grid (main card darker, visuals as
crossed placeholders with their description): review its overview for rhythm, hierarchy, density
and fit before styling. It is an intermediate artifact — delete `plan/wireframe/` after delivery
unless the user wants it.
