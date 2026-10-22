# iOS Glass Briefing · academic STYLE DESIGN SYSTEM

> 玻璃簡報 — bright-blue's palette and layouts in a calm glass material after iOS 27 (Liquid Glass with
> less transparency and more legibility): a soft blurred-colour wallpaper, top-lit white glass cards,
> app-icon tiles, tinted capsules, a large-title header. For public talks, tech and product
> briefings, modern research sharing.
> Preview: `preview.jpg` · Reference implementation: `sample_build.py` (`Kit(..., theme="ios-glass")`).

## PART A — Baseline
Same as `bright-blue-bento-briefing/design.md` PART A. The briefing templates share the storyboard,
the bento grid (`reference/storyboard.md` §3), card craft (`reference/decoration.md` §6) and polish
(§9); a deck switches between them with the `theme` argument alone. This template changes the
**material** only (`reference/decoration.md` §10) — every layout of bright-blue holds.

## PART B — Signature System

One-line signature: near-opaque white glass cards with a white rim floating on a blurred blue / mint
wallpaper, one blue tinted-glass feature card with a specular highlight, gradient app-icon tiles,
a photo in a glass frame with concentric corners on the cover.

【Material】 (tokens in `pptd_kit.IOS_GLASS`)
- Ground: `wallpaper` blobs blurred on `#F0F4FB` (Kit writes `media/wall.jpg`; the cover and closing
  use the livelier `wall-cover.jpg`). Light behind the large title, colour in the corners.
- Card: gradient white 96% → 86% (`GLASS_G`), 1.2px white rim, radius 6500, shadow
  `blur 26, #1E3A6026, offset 0/8`; no title band, no rule under the title.
- Feature card / hero band: blue tinted glass (`feature2` → `feature` at ~95%), white rim at 70%, a
  blue shadow, a specular highlight over the top 42% (`feature_pattern: highlight`).
- Icons: rounded-square tiles (`icon_style: tile`) in the meaning's gradient with a white glyph.
- Capsules: tinted (`pill: tint`) — the tone at 14% with text deepened to 4.5:1; filled capsules
  deepen until white reads.
- Takeaway: a glass capsule 16px under the body (`takeaway: capsule`).

【Colour】 bright-blue's palette and meanings (blue analysis · orange carbon & cost · green green power
/ benchmarks · teal a second group).

【Typography】 Sans `{latin: Liter, ea: MiSans}`; page title 28 bold (large title), caption 18 blue,
subtitle 18 gray; cover 54.

【Layout Skeleton】
Header `large`: caption (chapter), large title, subtitle; a page control on the right (dots, the
current chapter a stretched blue capsule). Body box, grid and modules as bright-blue.

【Slide Types】
Cover (`glass`) | wallpaper; photo in a glass frame on the right (488, 36, 436×468, inset 10, corners
concentric); gradient kicker capsule; 2-line title; glass meta capsules (`meta` items may be
`(icon, text)`); optional floating widget `widget=(icon, tone, title, line)` overlapping the frame.
Breather | photo panel left; the giant number, stats and bar in a glass card on the right.
Closing (`glass`) | the cover's frame with another photo; 謝謝聆聽 / Q & A; recap as an iOS grouped list
(one glass card, icon tiles, hairline separators); byline.

【Prohibited】
Translucent fills under text (glass stays ≥ 85% white where copy sits); heavy colour blocks behind
content (a block under the cards fights the glass — learned from a rejected iteration); more than
one tinted feature surface per page; outline pills next to tinted ones; wallpapers blurred on
transparent black (gray fringe, see `pptd_kit.wallpaper`).
