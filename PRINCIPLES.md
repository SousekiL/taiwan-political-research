# Project Principles & Standards

This document summarizes the data processing principles, visualization standards, report writing conventions, and other guidelines established throughout the project.

---

## I. Core Research Questions

| No. | Question | Description |
|------|------|------|
| **RQ0** | Is long-term single-party governance good or bad for local economic development? | Core question requiring a clear answer |
| **RQ1** | Does vertical alignment (same/different parties at central and local levels) affect local economic development? | Vertical Alignment Effect |
| **RQ2** | Do counties governed long-term by different parties show different economic development performance? | Horizontal Partisan Effect |

**Requirement for final answer**: Must provide a clear conclusion (good/bad), but may explain from multiple dimensions.

---

## II. Data Processing Principles

### 2.1 Time Range

| Item | Value |
|------|-----|
| Panel data span | **1990–2024** (Economic + Election panels) |
| Actual analysis window | **1996–2024** (Some county data missing before 1996) |
| Growth calculation baseline | 1996 → 2024 |

### 2.2 Core Variable Definitions

| Variable | Definition | Source |
|------|------|------|
| `per_capita_income` | Per capita disposable income (NTD) | 行政院主計總處 Household Income and Expenditure Survey |
| `log_income` | `ln(per_capita_income)` | Derived variable |
| `dpp_dummy` | =1 when local head is 民主進步黨 (DPP) | 中選會 Election Results |
| `kmt_dummy` | =1 when local head is 國民黨 (KMT) | 中選會 Election Results |
| `aligned` | =1 when local head party = Presidential party | Derived variable |
| `party_alternation` | =1 within 4 years after party alternation | Derived variable, referencing Huang (2023) |
| `excess_growth_pct` | County growth rate − National average growth rate (percentage points) | Derived |

### 2.3 Definition of Long-Term Single-Party Governance

- **Threshold**: ≥ **70%** (explicitly set by user)
- In 1996–2024 (29 years), a party governing ≥ 20.3 years → classified as that party's dominant county
- **11 counties meet the threshold** (excluding Kinmen and Lienchiang):

| County | Dominant Party | Percentage |
|------|---------|------|
| 屏東縣 | DPP | 100% |
| 花蓮縣 | KMT | 100% (includes 2009–2017 independent years, belongs to Pan-Blue camp) |
| 臺南市 | DPP | 97% |
| 新竹縣 | KMT | 83% |
| 嘉義縣 | DPP | 83% |
| 高雄市 | DPP | 79% |
| 南投縣 | KMT | 72% |
| 彰化縣 | KMT | 72% |
| 澎湖縣 | KMT | 72% |
| 臺中市 | KMT | 72% |
| 臺東縣 | KMT | 72% |

- **Counties not meeting threshold** (9 counties) labeled as MIXED, do not use blue/green colors

### 2.4 Special Handling

| Issue | Handling Method |
|------|---------|
| No county-level GDP in Taiwan | Proxy with per capita disposable income + unemployment rate + tax revenue and other multi-indicators |
| 2010 Five Municipalities merger and other administrative division changes | Add caveat in text, use growth rate instead of raw ranking for comparison |
| 花蓮縣 independent years (Fu Kun-chi 2009–2017) | Classified under KMT (belongs to Pan-Blue camp), no separate handling |
| Kinmen, Lienchiang | Excluded from analysis (special political ecology, limited data) |

### 2.5 Ranking Handling

- Rankings are for reference only (administrative division changes affect comparability)
- Core indicator changed to **excess growth rate relative to national average** (excess growth) instead of ranking

---

## III. Visualization Standards

### 3.1 Color System (Iron Rule)

| Meaning | Hex Code | Applicable Scenario |
|------|------|---------|
| **KMT (國民黨)** | `#0052A5` (Dark Blue) | Party identifier for KMT-dominant counties |
| **DPP (民主進步黨)** | `#1B9431` (Dark Green) | Party identifier for DPP-dominant counties |
| **MIXED / Non-dominant** | `#888888` or `#9ca3af` (Gray) | Counties not meeting 70% threshold |
| **Good (Positive conclusion)** | `#dcfce7` background / `#16a34a` text | Cases determined as "Good" |
| **Bad (Negative conclusion)** | `#fee2e2` background / `#dc2626` text | Cases determined as "Bad" |
| **Neutral** | `#eff6ff` (Blue) / `#fffbeb` (Yellow) | Modest +/− |

- **Absolutely prohibited**: MIXED (non-dominant) counties using blue or green colors
- **Code level**: All color assignments must have explicit `else` fallback, no bare ternary expressions allowed

### 3.2 Chinese Fonts

| Requirement | Value |
|------|-----|
| Font | **PingFang TC（蘋方 - 繁）** |
| Search path | `/System/Library/AssetsV2/com_apple_MobileAsset_Font8/.../PingFang.ttc` |
| matplotlib configuration | `plt.rcParams['font.sans-serif'] = ['PingFang TC', ...]` |
| Fallback fonts | `Arial Unicode MS`, `Helvetica` |

