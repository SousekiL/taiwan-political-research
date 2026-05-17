# Long-Term Party Rule and Local Economic Development in Taiwan

A multi-method empirical study examining whether long-term single-party rule (≥70% of 1996–2024) affects county-level economic outcomes in Taiwan.

## Quick Start

Open `research-design-report.html` in any browser — a self-contained academic report with embedded charts.

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

## Reproduction

See the analysis scripts in this repo. Raw data can be obtained from the public sources listed above.

```
python3 build_election_data.py   # build election panel
python3 fetch_data.py            # build economic panel
python3 run_analysis_v2.py       # SCM + panel FE + all charts
python3 make_dashboard.py        # summary dashboard chart
python3 build_final_report.py    # assemble final HTML report
```

## Author

Souseki Liu · May 2026
