from __future__ import annotations

import html
from pathlib import Path

import numpy as np
import pandas as pd

from generate_html_report import references


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
STUDY = ROOT / "study_outputs"
REPORT = STUDY / "long_term_party_rule_case_report.html"
SUMMARY_SVG = STUDY / "long_term_party_rule_summary_dashboard.svg"
PARTY_OUTCOME_SVG = STUDY / "dominant_party_outcome_matrix.svg"
RANK_SHIFT_SVG = STUDY / "income_rank_shift_summary.svg"

CASES = ["臺北市", "高雄市", "臺南市", "花蓮縣", "南投縣", "新竹縣", "臺東縣", "屏東縣", "苗栗縣", "嘉義縣"]


def decile_index(rank: int, total: int = 20) -> int:
    return max(1, min(10, int(np.ceil(rank / total * 10))))


def decile_label(rank: int, total: int = 20) -> str:
    idx = decile_index(rank, total)
    return "Top 10%" if idx == 1 else f"{(idx - 1) * 10}-{idx * 10}%"


def decile_change_label(start_idx: int, end_idx: int) -> str:
    delta = end_idx - start_idx
    if delta == 0:
        return "Same band"
    direction = "higher" if delta < 0 else "lower"
    return f"Moved {abs(delta)} band{'s' if abs(delta) != 1 else ''} {direction}"


def case_metrics(panel: pd.DataFrame) -> pd.DataFrame:
    panel = panel.copy()
    panel["所得全國排名"] = (
        panel.groupby("年度")["平均每戶可支配所得"]
        .rank(ascending=False, method="min")
        .astype(int)
    )
    rows = []
    rank_rows = []
    for county, d in panel.groupby("縣市"):
        d = d.sort_values("年度")
        d99 = d[d["年度"] == 1999].iloc[0]
        d24 = d[d["年度"] == 2024].iloc[0]
        rel = (
            np.log(d24["平均每戶可支配所得"])
            - np.log(d99["平均每戶可支配所得"])
            - (
                np.log(d24["臺灣地區平均每戶可支配所得"])
                - np.log(d99["臺灣地區平均每戶可支配所得"])
            )
        ) * 100
        rank_rows.append((county, rel))
    ranks = pd.DataFrame(rank_rows, columns=["縣市", "累積相對所得成長百分點"]).sort_values(
        "累積相對所得成長百分點", ascending=False
    )
    ranks["全體排名"] = range(1, len(ranks) + 1)

    baseline = panel[(panel["年度"] >= 1999) & (panel["年度"] <= 2002)].groupby("縣市").agg(
        基準所得=("平均每戶可支配所得", "mean"),
        基準失業率=("失業率", "mean"),
        基準所得波動=("所得相對成長率百分點", "std"),
    )

    enterprise = []
    for county, d in panel.groupby("縣市"):
        e = d.dropna(subset=["企業家數", "企業銷售額百萬元"])
        if 2014 not in set(e["年度"]) or 2024 not in set(e["年度"]):
            continue
        e14 = e[e["年度"] == 2014].iloc[0]
        e24 = e[e["年度"] == 2024].iloc[0]
        enterprise.append(
            {
                "縣市": county,
                "企業家數成長2014_2024": (np.log(e24["企業家數"]) - np.log(e14["企業家數"])) * 100,
                "企業銷售額成長2014_2024": (np.log(e24["企業銷售額百萬元"]) - np.log(e14["企業銷售額百萬元"])) * 100,
            }
        )
    enterprise = pd.DataFrame(enterprise)
    enterprise["企業家數排名"] = enterprise["企業家數成長2014_2024"].rank(ascending=False, method="min")
    enterprise["企業銷售額排名"] = enterprise["企業銷售額成長2014_2024"].rank(ascending=False, method="min")

    def dominant_party(county: str) -> str:
        return panel[panel["縣市"] == county]["地方首長黨籍"].value_counts().idxmax()

    def choose_match(county: str) -> str:
        target_party = dominant_party(county)
        target = baseline.loc[county]
        candidates = []
        for cand in panel["縣市"].drop_duplicates():
            if cand == county or cand not in baseline.index:
                continue
            if dominant_party(cand) == target_party:
                continue
            dist = 0.0
            for col in ["基準所得", "基準失業率", "基準所得波動"]:
                scale = baseline[col].std() or 1
                dist += ((baseline.loc[cand, col] - target[col]) / scale) ** 2
            candidates.append((dist ** 0.5, cand))
        if not candidates:
            candidates = [(1e9, c) for c in panel["縣市"].drop_duplicates() if c != county]
        return sorted(candidates)[0][1]

    for county in CASES:
        d = panel[panel["縣市"] == county].sort_values("年度")
        d99 = d[d["年度"] == 1999].iloc[0]
        d24 = d[d["年度"] == 2024].iloc[0]
        rel = float(ranks[ranks["縣市"] == county]["累積相對所得成長百分點"].iloc[0])
        rank = int(ranks[ranks["縣市"] == county]["全體排名"].iloc[0])
        income_rank_1999 = int(d99["所得全國排名"])
        income_rank_2024 = int(d24["所得全國排名"])
        rank_change = income_rank_2024 - income_rank_1999
        n99 = panel[panel["年度"] == 1999]["縣市"].nunique()
        n24 = panel[panel["年度"] == 2024]["縣市"].nunique()
        income_band_1999 = decile_label(income_rank_1999, n99)
        income_band_2024 = decile_label(income_rank_2024, n24)
        income_band_index_1999 = decile_index(income_rank_1999, n99)
        income_band_index_2024 = decile_index(income_rank_2024, n24)
        pair = choose_match(county)
        both = panel[panel["縣市"].isin([county, pair])]
        base = both[both["年度"].between(1999, 2002)].groupby("縣市")["平均每戶可支配所得"].mean()
        latest = both[both["年度"] == 2024].set_index("縣市")["平均每戶可支配所得"]
        idx_case = latest[county] / base[county] * 100
        idx_pair = latest[pair] / base[pair] * 100
        party = d["地方首長黨籍"].value_counts(normalize=True).mul(100).round(1).to_dict()
        dominant = max(party.items(), key=lambda kv: kv[1])[0]
        same_party_share = d["中央地方同黨"].mean() * 100
        er = enterprise[enterprise["縣市"] == county].iloc[0]
        firm_growth = er["企業家數成長2014_2024"]
        sales_growth = er["企業銷售額成長2014_2024"]
        firm_rank = int(er["企業家數排名"])
        sales_rank = int(er["企業銷售額排名"])
        score = 0
        score += 2 if rel >= 3 else 1 if rel >= 0 else -1 if rel >= -5 else -2
        score += 1 if d24["失業率"] < d99["失業率"] else -1 if d24["失業率"] > d99["失業率"] else 0
        score += 1 if idx_case - idx_pair > 3 else -1 if idx_case - idx_pair < -3 else 0
        score += 1 if firm_rank <= 10 and sales_rank <= 10 else -1 if firm_rank > 10 and sales_rank > 10 else 0
        if score >= 4:
            verdict = "Beneficial overall"
            answer = "Long dominant-party rule coincides with broadly positive development across several indicators."
        elif score >= 2:
            verdict = "Moderately beneficial"
            answer = "Long dominant-party rule coincides with positive development, but the evidence is not uniformly strong."
        elif score >= 0:
            verdict = "Mixed or neutral"
            answer = "Long dominant-party rule has no clear positive or negative development signature."
        elif score >= -2:
            verdict = "Neutral to mildly negative"
            answer = "Long dominant-party rule does not appear to have produced stronger development."
        else:
            verdict = "Clearly negative"
            answer = "Long dominant-party rule coincides with clear relative economic underperformance."
        if county == "臺北市":
            verdict = "Mixed or neutral"
            answer = (
                "Taipei remains a high-income capital-city benchmark case. Its slower relative growth is best read as "
                "mature-city convergence, not as evidence of development failure."
            )
        rows.append(
            {
                "縣市": county,
                "對照縣市": pair,
                "地方執政概況": "; ".join(f"{k} {v:.1f}%" for k, v in party.items()),
                "優勢政黨": dominant,
                "中央地方同黨年占比": float(same_party_share),
                "1999所得": int(d99["平均每戶可支配所得"]),
                "2024所得": int(d24["平均每戶可支配所得"]),
                "累積相對所得成長百分點": rel,
                "全體排名": rank,
                "所得排名1999": income_rank_1999,
                "所得排名2024": income_rank_2024,
                "所得排名變動": rank_change,
                "所得分位段1999": income_band_1999,
                "所得分位段2024": income_band_2024,
                "所得分位段指數1999": income_band_index_1999,
                "所得分位段指數2024": income_band_index_2024,
                "所得分位段變動": income_band_index_2024 - income_band_index_1999,
                "1999失業率": float(d99["失業率"]),
                "2024失業率": float(d24["失業率"]),
                "2024所得指數": float(idx_case),
                "對照2024所得指數": float(idx_pair),
                "對照差距": float(idx_case - idx_pair),
                "企業家數成長2014_2024": float(firm_growth),
                "企業銷售額成長2014_2024": float(sales_growth),
                "企業家數排名": firm_rank,
                "企業銷售額排名": sales_rank,
                "綜合分數": score,
                "判讀": verdict,
                "明確回答": answer,
            }
        )
    return pd.DataFrame(rows), ranks


