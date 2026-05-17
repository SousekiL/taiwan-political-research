#!/usr/bin/env python3
"""Build the final compact academic report with embedded charts.

NOTE: This script is OUTDATED. The current docs/index.html was built manually
and contains a dashboard chart that this script does not generate.
Kept for reference only; to regenerate the report, update b64 filenames first.
"""
import base64
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parents[1]
RESULTDIR = DOCS_DIR / "results"
OUT = DOCS_DIR / "index.html"

# Load chart base64
summary_b64 = open(RESULTDIR / 'summary_conclusion_b64.b64').read().strip()
traj_b64 = open(RESULTDIR / 'income_trajectories_b64_v2.b64').read().strip()
scm_b64 = open(RESULTDIR / 'scm_effects_1996_b64_v2.b64').read().strip()

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Long-Term Party Rule and Local Economic Development in Taiwan</title>
<style>
  :root {{ --bg: #fafaf9; --text: #1c1917; --muted: #6b6560; --border: #d6d3d1; --accent: #1d4ed8; --accent-light: #dbeafe; --surface: #fff; --red: #dc2626; --green: #16a34a; --amber: #d97706; --radius: 6px; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: "Helvetica Neue", "Noto Sans TC", Arial, sans-serif; background: var(--bg); color: var(--text); line-height: 1.75; font-size: 16px; }}
  .container {{ max-width: 820px; margin: 0 auto; padding: 50px 24px; }}

  .cover {{ text-align: center; padding: 70px 0 50px; border-bottom: 1px solid var(--border); margin-bottom: 50px; }}
  .cover .tag {{ display: inline-block; background: var(--accent-light); color: var(--accent); font-size: 12px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; padding: 4px 10px; border-radius: 100px; margin-bottom: 20px; }}
  .cover h1 {{ font-size: 32px; font-weight: 700; letter-spacing: -0.02em; line-height: 1.3; margin-bottom: 12px; }}
  .cover .subtitle {{ font-size: 16px; color: var(--muted); max-width: 520px; margin: 0 auto 24px; }}
  .cover .meta {{ color: var(--muted); font-size: 13px; }}

  section {{ margin-bottom: 44px; }}
  h2 {{ font-size: 20px; font-weight: 700; letter-spacing: -0.01em; margin-bottom: 16px; padding-bottom: 6px; border-bottom: 2px solid var(--accent); }}
  h3 {{ font-size: 16px; font-weight: 600; margin: 24px 0 10px; }}
  p {{ margin-bottom: 13px; }}
  .zh {{ color: var(--muted); font-size: 13px; }}

  .table-wrapper {{ overflow-x: auto; margin: 18px 0; border: 1px solid var(--border); border-radius: var(--radius); }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13.5px; }}
  thead {{ background: #f5f5f4; }}
  th {{ text-align: left; padding: 10px 14px; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); border-bottom: 1px solid var(--border); }}
  td {{ padding: 10px 14px; border-bottom: 1px solid var(--border); vertical-align: top; }}
  tr:last-child td {{ border-bottom: none; }}

  .callout {{ padding: 16px 20px; border-radius: var(--radius); margin: 18px 0; font-size: 14px; }}
  .callout.info {{ background: #eff6ff; border: 1px solid #bfdbfe; color: #1e40af; }}
  .callout.warning {{ background: #fffbeb; border: 1px solid #fde68a; color: #92400e; }}
  .badge {{ display: inline-block; padding: 2px 6px; border-radius: 3px; font-size: 11px; font-weight: 600; }}
  .badge.green {{ background: #dcfce7; color: #16a34a; }}
  .badge.red {{ background: #fee2e2; color: #dc2626; }}
  .badge.amber {{ background: #fef3c7; color: #d97706; }}
  .badge.blue {{ background: #dbeafe; color: #1d4ed8; }}

  .ref-list {{ font-size: 13.5px; }}
  .ref-list li {{ margin-bottom: 6px; }}

  footer {{ text-align: center; padding: 30px 0 20px; border-top: 1px solid var(--border); color: var(--muted); font-size: 12px; }}

  @media print {{ body {{ font-size: 13px; line-height: 1.55; }} .container {{ max-width: 100%; padding: 0; }} section {{ page-break-inside: avoid; margin-bottom: 28px; }} }}
</style>
</head>
<body>
<div class="container">

<div class="cover">
  <span class="tag">Political Economy · Taiwan</span>
  <h1>Long-Term Party Rule and Local Economic Development in Taiwan</h1>
  <p class="subtitle">Evidence from County-Level Panel Data, 1996–2024</p>
  <p class="meta">May 2026</p>
</div>

<section>
  <h2>1. Background and Motivation <span class="zh">（研究背景）</span></h2>

  <p>Taiwan's local politics is characterized by a small number of jurisdictions where a single party has governed continuously for multiple decades. These cases — most notably Kaohsiung City <span class="zh">（高雄市）</span> and Tainan City <span class="zh">（臺南市）</span> under the Democratic Progressive Party <span class="zh">（民主進步黨，DPP）</span>, and Hualien County <span class="zh">（花蓮縣）</span> and Nantou County <span class="zh">（南投縣）</span> under the Kuomintang <span class="zh">（國民黨，KMT）</span> — raise a straightforward but politically significant question: <strong>has long-term rule by a single party helped or hurt these localities' economic development?</strong> Citizens, commentators, and policymakers routinely debate this question, but systematic empirical evidence remains scarce. Existing Taiwan-based research has examined fiscal effects of party alternation (Huang 2023), the impact of local government expenditure composition on growth (Huang 2016), and partisan differences in land development strategies (Chang and Liu 2022), but no study has directly estimated whether jurisdictions governed by one party for decades achieved better or worse economic outcomes than they would have under different governance.</p>

  <p>This study addresses that gap. Using a county-year panel covering 20 jurisdictions from 1996 through 2024, and employing the Synthetic Control Method <span class="zh">（合成控制法，SCM）</span> supplemented by panel fixed effects regression, we estimate the economic effect of long-term single-party rule across multiple dimensions. The analysis is designed to be <strong>methodologically rigorous and politically neutral</strong>: cases are selected symmetrically from both major parties, the null hypothesis of no party effect is taken seriously, and conclusions follow the evidence rather than any prior expectation.</p>

  <p>A note on measurement. Taiwan does not publish county-level GDP. Following established practice in the Taiwanese political economy literature (Huang 2023), we proxy economic output with per capita disposable income <span class="zh">（每人可支配所得）</span> from the Directorate-General of Budget, Accounting and Statistics <span class="zh">（行政院主計總處）</span> Household Income and Expenditure Survey. Administrative boundary changes — notably the 2010 upgrade of several counties to special municipalities <span class="zh">（直轄市改制）</span> and various mergers — affect the comparability of county-level rankings across time. We therefore focus on <strong>growth rates relative to the national average</strong> rather than raw ranking positions, which are sensitive to such boundary changes.</p>
</section>

<section>
  <h2>2. Findings and Conclusions <span class="zh">（研究發現與結論）</span></h2>

  <div class="callout warning">
    <strong>Summary.</strong> Long-term single-party rule is neither uniformly beneficial nor uniformly harmful. The decisive factor is whether the jurisdiction is structurally connected to Taiwan's semiconductor-driven, export-oriented growth model — not which party holds power. Party control itself exerts no statistically distinguishable effect on income (DPP vs. KMT dummy: p = 0.77). <strong>Both parties have clear success cases and clear failure cases among their long-term strongholds.</strong> The only political variable that consistently predicts better outcomes is party alternation <span class="zh">（政黨輪替）</span>, suggesting that political competition, rather than partisan identity, is what matters for governance quality.
  </div>

  <h3>The Central Finding in One Chart</h3>
  <p>Figure 1 shows each county's per capita disposable income growth from 1996 to 2024, expressed as the excess over the national average growth rate (approximately 18.6%). Counties to the right of zero grew faster than the national average; counties to the left grew more slowly. The color of each bar indicates which party dominated governance during this period — <strong style="color:#0052A5;">blue for KMT</strong>, <strong style="color:#1B9431;">green for DPP</strong>. <strong>The distribution is symmetric: both colors appear on both sides of the line.</strong></p>

  <div style="text-align:center; margin:22px 0;">
    <img src="data:image/png;base64,{summary_b64}" alt="Summary Conclusion Chart" style="max-width:100%; border:1px solid var(--border); border-radius: var(--radius);">
    <p style="font-size:11px; color:var(--muted); margin-top:6px;"><strong>Figure 1. Excess Income Growth by County, 1996–2024.</strong> Bars show per capita disposable income growth relative to the national average. Blue = KMT-dominant counties, green = DPP-dominant counties, gray = mixed/alternating. The DPP-dominant group averages +0.2 percentage points of excess growth; the KMT-dominant group averages –0.6 pp. This difference is negligible and not statistically distinguishable.</p>
  </div>

  <p>The four original target cases tell the story most clearly. <strong>Tainan (DPP, 30+ years of continuous rule)</strong> recorded the strongest excess growth among all southern counties at +9.1 percentage points, driven overwhelmingly by the Southern Taiwan Science Park <span class="zh">（南部科學園區）</span>, a national-level project whose placement was determined by central government industrial policy. The local government's role was facilitative — coordinating land, infrastructure, and permitting — rather than causal. <strong>Kaohsiung (DPP, 26+ years)</strong> shows a much more modest +3.1 pp excess, reflecting two decades of structural deindustrialization that stable DPP governance did not reverse. The very recent arrival of TSMC's 2nm fabrication plant at Nanzih <span class="zh">（楠梓）</span> may represent a turning point, but it is too early to evaluate. <strong>Hualien (KMT, multi-decade dominance)</strong> records approximately –16 pp excess growth — among the worst performances — with a persistently low salary share of income (48.9%) and high transfer dependency (25.7%). <strong>Nantou (KMT, multi-decade dominance)</strong> is the worst case at –19 pp excess, trapped in a documented downward spiral of industrial hollowing, youth outmigration, and fiscal decline that the county government itself acknowledges.</p>

  <p>These four cases span the full range of outcomes: the best southern performer (Tainan, DPP) and the three worst performers (Nantou, Hualien, Miaoli; KMT or KMT-leaning). <strong>Party cannot explain this distribution.</strong> Economic geography and connection to global semiconductor supply chains can. Taipei (KMT-dominant) maintained its position as the richest jurisdiction, benefiting from being the political and financial capital. The science-park-anchored counties of Northern Taiwan (Hsinchu, Taoyuan) cluster among the top performers irrespective of party.</p>

  <h3>Mechanisms: Political Alignment and Competition</h3>

  <p>The panel fixed effects model (N = 580, R² = 0.989) confirms that the partisan dummy is economically and statistically insignificant (coefficient = –0.0006, p = 0.771), meaning we cannot reject the null hypothesis that DPP and KMT governance produce identical income levels after controlling for economic fundamentals. Political alignment between central and local governments shows a marginally significant positive effect (coefficient = +0.0029, p = 0.094), corresponding to roughly a 0.3% income premium. Party alternation shows a consistently significant positive coefficient (+0.0036, p = 0.046), equivalent to a 0.36% income boost in post-alternation years — modest in magnitude but statistically reliable across specifications. This is the only political variable that consistently matters, and its direction is consistent with the hypothesis that political competition improves governance incentives.</p>

  <p>The Synthetic Control Method analysis, which constructs counterfactuals for eight long-term rule cases, reinforces this pattern. Both DPP and KMT rule cases appear among outperformers and underperformers. Notably, the two cases with frequent party alternation (Changhua and Yilan) both show positive SCM gaps, providing a quasi-experimental complement to the panel FE finding on alternation effects.</p>
</section>

<section>
  <h2>3. Data and Methods <span class="zh">（數據與方法）</span></h2>

  <p>The analysis uses a balanced county-year panel covering 20 jurisdictions over 1996–2024 (580 observations). The primary outcome variable is per capita disposable income (in logarithms for the SCM and FE models). Core political variables include a DPP dummy (1 when the county executive is DPP), an alignment dummy (1 when the county executive's party matches the president's party), and a party alternation dummy (1 in the four years following a change in the county executive's party). Control variables include the unemployment rate, tax revenue per capita, and county- and year-fixed effects.</p>

  <p>Economic data were sourced from the DGBAS County Important Statistical Indicators system <span class="zh">（縣市重要統計指標查詢系統）</span> and the Household Income and Expenditure Survey. Election results for county executives from 1989 through 2022 were collected from the Central Election Commission <span class="zh">（中央選舉委員會）</span> and verified against Wikipedia's county magistrate lists and the Aretz (2014) compilation.</p>

  <div class="table-wrapper">
    <table>
      <thead><tr><th>Variable</th><th>Chinese Name</th><th>Source</th></tr></thead>
      <tbody>
        <tr><td>Per Capita Disposable Income</td><td>每人可支配所得</td><td>DGBAS Household Income and Expenditure Survey</td></tr>
        <tr><td>Unemployment Rate</td><td>失業率</td><td>DGBAS County Indicators</td></tr>
        <tr><td>Tax Revenue per Capita</td><td>每人稅課收入</td><td>Ministry of Audit</td></tr>
        <tr><td>Population</td><td>人口總數</td><td>DGBAS County Indicators</td></tr>
        <tr><td>Local Ruling Party</td><td>地方執政黨</td><td>Central Election Commission</td></tr>
        <tr><td>Vote Margin (RDD)</td><td>得票差距</td><td>Central Election Commission</td></tr>
      </tbody>
    </table>
  </div>

  <h3>Synthetic Control Method</h3>
  <p>Our primary identification strategy is the Synthetic Control Method (Abadie and Gardeazabal 2003; Abadie, Diamond, and Hainmueller 2010). For each treated county (a jurisdiction under long-term single-party rule), we construct a synthetic counterfactual as a weighted combination of donor counties that were not under extended single-party rule. The donor weights are chosen via constrained quadratic programming to minimize the mean squared prediction error between the treated unit and its synthetic counterpart on pre-treatment outcomes and predictors, which include pre-treatment income levels, unemployment rates, and tax revenue. The post-treatment gap between the actual and synthetic income path provides a quantitative estimate of the treatment effect.</p>

  <p>Figure 2 illustrates the income trajectories for eight key cases, with party-colored segments and markers for party transitions.</p>

  <div style="text-align:center; margin:18px 0;">
    <img src="data:image/png;base64,{traj_b64}" alt="Income Trajectories" style="max-width:100%; border:1px solid var(--border); border-radius: var(--radius);">
    <p style="font-size:11px; color:var(--muted); margin-top:6px;"><strong>Figure 2. Per Capita Disposable Income Trajectories (1996–2024).</strong> Blue segments = KMT rule, green = DPP rule. Red dashed lines = party transitions. Black dashed line = national average. Titles include the county's dominant party.</p>
  </div>

  <p>Figure 3 presents the SCM treatment effect estimates — the average post-treatment gap between actual and synthetic income in log points.</p>

  <div style="text-align:center; margin:18px 0;">
    <img src="data:image/png;base64,{scm_b64}" alt="SCM Effects" style="max-width:100%; border:1px solid var(--border); border-radius: var(--radius);">
    <p style="font-size:11px; color:var(--muted); margin-top:6px;"><strong>Figure 3. SCM Treatment Effects (1996 baseline).</strong> Positive values indicate outperformance relative to the synthetic counterfactual. Both KMT and DPP rule cases appear on both sides of zero.</p>
  </div>

  <h3>Panel Fixed Effects and Triangulation</h3>
  <p>We complement the SCM with a standard two-way fixed effects regression that estimates the partial correlation between political variables and log per capita income, controlling for time-invariant county characteristics and common year shocks. While the FE model does not identify causal effects with the same credibility as SCM under the standard assumptions, it provides an independent check: if SCM identifies large partisan gaps but the FE model finds the DPP dummy irrelevant, the gap is likely driven by county-level structural differences rather than governance per se. This is precisely the pattern we observe.</p>

  <p>We also outline a Regression Discontinuity Design <span class="zh">（斷點回歸設計）</span> strategy — comparing economic outcomes in counties where a party narrowly won an election to those where it narrowly lost — as a planned extension that would strengthen causal identification. The RDD is not executed in the current analysis due to power constraints (only ~20 counties across ~9 election cycles), but it remains a viable avenue for follow-up work.</p>
</section>

<section>
  <h2>4. Related Literature <span class="zh">（相關文獻）</span></h2>

  <p>This study contributes to three bodies of literature. First, the political economy of fiscal federalism has produced extensive evidence on whether political alignment between central and local governments affects fiscal transfers and economic outcomes. Bracco, Porcelli, and Redoano (2015) find that aligned Italian municipalities receive approximately €26 per capita more in grants and impose lower taxes. Brunnschweiler and Obeng (2020) document similar alignment effects in Ghana despite formula-based transfer allocation rules. However, these effects are not universal: Hessami (2017) shows that in Germany the direction of favoritism depends on local political conditions, and Brollo and Nannicini (2012) find alignment effects in Brazil only in pre-election years. Our finding of a marginally significant but economically small alignment effect in Taiwan (p = 0.094, ~0.3% income premium) places Taiwan in the "weak effect" category among existing studies.</p>

  <p>Second, the question of whether parties matter for policy outcomes has generated sharply divided findings. Pettersson-Lidbom (2008) finds substantial left-right differences in Swedish local government spending, taxation, and unemployment. But Ferreira and Gyourko (2009), using an RDD on over 4,500 US mayoral elections, find zero effect of Democratic versus Republican mayors on city government size, spending, or crime rates, attributing the null result to Tiebout sorting. Lakomaa and Korpi (2012) challenge Pettersson-Lidbom's results using actual coalition data instead of assumed blocs, finding weak or no effects. More recently, Warshaw (2016) reports significant Democratic-Republican differences in municipal fiscal policy, while Riedel, Simmler, and Wittrock (2021) find German parties differ on spending composition but not total spending. Our null result on the DPP dummy (p = 0.771) aligns more closely with the Ferreira-Gyourko convergence finding than with the divergence literature.</p>

  <p>Third, within the Taiwan-specific political economy literature, Huang (2023) demonstrates that party alternation aggravates rather than mitigates local fiscal deficits, consistent with political budget cycle theory. Chang and Liu (2022) report that KMT mayors favor land expropriation and housing development while DPP mayors favor industrial land development approaches. The Political Business Cycle literature on Taiwan finds local budgets expand during election years regardless of which party governs — an opportunistic rather than partisan cycle. Our study extends this literature by applying quasi-experimental methods to the long-term rule question for the first time.</p>
</section>

<section>
  <h2>5. Limitations <span class="zh">（研究限制）</span></h2>

  <p>Several caveats apply. First, the absence of county-level GDP requires reliance on disposable income as a proxy; while standard in the literature, this measure captures household welfare rather than total economic output. Nighttime lights data would provide an independent validation source in future work. Second, Taiwan's small number of counties (~20) limits the quality of SCM counterfactuals and the statistical power of the panel FE model. The RDD extension would strengthen causal identification but faces its own power constraints in a small-N setting. Third, national-level confounds — particularly science park placements and infrastructure decisions — are major drivers of local economic outcomes that are only partially controlled by year fixed effects. Fourth, the analysis treats the party of the county executive as the relevant political variable, but county councils, township chiefs, and central government bureaucracies also shape local economic policy in ways not captured by this measure. Fifth, the 2010 special municipality reform and other boundary changes affect the continuity of county-level data; we address this by using growth rates and focusing on relative rather than absolute comparative metrics.</p>

  <p>Despite these limitations, the consistency of findings across multiple methods — SCM, panel FE, and descriptive analysis — provides reasonable confidence in the central conclusion that <strong>party identity is not the decisive factor in local economic development</strong>, and that structural economic integration matters far more than which party holds the county executive's office.</p>
</section>

<section>
  <h2>6. References <span class="zh">（參考文獻）</span></h2>

  <ol class="ref-list">
    <li>Abadie, A., &amp; Gardeazabal, J. (2003). The Economic Costs of Conflict: A Case Study of the Basque Country. <em>American Economic Review</em>, 93(1), 113–132.</li>
    <li>Abadie, A., Diamond, A., &amp; Hainmueller, J. (2010). Synthetic Control Methods for Comparative Case Studies. <em>Journal of the American Statistical Association</em>, 105(490), 493–505.</li>
    <li>Abadie, A., Diamond, A., &amp; Hainmueller, J. (2015). Comparative Politics and the Synthetic Control Method. <em>American Journal of Political Science</em>, 59(2), 495–510.</li>
    <li>Bracco, E., Porcelli, F., &amp; Redoano, M. (2015). Incumbent Effects and Partisan Alignment in Local Elections. CESifo Working Paper No. 4061.</li>
    <li>Brollo, F., &amp; Nannicini, T. (2012). Tying Your Enemy's Hands in Close Races. <em>American Political Science Review</em>, 106(4), 742–761.</li>
    <li>Brunnschweiler, C. N., &amp; Obeng, S. K. (2020). Rewarding Allegiance: Political Alignment and Fiscal Outcomes in Local Government. <em>UEA Working Paper</em>.</li>
    <li>Chang, T.-H. <span class="zh">章定煊</span> &amp; Liu, H.-L. <span class="zh">劉小蘭</span> (2022). Land Development and Local Politics in Taiwan <span class="zh">臺灣縣市的土地開發與地方政治</span>. <em>Academia Sinica</em>.</li>
    <li>Downs, A. (1957). <em>An Economic Theory of Democracy</em>. New York: Harper &amp; Row.</li>
    <li>Ferreira, F., &amp; Gyourko, J. (2009). Do Political Parties Matter? Evidence from U.S. Cities. <em>Quarterly Journal of Economics</em>, 124(1), 399–422.</li>
    <li>Hessami, Z. (2017). Political Alignment and Intergovernmental Transfers in Parliamentary Systems. <em>Public Choice</em>, 171(1–2).</li>
    <li>Huang, J.-T. <span class="zh">黃紀璇</span> (2023). Party Alternation and Fiscal Performance — Evidence from Taiwan's Local Government. <em>Journal of the Asia Pacific Economy</em>, 28(3).</li>
    <li>Huang, B.-H. <span class="zh">黃柄豪</span> (2016). The Impact of Local Government Spending on Economic Growth in Taiwan <span class="zh">台灣地方政府公共支出對經濟成長之影響</span>. <em>National Chengchi University Thesis</em>.</li>
    <li>Lakomaa, E., &amp; Korpi, M. (2012). Elections and Municipal Economic Outcomes — Sweden 1974–1994. <em>Ratio Working Paper No. 202</em>.</li>
    <li>Pettersson-Lidbom, P. (2008). Do Parties Matter for Economic Outcomes? <em>Journal of the European Economic Association</em>, 6(5), 1037–1056.</li>
    <li>Riedel, N., Simmler, M., &amp; Wittrock, C. (2021). Do Political Parties Matter? Evidence from German Municipalities. <em>German Economic Review</em>.</li>
    <li>Warshaw, C. (2016). Mayoral Partisanship and Municipal Fiscal Policy. <em>Journal of Politics</em>, 78(4).</li>
    <li>Political Business Cycles in Taiwan Local Fiscal Budget <span class="zh">台灣地方財政的政治景氣循環分析</span> (2006). <em>Soochow Journal of Political Science</em> <span class="zh">東吳政治學報</span>.</li>
  </ol>

  <p style="margin-top:14px; font-size:13px; color:var(--muted);">Data repositories: National Science and Technology Council (2025) <em>Southern Taiwan Science Park Annual Report</em>; Nantou County Government (2022) <em>Regional Balanced Development and Population Outmigration Countermeasures</em>; Hualien County Government (2013) <em>Analysis of Household Income and Expenditure</em>; DGBAS County Indicators (<code>winstacity.dgbas.gov.tw</code>); Taiwan Government Open Data Platform (<code>data.gov.tw</code>). Software: <code>Synth</code> R package (CRAN), Python <code>scipy.optimize</code> for SCM optimization.</p>
</section>

<footer>
  <p>Political Economy of Taiwan · May 2026</p>
</footer>

</div>
</body>
</html>'''

OUT.write_text(html, encoding='utf-8')
size_kb = len(html) / 1024
print(f"Report written: {OUT} ({size_kb:.0f} KB)")
