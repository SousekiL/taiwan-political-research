# Taiwan Local Party Economy Research

Two parallel empirical research packages on Taiwan local political economy. The main package is `taiwan_local_party_economy_study`; the published HTML report remains under `docs/` for GitHub Pages.

## Quick Start

Open the report directly in your browser (no download needed):

- **[View Report](https://sousekil.github.io/taiwan-political-research/)** ← GitHub Pages

Or clone the repo and open `docs/index.html` locally. The supplemental alignment report is available at `docs/party_alignment_report.html`.

## Methods

- **Main package:** case-focused dashboard, central-local party alignment models, event study, matched case comparisons, and long-run income-rank diagnostics.
- **Secondary package:** earlier SCM / panel FE report on long-term single-party rule, preserved as a parallel implementation.

## Data Sources

- DGBAS Household Income and Expenditure Survey (`每人可支配所得`, 1996–2024)
- Central Election Commission (`中央選舉委員會`) — county executive election results (1989–2022)
- DGBAS County Important Statistical Indicators (`縣市重要統計指標`)

## Key Finding

The main report finds mixed outcomes under long-term dominant-party local rule. Party label alone does not explain development performance; local economic structure, industrial geography, central-local alignment channels, and political competition all require separate interpretation.

## Project Structure

```
├── docs/
│   ├── index.html                        # Main published report from taiwan_local_party_economy_study
│   └── party_alignment_report.html       # Supplemental central-local alignment report
├── taiwan_local_party_economy_study/     # Main research package
│   ├── scripts/                          # Main data, model, chart, and report builders
│   ├── data/                             # Main raw/intermediate data
│   ├── outputs/                          # First-stage visualization outputs
│   └── study_outputs/                    # Main generated reports, figures, and model outputs
├── county_party_rule_panel_study/        # Secondary parallel package, previous main scheme
│   ├── index.html
│   ├── scripts/
│   ├── data/
│   └── results/
├── README.md                             # This file
├── PRINCIPLES.md                         # Full project standards & conventions
└── .gitignore
```

## Reproduction

Raw data can be obtained from the public sources listed above.

```bash
cd taiwan_local_party_economy_study
python3 scripts/run_party_alignment_study.py
python3 scripts/generate_html_report.py
python3 scripts/generate_case_focused_report.py
cp study_outputs/long_term_party_rule_case_report.html ../docs/index.html
cp study_outputs/party_alignment_report.html ../docs/party_alignment_report.html
```

## Author

Souseki Liu · May 2026
