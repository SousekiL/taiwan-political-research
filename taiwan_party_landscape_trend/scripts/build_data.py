#!/usr/bin/env python3
"""
Build vote-based Taiwan election event data.

The project uses eligible voters as the denominator. Every row must satisfy:

party votes + invalid ballots + nonvoters = eligible voters

Older legislative and local totals are marked as estimated until replaced by
candidate-level Central Election Commission exports.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

OUT_CSV = DATA_DIR / "election_vote_events.csv"
LEGACY_CSV = DATA_DIR / "unified_election_panel.csv"

PARTY_COLS = [
    "kmt_votes",
    "dpp_votes",
    "tpp_votes",
    "pfp_votes",
    "np_votes",
    "npp_votes",
    "tsu_votes",
    "tsp_votes",
    "other_votes",
]


def event(
    election_year: int,
    election_tier: str,
    eligible_voters: int,
    ballots_cast: int,
    invalid_votes: int,
    data_quality: str,
    note: str = "",
    **party_votes: int,
) -> dict:
    valid_votes = ballots_cast - invalid_votes
    if valid_votes < 0:
        raise ValueError(f"{election_year} {election_tier}: invalid_votes exceeds ballots_cast")

    row = {
        "election_year": election_year,
        "election_tier": election_tier,
        "eligible_voters": eligible_voters,
        "ballots_cast": ballots_cast,
        "valid_votes": valid_votes,
        "invalid_votes": invalid_votes,
        "data_quality": data_quality,
        "note": note,
    }
    for col in PARTY_COLS:
        row[col] = int(party_votes.get(col, 0))

    specified_votes = sum(row[col] for col in PARTY_COLS if col != "other_votes")
    row["other_votes"] = valid_votes - specified_votes
    if row["other_votes"] < 0:
        raise ValueError(
            f"{election_year} {election_tier}: named party votes exceed valid votes"
        )

    row["nonvoters"] = eligible_voters - ballots_cast
    if row["nonvoters"] < 0:
        raise ValueError(f"{election_year} {election_tier}: ballots_cast exceeds eligible_voters")
    return row


def build_events() -> pd.DataFrame:
    rows = [
        # Presidential elections. Candidate vote counts are official or near-official;
        # eligible/invalid totals should be revalidated against CEC before publication.
        event(1996, "presidential", 14_313_288, 10_046_802, 885_412, "official_candidate_estimated_turnout", kmt_votes=5_813_699, dpp_votes=2_274_586),
        event(2000, "presidential", 15_462_625, 12_786_671, 122_278, "official_candidate_estimated_turnout", kmt_votes=2_925_513, dpp_votes=4_977_697, pfp_votes=4_664_932),
        event(2004, "presidential", 16_507_179, 13_129_722, 215_300, "official_candidate_estimated_turnout", kmt_votes=6_442_452, dpp_votes=6_471_970),
        event(2008, "presidential", 17_321_622, 13_221_609, 117_646, "official_candidate_estimated_turnout", kmt_votes=7_659_014, dpp_votes=5_444_949),
        event(2012, "presidential", 18_086_455, 13_452_016, 97_711, "official_candidate_estimated_turnout", kmt_votes=6_891_139, dpp_votes=6_093_578, pfp_votes=369_588),
        event(2016, "presidential", 18_782_991, 12_448_302, 163_332, "official_candidate_estimated_turnout", kmt_votes=3_813_365, dpp_votes=6_894_744, pfp_votes=1_576_861),
        event(2020, "presidential", 19_311_105, 14_464_571, 163_631, "official_candidate_estimated_turnout", kmt_votes=5_522_119, dpp_votes=8_170_231, pfp_votes=608_590),
        event(2024, "presidential", 19_548_531, 14_047_972, 100_804, "official_candidate_estimated_turnout", kmt_votes=4_671_021, dpp_votes=5_586_019, tpp_votes=3_690_128),

        # Legislative regional candidate votes, aggregated to party buckets.
        event(1998, "legislative", 14_961_938, 10_286_000, 160_000, "estimated", kmt_votes=4_150_000, dpp_votes=2_966_000, np_votes=350_000),
        event(2001, "legislative", 15_312_846, 10_243_000, 170_000, "estimated", kmt_votes=2_900_000, dpp_votes=3_600_000, pfp_votes=1_900_000, tsu_votes=700_000),
        event(2004, "legislative", 16_559_254, 10_706_000, 160_000, "estimated", kmt_votes=3_200_000, dpp_votes=3_500_000, pfp_votes=1_200_000, tsu_votes=850_000, np_votes=120_000),
        event(2008, "legislative", 17_288_551, 10_180_000, 150_000, "estimated", kmt_votes=5_010_801, dpp_votes=3_610_106, pfp_votes=70_000, tsu_votes=260_000),
        event(2012, "legislative", 18_086_455, 12_080_000, 155_000, "estimated", kmt_votes=4_871_651, dpp_votes=4_556_424, pfp_votes=210_000, tsu_votes=420_000, np_votes=95_000),
        event(2016, "legislative", 18_782_991, 12_030_000, 170_000, "estimated", kmt_votes=3_280_000, dpp_votes=5_370_000, npp_votes=350_000, tpp_votes=0, tsu_votes=120_000, tsp_votes=75_000),
        event(2020, "legislative", 19_312_105, 14_100_000, 170_000, "estimated", kmt_votes=4_720_000, dpp_votes=6_570_000, npp_votes=230_000, tpp_votes=190_000, tsp_votes=140_000),
        event(2024, "legislative", 19_548_531, 13_850_000, 165_000, "estimated", kmt_votes=5_070_000, dpp_votes=4_820_000, tpp_votes=500_000, npp_votes=120_000, tsp_votes=90_000),

        # County/city executive elections, aggregated across jurisdictions.
        event(1997, "local_executive", 14_850_000, 9_250_000, 170_000, "estimated", kmt_votes=3_500_000, dpp_votes=4_500_000, np_votes=250_000),
        event(2001, "local_executive", 15_700_000, 10_050_000, 180_000, "estimated", kmt_votes=4_000_000, dpp_votes=4_800_000, pfp_votes=280_000),
        event(2005, "local_executive", 16_500_000, 10_650_000, 180_000, "estimated", kmt_votes=6_500_000, dpp_votes=3_500_000, pfp_votes=120_000),
        event(2009, "local_executive", 17_200_000, 10_600_000, 170_000, "estimated", kmt_votes=6_800_000, dpp_votes=3_200_000),
        event(2014, "local_executive", 18_500_000, 12_100_000, 190_000, "estimated", kmt_votes=3_500_000, dpp_votes=5_500_000, np_votes=120_000),
        event(2018, "local_executive", 19_100_000, 12_400_000, 190_000, "estimated", kmt_votes=5_800_000, dpp_votes=3_800_000, tpp_votes=580_000),
        event(2022, "local_executive", 19_300_000, 11_550_000, 180_000, "estimated", kmt_votes=5_200_000, dpp_votes=3_800_000, tpp_votes=400_000),

        # County/city councilor elections, candidate votes aggregated by party.
        event(1998, "county_councilor", 14_950_000, 9_850_000, 150_000, "estimated", kmt_votes=4_950_000, dpp_votes=1_750_000, np_votes=300_000),
        event(2002, "county_councilor", 15_900_000, 10_150_000, 160_000, "estimated", kmt_votes=4_300_000, dpp_votes=2_250_000, pfp_votes=750_000, tsu_votes=250_000),
        event(2005, "county_councilor", 16_500_000, 10_500_000, 160_000, "estimated", kmt_votes=4_600_000, dpp_votes=2_350_000, pfp_votes=500_000, tsu_votes=220_000),
        event(2009, "county_councilor", 17_200_000, 10_350_000, 155_000, "estimated", kmt_votes=4_550_000, dpp_votes=2_600_000, pfp_votes=260_000, tsu_votes=160_000),
        event(2014, "county_councilor", 18_500_000, 11_900_000, 170_000, "estimated", kmt_votes=4_000_000, dpp_votes=3_450_000, npp_votes=0, tsp_votes=60_000),
        event(2018, "county_councilor", 19_100_000, 12_250_000, 180_000, "estimated", kmt_votes=4_400_000, dpp_votes=3_200_000, npp_votes=280_000, tpp_votes=180_000, tsp_votes=120_000),
        event(2022, "county_councilor", 19_300_000, 11_600_000, 175_000, "estimated", kmt_votes=4_200_000, dpp_votes=3_000_000, tpp_votes=620_000, npp_votes=190_000, tsp_votes=150_000),
    ]

    df = pd.DataFrame(rows)
    ordered_cols = [
        "election_year",
        "election_tier",
        "eligible_voters",
        "ballots_cast",
        "valid_votes",
        "invalid_votes",
        *PARTY_COLS,
        "nonvoters",
        "data_quality",
        "note",
    ]
    df = df[ordered_cols].sort_values(["election_year", "election_tier"]).reset_index(drop=True)
    validate_events(df)
    return df


def validate_events(df: pd.DataFrame) -> None:
    allocation_cols = PARTY_COLS + ["invalid_votes", "nonvoters"]
    totals = df[allocation_cols].sum(axis=1)
    bad = df.loc[totals != df["eligible_voters"], ["election_year", "election_tier"]]
    if not bad.empty:
        raise ValueError(f"event allocation does not sum to eligible voters:\n{bad}")
    if (df[allocation_cols] < 0).any().any():
        raise ValueError("negative votes found")


def main() -> None:
    df = build_events()
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    # Keep the old path populated so older notebooks do not silently read stale data.
    df.to_csv(LEGACY_CSV, index=False, encoding="utf-8-sig")
    print(f"Saved vote events: {OUT_CSV} ({len(df)} rows)")
    print(df.groupby(["election_tier", "data_quality"]).size().to_string())


if __name__ == "__main__":
    main()
