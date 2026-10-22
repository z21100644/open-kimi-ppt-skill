"""Reference implementation of the Bright Blue Bento Briefing style (3 archetype pages).

Run:  python sample_build.py <out_dir>
Then: python ../../../../scripts/lint_pptd.py <out_dir>/sample.pptd
      python ../../../../scripts/pptd2pptx.py <out_dir>/sample.pptd --force
Content: a fictional public-facing research briefing (DEA energy & carbon efficiency of 20 city bus
routes; every name and number is made up). Copy the page functions and replace the data — keep the grid
numbers.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))
from pptd_kit import Kit, b, c, unit  # noqa: E402

kit = Kit(sys.argv[1] if len(sys.argv) > 1 else "sample_out", total=3,
          footer="公車跑得多，也排得多嗎？｜城市交通研究簡報（虛構範例）",
          chapters=["研究背景", "文獻探討", "研究設計", "初步發現", "限制結論"])
L, R, T = kit.L, kit.R, kit.T
th = kit.th
NAVY, GRAY, BLUE, GREEN, ORANGE, WHITE, SKY = th["navy"], th["gray"], th["blue"], th["green"], th["orange"], th["white"], th["sky"]

# ---- archetype A: purpose / research questions (hero card 1/3 + numbered list 2/3) ----
p = kit.page()
p.header(1, "研究目的：將碳排放納入公車路線的營運效率評估", "對應報告第一章｜研究背景、動機與研究問題")
p.card(L, T, 316, 322, "研究架構", "star5", feature=True)
for i, (k, v) in enumerate([("研究對象", "2025 年 20 條市區公車路線"), ("分析方法", "資料包絡分析（DEA）"), ("資料來源", "營運報表、能源帳單、車機紀錄")]):
    y = T + 70 + i * 82
    p.text(L + 20, y, 276, 26, k, 18, "#FFFFFF", wrap=False)
    p.text(L + 20, y + 26, 276, 50, b(v), 18, WHITE, lineHeight=1.2)
    if i < 2:
        p.solid(L + 20, y + 74, 276, 1, "#FFFFFF40")
rq = [("Q1", "技術效率與規模效率", "<p>以車輛、司機、能源為投入、載客量為產出</p><p>衡量技術效率與規模報酬型態</p>", "CCR／BCC"),
      ("Q2", "納入非期望產出", "<p>將車隊的碳排放視為非期望產出</p><p>檢視效率值與排序的變動</p>", "SBM"),
      ("Q3", "群組差異與穩健性", "<p>比較柴油與電動路線的效率差距</p><p>並檢驗結果是否受最大路線影響</p>", "敏感度")]
for i, (n, h, q, tag) in enumerate(rq):
    y = T + i * 110
    p.card(368, y, 556, 100)
    p.numdot(408, y + 50, 44, n)
    p.text(444, y + 12, 340, 32, b(h), 20, NAVY, wrap=False, align=["left", "middle"])
    p.pill(812, y + 14, 96, tag)
    p.text(444, y + 46, 466, 50, q, 18, GRAY, lineHeight=1.25)
p.takeaway("核心：把碳排放算進效率，並檢驗結論在不同碳排口徑與樣本下是否穩健")
p.footer(1)
p.save("01_purpose.page")

# ---- archetype B: background data page (two stacked stat cards + one ring/bar card) ----
p = kit.page()
p.header(1, "碳定價上路：排放成本化，車隊電動化的壓力變大", "對應報告第一章｜政策背景與車隊用電")
p.card(L, T, 436, 154, "碳費制度", "flowChartDocument")
for i, (n, lab) in enumerate([("2023", "<p>氣候變遷</p><p>因應法施行</p>"), ("≥2.5萬噸", "<p>年排放量</p><p>徵收門檻</p>"), ("2026", "<p>首期碳費</p><p>開始徵收</p>")]):
    x = L + 20 + i * 136
    p.gtext(x, T + 66, 132, 40, n, 26, wrap=False)
    p.text(x, T + 104, 128, 46, lab, 18, GRAY, lineHeight=1.15)
p.card(L, T + 168, 436, 154, "費率結構（元／噸 CO₂e）", "pie")
for i, (n, lab, st, col) in enumerate([("300", "一般費率", kit.ORANGE_G, ORANGE), ("100", "優惠 B", kit.BLUE_G, BLUE), ("50", "優惠 A", kit.GREEN_G, GREEN)]):
    x = L + 20 + i * 136
    p.gtext(x, T + 234, 128, 40, n, 30, st, wrap=False, align=["center", "top"])
    p.pill(x + 14, T + 276, 100, lab, col)
p.card(488, T, 436, 322, "示範車隊用電概況（2025）", "lightningBolt")
p.ring(574, T + 132, 112, 0.35, "35%", None, kit.BLUE_G, 13000, 24)
p.text(504, T + 194, 140, 28, b("電動車占比"), 18, NAVY, align=["center", "top"], wrap=False)
p.stat(660, T + 76, 250, "1,280", " 萬度", "年用電量", None, kit.BLUE_G, 28, 26)
p.hdash(660, T + 146, 244)
p.stat(660, T + 156, 250, "+18.4%", "", "年增率（+199 萬度）", None, kit.ORANGE_G, 28, 26)
p.hdash(508, T + 236, 396)
p.text(508, T + 244, 300, 28, b("再生能源占比"), 18, NAVY, wrap=False)
p.text(704, T + 244, 200, 28, "2025 → 2030 目標", 18, GRAY, wrap=False, align=["right", "top"])
p.bar(508, T + 282, 396, 0.25, target=0.60)
p.text(508, T + 298, 120, 24, b(c("25%", GREEN)), 18, wrap=False)
p.text(508 + 396 * 0.6 - 40, T + 298, 120, 24, b(c("60%", GREEN)), 18, wrap=False)
p.takeaway("以一般費率估算，年排放 1 萬噸約需繳納 300 萬元，排放效率將直接反映於成本")
p.footer(2)
p.save("02_background.page")

# ---- archetype C: findings (ring row + distribution strip | chart + delta stat) ----
p = kit.page()
p.header(4, "初步發現：納入碳排後效率下降，結果對最大路線敏感", "預試結果｜虛構數據")
p.card(L, T, 436, 322, "平均效率值", "gear9")
for i, (v, ctr, lab, st) in enumerate([(0.81, "0.81", "CCR", kit.BLUE_G), (0.86, "0.86", "BCC", kit.BLUE_G),
                                       (0.64, "0.64", "SBM 實測", kit.ORANGE_G), (0.61, "0.61", "SBM 推估", kit.ORANGE_G)]):
    cx = L + 62 + i * 104
    p.ring(cx, T + 112, 80, v, ctr, None, st, 14000, 20)
    p.text(cx - 52, T + 156, 104, 28, b(lab), 18, NAVY, align=["center", "top"], wrap=False)
p.hdash(L + 20, T + 196, 396)
p.text(L + 20, T + 204, 396, 28, b("SBM 效率值分布（20 條）"), 18, NAVY, wrap=False)
p.segments(L + 20, T + 240, 396, [(4, "=1", BLUE), (5, "0.6+", "#4D9BF0"), (7, "0.4+", "#8CBEF5"), (4, "<0.4", ORANGE)])
p.card(488, T, 436, 322, "敏感度分析：排除 1 路", "upArrow")
p.text(508, T + 62, 396, 26, f"{c('■', '#B9C7D8')} 原樣本　{c('■', BLUE)} 排除 1 路", 18, GRAY, wrap=False)
p.chart([498, T + 88, 416, 170], ["路線", "原本", "排除"],
        [["2 路", 0.48, 1.0], ["5 路", 0.52, 1.0], ["7 路", 0.61, 1.0], ["9 路", 0.79, 1.0], ["12 路", 0.42, 0.63], ["15 路", 0.58, 0.70], ["18 路", 0.66, 0.81]],
        [{"type": "bar", "encode": {"x": "路線", "y": "原本"}, "fill": "#B9C7D8"}, {"type": "bar", "encode": {"x": "路線", "y": "排除"}, "fill": BLUE}],
        xAxis={"label": {"fontSize": 18, "color": th["text"]}, "gridLine": False, "axisLine": {"color": th["line"]}},
        yAxis={"show": False, "min": 0, "max": 1.1, "gridLine": False}, barGap=0.08, barWidth=0.72)
p.hdash(508, T + 264, 396)
p.gtext(508, T + 270, 120, 44, f"+4{unit(' 條')}", 30, kit.GREEN_G, wrap=False)
p.text(620, T + 270, 290, 44, "<p>轉為有效：2 路、5 路</p><p>　　　　　7 路、9 路</p>", 18, th["text"], align=["left", "middle"], lineHeight=1.15)
p.takeaway("效率前緣：1 路、3 路、8 路、20 路；20 路班次極少，不宜解讀為最佳")
p.footer(3)
p.save("03_findings.page")

kit.write_manifest("sample.pptd", "Bright Blue Bento Briefing — sample")
print(f"wrote {len(kit.saved)} pages to {kit.out}")