### 3.3 Chart Layout Standards

| Item | Standard |
|------|------|
| Minimum font size | **8pt** |
| Chart resolution | **150–200 DPI** |
| Embedding method | Base64 embedded in HTML (self-contained) |
| Image format | PNG (report embedding) + PDF (academic citation) |

### 3.4 Dashboard (Article Homepage Overview) Design Specifications

- Position: After cover, before §1
- Structure (left to right):
    1. County name
    2. Rule Mix: Dominant party name + percentage %
    3. Verdict: Colored label (Good/Bad/Modest)
    4. TW Growth Gap: Bar chart of growth gap relative to national average
    5. Income change (NTD 10k, 1996→2024)
    6. Unemployment rate (2019–2024 average)
    7. Population change (1996→2024 %)
    8. Political alignment (% years central = local)
- Only display cases ≥70%
- Alternating gray/white background per row for readability

### 3.5 Figures in §2–§3

| Figure No. | Position | Content |
|------|------|------|
| Figure 1 | §2 (Conclusion section) | Excess growth rate bar chart (20 counties) |
| Figure 2 | §3 (Method section) | Income trend charts for 8 key counties |
| Figure 3 | §3 (Method section) | SCM treatment effect chart |

---

## IV. Report Writing Standards

### 4.1 Language and Layout

| Requirement | Description |
|------|------|
| Primary language | **English** |
| Proper nouns | Annotate with **Traditional Chinese** (Taiwan Traditional Chinese) |
| Paragraph style | **Natural paragraphs**, avoid bullet points / excessive subheadings |
| Academic style | Rigorous, objective, concise |

### 4.2 Report Structure (6 Sections)

| No. | Section | Positioning |
|------|------|------|
| 1 | Background and Motivation | Research background, data source description, threshold definition |
| 2 | **Findings and Conclusions** | **Conclusions first** — Summary box + Core figure + Mechanism analysis |
| 3 | Data and Methods | Data source table + SCM + Panel FE description |
| 4 | Related Literature | Three-part literature review |
| 5 | Limitations | Research limitations |
| 6 | References | 17 references |

### 4.3 Political Neutrality Requirements (Iron Rule)

| Requirement | Implementation Method |
|------|---------|
| No bias toward any party | Symmetric case selection (KMT/DPP each with several cases), let data speak |
| Null hypothesis treated seriously | Explicitly state "The null hypothesis of no party effect is a valid and potentially correct answer" |
| Researcher positionality statement | Positionality Statement at end of §1 |
| Symmetric judgment criteria | Both parties evaluated using same indicators and thresholds |
| Language without bias | No preset stance like "certain party is better/worse" |

---

## V. Technical Implementation Standards

### 5.1 Analysis Scripts

| Script | Function | Language |
|------|------|------|
| `fetch_data.py` | Economic data collection | Python |
| `build_election_data.py` | Election data construction | Python |
| `run_analysis_v2.py` | SCM + Panel FE + All charts | Python |
| `make_dashboard.py` | Dashboard summary chart | Python |
| `make_summary_chart.py` | Figure 1 excess growth rate chart | Python |
| `build_final_report.py` | Assemble final HTML report | Python |
| `run_scm.R` | R version SCM (alternative) | R |

### 5.2 SCM Implementation Plan

| Component | Plan |
|------|------|
| Optimization method | `scipy.optimize.minimize` (SLSQP) |
| Constraints | weights ∈ [0,1], Σ weights = 1 |
| Objective function | minimise Σ (Y_treated − Y_synthetic)² |
| Post-processing | weights < 0.001 → set to zero → re-normalize |

### 5.3 Code Robustness Requirements

| Requirement | Description |
|------|------|
| Explicit else fallback | Color assignments cannot use bare ternary |
| Constants defined centrally | `THRESHOLD`, color codes, etc. placed at script top |
| Handle missing data | SCM skips counties with insufficient pre-treatment data |

---

## VI. Project File List

```
taiwan-political-research/
├── .gitignore
├── README.md
├── index.html                   # GitHub Pages entry (= final report version)
├── research-design-report.html  # Main report file
├── fetch_data.py                # Economic data collection
├── build_election_data.py       # Election data construction
├── run_analysis_v2.py           # Main analysis pipeline
├── make_dashboard.py            # Dashboard summary chart
├── make_summary_chart.py        # Figure 1 excess growth rate chart
├── build_final_report.py        # Report assembly
├── run_analysis.py              # Early version (kept for reference)
├── run_scm.R                    # R version SCM
├── data/                        # CSV panel data (.gitignore)
└── results/                     # Generated charts (.gitignore)
```

---

## VII. Key Lessons Learned

1. **Define threshold before analysis**: Filter cases only after 70% standard is clear, avoid post-hoc selection
2. **Color is signal**: Once chart color system is set, do not mix arbitrarily
3. **Conclusions first, methods later**: Academic report is not a method manual
4. **Ranking is not truth**: Administrative division changes can distort ranking signals
5. **Code needs defense**: else fallback is not optional, it is mandatory
