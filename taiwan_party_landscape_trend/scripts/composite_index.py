#!/usr/bin/env python3
"""
Compute annual electorate allocation from vote-based election events.

The output is a set of annual 0-1 shares over eligible voters, with an 8-year
rolling window and a 4-year half-life.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "outputs"
OUT_DIR.mkdir(exist_ok=True)

EVENTS_CSV = DATA_DIR / "election_vote_events.csv"

PARTY_LEVEL_CSV = OUT_DIR / "electorate_allocation_annual_party_level.csv"
PARTY_SMOOTH_CSV = OUT_DIR / "electorate_allocation_smoothed_party_level.csv"
CAMP_LEVEL_CSV = OUT_DIR / "electorate_allocation_annual_camp_level.csv"
CAMP_SMOOTH_CSV = OUT_DIR / "electorate_allocation_smoothed_camp_level.csv"

WINDOW_YEARS = 8
HALF_LIFE_YEARS = 4
START_YEAR = 1996
END_YEAR = 2024

TIER_WEIGHTS = {
    "presidential": 0.35,
    "legislative": 0.25,
    "local_executive": 0.20,
    "county_councilor": 0.20,
}

PARTY_COLS = [
    "nonvoters",
    "invalid_votes",
    "other_votes",
    "tsp_votes",
    "tsu_votes",
    "npp_votes",
    "np_votes",
    "pfp_votes",
    "tpp_votes",
    "kmt_votes",
    "dpp_votes",
]

CAMP_MAP = {
    "nonvoters": ["nonvoters"],
    "invalid_votes": ["invalid_votes"],
    "other_votes": ["other_votes"],
    "tpp_votes": ["tpp_votes"],
    "pan_blue_votes": ["kmt_votes", "pfp_votes", "np_votes"],
    "pan_green_votes": ["dpp_votes", "tsu_votes", "npp_votes", "tsp_votes"],
}


def share_col(vote_col: str) -> str:
    if vote_col == "nonvoters":
        return "nonvoters_share"
    return vote_col.replace("_votes", "_share")


def load_events() -> pd.DataFrame:
    return pd.read_csv(EVENTS_CSV, encoding="utf-8-sig")


def event_weight(year: int, event_year: int, tier: str) -> float:
    age = year - event_year
    if age < 0 or age > WINDOW_YEARS:
        return 0.0
    return TIER_WEIGHTS[tier] * (0.5 ** (age / HALF_LIFE_YEARS))


def annual_party_allocation(events: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year in range(START_YEAR, END_YEAR + 1):
        weighted = {col: 0.0 for col in PARTY_COLS}
        denom = 0.0
        weight_total = 0.0
        included = []

        for _, event in events.iterrows():
            weight = event_weight(year, int(event["election_year"]), event["election_tier"])
            if weight == 0:
                continue
            denom += float(event["eligible_voters"]) * weight
            weight_total += weight
            included.append(f"{event['election_tier']}:{int(event['election_year'])}")
            for col in PARTY_COLS:
                weighted[col] += float(event[col]) * weight

        if denom == 0:
            continue

        row = {
            "year": year,
            "weighted_eligible_voters": denom,
            "total_event_weight": weight_total,
            "included_events": ";".join(included),
        }
        for col in PARTY_COLS:
            row[share_col(col)] = weighted[col] / denom
        rows.append(row)

    df = pd.DataFrame(rows)
    validate_annual(df, [share_col(col) for col in PARTY_COLS])
    return df


def camp_allocation(party_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in party_df.iterrows():
        out = {
            "year": row["year"],
            "weighted_eligible_voters": row["weighted_eligible_voters"],
            "total_event_weight": row["total_event_weight"],
            "included_events": row["included_events"],
        }
        for camp, cols in CAMP_MAP.items():
            out[share_col(camp)] = sum(row[share_col(col)] for col in cols)
        rows.append(out)
    df = pd.DataFrame(rows)
    validate_annual(df, [share_col(col) for col in CAMP_MAP])
    return df


def smooth_shares(df: pd.DataFrame, share_cols: list[str]) -> pd.DataFrame:
    try:
        from scipy.ndimage import gaussian_filter1d

        out = df.copy()
        for col in share_cols:
            out[col] = gaussian_filter1d(out[col].to_numpy(dtype=float), sigma=1.1, mode="nearest")
    except Exception:
        out = df.copy()
        out[share_cols] = out[share_cols].rolling(window=3, center=True, min_periods=1).mean()

    out[share_cols] = out[share_cols].clip(lower=0)
    row_sums = out[share_cols].sum(axis=1)
    out[share_cols] = out[share_cols].div(row_sums, axis=0)
    validate_annual(out, share_cols)
    return out


def validate_annual(df: pd.DataFrame, share_cols: list[str]) -> None:
    sums = df[share_cols].sum(axis=1)
    if not np.allclose(sums, 1.0, atol=1e-9):
        raise ValueError("annual shares do not sum to 1.0")
    if (df[share_cols] < -1e-12).any().any():
        raise ValueError("negative annual share found")


def main() -> None:
    events = load_events()
    party = annual_party_allocation(events)
    party.to_csv(PARTY_LEVEL_CSV, index=False, encoding="utf-8-sig")

    party_share_cols = [share_col(col) for col in PARTY_COLS]
    party_smooth = smooth_shares(party, party_share_cols)
    party_smooth.to_csv(PARTY_SMOOTH_CSV, index=False, encoding="utf-8-sig")

    camp = camp_allocation(party)
    camp.to_csv(CAMP_LEVEL_CSV, index=False, encoding="utf-8-sig")

    camp_share_cols = [share_col(col) for col in CAMP_MAP]
    camp_smooth = smooth_shares(camp, camp_share_cols)
    camp_smooth.to_csv(CAMP_SMOOTH_CSV, index=False, encoding="utf-8-sig")

    print(f"Saved party allocation: {PARTY_LEVEL_CSV}")
    print(f"Saved party smoothed:   {PARTY_SMOOTH_CSV}")
    print(f"Saved camp allocation:  {CAMP_LEVEL_CSV}")
    print(f"Saved camp smoothed:    {CAMP_SMOOTH_CSV}")


if __name__ == "__main__":
    main()
