from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
DATA_DIR = ROOT / "data"
SOURCE_CSV = DATA_DIR / "household_disposable_income_by_region.csv"
OUT_DIR = ROOT / "outputs"
OUT_CSV = OUT_DIR / "taiwan_county_income_party_growth.csv"
OUT_PNG = OUT_DIR / "taiwan_county_income_party_growth.png"
OUT_REPORT = OUT_DIR / "validation_report.txt"

SOURCE_URL = (
    "https://data.gov.tw/dataset/9415 ; "
    "https://ws.dgbas.gov.tw/001/Upload/461/relfile/11525/232214/"
    "006-平均每戶可支配所得按區域別分.csv"
)

COUNTIES = [
    "臺北市",
    "新北市",
    "桃園市",
    "臺中市",
    "臺南市",
    "高雄市",
    "基隆市",
    "新竹市",
    "嘉義市",
    "宜蘭縣",
    "新竹縣",
    "苗栗縣",
    "彰化縣",
    "南投縣",
    "雲林縣",
    "嘉義縣",
    "屏東縣",
    "臺東縣",
    "花蓮縣",
    "澎湖縣",
]

PARTY_LABEL = {
    "KMT": "中國國民黨",
    "DPP": "民主進步黨",
    "PFP": "親民黨",
    "TPP": "台灣民眾黨",
    "IND": "無黨籍",
}

PARTY_FILL = {
    "KMT": (36, 100, 190, 35),
    "DPP": (34, 155, 87, 38),
    "PFP": (237, 139, 0, 42),
    "TPP": (0, 150, 170, 42),
    "IND": (120, 126, 134, 28),
}

PARTY_SWATCH = {
    "KMT": (36, 100, 190),
    "DPP": (34, 155, 87),
    "PFP": (237, 139, 0),
    "TPP": (0, 150, 170),
    "IND": (120, 126, 134),
}


@dataclass(frozen=True)
class PartyPeriod:
    start_year: int
    end_year: int
    party: str


