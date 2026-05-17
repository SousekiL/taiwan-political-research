#!/usr/bin/env python3
"""Render party-level and camp-level electorate allocation stack charts."""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
OUT_DIR = ROOT / "outputs"

PARTY_CSV = OUT_DIR / "electorate_allocation_smoothed_party_level.csv"
CAMP_CSV = OUT_DIR / "electorate_allocation_smoothed_camp_level.csv"
PARTY_RAW_CSV = OUT_DIR / "electorate_allocation_annual_party_level.csv"
CAMP_RAW_CSV = OUT_DIR / "electorate_allocation_annual_camp_level.csv"

PARTY_PNG = OUT_DIR / "taiwan_party_electorate_stack_party_level.png"
PARTY_SVG = OUT_DIR / "taiwan_party_electorate_stack_party_level.svg"
CAMP_PNG = OUT_DIR / "taiwan_party_electorate_stack_camp_level.png"
CAMP_SVG = OUT_DIR / "taiwan_party_electorate_stack_camp_level.svg"

FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
]

PARTY_LAYERS = [
    ("dpp_share", "DPP 民主進步黨", "#1B9431"),
    ("tsp_share", "Taiwan Statebuilding 台灣基進", "#A00000"),
    ("tsu_share", "TSU 台灣團結聯盟", "#007A3D"),
    ("npp_share", "NPP 時代力量", "#F6C100"),
    ("tpp_share", "TPP 台灣民眾黨", "#28C8C8"),
    ("other_share", "Other / Independent 其他／無黨籍", "#9CA3AF"),
    ("invalid_share", "Invalid ballots 無效票", "#D1D5DB"),
    ("nonvoters_share", "Nonvoters 政治冷感／未投票", "#E5E7EB"),
    ("pfp_share", "PFP 親民黨", "#F39800"),
    ("np_share", "New Party 新黨", "#FFD400"),
    ("kmt_share", "KMT 中國國民黨", "#005BAC"),
]

CAMP_LAYERS = [
    ("pan_green_share", "Pan-Green 泛綠", "#1B9431"),
    ("tpp_share", "TPP / Third Force 民眾黨／第三勢力", "#28C8C8"),
    ("other_share", "Other / Independent 其他／無黨籍", "#9CA3AF"),
    ("invalid_share", "Invalid ballots 無效票", "#D1D5DB"),
    ("nonvoters_share", "Nonvoters 政治冷感／未投票", "#E5E7EB"),
    ("pan_blue_share", "Pan-Blue 泛藍", "#005BAC"),
]

EVENT_YEARS = [2000, 2008, 2014, 2016, 2020, 2022, 2024]
EVENT_LABELS = {
    2000: "2000\nFirst DPP win\n首次政黨輪替",
    2008: "2008\nKMT returns\n國民黨重新執政",
    2014: "2014\nSunflower shift\n太陽花後地方變局",
    2016: "2016\nDPP unified gov.\n民進黨完全執政",
    2020: "2020\nTsai re-election\n蔡英文連任",
    2022: "2022\nKMT local rebound\n國民黨地方反彈",
    2024: "2024\nThree-way race\n三腳督總統選舉",
}
EVENT_LABEL_OFFSETS = {
    2020: -0.15,
    2022: 0.0,
    2024: 0.15,
}


def configure_font() -> None:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            prop = fm.FontProperties(fname=path)
            plt.rcParams["font.family"] = prop.get_name()
            break
    else:
        plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "PingFang TC", "sans-serif"]
    plt.rcParams["axes.unicode_minus"] = False


def percent_axis(value: float, _pos: int) -> str:
    return f"{value:.0%}"


def render_stack(
    df: pd.DataFrame,
    raw_df: pd.DataFrame,
    layers: list[tuple[str, str, str]],
    title: str,
    subtitle: str,
    annotation_kind: str,
    out_png: Path,
    out_svg: Path,
) -> None:
    years = df["year"].to_numpy()
    cols = [col for col, _label, _color in layers]
    labels = [label for _col, label, _color in layers]
    colors = [color for _col, _label, color in layers]
    values = [df[col].to_numpy() for col in cols]

    fig, ax = plt.subplots(figsize=(19, 9.5))
    ax.stackplot(years, values, labels=labels, colors=colors, linewidth=0.35, edgecolor="white")

    ax.set_xlim(1996, 2024)
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(FuncFormatter(percent_axis))
    ax.set_yticks([i / 10 for i in range(0, 11)])
    ax.set_xticks(list(range(1996, 2025, 4)))
    ax.grid(axis="y", color="#E5E7EB", linewidth=0.8, alpha=0.8)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#D1D5DB")
    ax.spines["bottom"].set_color("#D1D5DB")

    fig.text(0.065, 0.975, title, ha="left", va="top", fontsize=18, fontweight="bold", color="#111827")
    fig.text(0.065, 0.945, subtitle, ha="left", va="top", fontsize=10, color="#4B5563")
    ax.set_ylabel("Share of eligible voters 合格選民比例", fontsize=11, color="#374151")

    add_event_axis_labels(ax)
    add_blue_green_value_labels(ax, raw_df, annotation_kind)

    ax.legend(
        loc="center left",
        bbox_to_anchor=(1.01, 0.5),
        frameon=False,
        fontsize=9,
        title="Layer 圖層",
        title_fontsize=10,
    )

    fig.text(
        0.01,
        0.01,
        "Source: CEC election data structure; estimated rows are marked in data/election_vote_events.csv. "
        "Method: 8-year rolling allocation, 4-year half-life, denominator includes eligible nonvoters.",
        fontsize=8,
        color="#6B7280",
    )

    plt.tight_layout(rect=(0, 0.09, 0.84, 0.875))
    fig.savefig(out_png, dpi=300, facecolor="white")
    fig.savefig(out_svg, facecolor="white")
    plt.close(fig)