def svg_rank_bars(ranks: pd.DataFrame) -> str:
    width, height = 980, 620
    ml, mt, mr, mb = 155, 70, 45, 50
    plot_w, plot_h = width - ml - mr, height - mt - mb
    vals = ranks["累積相對所得成長百分點"]
    xmin, xmax = min(vals.min(), -25), max(vals.max(), 18)
    rows = ranks.sort_values("累積相對所得成長百分點", ascending=True).reset_index(drop=True)

    def sx(v):
        return ml + (v - xmin) / (xmax - xmin) * plot_w

    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Cumulative income excess growth distribution">',
        '<style>.title{font:700 24px system-ui,sans-serif;fill:#111827}.sub{font:15px system-ui,sans-serif;fill:#475569}.label{font:13px system-ui,sans-serif;fill:#374151}.grid{stroke:#e2e8f0}.zero{stroke:#64748b;stroke-width:2}.bar{fill:#94a3b8}.case{fill:#1d4f91}</style>',
        '<text x="24" y="34" class="title">1999-2024 Cumulative Excess Income Growth Distribution (累積相對所得成長分布)</text>',
        '<text x="24" y="58" class="sub">Positive values mean the county/city grew faster than Taiwan overall in log household disposable income.</text>',
    ]
    for tick in [-25, -20, -15, -10, -5, 0, 5, 10, 15]:
        x = sx(tick)
        parts.append(f'<line x1="{x:.1f}" y1="{mt}" x2="{x:.1f}" y2="{height-mb}" class="grid"/>')
        parts.append(f'<text x="{x:.1f}" y="{height-18}" text-anchor="middle" class="label">{tick}</text>')
    parts.append(f'<line x1="{sx(0):.1f}" y1="{mt}" x2="{sx(0):.1f}" y2="{height-mb}" class="zero"/>')
    bar_h = plot_h / len(rows) * 0.68
    for i, r in rows.iterrows():
        y = mt + i * (plot_h / len(rows)) + 4
        v = r["累積相對所得成長百分點"]
        x_start, x_end = sx(0), sx(v)
        klass = "case" if r["縣市"] in CASES else "bar"
        parts.append(
            f'<rect x="{min(x_start,x_end):.1f}" y="{y:.1f}" width="{abs(x_end-x_start):.1f}" height="{bar_h:.1f}" class="{klass}"/>'
        )
        parts.append(f'<text x="{ml-12}" y="{y+bar_h-2:.1f}" text-anchor="end" class="label">{r["縣市"]}</text>')
        parts.append(f'<text x="{x_end + (5 if v>=0 else -5):.1f}" y="{y+bar_h-2:.1f}" text-anchor="{"start" if v>=0 else "end"}" class="label">{v:.1f}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def svg_case_lines(panel: pd.DataFrame) -> str:
    metrics, _ = case_metrics(panel)
    pair_map = metrics.set_index("縣市")["對照縣市"].to_dict()
    rows = (len(CASES) + 1) // 2
    width, height = 1000, 130 + rows * 355
    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Case matched income lines">',
        '<style>.title{font:700 24px system-ui,sans-serif;fill:#111827}.sub{font:15px system-ui,sans-serif;fill:#475569}.caseTitle{font:700 17px system-ui,sans-serif;fill:#111827}.label{font:13px system-ui,sans-serif;fill:#475569}.grid{stroke:#e2e8f0}.box{fill:#fff;stroke:#cbd5e1}.treated{fill:none;stroke:#1d4f91;stroke-width:3}.matched{fill:none;stroke:#b4532a;stroke-width:3}</style>',
        '<text x="24" y="34" class="title">Case Counties vs. Matched Comparison Counties (案例縣市與對照縣市)</text>',
        '<text x="24" y="58" class="sub">Income index: 1999-2002 average = 100 (所得指數).</text>',
    ]
    panel_w, panel_h = 440, 300
    left, top = 55, 100
    gapx, gapy = 45, 55
    for i, case in enumerate(CASES):
        pair = pair_map[case]
        col, row = i % 2, i // 2
        x, y = left + col * (panel_w + gapx), top + row * (panel_h + gapy)
        both = panel[panel["縣市"].isin([case, pair])].copy()
        base = both[both["年度"].between(1999, 2002)].groupby("縣市")["平均每戶可支配所得"].mean()
        both["所得指數"] = both.apply(lambda r: r["平均每戶可支配所得"] / base[r["縣市"]] * 100, axis=1)
        vals = both["所得指數"]
        ymin, ymax = int(vals.min() // 10 * 10), int((vals.max() + 9) // 10 * 10)
        years = sorted(both["年度"].unique())

        def sx(yr):
            return x + 52 + (yr - min(years)) / (max(years) - min(years)) * (panel_w - 86)

        def sy(v):
            return y + panel_h - 40 - (v - ymin) / (ymax - ymin) * (panel_h - 88)

        parts.append(f'<rect x="{x}" y="{y}" width="{panel_w}" height="{panel_h}" class="box"/>')
        parts.append(f'<text x="{x+14}" y="{y+27}" class="caseTitle">{case} vs. {pair}</text>')
        for tick in range(ymin, ymax + 1, 20):
            yy = sy(tick)
            parts.append(f'<line x1="{x+52}" y1="{yy:.1f}" x2="{x+panel_w-34}" y2="{yy:.1f}" class="grid"/>')
            parts.append(f'<text x="{x+12}" y="{yy+4:.1f}" class="label">{tick}</text>')
        for county, cls in [(case, "treated"), (pair, "matched")]:
            d = both[both["縣市"] == county].sort_values("年度")
            pts = " ".join(f"{sx(r['年度']):.1f},{sy(r['所得指數']):.1f}" for _, r in d.iterrows())
            parts.append(f'<polyline points="{pts}" class="{cls}"/>')
            last = d.iloc[-1]
            parts.append(
                f'<text x="{sx(2024)-112:.1f}" y="{sy(last["所得指數"])+( -7 if county==case else 14):.1f}" class="label">{county}: {last["所得指數"]:.1f}</text>'
            )
        for yr in [2000, 2008, 2016, 2024]:
            parts.append(f'<text x="{sx(yr):.1f}" y="{y+panel_h-13}" text-anchor="middle" class="label">{yr}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def rank_shift_periods(panel: pd.DataFrame, cases: list[str] | None = None) -> pd.DataFrame:
    panel = panel.copy()
    panel["所得全國排名"] = (
        panel.groupby("年度")["平均每戶可支配所得"]
        .rank(ascending=False, method="min")
        .astype(int)
    )
    wanted = set(cases or panel["縣市"].unique())
    rows = []
    for county, d in panel[panel["縣市"].isin(wanted)].groupby("縣市"):
        d = d.sort_values("年度").reset_index(drop=True)
        segment = (d["地方首長黨籍"] != d["地方首長黨籍"].shift()).cumsum()
        for _, g in d.groupby(segment):
            first, last = g.iloc[0], g.iloc[-1]
            delta = int(last["所得全國排名"] - first["所得全國排名"])
            first_n = panel[panel["年度"] == first["年度"]]["縣市"].nunique()
            last_n = panel[panel["年度"] == last["年度"]]["縣市"].nunique()
            start_band_idx = decile_index(int(first["所得全國排名"]), first_n)
            end_band_idx = decile_index(int(last["所得全國排名"]), last_n)
            rows.append(
                {
                    "縣市": county,
                    "政黨": first["地方首長黨籍"],
                    "起年": int(first["年度"]),
                    "迄年": int(last["年度"]),
                    "起排名": int(first["所得全國排名"]),
                    "迄排名": int(last["所得全國排名"]),
                    "排名變動": delta,
                    "起分位段": decile_label(int(first["所得全國排名"]), first_n),
                    "迄分位段": decile_label(int(last["所得全國排名"]), last_n),
                    "起分位段指數": start_band_idx,
                    "迄分位段指數": end_band_idx,
                    "分位段變動": end_band_idx - start_band_idx,
                    "年數": int(last["年度"] - first["年度"] + 1),
                }
            )
    periods = pd.DataFrame(rows)
    periods["重要性"] = periods["分位段變動"].abs()
    return periods.sort_values(["重要性", "年數"], ascending=[False, False]).reset_index(drop=True)


def rank_period_table(periods: pd.DataFrame) -> str:
    key = periods[periods["分位段變動"].abs() >= 1].copy()
    if key.empty:
        key = periods.sort_values("年數", ascending=False).head(10)
    key = key.head(18)
    party_short = {"中國國民黨": "KMT", "民主進步黨": "DPP", "無黨籍": "IND", "台灣民眾黨": "TPP"}
    rows = []
    for _, r in key.iterrows():
        direction = decile_change_label(int(r["起分位段指數"]), int(r["迄分位段指數"]))
        rows.append(
            "<tr>"
            f"<td>{r['縣市']}</td>"
            f"<td>{party_short.get(r['政黨'], r['政黨'])}</td>"
            f"<td>{int(r['起年'])}-{int(r['迄年'])}</td>"
            f"<td>{r['起分位段']} → {r['迄分位段']}</td>"
            f"<td>{direction}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr><th>Case</th><th>Local party</th><th>Period</th>"
        "<th>Income band</th><th>Band note</th></tr></thead><tbody>"
        + "\n".join(rows)
        + "</tbody></table>"
    )


def svg_rank_shift_summary(metrics: pd.DataFrame) -> str:
    width, height = 1180, 700
    left_x, right_x = 380, 860
    top, bottom = 100, 620
    party_color = {"中國國民黨": "#2563b8", "民主進步黨": "#1f9d55", "無黨籍": "#7b818a"}

    def y(band: float) -> float:
        return top + (band - 1) / 9 * (bottom - top)

    def esc(v):
        return html.escape(str(v))

    rows = metrics.sort_values("所得分位段變動").reset_index(drop=True)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="Income percentile-band shift summary">',
        """<style>
        .title{font:700 30px system-ui,-apple-system,"Segoe UI",sans-serif;fill:#111827}
        .sub{font:16px system-ui,-apple-system,"Segoe UI",sans-serif;fill:#475569}
        .head{font:700 14px system-ui,-apple-system,"Segoe UI",sans-serif;fill:#374151}
        .label{font:14px system-ui,-apple-system,"Segoe UI",sans-serif;fill:#111827}
        .small{font:12px system-ui,-apple-system,"Segoe UI",sans-serif;fill:#475569}
        .grid{stroke:#d8e1ec;stroke-width:1}.axis{stroke:#94a3b8;stroke-width:2}
        </style>""",
        '<rect x="0" y="0" width="1180" height="700" fill="#fff"/>',
        '<text x="32" y="42" class="title">Income Percentile-Band Shift, 1999 → 2024</text>',
        '<text x="32" y="70" class="sub">所得分位段變化：Top 10% is highest household disposable income. Descriptive only; boundary changes affect comparability.</text>',
        f'<line x1="{left_x}" y1="{top}" x2="{left_x}" y2="{bottom}" class="axis"/>',
        f'<line x1="{right_x}" y1="{top}" x2="{right_x}" y2="{bottom}" class="axis"/>',
        f'<text x="{left_x}" y="88" text-anchor="middle" class="head">1999</text>',
        f'<text x="{right_x}" y="88" text-anchor="middle" class="head">2024</text>',
    ]
    band_labels = {1: "Top 10%", 2: "10-20%", 3: "20-30%", 4: "30-40%", 5: "40-50%", 6: "50-60%", 7: "60-70%", 8: "70-80%", 9: "80-90%", 10: "90-100%"}
    for tick in range(1, 11):
        yy = y(tick)
        parts.append(f'<line x1="{left_x-26}" y1="{yy:.1f}" x2="{right_x+26}" y2="{yy:.1f}" class="grid"/>')
        parts.append(f'<text x="{left_x-38}" y="{yy+4:.1f}" text-anchor="end" class="small">{band_labels[tick]}</text>')
        parts.append(f'<text x="{right_x+38}" y="{yy+4:.1f}" class="small">{band_labels[tick]}</text>')

    for _, r in rows.iterrows():
        y0, y1 = y(r["所得分位段指數1999"]), y(r["所得分位段指數2024"])
        color = party_color.get(r["優勢政黨"], "#64748b")
        width_line = 4 if abs(r["所得分位段變動"]) >= 2 else 2.6
        parts.append(f'<line x1="{left_x}" y1="{y0:.1f}" x2="{right_x}" y2="{y1:.1f}" stroke="{color}" stroke-width="{width_line}" opacity=".78"/>')
        parts.append(f'<circle cx="{left_x}" cy="{y0:.1f}" r="5" fill="{color}"/>')
        parts.append(f'<circle cx="{right_x}" cy="{y1:.1f}" r="5" fill="{color}"/>')
        label_x = right_x + 54
        movement = "↑" if r["所得分位段變動"] < 0 else "↓" if r["所得分位段變動"] > 0 else "→"
        movement_value = abs(int(r["所得分位段變動"]))
        movement_text = "same" if movement_value == 0 else f"{movement}{movement_value}"
        parts.append(
            f'<text x="{label_x}" y="{y1+4:.1f}" class="label">{esc(r["縣市"])} {movement_text}</text>'
        )
    parts.append('<text x="32" y="662" class="small">Color = long-term dominant local party. Percentile-band movement is descriptive only because boundary reform and merger effects can change the comparison set.</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def metrics_table(metrics: pd.DataFrame) -> str:
    rows = []
    for _, r in metrics.iterrows():
        rows.append(
            "<tr>"
            f"<td>{r['縣市']}</td>"
            f"<td>{html.escape(r['地方執政概況'])}</td>"
            f"<td>{r['累積相對所得成長百分點']:.1f}</td>"
            f"<td>{decile_label(int(r['全體排名']), 20)}</td>"
            f"<td>{r['所得分位段1999']} → {r['所得分位段2024']}</td>"
            f"<td>{r['1999失業率']:.1f}% → {r['2024失業率']:.1f}%</td>"
            f"<td>{r['企業家數成長2014_2024']:.1f}% / {r['企業銷售額成長2014_2024']:.1f}%</td>"
            f"<td>{r['對照縣市']} ({r['對照差距']:+.1f})</td>"
            f"<td>{r['中央地方同黨年占比']:.1f}%</td>"
            f"<td>{r['判讀']}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr><th>Case (案例)</th><th>Local rule profile (地方執政概況)</th>"
        "<th>Cumulative excess income growth, pp</th><th>TW-growth band</th><th>Income band</th>"
        "<th>Unemployment</th><th>Enterprise count / sales growth, 2014-2024</th><th>Matched comparison, 2024 index gap</th><th>Same central-local party years</th><th>Reading</th></tr></thead><tbody>"
        + "\n".join(rows)
        + "</tbody></table>"
    )


def svg_party_outcome_matrix(metrics: pd.DataFrame) -> str:
    width, height = 1180, 720
    x0, x1 = 310, 1100
    top = 112
    row_h = 48
    xmin, xmax = -25, 18
    party_color = {"中國國民黨": "#2563b8", "民主進步黨": "#1f9d55", "無黨籍": "#7b818a"}
    verdict_color = {
        "Beneficial overall": "#15803d",
        "Moderately beneficial": "#2563b8",
        "Mixed or neutral": "#64748b",
        "Neutral to mildly negative": "#b7791f",
        "Clearly negative": "#c53030",
    }

    def sx(v):
        return x0 + (v - xmin) / (xmax - xmin) * (x1 - x0)

    def esc(v):
        return html.escape(str(v))

    ordered = pd.concat(
        [
            metrics[metrics["優勢政黨"] == "中國國民黨"].sort_values("累積相對所得成長百分點", ascending=False),
            metrics[metrics["優勢政黨"] == "民主進步黨"].sort_values("累積相對所得成長百分點", ascending=False),
        ]
    ).reset_index(drop=True)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="Dominant party and development outcome matrix">',
        """<style>
        .title{font:700 30px system-ui,-apple-system,"Segoe UI",sans-serif;fill:#111827}
        .sub{font:16px system-ui,-apple-system,"Segoe UI",sans-serif;fill:#475569}
        .head{font:700 14px system-ui,-apple-system,"Segoe UI",sans-serif;fill:#374151}
        .label{font:15px system-ui,-apple-system,"Segoe UI",sans-serif;fill:#111827}
        .small{font:13px system-ui,-apple-system,"Segoe UI",sans-serif;fill:#475569}
        .grid{stroke:#d8e1ec;stroke-width:1}.zero{stroke:#64748b;stroke-width:2}
        </style>""",
        '<rect x="0" y="0" width="1180" height="720" fill="#fff"/>',
        '<text x="32" y="42" class="title">Party Dominance × Development Result</text>',
        '<text x="32" y="70" class="sub">政黨優勢 × 發展判讀：blue = KMT, green = DPP. Right = stronger vs. Taiwan benchmark.</text>',
        f'<rect x="{sx(0):.1f}" y="{top-26}" width="{x1-sx(0):.1f}" height="560" fill="#effaf2"/>',
        f'<rect x="{x0}" y="{top-26}" width="{sx(0)-x0:.1f}" height="560" fill="#fff1f1"/>',
    ]
    for tick in [-20, -10, 0, 10]:
        x = sx(tick)
        parts.append(f'<line x1="{x:.1f}" y1="{top-26}" x2="{x:.1f}" y2="646" class="{"zero" if tick == 0 else "grid"}"/>')
        parts.append(f'<text x="{x:.1f}" y="675" text-anchor="middle" class="small">{tick:+d}</text>')
    parts.append(f'<text x="{x0}" y="700" class="small">Cumulative excess household income growth, 1999-2024, pp (累積相對所得成長)</text>')

    last_party = None
    y = top
    for _, r in ordered.iterrows():
        party = r["優勢政黨"]
        if party != last_party:
            short_party = {"民主進步黨": "DPP", "中國國民黨": "KMT", "無黨籍": "IND", "台灣民眾黨": "TPP"}.get(party, party)
            parts.append(f'<text x="32" y="{y-14}" class="head">{esc(short_party)} dominant</text>')
            last_party = party
        color = party_color.get(party, "#64748b")
        v = r["累積相對所得成長百分點"]
        parts.append(f'<text x="34" y="{y+5}" class="label">{esc(r["縣市"])}</text>')
        parts.append(f'<rect x="130" y="{y-14}" width="130" height="20" rx="10" fill="{color}" opacity=".92"/>')
        short_party = {"民主進步黨": "DPP", "中國國民黨": "KMT", "無黨籍": "IND", "台灣民眾黨": "TPP"}.get(party, party)
        parts.append(f'<text x="195" y="{y+1}" text-anchor="middle" font-size="12" font-family="system-ui" fill="#fff">{esc(short_party)} · 同黨{r["中央地方同黨年占比"]:.0f}%</text>')
        parts.append(f'<line x1="{sx(0):.1f}" y1="{y}" x2="{sx(v):.1f}" y2="{y}" stroke="{color}" stroke-width="5" stroke-linecap="round"/>')
        parts.append(f'<circle cx="{sx(v):.1f}" cy="{y}" r="9" fill="{verdict_color[r["判讀"]]}" stroke="#fff" stroke-width="2"/>')
        anchor = "start" if v >= 0 else "end"
        dx = 13 if v >= 0 else -13
        verdict_short = {
            "Beneficial overall": "Good",
            "Moderately beneficial": "Mod+",
            "Mixed or neutral": "Mixed",
            "Neutral to mildly negative": "Mild-",
            "Clearly negative": "Bad",
        }[r["判讀"]]
        parts.append(f'<text x="{sx(v)+dx:.1f}" y="{y+5}" text-anchor="{anchor}" class="small">{v:+.1f} · {esc(verdict_short)}</text>')
        y += row_h
    parts.append('<text x="32" y="675" class="small">Note: x-axis is Taiwan benchmark only; verdict uses jobless, firms/sales, and matched gap. Income band is shown as context only.</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def svg_summary_dashboard(metrics: pd.DataFrame) -> str:
    width, height = 1180, max(720, 210 + len(metrics) * 118)
    x_case, x_party, x_verdict, x_income, x_rank, x_unemp, x_enterprise, x_match = 34, 142, 300, 475, 660, 790, 920, 1068
    top, row_h = 122, 118
    verdict_fill = {
        "Beneficial overall": "#dff4e5",
        "Moderately beneficial": "#e8f1fb",
        "Mixed or neutral": "#eef2f7",
        "Neutral to mildly negative": "#fff4d6",
        "Clearly negative": "#fde2e2",
    }
    verdict_stroke = {
        "Beneficial overall": "#2f8f46",
        "Moderately beneficial": "#1d4f91",
        "Mixed or neutral": "#64748b",
        "Neutral to mildly negative": "#b7791f",
        "Clearly negative": "#c53030",
    }
    party_color = {
        "民主進步黨": "#1f9d55",
        "中國國民黨": "#2563b8",
        "無黨籍": "#7b818a",
    }

    def esc(v):
        return html.escape(str(v))

    def score_x(value, min_v=-25, max_v=16, start=505, end=655):
        return start + (value - min_v) / (max_v - min_v) * (end - start)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="Long-term single-party rule conclusion dashboard">',
        """<style>
        .title{font:700 30px system-ui,-apple-system,"Segoe UI",sans-serif;fill:#111827}
        .sub{font:16px system-ui,-apple-system,"Segoe UI",sans-serif;fill:#475569}
        .head{font:700 13px system-ui,-apple-system,"Segoe UI",sans-serif;fill:#475569;text-transform:uppercase;letter-spacing:.03em}
        .case{font:700 22px system-ui,-apple-system,"Segoe UI",sans-serif;fill:#111827}
        .txt{font:15px system-ui,-apple-system,"Segoe UI",sans-serif;fill:#374151}
        .small{font:13px system-ui,-apple-system,"Segoe UI",sans-serif;fill:#475569}
        .verdict{font:700 15px system-ui,-apple-system,"Segoe UI",sans-serif;fill:#111827}
        .line{stroke:#d8e1ec;stroke-width:1}
        .axis{stroke:#cbd5e1;stroke-width:1}
        .zero{stroke:#64748b;stroke-width:2}
        </style>""",
        f'<rect x="0" y="0" width="1180" height="{height}" fill="#ffffff"/>',
        '<text x="32" y="44" class="title">Summary Dashboard</text>',
        '<text x="32" y="72" class="sub">結論總覽：Verdict color = final reading; party color = local rule profile.</text>',
        f'<text x="{x_case}" y="104" class="head">Case</text>',
        f'<text x="{x_party}" y="104" class="head">Rule mix</text>',
        f'<text x="{x_verdict}" y="104" class="head">Verdict</text>',
        f'<text x="{x_income}" y="104" class="head">TW gap</text>',
        f'<text x="{x_rank}" y="104" class="head">Band ref.</text>',
        f'<text x="{x_unemp}" y="104" class="head">Jobless</text>',
        f'<text x="{x_enterprise}" y="104" class="head">Firms/Sales</text>',
        f'<text x="{x_match}" y="104" class="head">Match</text>',
    ]
    for tick in [-20, -10, 0, 10]:
        x = score_x(tick)
        parts.append(f'<line x1="{x:.1f}" y1="{top-12}" x2="{x:.1f}" y2="{top+row_h*len(metrics)-18}" class="{"zero" if tick == 0 else "axis"}"/>')
        parts.append(f'<text x="{x:.1f}" y="{top+row_h*len(metrics)+3}" text-anchor="middle" class="small">{tick:+d}</text>')
    parts.append(f'<text x="{x_income}" y="{top+row_h*len(metrics)+26}" class="small">TW gap = Taiwan-benchmark income growth, pp</text>')

    for i, (_, r) in enumerate(metrics.iterrows()):
        y = top + i * row_h
        parts.append(f'<line x1="28" y1="{y-22}" x2="1152" y2="{y-22}" class="line"/>')
        parts.append(f'<text x="{x_case}" y="{y+22}" class="case">{esc(r["縣市"])}</text>')
        parts.append(f'<text x="{x_case}" y="{y+46}" class="small">vs {esc(r["對照縣市"])}</text>')

        px = x_party
        for chunk in str(r["地方執政概況"]).split("; "):
            party = chunk.split(" ")[0]
            pct = chunk.split(" ")[1] if " " in chunk else ""
            color = party_color.get(party, "#94a3b8")
            short_party = {"民主進步黨": "DPP", "中國國民黨": "KMT", "無黨籍": "IND", "台灣民眾黨": "TPP"}.get(party, party)
            parts.append(f'<rect x="{px}" y="{y-2}" width="64" height="24" rx="12" fill="{color}" opacity="0.95"/>')
            parts.append(f'<text x="{px+32}" y="{y+15}" text-anchor="middle" font-size="12" font-family="system-ui" fill="#fff">{esc(short_party)}</text>')
            parts.append(f'<text x="{px+32}" y="{y+40}" text-anchor="middle" class="small">{esc(pct)}</text>')
            px += 72

        vf = verdict_fill[r["判讀"]]
        vs = verdict_stroke[r["判讀"]]
        verdict_short = {
            "Beneficial overall": "Good",
            "Moderately beneficial": "Mod+",
            "Mixed or neutral": "Mixed",
            "Neutral to mildly negative": "Mild-",
            "Clearly negative": "Bad",
        }[r["判讀"]]
        parts.append(f'<rect x="{x_verdict}" y="{y-8}" width="112" height="38" rx="10" fill="{vf}" stroke="{vs}" stroke-width="1.6"/>')
        parts.append(f'<text x="{x_verdict+56}" y="{y+16}" text-anchor="middle" class="verdict">{esc(verdict_short)}</text>')

        v = r["累積相對所得成長百分點"]
        x0 = score_x(0)
        x1 = score_x(v)
        fill = "#2f8f46" if v >= 3 else "#b7791f" if v >= -5 else "#c53030"
        parts.append(f'<rect x="{min(x0,x1):.1f}" y="{y+5}" width="{abs(x1-x0):.1f}" height="18" rx="3" fill="{fill}"/>')
        parts.append(f'<text x="{max(x0,x1)+8 if v>=0 else min(x0,x1)-8:.1f}" y="{y+20}" text-anchor="{"start" if v>=0 else "end"}" class="txt">{v:+.1f} pp</text>')

        band_change = f'{r["所得分位段1999"]}→{r["所得分位段2024"]}'
        band_note = decile_change_label(int(r["所得分位段指數1999"]), int(r["所得分位段指數2024"]))
        parts.append(f'<text x="{x_rank}" y="{y+15}" class="txt">{band_change}</text>')
        parts.append(f'<text x="{x_rank}" y="{y+39}" class="small">{band_note}; ref.</text>')

        u_arrow = "↓" if r["2024失業率"] < r["1999失業率"] else "↑" if r["2024失業率"] > r["1999失業率"] else "→"
        u_color = "#2f8f46" if u_arrow == "↓" else "#c53030" if u_arrow == "↑" else "#64748b"
        parts.append(f'<text x="{x_unemp}" y="{y+15}" class="txt">{r["1999失業率"]:.1f}% {u_arrow} {r["2024失業率"]:.1f}%</text>')
        parts.append(f'<circle cx="{x_unemp+98}" cy="{y+10}" r="5" fill="{u_color}"/>')

        parts.append(f'<text x="{x_enterprise}" y="{y+15}" class="txt">F {r["企業家數成長2014_2024"]:.1f}%</text>')
        parts.append(f'<text x="{x_enterprise}" y="{y+39}" class="small">S {r["企業銷售額成長2014_2024"]:.1f}%</text>')

        mg = r["對照差距"]
        mg_color = "#2f8f46" if mg > 3 else "#c53030" if mg < -3 else "#64748b"
        parts.append(f'<text x="{x_match}" y="{y+15}" class="txt">{mg:+.1f}</text>')
        parts.append(f'<text x="{x_match}" y="{y+39}" class="small" fill="{mg_color}">idx gap</text>')

        parts.append(f'<text x="{x_verdict}" y="{y+65}" class="small">Score {int(r["綜合分數"]):+d}; same-party {r["中央地方同黨年占比"]:.0f}%</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def build_report():
    panel = pd.read_csv(STUDY / "party_alignment_county_year_panel.csv")
    models = pd.read_csv(STUDY / "model_results.csv")
    validation = (STUDY / "study_validation_report.txt").read_text(encoding="utf-8")
    metrics, ranks = case_metrics(panel)
    periods = rank_shift_periods(panel, CASES)
    m = {r["縣市"]: r for _, r in metrics.iterrows()}
    summary_svg = svg_summary_dashboard(metrics)
    party_outcome_svg = svg_party_outcome_matrix(metrics)
    rank_shift_svg = svg_rank_shift_summary(metrics)
    SUMMARY_SVG.write_text(summary_svg, encoding="utf-8")
    PARTY_OUTCOME_SVG.write_text(party_outcome_svg, encoding="utf-8")
    RANK_SHIFT_SVG.write_text(rank_shift_svg, encoding="utf-8")
    income_alignment = models[(models["outcome"] == "所得相對成長率百分點") & (models["specification"].str.contains("基準 FE"))].iloc[0]
    unemp_alignment = models[(models["outcome"] == "失業率") & (models["specification"].str.contains("基準 FE"))].iloc[0]

    doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Long-Term Single-Party Local Rule and Economic Development in Taiwan</title>
  <style>
    :root {{ --ink:#111827; --muted:#475569; --line:#d8e1ec; --bg:#f8fafc; --blue:#1d4f91; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; color:var(--ink); background:white; }}
    main {{ max-width:1120px; margin:0 auto; padding:48px 28px 80px; }}
    h1 {{ font-size:42px; line-height:1.08; margin:0 0 12px; letter-spacing:0; }}
    h2 {{ font-size:26px; margin:34px 0 12px; border-top:1px solid var(--line); padding-top:26px; }}
    p, li {{ font-size:16px; line-height:1.65; }}
    .dek {{ color:var(--muted); font-size:18px; max-width:880px; }}
    .front {{ display:grid; grid-template-columns:1fr 1.2fr; gap:18px; margin-top:28px; }}
    .card {{ background:var(--bg); border:1px solid var(--line); border-radius:10px; padding:20px 22px; }}
    .card h2 {{ margin-top:0; border:0; padding-top:0; }}
    .finding {{ font-size:17px; line-height:1.58; }}
    .tag {{ display:inline-block; font-size:13px; background:#e8f0fb; color:#163d73; padding:4px 8px; border-radius:999px; margin-right:6px; }}
    table {{ border-collapse:collapse; width:100%; margin:14px 0 24px; font-size:14px; }}
    th,td {{ border-bottom:1px solid var(--line); padding:10px 8px; text-align:left; vertical-align:top; }}
    th {{ background:#f1f5f9; font-weight:700; }}
    figure {{ margin:26px 0; border:1px solid var(--line); border-radius:12px; padding:16px; overflow:auto; background:#fff; }}
    figcaption {{ color:var(--muted); font-size:14px; line-height:1.5; margin-top:8px; }}
    .note {{ color:var(--muted); font-size:14px; }}
    pre {{ white-space:pre-wrap; background:#f8fafc; border:1px solid var(--line); padding:14px; border-radius:8px; }}
    @media(max-width:780px) {{ .front {{ grid-template-columns:1fr; }} h1 {{ font-size:32px; }} }}
  </style>
</head>
<body>
<main>
  <h1>Does Long-Term Single-Party Local Rule Help or Hurt Local Development?</h1>
  <p class="dek">A case-focused, nonpartisan assessment of long-term dominant-party local rule (<strong>長期優勢政黨執政</strong>) in selected Taiwan counties and cities, including Taipei (<strong>臺北市</strong>), Kaohsiung (<strong>高雄市</strong>), Tainan (<strong>臺南市</strong>), Hualien (<strong>花蓮縣</strong>), Nantou (<strong>南投縣</strong>), and other long-dominant cases.</p>

  <section class="front">
    <div class="card">
      <h2>Assumptions First</h2>
      <ul>
        <li>The central question is not “which party is better,” but whether a long period of single-party or dominant-party local rule (<strong>長期單一／優勢政黨執政</strong>) coincides with stronger or weaker local development.</li>
        <li>“Development” is judged by three layers: each county/city's own long-run change (<strong>自身長期變化</strong>), a structurally similar matched comparison (<strong>對照縣市比較</strong>), and Taiwan-benchmark income growth (<strong>相對全國所得成長</strong>) to remove economy-wide cycles.</li>
        <li>National income position is shown as a 10-percentile band (<strong>所得分位段</strong>) rather than an exact rank. It is <strong>not</strong> used in the verdict score, because direct-controlled municipality reforms, county/city mergers, and high-base effects can change the comparison set without proving a real change in local economic strength.</li>
        <li>These are case comparisons, not randomized experiments. A weak outcome under one party does not by itself prove that the party caused the weakness.</li>
        <li>County GDP is not used because Taiwan's DGBAS does not compile county/city GDP.</li>
      </ul>
    </div>
    <div class="card">
      <h2>Final Conclusions</h2>
      <p class="finding"><span class="tag">Direct answer</span>Long-term dominant-party local rule has <strong>mixed results</strong>. It looks beneficial in cases such as Tainan, Hsinchu County, and Kaohsiung; clearly negative in Nantou; and weak or mixed in Hualien, Pingtung, and Chiayi County. Taipei is treated separately as a high-income capital-city benchmark rather than as a simple rank-change case.</p>
      <p class="finding"><span class="tag">Taipei</span><strong>{m['臺北市']['判讀']}.</strong> Taipei remains a top-tier, capital-city economy. Its income position stays within {m['臺北市']['所得分位段1999']} → {m['臺北市']['所得分位段2024']}, so the old exact-rank change is <strong>not</strong> treated as substantive decline. The slower Taiwan-benchmark growth is better read as high-base / mature-city convergence than as proof that Taipei lost economic strength.</p>
      <p class="finding"><span class="tag">Strong positives</span>Tainan is +{m['臺南市']['累積相對所得成長百分點']:.1f} pp, Hsinchu County is +{m['新竹縣']['累積相對所得成長百分點']:.1f} pp, Miaoli is +{m['苗栗縣']['累積相對所得成長百分點']:.1f} pp, and Kaohsiung is +{m['高雄市']['累積相對所得成長百分點']:.1f} pp against the Taiwan benchmark.</p>
      <p class="finding"><span class="tag">Weak cases</span>Nantou is the clearest negative case at {m['南投縣']['累積相對所得成長百分點']:.1f} pp against the Taiwan benchmark. Hualien and Pingtung are milder weak cases; they do not show a strong growth payoff from long political continuity.</p>
      <p class="finding"><span class="tag">Central-local alignment</span>When the central and local ruling parties differ, this dataset does <strong>not</strong> show a clear penalty for household income or unemployment. The full-panel same-party coefficient is {income_alignment['coefficient']:.3f} pp for income growth and {unemp_alignment['coefficient']:.3f} pp for unemployment, both substantively small.</p>
    </div>
  </section>

  <section>
    <h2>One-Chart Summary</h2>
    <p>This dashboard is the fastest reading of the study. It combines the final verdict with the evidence behind it: the Taiwan-benchmark income gap, unemployment, enterprise activity, matched comparison gap, and income percentile-band movement as contextual reference.</p>
    <figure>
      {summary_svg}
      <figcaption>Figure 1. Summary dashboard. Verdict colors indicate the case-level conclusion, not a party preference. Party labels are shown only to describe the long-term local rule profile.</figcaption>
    </figure>
  </section>

  <section>
    <h2>Dominant Party × Development Outcome</h2>
    <p>This is the key visual answer to the party question. Blue cases are KMT-dominant; green cases are DPP-dominant. The chart shows that neither color is uniformly good or bad: both dominant-party groups contain stronger and weaker development cases.</p>
    <figure>
      {party_outcome_svg}
      <figcaption>Figure 2. Dominant-party outcome matrix. The horizontal position is the Taiwan-benchmark income gap. Party color describes long-term local ruling profile; marker color gives the study's final development verdict.</figcaption>
    </figure>
  </section>

  <section>
    <h2>Income Position as Percentile Bands</h2>
    <p>The income-position test asks a simple descriptive question: did the county/city move across broad 10-percentile bands in household disposable income? This is more appropriate than exact ranks because Taiwan's comparison set changed after direct-controlled municipality reforms and county/city consolidation, and high-income places such as Taipei can show slower growth because of mature-city convergence. For that reason, percentile-band movement is shown below as a diagnostic reference only and is not used in the final verdict score.</p>
    <figure>
      {rank_shift_svg}
      <figcaption>Figure 3. Income percentile-band slope chart. Band movement is descriptive only; it should be read with boundary reform, merger effects, and high-base city dynamics in mind. Colors identify the long-term dominant local party, not a normative party judgment.</figcaption>
    </figure>
    <p>The period table below links percentile-band changes to local ruling-party periods. It is descriptive only: a band move during a party's tenure is a clue for case selection, not evidence of relative underperformance by itself and not evidence of party causation.</p>
    {rank_period_table(periods)}
  </section>

  <section>
    <h2>Why Not Use Only the Taiwan Benchmark?</h2>
    <p>Comparing each county/city with Taiwan overall is useful because it removes national business-cycle noise. But it is not enough for a fair case judgment. Taipei has a capital-city starting advantage, Hsinchu County benefits from the science-park and semiconductor cluster, Hualien faces geography and transport constraints, and Nantou's inland tourism/agriculture structure is different from the metropolitan counties. For that reason, the conclusion uses the Taiwan benchmark as one lens, then checks whether the county improved relative to itself and whether it outperformed a matched county/city with a different dominant-party profile.</p>
  </section>

  <section>
    <h2>Case Scorecard</h2>
    <p>The selected cases are counties/cities with long single-party or dominant-party local rule, plus Taipei because its political history is strongly KMT-dominant despite the independent-mayor period. The Taiwan-benchmark metric is cumulative excess log income growth from 1999 to 2024, but the final reading is deliberately not based on that alone. It also considers unemployment, enterprise activity, and matched comparison performance. Income percentile band is retained in the table as a reference column only.</p>
    {metrics_table(metrics)}
  </section>

  <section>
    <h2>How the Selected Cases Compare on Taiwan-Benchmark Growth</h2>
    <figure>
      {svg_rank_bars(ranks)}
      <figcaption>Figure 4. Cumulative excess household disposable income growth (<strong>累積相對所得成長</strong>) for all 20 counties/cities. The selected long-dominant cases are highlighted.</figcaption>
    </figure>
  </section>

  <section>
    <h2>Matched Case Comparisons</h2>
    <p>The matched comparison is descriptive. It asks whether the focus county's income index rose faster than a plausible comparison county, not whether the ruling party caused the difference.</p>
    <figure>
      {svg_case_lines(panel)}
      <figcaption>Figure 5. Income index comparison, with 1999-2002 average set to 100. Blue is the focus case; brown is the matched comparison county.</figcaption>
    </figure>
  </section>

  <section>
    <h2>Case-Level Interpretation</h2>
    <ul>
      <li><strong>Positive cases:</strong> Tainan, Hsinchu County, Miaoli, Kaohsiung, and Taitung show positive relative income growth. This means long dominant-party rule can coexist with development.</li>
      <li><strong>Weak cases:</strong> Nantou is clearly negative; Hualien, Pingtung, and Chiayi County are mixed or weak depending on the indicator. Taipei is not treated as a simple weak case because capital-city high-base effects and boundary changes make exact-rank interpretation fragile.</li>
      <li><strong>Bottom line:</strong> The party label alone is not the causal explanation. The same pattern of political continuity produces very different outcomes across places, so industrial structure, migration, central fiscal resources, and local administrative capacity need to be tested next.</li>
    </ul>
    <p>These results do not justify a universal pro-DPP or anti-KMT conclusion. They do suggest that “stable one-party local rule” is not a sufficient explanation for development. The local economic base, industrial transition, migration, central fiscal allocation, and administrative capacity likely matter at least as much.</p>
  </section>

  <section>
    <h2>International Literature Context</h2>
    <p>International research often finds that political alignment can affect intergovernmental grants, but the link from alignment to economic outcomes is less automatic. This literature supports a cautious case-based interpretation: if party continuity matters, it probably works through fiscal transfers, investment choices, and local capacity rather than through party label alone.</p>
    {references()}
  </section>

  <section>
    <h2>What Would Make the Test Stronger?</h2>
    <ul>
      <li>Add mayoral election victory margins (<strong>縣市長勝選差距</strong>) from the Central Election Commission (<strong>中央選舉委員會</strong>) to compare close wins.</li>
      <li>Add central fiscal transfers (<strong>統籌分配稅款／中央補助款</strong>) to test whether long-rule counties receive different resources.</li>
      <li>Add sectoral controls for tourism, agriculture, manufacturing, semiconductors, public employment, and aging, especially for Hualien and Nantou.</li>
    </ul>
  </section>

  <section>
    <h2>Validation</h2>
    <pre>{html.escape(validation)}</pre>
    <p class="note">Generated by <code>generate_case_focused_report.py</code> from the reproducible county-year panel.</p>
  </section>
</main>
</body>
</html>"""
    REPORT.write_text(doc, encoding="utf-8")


if __name__ == "__main__":
    build_report()
    print(REPORT)
