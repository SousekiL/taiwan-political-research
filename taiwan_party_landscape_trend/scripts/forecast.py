#!/usr/bin/env python3
"""Generate an 8-year trend projection chart for camp-level electorate shares."""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
OUT_DIR = ROOT / "outputs"

INPUT_CSV = OUT_DIR / "electorate_allocation_smoothed_camp_level.csv"
FORECAST_CSV = OUT_DIR / "electorate_allocation_forecast_camp_level.csv"
FORECAST_PNG = OUT_DIR / "taiwan_party_electorate_stack_camp_forecast.png"
FORECAST_SVG = OUT_DIR / "taiwan_party_electorate_stack_camp_forecast.svg"

HISTORY_START = 1996
HISTORY_END = 2024
FORECAST_END = 2032
TREND_START = 2016

FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
]

LAYERS = [
    ("pan_green_share", "Pan-Green 泛綠", "#1B9431"),
    ("tpp_share", "TPP / Third Force 民眾黨／第三勢力", "#28C8C8"),
    ("other_share", "Other / Independent 其他／無黨籍", "#9CA3AF"),
    ("invalid_share", "Invalid ballots 無效票", "#D1D5DB"),
    ("nonvoters_share", "Nonvoters 政治冷感／未投票", "#E5E7EB"),
    ("pan_blue_share", "Pan-Blue 泛藍", "#005BAC"),
]


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


def project_share(history: pd.DataFrame, col: str, forecast_years: np.ndarray) -> np.ndarray:
    trend = history.loc[history["year"].between(TREND_START, HISTORY_END), ["year", col]]
    slope, intercept = np.polyfit(trend["year"].to_numpy(), trend[col].to_numpy(), 1)
    projected = slope * forecast_years + intercept
    return np.clip(projected, 0, 1)


def build_forecast() -> pd.DataFrame:
    history = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")
    share_cols = [col for col, _label, _color in LAYERS]
    forecast_years = np.arange(HISTORY_END + 1, FORECAST_END + 1)

    rows = []
    for year, values in zip(
        forecast_years,
        np.column_stack([project_share(history, col, forecast_years) for col in share_cols]),
    ):
        values = np.clip(values, 0, None)
        values = values / values.sum()
        row = {
            "year": int(year),
            "series_type": "forecast",
            "method": f"linear trend from {TREND_START}-{HISTORY_END}, renormalized",
        }
        row.update({col: value for col, value in zip(share_cols, values)})
        rows.append(row)

    historical = history[["year", *share_cols]].copy()
    historical["series_type"] = "historical"
    historical["method"] = "8-year rolling allocation, smoothed"
    historical = historical[["year", "series_type", "method", *share_cols]]

    forecast = pd.DataFrame(rows)[["year", "series_type", "method", *share_cols]]
    combined = pd.concat([historical, forecast], ignore_index=True)
    validate(combined, share_cols)
    combined.to_csv(FORECAST_CSV, index=False, encoding="utf-8-sig")
    return combined


def validate(df: pd.DataFrame, share_cols: list[str]) -> None:
    sums = df[share_cols].sum(axis=1)
    if not np.allclose(sums, 1.0, atol=1e-9):
        raise ValueError("forecast shares do not sum to 1.0")
    if (df[share_cols] < 0).any().any():
        raise ValueError("negative forecast share found")


def render(df: pd.DataFrame) -> None:
    years = df["year"].to_numpy()
    cols = [col for col, _label, _color in LAYERS]
    labels = [label for _col, label, _color in LAYERS]
    colors = [color for _col, _label, color in LAYERS]
    values = [df[col].to_numpy() for col in cols]

    fig, ax = plt.subplots(figsize=(19, 9.5))
    ax.axvspan(HISTORY_END, FORECAST_END, color="#F9FAFB", zorder=0)
    ax.stackplot(years, values, labels=labels, colors=colors, linewidth=0.35, edgecolor="white")
    ax.axvline(HISTORY_END, color="#111827", linewidth=1.0, linestyle="--", alpha=0.7)
    ax.text(
        HISTORY_END + 0.25,
        0.97,
        "Projection begins\n預測起點",
        ha="left",
        va="top",
        fontsize=9,
        color="#111827",
        bbox={"boxstyle": "round,pad=0.28", "facecolor": "white", "edgecolor": "#D1D5DB"},
    )

    ax.set_xlim(HISTORY_START, FORECAST_END)
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(FuncFormatter(percent_axis))
    ax.set_yticks([i / 10 for i in range(0, 11)])
    ax.set_xticks(list(range(HISTORY_START, FORECAST_END + 1, 4)))
    ax.grid(axis="y", color="#E5E7EB", linewidth=0.8, alpha=0.8)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#D1D5DB")
    ax.spines["bottom"].set_color("#D1D5DB")
    ax.set_ylabel("Share of eligible voters 合格選民比例", fontsize=11, color="#374151")

    fig.text(
        0.065,
        0.975,
        "Taiwan Electorate Allocation by Political Camp, 1996-2032 Trend Projection",
        ha="left",
        va="top",
        fontsize=18,
        fontweight="bold",
        color="#111827",
    )
    fig.text(
        0.065,
        0.945,
        "2025-2032 is a mechanical trend projection from 2016-2024, not a polling forecast",
        ha="left",
        va="top",
        fontsize=10,
        color="#4B5563",
    )

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
        "Historical method: 8-year rolling allocation, 4-year half-life. "
        "Projection method: linear trend by layer from 2016-2024, clipped and renormalized to 100%.",
        fontsize=8,
        color="#6B7280",
    )

    plt.tight_layout(rect=(0, 0.06, 0.84, 0.89))
    fig.savefig(FORECAST_PNG, dpi=300, facecolor="white")
    fig.savefig(FORECAST_SVG, facecolor="white")
    plt.close(fig)


def main() -> None:
    configure_font()
    df = build_forecast()
    render(df)
    print(f"Saved forecast CSV:   {FORECAST_CSV}")
    print(f"Saved forecast chart: {FORECAST_PNG}")


if __name__ == "__main__":
    main()