def event_label_text(year: int) -> str:
    return EVENT_LABELS[year]


def add_event_axis_labels(ax) -> None:
    top = True
    for year in EVENT_YEARS:
        ax.axvline(year, color="#6B7280", linewidth=0.7, alpha=0.35)
        label_x = year + EVENT_LABEL_OFFSETS.get(year, 0.0)
        label_y = 1.035 if top else -0.105
        valign = "bottom" if top else "top"
        ax.text(
            label_x,
            label_y,
            event_label_text(year),
            transform=ax.get_xaxis_transform(),
            ha="center",
            va=valign,
            fontsize=7.2,
            linespacing=1.12,
            color="#374151",
            bbox={
                "boxstyle": "round,pad=0.28",
                "facecolor": "white",
                "edgecolor": "#D1D5DB",
                "linewidth": 0.7,
                "alpha": 0.92,
            },
            zorder=10,
        )
        top = not top


def add_blue_green_value_labels(ax, raw_df: pd.DataFrame, annotation_kind: str) -> None:
    for year in EVENT_YEARS:
        match = raw_df.loc[raw_df["year"].eq(year)]
        if match.empty:
            continue

        row = match.iloc[0]
        label_x = year + EVENT_LABEL_OFFSETS.get(year, 0.0)
        if annotation_kind == "party":
            blue_label = f"KMT {row['kmt_share']:.1%}"
            green_label = f"DPP {row['dpp_share']:.1%}"
            blue_share = float(row["kmt_share"])
            green_share = float(row["dpp_share"])
        else:
            blue_label = f"Blue {row['pan_blue_share']:.1%}"
            green_label = f"Green {row['pan_green_share']:.1%}"
            blue_share = float(row["pan_blue_share"])
            green_share = float(row["pan_green_share"])

        add_value_tag(ax, label_x, 1 - blue_share / 2, blue_label, "#005BAC")
        add_value_tag(ax, label_x, green_share / 2, green_label, "#1B9431")


def add_value_tag(ax, x: float, y: float, label: str, color: str) -> None:
    ax.text(
        x,
        y,
        label,
        ha="center",
        va="center",
        fontsize=7.4,
        color=color,
        fontweight="bold",
        bbox={
            "boxstyle": "round,pad=0.22",
            "facecolor": "white",
            "edgecolor": color,
            "linewidth": 0.8,
            "alpha": 0.88,
        },
        zorder=11,
    )


def main() -> None:
    configure_font()
    party = pd.read_csv(PARTY_CSV, encoding="utf-8-sig")
    camp = pd.read_csv(CAMP_CSV, encoding="utf-8-sig")
    party_raw = pd.read_csv(PARTY_RAW_CSV, encoding="utf-8-sig")
    camp_raw = pd.read_csv(CAMP_RAW_CSV, encoding="utf-8-sig")

    render_stack(
        party,
        party_raw,
        PARTY_LAYERS,
        "Taiwan Electorate Allocation by Party, 1996-2024",
        "台灣合格選民分布：政黨層級；綠營在下緣、藍營在上緣；標註值使用未平滑年度資料",
        "party",
        PARTY_PNG,
        PARTY_SVG,
    )
    render_stack(
        camp,
        camp_raw,
        CAMP_LAYERS,
        "Taiwan Electorate Allocation by Political Camp, 1996-2024",
        "台灣合格選民分布：泛綠在下緣、泛藍在上緣；標註值使用未平滑年度資料",
        "camp",
        CAMP_PNG,
        CAMP_SVG,
    )

    print(f"Saved party chart: {PARTY_PNG}")
    print(f"Saved camp chart:  {CAMP_PNG}")


if __name__ == "__main__":
    main()
