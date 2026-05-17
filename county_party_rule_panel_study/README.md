# County Party Rule Panel Study

This is the secondary parallel research package. It preserves the earlier SCM / panel fixed-effects implementation and its original published HTML report as `index.html`.

The main project report now comes from `../taiwan_local_party_economy_study/` and is published through `../docs/index.html`.

## Reproduction

```bash
cd county_party_rule_panel_study/scripts
python3 fetch_data.py
python3 build_election_data.py
python3 run_analysis_v2.py
python3 make_dashboard.py
```
