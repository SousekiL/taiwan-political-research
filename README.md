# Long-Term Party Rule and Local Economic Development in Taiwan

A multi-method empirical study examining whether long-term single-party rule (≥70% of 1996–2024) affects county-level economic outcomes in Taiwan.

## Quick Start

Open `index.html` in any browser — a self-contained academic report with embedded charts.

## Methods

- **Synthetic Control Method** (SCM) — primary identification strategy
- **Panel Fixed Effects** regression (county + year FE)
- **Regression Discontinuity Design** — outlined for planned extension

## Data Sources

- DGBAS Household Income and Expenditure Survey (`每人可支配所得`, 1996–2024)
- Central Election Commission (`中央選舉委員會`) — county executive election results (1989–2022)
- DGBAS County Important Statistical Indicators (`縣市重要統計指標`)

## Key Finding

Party identity (DPP vs. KMT) has **no statistically significant effect** on county income levels (p = 0.77). Both parties have clear success cases and clear failure cases. The only political variable that consistently predicts better outcomes is **party alternation** (p = 0.046). Economic geography and connection to semiconductor supply chains are the dominant forces.

## Project Structure

```
├── index.html                          # Self-contained report (open in browser)
├── research-design-report.html         # Same as index.html (mirror)
├── README.md                           # This file
├── PRINCIPLES.md                       # Full project standards & conventions
├── .gitignore
├── scripts/                            # All analysis scripts
│   ├── fetch_data.py                   # Build economic panel from DGBAS data
│   ├── build_election_data.py          # Build election panel from CEC data
│   ├── run_analysis_v2.py              # SCM + panel FE + all figures
│   ├── run_analysis.py                 # Earlier analysis version (reference)
│   ├── make_dashboard.py               # Summary dashboard chart (report § header)
│   ├── make_summary_chart.py           # Figure 1: excess growth bar chart
│   ├── build_final_report.py           # Assemble final HTML report
│   └── run_scm.R                       # R-based SCM implementation (alternative)
├── data/                               # CSV panel data (not tracked)
│   ├── county_economic_panel.csv       # Economic indicators 1990–2024
│   ├── county_election_panel.csv       # Party affiliations 1990–2024
│   └── merged_panel.csv                # Merged analysis panel
└── results/                            # Generated figures & tables (not tracked)
    ├── dashboard.png / .pdf            # Summary dashboard
    ├── summary_conclusion.png / .pdf   # Figure 1: excess growth
    ├── income_trajectories.png / .pdf  # Figure 2: income paths
    ├── scm_effects_1996.png / .pdf     # Figure 3: SCM treatment effects
    ├── *.csv                           # Output data tables
    └── *.json                          # Analysis summary stats
```

## Reproduction

Raw data can be obtained from the public sources listed above. The generated `data/` and `results/` directories are excluded from version control.

```bash
cd scripts
python3 fetch_data.py             # build economic panel
python3 build_election_data.py    # build election panel
python3 run_analysis_v2.py        # SCM + panel FE + all charts
python3 make_dashboard.py         # summary dashboard chart
python3 build_final_report.py     # assemble final HTML report (requires charts)
```

## Author

Souseki Liu · May 2026
