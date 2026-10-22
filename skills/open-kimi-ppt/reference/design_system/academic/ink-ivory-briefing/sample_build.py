"""Reference implementation of the briefing templates driven by storyboard modules (4 pages).

The same pages render in every kit template — pass the template name to switch:
  python sample_build.py <out_dir> [ink-ivory | sage-mist | bright-blue]
Then: python ../../../../scripts/lint_pptd.py <out_dir>/sample.pptd
      python ../../../../scripts/pptd2pptx.py <out_dir>/sample.pptd --force
Content: a fictional DEA energy & carbon-efficiency briefing on 20 city bus routes (every name and
number is made up). Every page is
cover recipe / header / p.modules (card frame) / takeaway / footer — no hand-placed elements, so
copy the module lists and replace the data.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))
from pptd_kit import Kit  # noqa: E402

I = "tabler-filled/"
PAGES = [
    (1, "1 路一條線，就用掉車隊約兩成的電", "用電也會產生碳排（Scope 2）；用電越多，排放越多",
     "用電大戶的排碳效率，會直接反映在成本上", {"layout": "split-5-7", "modules": [
         {"role": "main", "kind": "stack", "title": "1 路的用電與綠電（2025）", "icon": I + "leaf", "parts": [
             {"kind": "stat", "data": {"items": [{"value": "261", "unit": " 萬度", "label": "年用電量"},
                                                 {"value": "+18.4%", "label": "比前一年", "tone": "orange"}]}},
             {"kind": "bar", "title": "再生能源占比", "data": {"items": [
                 {"label": "2025 年", "value": 0.25, "target": 0.6, "display": "25%（2030 目標 60%）"}]}}]},
         {"kind": "stack", "title": "車隊每 10 度電", "icon": "lightningBolt", "parts": [
             {"kind": "pictogram", "weight": 1.3, "data": {"n": 5, "k": 1, "icon": I + "bolt", "tone": "orange"}},
             {"kind": "stat", "data": {"value": "20.4%", "label": "給 1 路（2025）", "tone": "orange"}}]}]}),
    (2, "20 條路線，每載 1 萬人次排碳最多差 6 倍", "碳排強度＝排放量 ÷ 載客量（噸 CO₂e／萬人次）",
     "1 路占車隊排放 31%，後面要檢查它對結果的影響", {"layout": "split-5-7", "modules": [
         {"role": "main", "kind": "rank", "title": "碳排強度（噸 CO₂e／萬人次）", "icon": "cloud", "data": {
             "groups": {"柴油路線": "blue", "電動路線": "orange"},
             "rows": [["12 路", 9.6, "柴油路線"], ["6 路", 7.3, "柴油路線"], ["15 路", 5.8, "電動路線"],
                      ["4 路", 4.9, "電動路線"], ["1 路", 2.1, "柴油路線"], ["3 路", 1.6, "電動路線"]]}},
         {"kind": "stack", "title": "研究樣本", "icon": "cube", "parts": [
             {"kind": "stat", "data": {"items": [{"value": "12", "unit": " 條", "label": "柴油路線"},
                                                 {"value": "8", "unit": " 條", "label": "電動路線", "tone": "orange"}]}},
             {"kind": "ring", "data": {"items": [{"value": 0.31, "label": "1 路占排放", "tone": "orange"},
                                                 {"value": 0.38, "label": "占載客"}]}}]}]}),
    (3, "拿掉 1 路重算，另外 4 條路線變成標竿", "初步結果（預試）；效率是相對分數",
     "效率是相對分數，標竿會隨樣本改變", {"layout": "split-2-1", "modules": [
         {"role": "main", "kind": "dumbbell", "title": "排除 1 路前後的 SBM 效率", "icon": I + "chart-dots", "data": {
             "labels": ["原本", "排除 1 路後"], "goal": 1,
             "rows": [["2 路", 0.48, 1.0], ["5 路", 0.52, 1.0], ["7 路", 0.61, 1.0], ["9 路", 0.79, 1.0],
                      ["12 路", 0.42, 0.63], ["18 路", 0.66, 0.81]]}},
         {"kind": "stack", "feature": True, "title": "標竿換人了", "icon": I + "award", "parts": [
             {"kind": "stat", "data": {"value": "+4", "unit": " 條", "label": "排除後升到效率 1"}},
             {"kind": "text", "text": "原本的標竿<br/>1 路、3 路、8 路、20 路"}]}]}),
]


def build(out, theme):
    kit = Kit(out, total=len(PAGES) + 1, footer="公車跑得多，也排得多嗎？｜研究分享（虛構範例）",
              chapters=["為什麼重要", "怎麼比較", "看到什麼"], theme=theme)
    media = Path(__file__).resolve().parent / "cover.jpg"  # generated abstract waves — free to reuse
    (Path(out) / "media").mkdir(parents=True, exist_ok=True)
    (Path(out) / "media" / media.name).write_bytes(media.read_bytes())
    p = kit.page()
    p.cover("公車跑得多，", "也排得多嗎？", "以資料包絡分析（DEA）評估市區公車路線的能源與碳排效率",
            kicker="城市交通研究簡報", meta=["20 條路線", "2025 年度資料", "3 種效率算法"],
            byline="報告人〔待填〕｜單位〔待填〕｜2026.10", photo=media.name)
    p.save("01_cover.page", "cover")
    for n, (chap, title, sub, takeaway, page) in enumerate(PAGES, 2):
        p = kit.page()
        p.header(chap, title, sub)
        p.modules(page, frame="card")
        p.takeaway(takeaway)
        p.footer(n)
        p.save(f"{n:02d}.page")
    kit.write_manifest("sample.pptd", "Briefing template sample")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "sample_out", sys.argv[2] if len(sys.argv) > 2 else "ink-ivory")
