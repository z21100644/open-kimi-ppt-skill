# Changelog

[简体中文](CHANGELOG.md) | [English](CHANGELOG_EN.md)

This project follows [Semantic Versioning](https://semver.org/). From 1.0.0 it is the offline, planning-first edition; upstream releases are kept under "Upstream history" at the end.

## [1.0.3] - 2026-10-11

### Added

- `pptd_kit.py` API index: `python pptd_kit.py [filter]` prints every public helper's signature with one line (plus THEMES / LAYOUTS / SEMANTIC_ICONS), the filter searching whole docs; about 13 KB instead of reading the 1,800-line file; the 24 helpers that had no doc (`Page.text`, `shape`, `solid`, `chart`, `save`, `Kit.area`…) get one line each
- `pptd2pptx.py --lang auto|zh-TW|zh-CN|ja|ko`: East Asian fonts follow the deck's text (Traditional Chinese Microsoft JhengHei / PMingLiU, Simplified Chinese Microsoft YaHei / SimSun, Japanese Yu Gothic / Yu Mincho, Korean Malgun Gothic / Batang), so Simplified Chinese, Japanese and Korean decks no longer fall back from a Traditional Chinese face; only kana letters count, so 「・」 and 「ー」 in Chinese copy do not read as Japanese — checked on 39 Traditional Chinese decks and 3 upstream Simplified Chinese examples, all detected correctly

### Changed

- SKILL.md: look up helpers in the API index while building; the conversion step explains the script-aware East Asian fonts

## [1.0.2] - 2026-10-11

### Changed

- `storyboard.py check`: `{placeholders}` that `build.py` fills from data are measured as short numbers inside titles, takeaways and subtitles, and a field that is one placeholder only (a sentence chosen from the data) is not measured, so titles are no longer reported as too long; pages with speaker `notes` are not warned for missing supporting points; a message repeated in 3 or more places prints as one line (`×19 no supporting points — journey, …`) while counts stay per page; an invalid `brief.mode` lists the three modes as `design-workflow.md` defines them (live = the author presents, reading = no presenter, hybrid = someone else presents) — on a finished 26-page deck, 29 lines of output became the 4 real issues
- README (zh, en): this edition is not on npm and `npx` installs upstream — install from the repository with `node bin/open-kimi-ppt-skill.js install` and start the editor with `serve`; claims that no longer hold ("fonts embedded automatically", "export PPTX from the editor any time") corrected; the Windows persistent-browser section marked as Kimi online export only; features list adds the planning workflow, kit and templates, speaker notes
- `design-workflow.md`: QA reads the paged overview sheets; a stale SKILL.md item number fixed; `storyboard.md` explains how placeholders are measured and the grouped output

## [1.0.1] - 2026-10-11

### Added

- `render_pptx.py`: decks over 8 slides also get `overview-<k>.jpg` sheets of 6 slides (`--per-sheet`, 0 to disable), so long decks stay legible; slide labels move to a strip above each thumbnail instead of covering the slide's page number and footer
- `Page.takeaway(..., reveal="第 1 題答案：B")`: a green check capsule at the band's right end, so quiz answers and other reveals always appear in the same place; storyboard pages take `reveal:`
- Wireframe: intro and appendix pages are labelled 「開場」/「附錄」 instead of showing chapter 1's progress

### Changed

- SKILL.md rewritten tighter (28.7 KB → 18.5 KB, same rules): a per-task table of which references to read, so kit builds no longer read all 88 KB of `pptd.md` (§1–§5 only for hand-written or converted `.page` files); fixes the stale "browser-side PPTX writer" definition, the misplaced "other formats" paragraph and the broken template sentence; the 17 visual QA items grouped as basics / design / material / main vs supporting / charts, in English; the final `--embed-fonts --pdf-to` pass sits in validation and delivery

### Fixed

- `lint_pptd.py` `container`: the container is the field holding the text's centre, so a small label straddling two adjacent fields (a numbered dot on a quadrant line) no longer runs "past" one
- `lint_pptd.py` `collision`: overlaps ignore line leading, so two ticks meeting at a chart's origin ("0.0" and "0.4") no longer collide; real overlaps are still reported
- `lint_pptd.py` `container`: overflow is measured on the estimated glyphs (no leading), not the text box — a label wider than its bar or cell with the number centred inside is fine; regression-checked on 39 existing decks: 10 false positives gone, 0 new ones, 1 real overflow newly caught

## [1.0.0] - 2026-10-11

First formal release of the offline, planning-first edition (forked from upstream binaryify/open-kimi-ppt-skill 1.2.0). It collects 1.0.0-rc.1 (offline PPTX conversion and render QA), 1.0.0-rc.2 (planning workflow, bento grid, icon library) and the decoration, card craft, templates, material and art direction work since, plus speaker notes, font embedding and the main-vs-supporting rules added for this release.

### Added

- Decoration pass `reference/decoration.md`: one visual anchor per content page (chart, photo, icon group, big number) plus 2–6 supporting marks with a named job; 2–3 recurring deck motifs (`brief.decor`); cards vs. blocks (edge bands, full-width strips, badges, tags) so pages can be decorated under the "no cards by default" rule; card-mode recipe; decoration budget per page type and QA
- Card-free decoration in `pptd_kit`: `band` (edge-anchored tint strip), `watermark` (12%-alpha ghost numeral / keyword), `photo` (image + color rule + caption), `motif` (corner dots / quarter rings / leaf), `pictogram` (unit chart, e.g. "1 in 10")
- `lint_pptd.py`: `plain` check (warns when a page has only text and thin rules); text whose color alpha is below 0.5 is treated as decoration and skipped by the contrast check
- Discovery: when no design is given, the same question round may offer a visual style (bento cards / open layout / photo-led); choosing cards counts as the user's explicit request
- `design-workflow.md` adds the decoration stage and a fix for 太素 / 不夠美 / 沒有圖塊; `storyboard.md` adds `brief.decor` and page `decor`; `SKILL.md` visual QA adds item 11
- Nicer `Page.module` defaults: short copy grows to the largest size that fits and every block is centred vertically in its module; `stat` takes up to 3 numbers; new `ring` / `bar` / `pictogram` kinds render from data; charts draw every data column as a series (with a text legend), keep decimals and rank horizontal bars top-down; diagram nodes without icons show step numbers; image modules become photo cards in card frame
- Bento grid: new `mosaic` layout (medium square + two small blocks + a tall strip); `storyboard.md` states the flexible module count (1–6) and the gutter conversion (16pt on 960 ≈ 21px on 1280, meeting ≥ 20px)
- `Page.module` tables size each row to its wrapped text; several short items only grow while they wrap onto no more lines, avoiding line-end opening brackets and line-start punctuation; chart labels share one decimal count (0.41 and 1.00)
- Card craft (`decoration.md` §6), four habits learned by comparing a user's hand-designed deck with kit-default rebuilds: compose every card from 2–3 element kinds split by dashed rules; at most one gradient feature card per page; one deck-wide color legend (`brief.colors`); finishing details (tags, target ticks, photo rules, cover arc). `design-workflow.md` adds a fix for 沒有原稿有設計感 / 卡片很空; `SKILL.md` visual QA adds item 12
- `Page.module` kinds `stack` (2–3 sub-modules in one card, dashed rules, column or row), `rank` (ranking bars colored by group, with legend) and `dumbbell` (before → after per row, rows reaching the goal turn green); `feature: true` draws a module on the gradient feature card (light text, no gradient numbers); `tone` takes blue / orange / green / gray, also on `pictogram`
- New `pptd_kit` components `chip` (tick + name + value), `tag` (soft name pill), `arc` (cover curve); theme keys `feature` / `feature2` / `on_feature`
- `lint_pptd.py`: `sparse` check (card content spans < 70% of the card body height); `storyboard.py check` warns about a large card holding one small element, several feature cards on a page, a chart or table on the feature card, and `tone` used without `brief.colors`
- Runnable templates: `pptd_kit` adds `ink-ivory` (ivory paper, serif titles, hairline cards, gold accents, no gradients) and `sage-mist` (sage-gray canvas, rounded borderless cards, soft shadows) next to `bright-blue`; all three share the storyboard and the build script, so `Kit(..., theme="ink-ivory")` switches the whole deck; each ships `design.md`, `sample_build.py` and `preview.jpg`, and `theme.md` / `theme_EN.md` gain a Runnable templates section
- A template is more than colors: card radius / title band / border / shadow, the rule under card titles, the header (`bar` / `rule`), the takeaway (`bar` / `rule`), gradients or solid marks, icon discs or bare glyphs, the title font and the cover recipe all come from the theme; new `Page.cover` (`photo-fade` / `frame` / `wash`), `Page.header(..., label=)` (intro / summary / appendix pages without chapter progress) and `Page.title_text`
- Polish defaults (`decoration.md` §9): one hero number per page (`hero: true` grows it and shrinks every other stat), one meaning per colour and per icon (`brief.colors` gains `teal`; icons can be named by meaning via `SEMANTIC_ICONS`: carbon, money, power…), a breather page or hero band in long decks, patterns only in card corners and clear of text, a closing page for live decks, subtitles and takeaways distilled to one clause; SKILL.md visual QA adds item 13
- `pptd_kit`: module `kind: hero` (full-width focus band), `Page.breather` (photo + giant-number breather page), `Page.closing` (closing page in the cover's recipe), `Page.coins` (coin stack), `hero_stat` (unit moves into the label; in a short card the label sits beside the number); feature cards carry small rings in the title corner (theme key `feature_pattern`, skipped when the title needs the room)
- `storyboard.py`: page `breather:` and top-level `closing:`; warns about many numbers with no hero, two heroes on a page, 8+ content pages with no breather or hero band, live decks without a closing page, subtitles or takeaways longer than one clause; accepts semantic icon names
- `lint_pptd.py`: `deco` check (a translucent or hollow decorative shape under text or over a card's edge)
- Runnable template `ios-glass-briefing` (`theme="ios-glass"`, glass): bright-blue's layouts in an iOS 27-style material — a blurred-colour wallpaper (Kit writes `media/wall.jpg`), top-lit white glass cards with a white rim, a blue tinted-glass feature card with a highlight, app-icon tiles, tinted capsules, a large-title header with a page control, a glass takeaway capsule; cover and closing put the photo in a glass frame (concentric corners, `Kit.rounded` bakes rounded PNGs), a floating widget and a grouped recap list
- `decoration.md` §10 Material: keep the layout and change only the material when the user prefers an earlier version, calm glass over transparency, concentric corners, every block in one material, self-review before iterating; `design-workflow.md` feedback table adds "not as good as vN / wrong finish" and "self-iterate"; SKILL.md visual QA adds item 14
- `lint_pptd.py` `sparse`: when a card's first-line caption reads as its title, a hero number that starts in the title band and runs into the body is no longer excluded (false positive fixed)
- `pptd_kit`: theme keys `material`, `pill`, `wallpaper`, `wallpaper_cover`; `icon_style: tile`, `header: large`, `takeaway: capsule`, `cover: glass`, `feature_pattern: highlight`, `card_rule: none`; functions `wallpaper` (blobs blurred on a transparent layer of their own hue — no gray fringe), `tint`, `deepen`; `Page.cover(widget=…)`, `meta` items may be `(icon, text)`
- Runnable template `clear-briefing` (`theme="clear"`, 清透): an art direction written as rules — white glass on a soft blurred ground, rounded rectangles only (circles are data), px radii (`radius_px`), pale feature cards with dark copy (`feature_style: tint`), one solid hero band per deck, numbered tiles (`marker: tile`, contrast-guarded), one solid divider (`divider: solid`), same-hue tonal transitions, a safe-area header (`header_top`, `title_px`, `dot_off`) and per-page source footers (`Page.footer(n, source=…)`)
- `pptd_kit`: in the glass material the breather photo and photo cards are rounded with their wash baked in (`Kit.rounded(corners=, shade=)`); `faint()` scales a wallpaper
- `decoration.md` §10.6 "keep the transitions" and §11 "art direction"; `design-workflow.md` feedback row "inconsistent style / looks cheap"; SKILL.md visual QA adds item 15
- Speaker notes: `Page.notes` is written as the page's PPTD `notes` and `pptd2pptx.py` carries it into the PowerPoint notes pane; storyboard pages take `notes:`; live talks (`brief.mode: live` / `hybrid`) get one paragraph of script per page by default
- `render_pptx.py --embed-fonts` (PowerPoint: saves the PPTX back with TrueType fonts embedded) and `--pdf-to` (the deliverable PDF); the JSON summary adds `fonts_embedded`
- `storyboard.py`: `intro:` opening pages (warm-up quiz, route map); `Storyboard.page_numbers()` numbers pages in deck order for cross-references ("answer on P5", "see appendix P26"); `check` warns about an appendix larger than max(3 pages, 15%) and page numbers typed into copy
- `pptd_kit.free_spot()` / `hit()`: collision-free point labels for scatter and quadrant charts (centred above → nudged → right → left → below), never over a dot, a caption or another label
- `decoration.md` §12 main vs supporting: an appendix of about three pages (glossary, data table, methods & sources on one page), one point per side card, pages on one idea folded together, a findings summary page with "finding N" markers, reveals in one place, one vocabulary, the takeaway as the main finding, page numbers from the deck order; §12.1 readable scatter / quadrant charts (ticks, labelled average lines, quadrant names in their corners, coinciding points merged with a count, lines broken behind labels, out-of-range points noted); §12.2 review pass
- `design-workflow.md` feedback table adds too-many-appendix / main-vs-supporting, review-and-iterate, unreadable chart labels and speaker-script rows; SKILL.md visual QA adds items 16 and 17

### Changed

- One design-system tree, `reference/design_system/<category>/<theme-id>/design.md`: the 16 numbered raw sheets duplicating a curated `design.md` are removed (the condensed `design.md` wins) and the other 14 move into their categories; `theme.md` / `theme_EN.md` links updated
- Slimmer docs: `SKILL.md` points to `design-workflow.md`, `storyboard.md` and the script docstrings instead of repeating the workflow, component list and lint checks; `design-workflow.md` points to `decoration.md` for card and decoration rules; the bright-blue design system uses the named layouts of `storyboard.md` and the kit's `module_body` offsets
- Version 1.0.0, the first formal release; 1.3.0-local and 1.4.0-local are recorded as 1.0.0-rc.1 and 1.0.0-rc.2; upstream releases move to "Upstream history" at the end
- SKILL.md: states the version; the font-embedding statement matches the tools (`pptd2pptx.py` does not embed, the final `render_pptx.py --embed-fonts` pass does); delivery adds `--embed-fonts --pdf-to`; speaker notes when the user asks or for live talks

### Fixed

- `pptd2pptx.py`: infer bar direction from the data when `axis.type` is omitted (PPTD §5) — `horizontal: true` charts produced files PowerPoint could not open
- `render_pptx.py`: PowerPoint errors were blank on zh-TW / zh-CN Windows because of a decoding failure; PowerPoint is now closed when opening fails
- `lint_pptd.py`, `storyboard.py`, `pptd2pptx.py`, `icons.py` and `render_pptx.py` always write UTF-8, so `PYTHONUTF8=1` is no longer needed
- `Page.module` numbers in one row share one font size; progress bars in a tall card spread over about 85% of it instead of huddling in the middle
- `Page.module`: growing copy no longer splits a number or Latin word across lines (PowerPoint moves the whole word, so the estimate went wrong); single paragraphs and quotes estimate line breaks at the width of the box actually drawn; rings in a short box sit beside their labels instead of running into the part title above
- `storyboard.py check` accepts preset shape names (`lightningBolt`, `cube`…) as icons, as `pptd_kit` does
- `lint_pptd.py` `container`: a borderless gradient that fades to fully clear (a sheen or wash) is no longer a container, so text on glass cards is not reported as running past it

## [1.0.0-rc.2] - 2026-10-05

Previously recorded as 1.4.0-local.

### Added

- Planning-first workflow: discovery (research first, then one round of ≤ 3 questions with options and defaults) → fact sheet `plan/facts.md` → pyramid-principle outline → storyboard `plan/storyboard.yaml` → grayscale wireframe → design → QA
- `scripts/storyboard.py`: `check` validates the outline (governing claim, part claims, claim titles, takeaways, group sizes, fact references) and the page plan (bento layouts, overlaps, main module on the largest area, draft copy fitting at the minimum font); `wireframe` renders the storyboard as a grayscale PPTD deck for `pptd2pptx.py` / `render_pptx.py`
- `scripts/pptd_kit.py`: 12 × 6 bento planning grid (`grid_area`, `Kit.area`, `Kit.layout`) and named layouts (`single`, `split`, `split-2-1`, `three`, `center-main`, `hero-top`, `quad`, `main-stack`, `mixed`)
- `reference/storyboard.md`: storyboard schema, pyramid outline rules, bento layout table and commands
- `tests/test_storyboard.py` and `tests/fixtures/storyboard/`
- Evidence table (ideas from [CyberPPT](https://github.com/crazyykhllc-bit/CyberPPT), MIT): `facts.md` gains type, exact source location, confidence, caveat/conflict and implication columns; missing-value labels (未提供 / 無法推導 / 需要外部驗證), conflicting sources kept side by side, derived metrics cite their inputs
- Storyline comparison: 2–3 alternatives before the outline (SCR by default for analysis, decision and proposal decks), exactly one `chosen`; pages may carry `role`, `caveat`, `bridge`
- `storyboard.py check`: storyline count/choice, low-confidence facts without a caveat, facts with missing values
- `lint_pptd.py`: `container` (text running past its card/panel), `collision` (overlapping text), `icon` (Font Awesome icons the offline converter drops), `--scale` (sizes must belong to the deck's type scale) and a summary of sizes in use
- Icon library: `assets/icons/tabler-filled/` ([Tabler Icons](https://github.com/tabler/tabler-icons) filled set, MIT, 1,053 icons); `scripts/icons.py` searches by keyword and turns library icons or any custom/edited SVG into editable PPTD custom shapes (path/circle/ellipse/rect/polygon, `<g transform>`, multiple colors, opacity); `pptd_kit` gains `Page.svg` and `Page.icon` accepts library ids; `reference/icons.md` covers when to use icons, free adjustment and limits
- Storyboard modules accept `icon`; the checker verifies it exists and the wireframe draws it
- `scripts/svgpath.py`: SVG path normalizer (relative commands, H/V, S/T, arcs → cubic Béziers, transforms)

### Changed

- SKILL.md and `reference/design-workflow.md`: discovery round and storyboard stage; new decks deliver `plan/`; whether layout modules are drawn as cards is a design-system decision — the scenario guides' "no cards by default" rule is unchanged
- Field-test iteration (fixes found by running full decks end to end):
  - Asymmetric layouts are the default (new `split-7-5`, `split-5-7`, `stack-main`, `three-uneven`, `hero-split`); evenly divided ones (`split`, `three`, `quad`, `hero-top`) need `layout_reason`, matching the scenario guides' ban on even splits
  - `storyboard.py check`: repeated skeletons on consecutive pages, under-filled main modules, orphans and leading punctuation in draft copy, icons inside `data`; `brief.frame` (`region` default / `card`) makes checks, wireframe and build measure the same body box
  - `pptd_kit`: `Page.module` / `Page.modules` render storyboard modules directly (text, quote, list, stat, table, chart, diagram, image); `Page.region` open modules; `takeaway(style="rule")`; theme key `on_accent`, and number dots, segments and pills pick a readable label color; `table` converts px to ratios
  - The wireframe uses the build's renderer and module frame
  - `lint_pptd.py`: `table` (ratios), `cell` (cell overflow), `chart` (non-PPTD series keys, unknown encode columns), `contrast` (text vs. the fill behind it, WCAG 3:1 for large text)
  - `icons.py search`: any query word counts; results rank by number of matches
  - `pptd2pptx.py`: chart series `fill` is optional (it used to crash); chart text defaults to 18; neutralizes the `p:style` effectRef so LibreOffice renders no shadow PowerPoint wouldn't show
  - `bright-blue-bento-briefing` sample: low-contrast label colors fixed
- `reference/design-workflow.md`: deck-language priority (user > source material > conversation), low-density covers and dividers, QA fix order and severity
- SKILL.md: replicated icons use preset/custom shapes (Font Awesome `icon` elements vanish from the offline PPTX)
- `pptd2pptx.py`: custom shapes accept the full PPTD path syntax (lowercase relative commands were previously treated as absolute, and A/S/T raised errors); small viewBoxes are scaled up to keep precision; shapes honor `flip`
- Pre-delivery review fixes:
  - `icons.py`: SVG fill parsing (named colors such as `white` were drawn black, `rgb()` became black, 3-digit `#f00` was not expanded); unreadable fills now warn; a mistyped project SVG path reports a missing file instead of a missing library icon
  - `storyboard.py check`: warns when chart, table, diagram or image modules have no `data` (they used to render as plain text); validates `brief.frame`; no false repeated-skeleton warning across section dividers; the wireframe resolves project SVGs inside diagram steps
  - `pptd_kit`: `table` always normalizes widths/heights to ratios summing to 1; diagram nodes scale with the module height so short areas no longer collide with the text below
  - The example storyboard carries real chart and diagram `data`; `package.json` ships `tests/fixtures/storyboard/` (the docs cite it as the complete example)
- `SKILL.md` line endings back from CRLF to LF (the only CRLF file in the repo; it broke the install test's frontmatter match and could break loaders that parse frontmatter with a simple regex); `.gitattributes` (`* text=auto eol=lf`) and `.editorconfig` (`end_of_line = lf`) keep it that way
- `package.json`: `files` now includes the offline scripts (`lint_pptd.py`, `pptd2pptx.py`, `pptd_kit.py`, `render_pptx.py`, `storyboard.py`, `icons.py`, `svgpath.py`) and `assets/` the default workflow needs

## Upstream history (binaryify/open-kimi-ppt-skill)

Releases before the fork; these version numbers belong to the upstream npm package `open-kimi-ppt-skill`.

### [upstream 1.2.0] - 2026-08-06

#### Added

- CLI supports `-h` / `--help` and `-V` / `--version`

#### Changed

- Renamed the npm package and CLI from `open-kimi-ppt-skills` to `open-kimi-ppt-skill` to match the GitHub repo. Use `npx open-kimi-ppt-skill@latest` going forward; the old package name will no longer receive updates

### [upstream 1.1.3] - 2026-08-06

#### Added

- Interactive `install` checklist for `.agents` / `.codex` / `.claude` / `.cursor` / `.workbuddy` skill directories (space to multi-select)
- `-y/--yes` (non-interactive default) and repeatable `--target`
- `--all` installs only into detected agent directories; missing agents are skipped with a notice instead of being created
- Windows export auto-starts a persistent debug browser (Chrome, falling back to Edge) to work around agent-browser failing to launch Chrome itself; the instance stays resident and is reused across exports, and `AGENT_BROWSER_CDP` can point to a debug browser you started yourself

#### Fixed

- Tolerate files vanishing mid-scan in `find_download` when Chrome renames `.crdownload` entries in Downloads, avoiding `FileNotFoundError` aborting export (Related to #4)

#### Changed

- README now steers agents to `npx open-kimi-ppt-skill@latest install -y` instead of cloning the repo

### [upstream 1.1.2] - 2026-08-06

#### Fixed

- Fix Chinese-locale Windows export hang / GBK decode errors in `export_pptx.py` / `export_images.py` (capture stdout via temp file + UTF-8)
- Work around agent-browser `--download-path` silently canceling Chrome downloads: click download and poll the default Downloads folder
- Stop shipping `__pycache__/*.pyc` in the npm package (list script sources explicitly in `files`)

### [upstream 1.1.1] - 2026-08-06

#### Added

- Align PPTD with official element-level `animations`; Skill notes for animation / `notes` usage bounds
- Align image priority, anti-AI copy rules, clarification asks, replicate guidance, and parallel page writes
- Ship ~30 preset design systems, invoked only when named
- Restore `customFonts` (Google Fonts) and poster size recommendations
- Root theme catalogs: `theme.md` / `theme_EN.md` (with preview images)
- Sample project `example/xiaomi-yu7-ppt-animation` (on-slide entrance animations)

#### Changed

- Sync scenario docs with official animation guidance and `customFonts` references
- README: document element animations, preset themes, and sample prompts

### [upstream 1.0.2] - 2026-08-06

#### Changed

- `install` overwrites an existing skill by default; `--force` is no longer required (still accepted for compatibility)

### [upstream 1.0.1] - 2026-08-06

#### Added

- Skill workflow **step0 prerequisite check**: verify Node.js 18+, npm/npx, and python3 before generation; note that a Chromium-based browser is required for export
- Export scripts check **Node.js 18+** and **npm** at startup, with clear install guidance when missing or too old
- CLI (`open-kimi-ppt-skill`) refuses to start when the Node.js major version is below 18
- Auto-install **PyYAML** via `pip install --user pyyaml` when missing (same pattern as Pillow / websocket-client)

#### Docs

- Added multi-agent / multi-model example screenshots (ChatGPT·Codex + 5.6 Luna, Reasonix + DeepSeek, WorkBuddy, and more)
- Clarified install as “automatic or manual — pick one”, with Windows path notes
- Updated README structure and example images

### [upstream 1.0.0] - 2026-08-05

#### Added

- Initial release of `open-kimi-ppt-skill`
- PPTD create / edit / replicate, delivering both an editable PPTD project and a PPTX by default
- Browser-side PPTX export (embedded fonts, fade transitions) with optional multimodal visual QA before export
- Local in-browser PPTD editor (`npx open-kimi-ppt-skill serve`)
- CLI to install the skill into `~/.agents/skills` (or another agent directory via `--target`)
