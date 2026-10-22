---
name: open-kimi-ppt
description: Create, edit, replicate, read and export presentations as an editable PPTD project (Kimi Slides' YAML format) plus an offline-generated PPTX with fade transitions and a PDF. Planning-first workflow (research-grounded discovery questions → fact sheet + pyramid outline → bento-grid storyboard and wireframe → build with a Python component kit → lint and rendered-image QA), runnable design templates (bright-blue, ink-ivory, sage-mist, ios-glass, clear) and preset design systems. Use for any presentation, PowerPoint, PPT/PPTX, slide deck, PPTD, infographic or poster task unless the user asks for another format. Deliver with absolute local file links.
---

> **Version 1.0.3 (2026-10-11)** — offline, planning-first edition (forked from upstream open-kimi-ppt-skill 1.2.0); changes in the repository's `CHANGELOG.md`.
> **Toolchain:** PPTX export is offline (`scripts/pptd2pptx.py`); visual QA renders with PowerPoint (Windows COM) or LibreOffice (`scripts/render_pptx.py`). Kimi's online PPTX writer fails server-side (`no available pptx export plan`) — `scripts/export_pptx.py` is legacy. Kimi image/PDF export (`scripts/export_images.py`) and the browser editor (`npx open-kimi-ppt-skill serve`) still work and are optional.
> `<skill_dir>` = the folder containing this SKILL.md (e.g. `~/.claude/skills/open-kimi-ppt`).

# Definition
PPTD is Kimi Slides' YAML abstraction of OOXML: a `.pptd` manifest (theme, page list) plus one self-contained `.page` file per slide — no masters, what you see is what you get. Unless the user opts out, every task delivers:

1. the complete PPTD project (`.pptd` + `pages/` + `media/` + `build.py` and `plan/` when used);
2. the matching `.pptx` (fade transition on every slide; fonts embedded where PowerPoint is available) and a PDF.

An existing PPTX can be converted to PPTD for editing; both outputs are then delivered again.

# Workflow

## Step 0 — prerequisites
1. **Python 3.9+** (required). If missing, stop and ask the user to install it (Windows: tick "Add python.exe to PATH"). The scripts `pip install --user` their soft deps when missing: PyYAML, python-pptx, lxml, Pillow (+ PyMuPDF for the LibreOffice path).
2. **Renderer** (strongly recommended): Microsoft PowerPoint (Windows) or LibreOffice (`soffice`). Without one, QA falls back to lint + structural review — say image QA was skipped.
3. **Optional**: Node.js 18+, a Chromium browser and network access, only for the browser editor / Kimi image export. Never block delivery on them.

## Step 1 — read the context
Read every file and URL the user gave. Read the references a task needs, not all of them:

| Task | Read |
|---|---|
| any new deck | `reference/design-workflow.md` (stages, QA order, feedback table), `reference/storyboard.md` (schema, layouts, commands) |
| decorating / polishing / iterating | `reference/decoration.md` (§6 card craft, §9 polish, §10 material, §11 art direction, §12 main vs supporting) |
| hand-written or converted `.page` files | `reference/pptd.md` §1–§5 (Chart §5 only for charts, §6 only for animations); `reference/shapes.md` for preset shapes |
| a scenario or preset | `reference/slides_categories.md` → its scenario guide; the preset by ID: glob `reference/design_system/*/<id>/design.md` (the illustrated catalog `theme.md` lives in the repository, not the installed skill) |
| icons / fonts / posters | `reference/icons.md`, `reference/fonts.md`, `reference/general-poster.md` (posters and single visuals only) |

Decks built with `scripts/pptd_kit.py` get valid PPTD from the kit; consult `pptd.md` only for an element the kit lacks.

## Step 2 — understand the request
1. **Purpose** — create (from scratch or a PPTX template), edit (local changes, single-page polish), or replicate (images / PDF → PPTD).
2. **Design direction** — self-directed (no or light style constraints), design system (a preset under `reference/design_system/`, or the user's full spec), template (a PPTX that must be used), or style transfer (images, web pages).
3. **Input** — topic only, full document, or page-by-page outline / script. With a document or outline and no word on expansion, search to add relevant material and cases unless the user says not to.
4. **Page count** — the user's number wins; an outline sets it; for a structured document ask how much one page should cover and estimate; for a topic recommend a count in the discovery round.

**Discovery round (需求調研).** For a new deck from a topic or a thin request: scan the topic first, then ask at most 3 questions in one round — audience + goal, scope / emphasis, length / mode — each with options and a recommended default drawn from the scan (`design-workflow.md` §0). Skip it when the request already fixes these or brings a full document or outline; record inferred defaults in `brief.assumptions`. After it, work through to delivery without approval stops unless the user asked to review the outline or wireframe.

**Ask (with the agent's question tool) when** the intent is unclear, files or URLs are inaccessible, intents conflict (a preset plus an incompatible style; "10 pages" plus "30+ pages"), or purpose / direction / input / page count cannot be determined. Fold these into the discovery round when one is due.

## Step 3 — produce

**Replicate.** Estimate positions, fonts and sizes from the images and replicate 1:1 (grid lines and close-ups help). Draw simple content as elements; approximate icons with the SVG library, your own SVG or preset shapes (never Font Awesome `icon` elements — the offline converter skips them); crop photos and avatars out of the source image.

**Edit.** Convert the PPTX to PPTD, review the converted pages (structure, key visuals, a few pages individually), change only the intended scope. Conversion is not lossless — if the user reports garbled formatting, compare with the original PPTX and repair.

**Generate.** Follow `design-workflow.md`: discovery → design brief → facts + pyramid outline → extraction → storyboard + wireframe → decoration → build → QA; its §7 maps feedback (字太小, 單調, 不夠美, 頁數太多, 搞清主次…) to fixes. The outline and page plan live in `plan/storyboard.yaml` (`storyboard.py check` / `wireframe`); content and layout are decided there before styling. Edits, replications and template fills that keep the structure skip the storyboard unless pages are added or moved.
- Decks over ~5 pages: write `build.py` (kept in the project) on `scripts/pptd_kit.py` — `p.modules(page)` renders storyboard modules. For the helpers (header, card, stat, ring, chart, table, decoration…) run the API index instead of reading the 1,800-line file: `python <skill_dir>/scripts/pptd_kit.py [filter]` prints each signature with one line (plus THEMES / LAYOUTS / SEMANTIC_ICONS). Worked example: `reference/design_system/academic/bright-blue-bento-briefing/sample_build.py`.
- Cross-references (「答案在 P5」) come from `Storyboard.page_numbers()`, never typed; quiz answers and other reveals use `p.takeaway(text, reveal="第 1 題答案：B")` (storyboard `reveal:`) so they always appear in the same place; speaker notes go in `page.notes` (Step 5.9).
- Iterations of a deck go in a new folder each time so versions can be compared.

**Design direction.**
- *Self-directed:* read `slides_categories.md` and the scenario guide, then design. You may *propose* a fitting preset (e.g. a briefing template below for research / ESG / data talks); use it only once the user agrees.
- *Design system:* read the general constraints in `slides_categories.md` and the scenario guide, then the specified system — the user's spec or the preset found by ID (`reference/design_system/*/<theme-id>/design.md`). Never mix in other styles; never auto-pick a preset.
- *Runnable templates* (a `design.md`, `sample_build.py`, `preview.jpg` and a kit theme each; one storyboard and build script fits all — `Kit(..., theme=…)` switches the whole look, cover included via `Page.cover`; copy the archetype page functions, replace the data, keep the grid numbers):
  `academic/bright-blue-bento-briefing` (`"bright-blue"`, 亮藍資訊卡: bright, gradient numbers) · `academic/ink-ivory-briefing` (`"ink-ivory"`, 墨藍象牙: restrained, serif titles, hairline cards, no gradients) · `academic/sage-mist-briefing` (`"sage-mist"`, 霧綠: calm, rounded borderless cards) · `academic/ios-glass-briefing` (`"ios-glass"`, 玻璃: iOS 27-style glass over bright-blue layouts) · `academic/clear-briefing` (`"clear"`, 清透: one art direction — glass on a soft ground, rounded rectangles, pale feature cards, one solid hero band, same-hue tonal transitions, per-page source footers).
- *Template:* convert the PPTX, study its style (colours, fonts, element traits, layouts, density), read special pages (cover, summary, dividers) for layouts and reusable components, then build with it.
- *Style transfer:* analyse the reference's colours, fonts, layouts, components and element styles — look at a URL's visuals, not only its text — and reuse its illustrations, fonts and type hierarchy where possible.

**Other formats.** Infographics, posters and single visuals: read `general-poster.md`, build a one- or few-page editable PPTD; for an image, still build in PPTD, then render.

**Images.**
1. Use images on body pages too, to show subjects, explain, give evidence or set a scene — analytical, technical and academic decks included (evidence photos of products, experiments, interfaces, sites); never reduce every page to text, colour blocks and shapes. Logos, icons, textures and tiny thumbnails do not count.
2. Products, people, places, buildings, events, cases, interfaces, experiments and spaces get real images or screenshots first; generated images only when none can be found. Priority: the user's → official and credible sources → relevant search results → generated.
3. Decide the image list, fetch it in one batch into `media/`, then design around the proportions — never stretched or blurry. No images added only to fill a quota; each serves the page's point.
4. Icons: `python <skill_dir>/scripts/icons.py search <english words>` (1,000+ filled Tabler icons), placed as editable vectors (`page.icon` / `page.svg`, or `icons.py shape`); copy into `media/icons/` to edit or combine, or draw an SVG (`reference/icons.md`). Scenario and design-system icon rules take precedence.

**Copy.**
- Plain, concrete language: no stacked metaphors, slogans or abstract jargon (distribution, N-step argument, closed loop, deconstruction…); no AI phrasing ("not X, but Y", "X is Y", "why / how", "key takeaway", "N battlefronts"); no over-colloquial lines.
- Public decks keep a professional register: the technical term glossed once (「非期望產出（碳排）」), claim titles on body pages, no rhetorical questions in body copy.
- No trailing full stop on slide copy; every number has unit, year and scope; estimates are labelled.

## Step 4 — validate
1. **Lint**, fixing every error and every plausible warning (checks and fixes: `design-workflow.md` §6; estimates are conservative — confirm on the render). Hand-written pages are also checked against `pptd.md` for required fields, types, theme tokens and resource paths:
   ```bash
   python <skill_dir>/scripts/lint_pptd.py /abs/path/project/deck.pptd --min-font 18
   ```
2. **Rendered review** — required when the model reads images:
   ```bash
   python <skill_dir>/scripts/pptd2pptx.py /abs/path/project/deck.pptd --force
   python <skill_dir>/scripts/render_pptx.py /abs/path/project/deck.pptx --cols 2      # --pages 2,3,8 while fixing
   ```
   Output: `.qa-images/overview.jpg` (P1…Pn in manifest order, each slide under its label strip), `overview-<k>.jpg` sheets of 6 slides for decks over 8 slides, `.qa-images/pages/<n>.png`, a PDF. (`export_images.py` is an optional online alternative.) Read the sheets — one tall overview of a long deck is scaled until the copy is illegible — confirm suspects on the full-size page, fix in the `.page` or `build.py`, re-run lint → convert → render until every page passes — never deliver before. Check each page for:
   - **Basics** — sharp, undistorted images; no text over faces, products or logos; nothing outside the canvas; enough contrast (text vs ground, adjacent fills); consistent alignment, spacing, type scale and margins; no overflowing or hidden text; no orphans (1–2 characters on a last line) or line-initial punctuation; axis labels not skipped, legends not clipped, CJK labels in the right font; cards contrast with the ground and keep ≥ 16 px padding.
   - **Design** — one visual anchor per page (chart, photo, icon group, big number) with the deck's 2–3 recurring motifs; in card mode each card composed of 2–3 element kinds and filled, at most one gradient feature card per page, one meaning per colour; one largest number per page, one meaning per icon, a breather page or hero band breaking the skeleton, decoration inside cards and clear of text, a closing page for live decks, one-clause subtitles and takeaways (`decoration.md` §6, §9).
   - **Material and art direction** — when the user prefers an earlier version, its layout is kept and only the material changes; every block on the same material (glass: no data bare on the wallpaper), concentric corners, every decoration carrying data or linking pages; one shape language (rounded rectangles, circles only for data), radius scale, icon treatment, divider and surface set; same-hue tonal transitions kept on surfaces, tiles and lead numbers — fully flat reads cheap (`decoration.md` §10–11).
   - **Main vs supporting** — appendix about three pages (glossary, data, methods & sources); side cards make one point instead of repeating the chart; the takeaway states the main finding; reveals in one place; one vocabulary; page references computed (`decoration.md` §12).
   - **Readable charts** — ticks; average lines labelled with their values; quadrant names in their corners; coinciding points merged with a count; point names never overlapping (`free_spot`); reference lines broken behind labels; out-of-range points noted (`decoration.md` §12.1).
3. Without image input, review structure over several rounds (bounds, long text, contrast, hierarchy, density) and say image QA was skipped.
4. **Final pass** once the review passes — embeds fonts (PowerPoint) and writes the deliverable PDF; the summary reports `"fonts_embedded"`; then delete `.qa-images/`:
   ```bash
   python <skill_dir>/scripts/render_pptx.py /abs/path/project/deck.pptx --embed-fonts --pdf-to /abs/path/project/deck.pdf
   ```

## Step 5 — deliver
1. A self-contained project directory — never a manifest without its files:
   ```text
   deck/
     deck.pptd   pages/*.page   media/*      # PPTD project
     deck.pptx   deck.pdf                    # generated by default
     build.py                                # when built with pptd_kit
     plan/                                   # new decks: facts.md + storyboard.yaml (delete plan/wireframe/)
   ```
2. Always generate the `.pptx` after validation, even when the user only asked to create or edit; skip it only on an explicit PPTD-only request or a real blocker (report it and still deliver the PPTD project).
3. Final reply: absolute clickable links to the project directory, the `.pptd`, `pages/` and `media/`, the `.pptx` and PDF, and `plan/storyboard.yaml` + `plan/facts.md` when made; mention `brief.assumptions`, 〔待填〕 placeholders and estimates that need confirming; end with one optional next step (edit `build.py` or the `.page` files and re-run lint → convert → render, or `npx open-kimi-ppt-skill serve` to view and edit).
4. **Conversion** — `pptd2pptx.py` maps text and rich text, all preset shapes and custom paths, gradients and alpha, shadows, lines, images (local or http; cover / contain / crop), bar / pie / doughnut charts, tables with tableStyles, backgrounds and speaker notes to native editable objects; font families map to installed fonts via `FONT_MAP` (Liter → Segoe UI…), and East Asian faces follow the deck's script — `--lang auto` (default) detects Traditional / Simplified Chinese, Japanese or Korean and uses Microsoft JhengHei / Microsoft YaHei / Yu Gothic / Malgun Gothic (`--lang zh-TW|zh-CN|ja|ko` forces one); extend `FONT_MAP` / `EA_FONTS` for other families. A project directory works when it holds exactly one `.pptd`; `--force` overwrites; `--transition none` drops the default fade.
   ```bash
   python <skill_dir>/scripts/pptd2pptx.py /abs/path/project/deck.pptd --output /abs/path/project/deck.pptx --force
   ```
5. **Boundaries** — say so when relevant: element animations, groups, SmartArt and audio / video are not converted (`skip unsupported element …`); `pptd2pptx.py` does not embed fonts (the final render pass does, through PowerPoint — with LibreOffice only, the PPTX relies on installed fonts); the converter covers the kit's PPTD subset and common hand-written pages, so trust the render, not the assumption. Extend `pptd2pptx.py` generally (never deck-specifically) or tell the user.
6. **Verify** the output exists and opened in the renderer; each slide has exactly one root-level fade transition in CT_Slide order (`cSld`, optional `clrMapOvr`, `transition`, optional `timing` / `extLst`) — the converter writes it so.
7. **Legacy** `export_pptx.py` (Kimi's browser writer) fails with `no available pptx export plan`; use it only if the user reports the service works again, and never obtain, patch, recompile or bypass Kimi's WASM or signing.
8. **Browser editor** — when the user wants to open or edit the project by hand: `npx open-kimi-ppt-skill serve` (Node 18+), then open `http://127.0.0.1:55173/` and authorise the whole project folder (Chromium for write access; folder upload is read-only). Its PPTX download hits the same server failure; image / PDF export work.
9. **Speaker notes** (`notes` on a page): when the user asks, and for live talks (`brief.mode: live` / `hybrid`, a timed class or briefing) — `notes:` per page in the storyboard, one short paragraph with the page's point and its own numbers, set as `page.notes` in `build.py`; the converter puts them in PowerPoint's notes pane. Reading decks get none unless requested.
10. **Element animations** (`page.animations`, `pptd.md` §6): only on request, or for clearly live decks where staged disclosure, process, cause and effect, pacing or impact benefit; 1–3 groups per page, simple effects (fade, fly, zoom); none for reading, self-study or print decks. They are separate from the slide fade and are not carried into the PPTX — tell the user when a deck relies on them.
11. **Parallel tool calls** — write several page files per round and run independent commands together.
