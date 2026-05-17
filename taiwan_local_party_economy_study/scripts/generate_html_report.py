from __future__ import annotations

import html
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
STUDY = ROOT / "study_outputs"
REPORT = STUDY / "party_alignment_report.html"


def fmt(x, digits=3):
    if pd.isna(x):
        return ""
    return f"{x:.{digits}f}"


def pct(x):
    return f"{x:.3f}"


def read_data():
    panel = pd.read_csv(STUDY / "party_alignment_county_year_panel.csv")
    models = pd.read_csv(STUDY / "model_results.csv")
    events = pd.read_csv(STUDY / "event_study_income.csv")
    matches = pd.read_csv(STUDY / "matched_cases.csv")
    validation = (STUDY / "study_validation_report.txt").read_text(encoding="utf-8")
    return panel, models, events, matches, validation


def svg_event(events: pd.DataFrame) -> str:
    avg = (
        events[["相對年度", "平均所得相對成長率百分點", "事件數"]]
        .drop_duplicates()
        .sort_values("相對年度")
    )
    width, height = 900, 480
    ml, mt, mr, mb = 70, 80, 30, 62
    x0, y0, x1, y1 = ml, mt, width - mr, height - mb
    vals = avg["平均所得相對成長率百分點"].tolist()
    ymin, ymax = min(-8, min(vals)), max(8, max(vals))

    def sx(v):
        return x0 + (v + 5) / 10 * (x1 - x0)

    def sy(v):
        return y1 - (v - ymin) / (ymax - ymin) * (y1 - y0)

    pts = " ".join(
        f"{sx(r['相對年度']):.1f},{sy(r['平均所得相對成長率百分點']):.1f}"
        for _, r in avg.iterrows()
    )
    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Event study chart">',
        '<style>.axis{stroke:#cbd5e1;stroke-width:1}.zero{stroke:#475569;stroke-width:2}.line{fill:none;stroke:#1d4f91;stroke-width:4}.dot{fill:#1d4f91}.label{font:14px system-ui, sans-serif;fill:#475569}.title{font:700 24px system-ui, sans-serif;fill:#111827}.sub{font:15px system-ui, sans-serif;fill:#475569}</style>',
        '<text x="24" y="34" class="title">Local Party Alternation Event Study (地方政黨輪替事件研究)</text>',
        '<text x="24" y="59" class="sub">Outcome: excess log income growth, percentage points (所得相對成長率百分點). Event year = 0.</text>',
        f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="#fff" stroke="#cbd5e1"/>',
    ]
    for tick in range(int(ymin), int(ymax) + 1, 2):
        y = sy(tick)
        parts.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" class="axis"/>')
        parts.append(f'<text x="{x0-12}" y="{y+5:.1f}" text-anchor="end" class="label">{tick:+d}</text>')
    parts.append(f'<line x1="{sx(0):.1f}" y1="{y0}" x2="{sx(0):.1f}" y2="{y1}" class="zero"/>')
    parts.append(f'<polyline points="{pts}" class="line"/>')
    for _, r in avg.iterrows():
        parts.append(
            f'<circle cx="{sx(r["相對年度"]):.1f}" cy="{sy(r["平均所得相對成長率百分點"]):.1f}" r="5" class="dot"/>'
        )
    for rel in range(-5, 6):
        parts.append(f'<text x="{sx(rel):.1f}" y="{y1+28}" text-anchor="middle" class="label">{rel}</text>')
    parts.append(f'<text x="{x0}" y="{height-14}" class="label">Years relative to party alternation (相對年度)</text>')
    parts.append(f'<text x="{x0-45}" y="{y0-12}" class="label">pp</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def svg_model_plot(models: pd.DataFrame) -> str:
    base = models[models["specification"].str.contains("基準 FE")].copy()
    labels = {
        "所得相對成長率百分點": "Income excess growth (所得相對成長率)",
        "失業率": "Unemployment rate level (失業率)",
        "失業率變動": "Change in unemployment rate (失業率變動)",
        "企業家數對數成長率": "Enterprise count growth (企業家數成長)",
        "企業銷售額對數成長率": "Enterprise sales growth (企業銷售額成長)",
    }
    base["label"] = base["outcome"].map(labels)
    width, height = 940, 420
    x0, y0, x1 = 410, 88, 890
    row_h = 55
    xmin, xmax = -1.0, 4.5

    def sx(v):
        return x0 + (v - xmin) / (xmax - xmin) * (x1 - x0)

    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Coefficient plot">',
        '<style>.axis{stroke:#cbd5e1;stroke-width:1}.zero{stroke:#64748b;stroke-width:2}.ci{stroke:#1f2937;stroke-width:3}.pt{fill:#1d4f91}.label{font:14px system-ui, sans-serif;fill:#374151}.title{font:700 24px system-ui, sans-serif;fill:#111827}.sub{font:15px system-ui, sans-serif;fill:#475569}</style>',
        '<text x="24" y="34" class="title">Estimated Same-Party Association (同黨效果估計)</text>',
        '<text x="24" y="59" class="sub">Baseline county and year fixed effects; bars show ±1.96 clustered SE.</text>',
        f'<line x1="{sx(0):.1f}" y1="{y0-25}" x2="{sx(0):.1f}" y2="{y0+row_h*len(base)}" class="zero"/>',
    ]
    for tick in [-1, 0, 1, 2, 3, 4]:
        x = sx(tick)
        parts.append(f'<line x1="{x:.1f}" y1="{y0-25}" x2="{x:.1f}" y2="{y0+row_h*len(base)}" class="axis"/>')
        parts.append(f'<text x="{x:.1f}" y="{y0+row_h*len(base)+28}" text-anchor="middle" class="label">{tick}</text>')
    for i, (_, r) in enumerate(base.iterrows()):
        y = y0 + i * row_h
        coef = r["coefficient"]
        lo = coef - 1.96 * r["std_error"]
        hi = coef + 1.96 * r["std_error"]
        parts.append(f'<text x="24" y="{y+5}" class="label">{html.escape(r["label"])}</text>')
        parts.append(f'<line x1="{sx(lo):.1f}" y1="{y}" x2="{sx(hi):.1f}" y2="{y}" class="ci"/>')
        parts.append(f'<circle cx="{sx(coef):.1f}" cy="{y}" r="6" class="pt"/>')
        parts.append(f'<text x="{sx(hi)+8:.1f}" y="{y+5}" class="label">{coef:.3f}</text>')
    parts.append(f'<text x="{x0}" y="{height-18}" class="label">Coefficient on central-local same party (中央地方同黨)</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def svg_matches(matches: pd.DataFrame) -> str:
    cases = matches["案例縣市"].drop_duplicates().tolist()
    width, height = 1000, 1020
    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Matched cases">',
        '<style>.grid{stroke:#e2e8f0;stroke-width:1}.box{fill:#fff;stroke:#cbd5e1}.treated{fill:none;stroke:#1d4f91;stroke-width:3}.control{fill:none;stroke:#b4532a;stroke-width:3}.label{font:13px system-ui, sans-serif;fill:#475569}.title{font:700 24px system-ui, sans-serif;fill:#111827}.case{font:700 18px system-ui, sans-serif;fill:#111827}.sub{font:15px system-ui, sans-serif;fill:#475569}</style>',
        '<text x="24" y="34" class="title">Long-Run Single-Party Counties and Matched Cases (長期單一政黨縣市配對)</text>',
        '<text x="24" y="59" class="sub">Income index, 1999-2002 average = 100 (所得指數).</text>',
    ]
    panel_w, panel_h = 440, 245
    left, top = 55, 95
    gapx, gapy = 45, 55
    for i, case in enumerate(cases):
        col, row = i % 2, i // 2
        x, y = left + col * (panel_w + gapx), top + row * (panel_h + gapy)
        cdf = matches[matches["案例縣市"] == case]
        years = sorted(cdf["年度"].unique())
        vals = cdf["所得指數_1999_2002_100"]
        ymin = int(vals.min() // 10 * 10)
        ymax = int((vals.max() + 9) // 10 * 10)

        def sx(yr):
            return x + 45 + (yr - min(years)) / (max(years) - min(years)) * (panel_w - 72)

        def sy(v):
            return y + panel_h - 35 - (v - ymin) / (ymax - ymin) * (panel_h - 78)

        parts.append(f'<rect x="{x}" y="{y}" width="{panel_w}" height="{panel_h}" class="box"/>')
        parts.append(f'<text x="{x+14}" y="{y+26}" class="case">{case}</text>')
        for tick in range(ymin, ymax + 1, 20):
            yy = sy(tick)
            parts.append(f'<line x1="{x+45}" y1="{yy:.1f}" x2="{x+panel_w-27}" y2="{yy:.1f}" class="grid"/>')
            parts.append(f'<text x="{x+10}" y="{yy+4:.1f}" class="label">{tick}</text>')
        for role, cls in [("處理縣市", "treated"), ("配對縣市", "control")]:
            rdf = cdf[cdf["角色"] == role].sort_values("年度")
            pts = " ".join(f"{sx(r['年度']):.1f},{sy(r['所得指數_1999_2002_100']):.1f}" for _, r in rdf.iterrows())
            parts.append(f'<polyline points="{pts}" class="{cls}"/>')
            label = "treated" if role == "處理縣市" else "matched"
            parts.append(f'<text x="{x+250}" y="{y+28+(18 if role=="配對縣市" else 0)}" class="label">{label}: {rdf["縣市"].iloc[0]}</text>')
        for yr in [2000, 2008, 2016, 2024]:
            parts.append(f'<text x="{sx(yr):.1f}" y="{y+panel_h-12}" text-anchor="middle" class="label">{yr}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def table_model_summary(models: pd.DataFrame) -> str:
    base = models[models["specification"].str.contains("基準 FE")].copy()
    rows = []
    for _, r in base.iterrows():
        rows.append(
            "<tr>"
            f"<td>{html.escape(r['outcome'])}</td>"
            f"<td>{fmt(r['coefficient'])}</td>"
            f"<td>{fmt(r['std_error'])}</td>"
            f"<td>{fmt(r['p_value_normal'])}</td>"
            f"<td>{int(r['n'])}</td>"
            f"<td>{html.escape(r['years'])}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr><th>Outcome (結果變數)</th><th>Coefficient</th><th>Clustered SE</th>"
        "<th>Normal p-value</th><th>N</th><th>Years</th></tr></thead><tbody>"
        + "\n".join(rows)
        + "</tbody></table>"
    )


def glossary() -> str:
    terms = [
        ("Central ruling party", "中央執政黨"),
        ("Local ruling party / county or city mayor party", "地方執政黨／縣市首長黨籍"),
        ("Central-local same party", "中央地方同黨"),
        ("Disposable income", "可支配所得"),
        ("County/city fixed effects", "縣市固定效果"),
        ("Year fixed effects", "年度固定效果"),
        ("Event study", "事件研究"),
        ("Party alternation", "政黨輪替"),
        ("Matched case comparison", "配對案例比較"),
    ]
    return "<dl>" + "\n".join(f"<dt>{e}</dt><dd>{z}</dd>" for e, z in terms) + "</dl>"


def references() -> str:
    refs = [
        (
            "Solé-Ollé, A., & Sorribas-Navarro, P. (2008). “The effects of partisan alignment on the allocation of intergovernmental transfers.” Journal of Public Economics.",
            "https://www.sciencedirect.com/science/article/pii/S0047272707000990",
            "Spain; difference-in-differences evidence that alignment can affect grants.",
        ),
        (
            "Brollo, F., & Nannicini, T. (2012). “Tying Your Enemy’s Hands in Close Races: The Politics of Federal Transfers in Brazil.” American Political Science Review.",
            "https://www.cambridge.org/core/journals/american-political-science-review/article/tying-your-enemys-hands-in-close-races-the-politics-of-federal-transfers-in-brazil/15C1E15B8603C82B79592E34478C68D9",
            "Brazil; close-election design linking political incentives and federal transfers.",
        ),
        (
            "Bracco, E., Lockwood, B., Porcelli, F., & Redoano, M. (2015). “Intergovernmental grants as signals and the alignment effect: Theory and evidence.” Journal of Public Economics.",
            "https://www.sciencedirect.com/science/article/pii/S0047272714002291",
            "Theory and evidence on grants as political signals under alignment.",
        ),
        (
            "Siwińska-Gorzelak, J., & Bukowska, G. (2023). “Intragovernmental Grant Distribution and Party Alignment Bias under Democratic and Authoritarian Governments: The Case of Poland.” East European Politics and Societies.",
            "https://journals.sagepub.com/doi/10.1177/08883254221116787",
            "Poland; quasi-experimental evidence on alignment bias in grants.",
        ),
        (
            "Lee, H. et al. (2024). “Ideology, intergovernmental transfers, and public health spending: Evidence from South Korea.” Regional Science and Urban Economics.",
            "https://www.sciencedirect.com/science/article/pii/S0166046224001054",
            "South Korea; ideology, transfers, and local policy spending.",
        ),
        (
            "Dahlberg, M., Mörk, E., Rattsø, J., & Ågren, H. (2008). “Using a discontinuous grant rule to identify the effect of grants on local taxes and spending.” Journal of Public Economics.",
            "https://www.sciencedirect.com/science/article/pii/S0047272707001028",
            "Useful benchmark on grant effects and local fiscal behavior, separate from party alignment.",
        ),
    ]
    items = []
    for text, url, note in refs:
        items.append(
            f'<li>{html.escape(text)} <a href="{url}">link</a><br><span class="note">{html.escape(note)}</span></li>'
        )
    return "<ol>" + "\n".join(items) + "</ol>"


def build_report():
    panel, models, events, matches, validation = read_data()
    income_key = models[(models["outcome"] == "所得相對成長率百分點") & (models["specification"].str.contains("基準 FE"))].iloc[0]
    unemp_key = models[(models["outcome"] == "失業率") & (models["specification"].str.contains("基準 FE"))].iloc[0]
    firm_key = models[(models["outcome"] == "企業家數對數成長率") & (models["specification"].str.contains("基準 FE"))].iloc[0]
    sales_key = models[(models["outcome"] == "企業銷售額對數成長率") & (models["specification"].str.contains("基準 FE"))].iloc[0]
    event_avg = events[["相對年度", "平均所得相對成長率百分點", "事件數"]].drop_duplicates()
    pre_mean = event_avg[event_avg["相對年度"].isin([-3, -2, -1])]["平均所得相對成長率百分點"].mean()

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Central-Local Party Alignment and Local Economic Development in Taiwan</title>
  <style>
    :root {{ --ink:#111827; --muted:#475569; --line:#d8e1ec; --bg:#f8fafc; --blue:#1d4f91; }}
    body {{ margin:0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color:var(--ink); background:white; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 48px 28px 80px; }}
    h1 {{ font-size: 42px; line-height:1.08; margin:0 0 12px; letter-spacing:0; }}
    h2 {{ font-size: 26px; margin: 34px 0 12px; border-top:1px solid var(--line); padding-top:26px; }}
    h3 {{ font-size: 19px; margin: 24px 0 8px; }}
    p, li {{ font-size: 16px; line-height:1.65; }}
    .dek {{ color:var(--muted); font-size:18px; max-width:860px; }}
    .front {{ display:grid; grid-template-columns: 1fr 1fr; gap:18px; margin-top:28px; }}
    .card {{ background:var(--bg); border:1px solid var(--line); border-radius:10px; padding:20px 22px; }}
    .card h2 {{ margin-top:0; border:0; padding-top:0; }}
    .finding {{ font-size:17px; line-height:1.55; }}
    .tag {{ display:inline-block; font-size:13px; background:#e8f0fb; color:#163d73; padding:4px 8px; border-radius:999px; margin-right:6px; }}
    table {{ border-collapse: collapse; width:100%; margin: 14px 0 24px; font-size:14px; }}
    th, td {{ border-bottom:1px solid var(--line); padding:10px 8px; text-align:left; vertical-align:top; }}
    th {{ background:#f1f5f9; font-weight:700; }}
    figure {{ margin: 26px 0; border:1px solid var(--line); border-radius:12px; padding:16px; overflow:auto; background:#fff; }}
    figcaption {{ color:var(--muted); font-size:14px; line-height:1.5; margin-top:8px; }}
    dl {{ columns:2; column-gap:44px; }}
    dt {{ font-weight:700; break-inside:avoid; margin-top:10px; }}
    dd {{ margin:2px 0 10px; color:var(--muted); break-inside:avoid; }}
    .note {{ color:var(--muted); font-size:14px; }}
    code {{ background:#f1f5f9; padding:2px 5px; border-radius:4px; }}
    @media (max-width: 780px) {{ .front {{ grid-template-columns:1fr; }} dl {{ columns:1; }} h1 {{ font-size:32px; }} }}
  </style>
</head>
<body>
<main>
  <h1>Central-Local Party Alignment and Local Economic Development in Taiwan</h1>
  <p class="dek">A reproducible quasi-causal research report on whether sharing the same central and local ruling party (<strong>中央地方同黨</strong>) is associated with county/city economic outcomes in Taiwan.</p>

  <section class="front">
    <div class="card">
      <h2>Assumptions First</h2>
      <ul>
        <li><strong>Local economic development</strong> is proxied by disposable income (<strong>可支配所得</strong>), unemployment (<strong>失業率</strong>), and enterprise activity (<strong>企業活動</strong>), not by county GDP. Taiwan's DGBAS does not compile county/city GDP.</li>
        <li><strong>Central-local same party</strong> means the president's party (<strong>中央執政黨</strong>) matches the elected county/city mayor's party (<strong>縣市首長黨籍</strong>) on July 1 of each year.</li>
        <li>Independent and third-party mayors are treated as not same-party with the central government in the baseline.</li>
        <li>The estimates are quasi-causal evidence, not a randomized experiment.</li>
      </ul>
    </div>
    <div class="card">
      <h2>Final Conclusions</h2>
      <p class="finding"><span class="tag">Nonpartisan reading</span>The evidence does <strong>not</strong> show a broad, reliable advantage for either major party. It also does not show that same-party alignment consistently improves household income growth.</p>
      <p class="finding"><span class="tag">Main result</span>For household disposable income, the baseline same-party coefficient is {income_key['coefficient']:.3f} percentage points with clustered SE {income_key['std_error']:.3f}; this is substantively small and statistically indistinguishable from zero.</p>
      <p class="finding"><span class="tag">Labor market</span>The unemployment estimate is similarly small: {unemp_key['coefficient']:.3f} percentage points, SE {unemp_key['std_error']:.3f}.</p>
      <p class="finding"><span class="tag">Enterprise activity</span>Enterprise count and sales show positive same-party associations after 2014, but this shorter series may reflect sectoral composition, local selection, or transfer mechanisms. It should not be read as proof that any party governs the local economy better.</p>
    </div>
  </section>

  <section>
    <h2>Research Question</h2>
    <p>This report asks whether counties and cities governed by the same party as the central executive perform differently from those governed by a different party. It also asks whether counties long governed by one party can be compared with similar counties governed by another party.</p>
    <p>The report is written as a neutral empirical assessment. Party labels are treated as institutional variables, not as normative rankings. A positive or negative coefficient is interpreted as an association under a specific model, not as evidence of political virtue, competence, or blame.</p>
  </section>

  <section>
    <h2>Relevant International Literature</h2>
    <p>The international literature gives a balanced prior. In several countries, politically aligned local governments have been found to receive more intergovernmental transfers or infrastructure grants. However, the literature also warns that transfer advantages do not mechanically imply better local economic outcomes; institutional rules, fiscal formulas, local capacity, and industrial structure can dominate partisan channels.</p>
    {references()}
  </section>

  <section>
    <h2>Data and Measures</h2>
    <p>The panel covers 20 Taiwan counties/cities (<strong>縣市</strong>) from 1998 to 2024. Income and unemployment are available for the full panel. Enterprise count and sales are available from 2013, so their growth models begin in 2014.</p>
    <ul>
      <li><strong>Income outcome:</strong> excess log growth of average household disposable income (<strong>平均每戶可支配所得相對對數成長率</strong>), in percentage points.</li>
      <li><strong>Labor outcome:</strong> unemployment rate level and annual change (<strong>失業率、失業率變動</strong>).</li>
      <li><strong>Enterprise outcomes:</strong> log growth in enterprise count and enterprise sales (<strong>企業家數、企業銷售額</strong>).</li>
    </ul>
  </section>

  <section>
    <h2>Model Results</h2>
    <p>The baseline model uses county/city fixed effects (<strong>縣市固定效果</strong>) and year fixed effects (<strong>年度固定效果</strong>), with standard errors clustered by county/city.</p>
    {table_model_summary(models)}
    <figure>
      {svg_model_plot(models)}
      <figcaption>Figure 1. Baseline coefficient plot for central-local same-party alignment (<strong>中央地方同黨</strong>). Confidence bars use ±1.96 clustered standard errors.</figcaption>
    </figure>
  </section>

  <section>
    <h2>Event Study: Local Party Alternation</h2>
    <p>The event study averages counties/cities that switched between the two major parties (<strong>主要政黨輪替</strong>). The pre-period average from years -3 to -1 is {pre_mean:.3f} percentage points. Because the path is noisy and does not form a clean post-switch break, it should not be interpreted as strong causal evidence.</p>
    <figure>
      {svg_event(events)}
      <figcaption>Figure 2. Local party alternation event study (<strong>地方政黨輪替事件研究</strong>) for income excess growth.</figcaption>
    </figure>
  </section>

  <section>
    <h2>Matched Case Comparisons</h2>
    <p>For long-run single-party counties (<strong>長期單一政黨縣市</strong>), matched comparison counties were selected using baseline income, baseline unemployment, and baseline income volatility. The matched cases are descriptive and should be used to guide qualitative case selection.</p>
    <figure>
      {svg_matches(matches)}
      <figcaption>Figure 3. Income index comparison for long-run single-party counties and matched counties (<strong>配對縣市</strong>).</figcaption>
    </figure>
  </section>

  <section>
    <h2>Interpretation</h2>
    <p>The income and unemployment evidence does not support a broad claim that sharing the central ruling party systematically improves local economic development. The positive enterprise associations are worth investigating, but they rely on the shorter 2014-2024 growth window and may reflect policy channels, sectoral composition, metropolitan growth, or regional selection rather than a direct party-alignment effect.</p>
    <p>A fair reading is therefore cautious: party alignment may matter for specific fiscal or administrative channels, but this dataset does not show a stable economy-wide payoff in household income or unemployment. This conclusion is deliberately symmetric across parties.</p>
    <p>A stronger next version should add county mayor victory margins (<strong>縣市長勝選差距</strong>) from the Central Election Commission (<strong>中央選舉委員會</strong>) and central fiscal transfers (<strong>統籌分配稅款／中央補助款</strong>) from the National Treasury Administration. Those data would help distinguish whether any observed alignment effect works through central resource allocation rather than through local party governance itself.</p>
  </section>

  <section>
    <h2>Terminology Glossary</h2>
    {glossary()}
  </section>

  <section>
    <h2>Validation</h2>
    <pre>{html.escape(validation)}</pre>
    <p class="note">Generated from <code>run_party_alignment_study.py</code> and <code>generate_html_report.py</code>. Source data files and intermediate CSV outputs are stored in the same workspace.</p>
  </section>
</main>
</body>
</html>
"""
    REPORT.write_text(html_doc, encoding="utf-8")


if __name__ == "__main__":
    build_report()
    print(REPORT)