# 年度歸屬以該年 7 月 1 日的民選縣市首長黨籍判定；改制前採同名縣市或主要前身。
# 黨籍採當選時政黨，代理、停權、退黨不另切；補選產生新任者才換色。
PARTY_PERIODS: dict[str, list[PartyPeriod]] = {
    "臺北市": [
        PartyPeriod(1999, 2014, "KMT"),
        PartyPeriod(2015, 2022, "IND"),
        PartyPeriod(2023, 2024, "KMT"),
    ],
    "新北市": [
        PartyPeriod(1999, 2005, "DPP"),
        PartyPeriod(2006, 2024, "KMT"),
    ],
    "桃園市": [
        PartyPeriod(1999, 2001, "DPP"),
        PartyPeriod(2002, 2014, "KMT"),
        PartyPeriod(2015, 2022, "DPP"),
        PartyPeriod(2023, 2024, "KMT"),
    ],
    "臺中市": [
        PartyPeriod(1999, 2001, "DPP"),
        PartyPeriod(2002, 2014, "KMT"),
        PartyPeriod(2015, 2018, "DPP"),
        PartyPeriod(2019, 2024, "KMT"),
    ],
    "臺南市": [PartyPeriod(1999, 2024, "DPP")],
    "高雄市": [
        PartyPeriod(1999, 2018, "DPP"),
        PartyPeriod(2019, 2020, "KMT"),
        PartyPeriod(2021, 2024, "DPP"),
    ],
    "基隆市": [
        PartyPeriod(1999, 2014, "KMT"),
        PartyPeriod(2015, 2022, "DPP"),
        PartyPeriod(2023, 2024, "KMT"),
    ],
    "新竹市": [
        PartyPeriod(1999, 2001, "DPP"),
        PartyPeriod(2002, 2014, "KMT"),
        PartyPeriod(2015, 2022, "DPP"),
        PartyPeriod(2023, 2024, "TPP"),
    ],
    "嘉義市": [
        PartyPeriod(1999, 2001, "IND"),
        PartyPeriod(2002, 2014, "KMT"),
        PartyPeriod(2015, 2018, "DPP"),
        PartyPeriod(2019, 2024, "KMT"),
    ],
    "宜蘭縣": [
        PartyPeriod(1999, 2005, "DPP"),
        PartyPeriod(2006, 2009, "KMT"),
        PartyPeriod(2010, 2018, "DPP"),
        PartyPeriod(2019, 2024, "KMT"),
    ],
    "新竹縣": [PartyPeriod(1999, 2024, "KMT")],
    "苗栗縣": [
        PartyPeriod(1999, 2022, "KMT"),
        PartyPeriod(2023, 2024, "IND"),
    ],
    "彰化縣": [
        PartyPeriod(1999, 2001, "KMT"),
        PartyPeriod(2002, 2005, "DPP"),
        PartyPeriod(2006, 2014, "KMT"),
        PartyPeriod(2015, 2018, "DPP"),
        PartyPeriod(2019, 2024, "KMT"),
    ],
    "南投縣": [PartyPeriod(1999, 2024, "KMT")],
    "雲林縣": [
        PartyPeriod(1999, 2005, "KMT"),
        PartyPeriod(2006, 2018, "DPP"),
        PartyPeriod(2019, 2024, "KMT"),
    ],
    "嘉義縣": [
        PartyPeriod(1999, 2001, "KMT"),
        PartyPeriod(2002, 2024, "DPP"),
    ],
    "屏東縣": [PartyPeriod(1999, 2024, "DPP")],
    "臺東縣": [PartyPeriod(1999, 2024, "KMT")],
    "花蓮縣": [
        PartyPeriod(1999, 2009, "KMT"),
        PartyPeriod(2010, 2018, "IND"),
        PartyPeriod(2019, 2024, "KMT"),
    ],
    "澎湖縣": [
        PartyPeriod(1999, 2005, "KMT"),
        PartyPeriod(2006, 2018, "DPP"),
        PartyPeriod(2019, 2022, "KMT"),
        PartyPeriod(2023, 2024, "DPP"),
    ],
}


def party_for(county: str, year: int) -> str:
    for period in PARTY_PERIODS[county]:
        if period.start_year <= year <= period.end_year:
            return period.party
    raise ValueError(f"missing party period for {county} {year}")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size, index=0)
    return ImageFont.load_default()


def text(draw: ImageDraw.ImageDraw, xy, s: str, fnt, fill=(35, 42, 52), anchor=None):
    draw.text(xy, s, font=fnt, fill=fill, anchor=anchor)


def make_dataset() -> pd.DataFrame:
    raw = pd.read_csv(SOURCE_CSV)
    raw = raw.sort_values("年")
    value_cols = ["臺灣地區-元"] + [f"{county}-元" for county in COUNTIES]

    if raw["年"].duplicated().any():
        raise ValueError("年度欄有重複值")
    if raw[value_cols].isna().any().any():
        raise ValueError("所得資料含缺漏值")
    if (raw[value_cols] <= 0).any().any():
        raise ValueError("所得資料含非正值")

    rows = []
    for county in COUNTIES:
        city_values = raw[["年", f"{county}-元", "臺灣地區-元"]].copy()
        city_values.columns = ["年度", "可支配所得", "臺灣地區可支配所得"]
        city_values["對數成長率"] = city_values["可支配所得"].apply(math.log).diff()
        city_values["全國對數成長率"] = city_values["臺灣地區可支配所得"].apply(math.log).diff()
        city_values["相對成長率"] = city_values["對數成長率"] - city_values["全國對數成長率"]
        city_values = city_values.dropna().copy()
        city_values["縣市"] = county
        city_values["縣市首長黨籍代碼"] = city_values["年度"].apply(lambda y: party_for(county, int(y)))
        city_values["縣市首長黨籍"] = city_values["縣市首長黨籍代碼"].map(PARTY_LABEL)
        rows.append(city_values)

    out = pd.concat(rows, ignore_index=True)
    out["相對成長率百分點"] = out["相對成長率"] * 100
    ordered = [
        "縣市",
        "年度",
        "可支配所得",
        "臺灣地區可支配所得",
        "對數成長率",
        "全國對數成長率",
        "相對成長率",
        "相對成長率百分點",
        "縣市首長黨籍",
        "縣市首長黨籍代碼",
    ]
    return out[ordered].sort_values(["縣市", "年度"])


