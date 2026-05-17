# Vote-Based Electorate Allocation Methodology

## Overview

This project now measures party strength as a distribution of eligible voters,
not as seats won or KMT/DPP-only vote share. Each annual row answers:

> Out of all people eligible to vote, what share is allocated to each party,
> invalid ballots, and nonvoters?

## Election Tiers

| Tier | Chinese | Weight |
|---|---|---:|
| Presidential | 總統直選 | 35% |
| Legislative | 立法委員 | 25% |
| County/city executive | 縣市首長 | 20% |
| County/city councilor | 縣市議員 | 20% |

Council speakers (縣市議長) are excluded because voters do not directly elect
them.

## Event-Level Identity

For each election event:

```text
party votes + invalid ballots + nonvoters = eligible voters
```

where:

```text
nonvoters = eligible voters - ballots cast
```

Party buckets are KMT, DPP, TPP, PFP, New Party, NPP, TSU, Taiwan
Statebuilding Party, and other/independent.

## Annual Allocation

For each calendar year, all election events in the trailing 8-year window are
included. Each event receives:

```text
event weight = tier weight * 0.5 ** (event age / 4)
```

The annual share for each bucket is:

```text
weighted bucket votes / weighted eligible voters
```

This denominator includes nonvoters, so lower turnout becomes visible in the
stacked chart rather than being hidden.

## Camp Aggregation

Camp-level output is derived exactly from party-level output:

- Pan-blue 泛藍 = KMT + PFP + New Party
- Pan-green 泛綠 = DPP + TSU + NPP + Taiwan Statebuilding Party
- TPP remains separate
- Other/independent remains separate
- Invalid ballots and nonvoters remain separate

## Smoothing

The raw annual allocation is preserved. The chart uses a Gaussian-smoothed
version of annual shares, then renormalizes each year so all layers still sum
to exactly 100%.

## Data Quality

`data/election_vote_events.csv` contains a `data_quality` column. Presidential
candidate totals use official or near-official public counts. Legislative and
local election rows are currently marked `estimated` and should be replaced by
candidate-level CEC exports before publication as an official statistical
product.
