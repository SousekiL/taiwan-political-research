# Taiwan Party Electorate Stack, 1996-2024

This subproject visualises Taiwan's party landscape as a vote-based allocation
of the eligible electorate. It uses people, not seats: every election event is
represented by party votes, invalid ballots, and nonvoters.

## Outputs

- `data/election_vote_events.csv`
- `outputs/electorate_allocation_annual_party_level.csv`
- `outputs/electorate_allocation_smoothed_party_level.csv`
- `outputs/electorate_allocation_annual_camp_level.csv`
- `outputs/electorate_allocation_smoothed_camp_level.csv`
- `outputs/taiwan_party_electorate_stack_party_level.png`
- `outputs/taiwan_party_electorate_stack_party_level.svg`
- `outputs/taiwan_party_electorate_stack_camp_level.png`
- `outputs/taiwan_party_electorate_stack_camp_level.svg`

## Method

Election tiers:

| Tier | Chinese | Weight |
|---|---|---:|
| Presidential | 總統直選 | 35% |
| Legislative | 立法委員 | 25% |
| County/city executive | 縣市首長 | 20% |
| County/city councilor | 縣市議員 | 20% |

For each year, the script uses an 8-year rolling window with a 4-year half-life.
The denominator is weighted eligible voters, so nonvoters remain visible in the
stacked chart.

## Party Buckets

Party-level chart:

- KMT: 中國國民黨, `#005BAC`
- DPP: 民主進步黨, `#1B9431`
- TPP: 台灣民眾黨, `#28C8C8`
- PFP: 親民黨, `#F39800`
- New Party: 新黨, `#FFD400`
- NPP: 時代力量, `#F6C100`
- TSU: 台灣團結聯盟, `#007A3D`
- Taiwan Statebuilding Party: 台灣基進, `#A00000`
- Other / independent: 其他／無黨籍, `#9CA3AF`
- Invalid ballots: 無效票, `#D1D5DB`
- Nonvoters: 政治冷感／未投票, `#E5E7EB`

Camp-level chart:

- Pan-blue: KMT + PFP + New Party
- Pan-green: DPP + TSU + NPP + Taiwan Statebuilding Party
- TPP remains separate
- Other / independent remains separate
- Invalid ballots and nonvoters remain separate

## Run

```bash
python3 scripts/build_data.py
python3 scripts/composite_index.py
MPLCONFIGDIR=/tmp MPLBACKEND=Agg python3 scripts/visualize.py
```

## Data Status

Presidential candidate totals use official or near-official public counts.
Legislative and local election vote totals are currently marked `estimated` in
`data/election_vote_events.csv`; replace them with candidate-level CEC exports
before using the chart as a fully official statistical product.