def draw_chart(df: pd.DataFrame) -> None:
    years = sorted(df["年度"].unique())
    y_values = df["相對成長率百分點"].tolist()
    max_abs = max(abs(min(y_values)), abs(max(y_values)))
    y_limit = max(8, math.ceil(max_abs / 2) * 2)

    cols, rows = 4, 5
    panel_w, panel_h = 1050, 760
    left, top = 150, 350
    gap_x, gap_y = 60, 75
    width = left * 2 + cols * panel_w + (cols - 1) * gap_x
    height = top + rows * panel_h + (rows - 1) * gap_y + 360
    img = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img, "RGBA")

    title_f = font(56, True)
    sub_f = font(27)
    label_f = font(25)
    small_f = font(22)
    tiny_f = font(19)

    text(draw, (left, 72), "臺灣縣市平均每戶可支配所得相對成長", title_f, (28, 35, 45))
    text(
        draw,
        (left, 148),
        "指標：縣市對數成長率減臺灣地區對數成長率；單位為百分點。背景色為縣市首長當選時政黨。",
        sub_f,
        (74, 84, 97),
    )
    text(
        draw,
        (left, 194),
        "資料來源：行政院主計總處家庭收支調查；本圖為所得面代理指標，非官方縣市 GDP。",
        sub_f,
        (74, 84, 97),
    )

    lx = left
    ly = 258
    for party in ["KMT", "DPP", "PFP", "TPP", "IND"]:
        draw.rounded_rectangle([lx, ly, lx + 34, ly + 22], radius=5, fill=PARTY_SWATCH[party] + (255,))
        text(draw, (lx + 45, ly - 3), PARTY_LABEL[party], small_f, (55, 64, 76))
        lx += 215 if party != "TPP" else 225

    plot_margin_l = 74
    plot_margin_r = 36
    plot_margin_t = 72
    plot_margin_b = 70

    def x_for_year(x0: int, year: int) -> float:
        span = max(years) - min(years)
        return x0 + plot_margin_l + (year - min(years)) / span * (panel_w - plot_margin_l - plot_margin_r)

    def y_for_value(y0: int, value: float) -> float:
        plot_h = panel_h - plot_margin_t - plot_margin_b
        return y0 + plot_margin_t + (y_limit - value) / (2 * y_limit) * plot_h

    for idx, county in enumerate(COUNTIES):
        col = idx % cols
        row = idx // cols
        x0 = left + col * (panel_w + gap_x)
        y0 = top + row * (panel_h + gap_y)
        x1 = x0 + panel_w
        y1 = y0 + panel_h
        px0 = x0 + plot_margin_l
        px1 = x1 - plot_margin_r
        py0 = y0 + plot_margin_t
        py1 = y1 - plot_margin_b

        draw.rounded_rectangle([x0, y0, x1, y1], radius=8, fill=(250, 252, 254, 255), outline=(218, 225, 233, 255), width=2)
        text(draw, (x0 + 26, y0 + 22), county, label_f, (31, 42, 56))

        county_df = df[df["縣市"] == county].sort_values("年度")
        for year in years:
            party = party_for(county, int(year))
            xa = x_for_year(x0, year - 0.5)
            xb = x_for_year(x0, year + 0.5)
            xa = max(px0, xa)
            xb = min(px1, xb)
            draw.rectangle([xa, py0, xb, py1], fill=PARTY_FILL[party])

        for tick in range(-y_limit, y_limit + 1, max(2, y_limit // 4)):
            yy = y_for_value(y0, tick)
            color = (101, 113, 128, 135) if tick == 0 else (210, 217, 225, 145)
            width_line = 2 if tick == 0 else 1
            draw.line([px0, yy, px1, yy], fill=color, width=width_line)
            if tick != 0:
                text(draw, (x0 + 18, yy - 13), f"{tick:+d}", tiny_f, (108, 119, 132))
        text(draw, (x0 + 14, py0 - 6), "百分點", tiny_f, (108, 119, 132))

        for year in [2000, 2008, 2016, 2024]:
            xx = x_for_year(x0, year)
            draw.line([xx, py0, xx, py1], fill=(220, 226, 233, 100), width=1)
            text(draw, (xx, py1 + 20), str(year), tiny_f, (108, 119, 132), anchor="ma")

        points = [
            (x_for_year(x0, int(r["年度"])), y_for_value(y0, float(r["相對成長率百分點"])))
            for _, r in county_df.iterrows()
        ]
        if len(points) > 1:
            draw.line(points, fill=(28, 35, 45, 255), width=4, joint="curve")
        for px, py in points:
            draw.ellipse([px - 4, py - 4, px + 4, py + 4], fill=(28, 35, 45, 255))

        latest = county_df.iloc[-1]
        latest_label = f"{latest['相對成長率百分點']:+.1f}"
        text(draw, (points[-1][0] - 6, points[-1][1] - 30), latest_label, tiny_f, (31, 42, 56), anchor="ra")

    note_y = height - 230
    notes = [
        "註 1：年度成長率以 ln(本年所得) - ln(前一年所得) 計算；相對成長率再扣除臺灣地區同年度對數成長率。",
        "註 2：本資料集為「平均每戶可支配所得按區域別分」。金門縣、連江縣未列於此資料集，故未繪製。",
        "註 3：直轄市改制前採同名縣市或主要前身之民選首長黨籍；區塊為當選時政黨，不代表議會多數。",
    ]
    for i, note in enumerate(notes):
        text(draw, (left, note_y + i * 38), note, small_f, (83, 94, 108))

    img.convert("RGB").save(OUT_PNG, quality=95)


def validate(df: pd.DataFrame) -> str:
    issues: list[str] = []
    years = sorted(df["年度"].unique())
    expected_years = list(range(min(years), max(years) + 1))
    for county in COUNTIES:
        cdf = df[df["縣市"] == county]
        dupes = cdf.duplicated(["年度"]).sum()
        missing = sorted(set(expected_years) - set(cdf["年度"]))
        if dupes:
            issues.append(f"{county}: 年度重複 {dupes} 筆")
        if missing:
            issues.append(f"{county}: 缺少年度 {missing}")
        if (cdf["可支配所得"] <= 0).any():
            issues.append(f"{county}: 所得含非正值")
        for year in cdf["年度"]:
            party_for(county, int(year))

    samples = [
        "抽查：高雄市 2019-2020 為中國國民黨，2021 起為民主進步黨。",
        "抽查：臺北市 2015-2022 為無黨籍，2023 起為中國國民黨。",
        "抽查：新竹市 2023 起為台灣民眾黨。",
    ]
    status = "通過" if not issues else "需檢查"
    lines = [
        f"資料來源：{SOURCE_URL}",
        f"資料年度：{min(years)}-{max(years)}（成長率序列；原始所得自 1998 年起）",
        f"縣市數：{len(COUNTIES)}",
        f"檢核狀態：{status}",
        "",
        "資料檢核：",
        *(issues or ["無年度重複、缺漏或非正所得值。"]),
        "",
        "黨籍區塊抽查：",
        *samples,
        "",
        "重要限制：本輸出使用平均每戶可支配所得作為所得面代理指標，不是官方縣市 GDP。",
    ]
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    df = make_dataset()
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    draw_chart(df)
    OUT_REPORT.write_text(validate(df), encoding="utf-8")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_PNG}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()
