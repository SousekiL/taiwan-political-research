from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from make_taiwan_income_party_chart import COUNTIES, PARTY_LABEL, PARTY_PERIODS, party_for


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
DATA_DIR = ROOT / "data"
OUT = ROOT / "study_outputs"
OUT.mkdir(exist_ok=True)

INCOME_CSV = DATA_DIR / "household_disposable_income_by_region.csv"
UNEMPLOYMENT_CSV = DATA_DIR / "county_unemployment.csv"
ENTERPRISE_COUNT_CSV = DATA_DIR / "enterprise_count_sales_1.csv"
ENTERPRISE_SALES_CSV = DATA_DIR / "enterprise_count_sales_2.csv"

PANEL_CSV = OUT / "party_alignment_county_year_panel.csv"
MODEL_CSV = OUT / "model_results.csv"
EVENT_CSV = OUT / "event_study_income.csv"
MATCH_CSV = OUT / "matched_cases.csv"
MEMO_MD = OUT / "research_memo.md"
EVENT_PNG = OUT / "event_study_income.png"
MATCH_PNG = OUT / "matched_cases_income_index.png"
VALIDATION_TXT = OUT / "study_validation_report.txt"

SIX_MUNIS = {"臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市"}
SPECIAL_COUNTIES = {"臺北市", "新竹市"}
ISLAND_COUNTIES = {"澎湖縣"}
MAJOR_PARTIES = {"KMT", "DPP"}


def central_party(year: int) -> str:
    # Annual treatment is assigned by the party holding the presidency on July 1.
    if 1998 <= year <= 1999:
        return "KMT"
    if 2000 <= year <= 2007:
        return "DPP"
    if 2008 <= year <= 2015:
        return "KMT"
    if 2016 <= year <= 2024:
        return "DPP"
    raise ValueError(f"central party not defined for {year}")


def local_party(county: str, year: int) -> str:
    # The existing manually audited local-party table starts at 1999 because
    # growth outcomes begin in 1999. For baseline levels, assign 1998 to the
    # same elected local administration observed on 1999-07-01.
    if year == 1998:
        year = 1999
    return party_for(county, year)


def font(size: int) -> ImageFont.FreeTypeFont:
    for path in [
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    ]:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size, index=0)
    return ImageFont.load_default()


def norm_pvalue(z: float) -> float:
    return math.erfc(abs(z) / math.sqrt(2.0))


@dataclass
class RegressionResult:
    outcome: str
    specification: str
    n: int
    counties: int
    years: str
    coefficient: float
    std_error: float
    t_stat: float
    p_value_normal: float
    mean_outcome: float
    notes: str


def read_income_panel() -> pd.DataFrame:
    wide = pd.read_csv(INCOME_CSV).sort_values("年")
    rows = []
    for county in COUNTIES:
        temp = wide[["年", f"{county}-元", "臺灣地區-元"]].copy()
        temp.columns = ["年度", "平均每戶可支配所得", "臺灣地區平均每戶可支配所得"]
        temp["縣市"] = county
        temp["所得對數"] = np.log(temp["平均每戶可支配所得"])
        temp["全國所得對數"] = np.log(temp["臺灣地區平均每戶可支配所得"])
        temp["所得對數成長率"] = temp["所得對數"].diff()
        temp["全國所得對數成長率"] = temp["全國所得對數"].diff()
        temp["所得相對成長率百分點"] = (temp["所得對數成長率"] - temp["全國所得對數成長率"]) * 100
        rows.append(temp)
    return pd.concat(rows, ignore_index=True)


def read_unemployment_panel() -> pd.DataFrame:
    raw = pd.read_csv(UNEMPLOYMENT_CSV)
    annual = raw[raw["年月別_Year_and_month"].astype(str).str.fullmatch(r"\d{4}")].copy()
    annual["年度"] = annual["年月別_Year_and_month"].astype(int)
    rows = []
    for county in COUNTIES:
        col = next(c for c in annual.columns if c.startswith(f"{county}_"))
        temp = annual[["年度", col]].copy()
        temp.columns = ["年度", "失業率"]
        temp["縣市"] = county
        rows.append(temp)
    out = pd.concat(rows, ignore_index=True)
    return out[(out["年度"] >= 1998) & (out["年度"] <= 2024)]


def numeric_series(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.replace(r"^\s*$", np.nan, regex=True), errors="coerce")


def read_enterprise_panel() -> pd.DataFrame:
    counts = pd.read_csv(ENTERPRISE_COUNT_CSV)
    sales = pd.read_csv(ENTERPRISE_SALES_CSV)

    counts["中小企業(家)"] = numeric_series(counts["中小企業(家)"])
    counts["大企業(家)"] = numeric_series(counts["大企業(家)"])
    counts["企業家數"] = counts[["中小企業(家)", "大企業(家)"]].sum(axis=1, min_count=1)
    count_panel = (
        counts[counts["縣市別"].isin(COUNTIES)]
        .groupby(["縣市別", "年度"], as_index=False)["企業家數"]
        .sum()
        .rename(columns={"縣市別": "縣市"})
    )

    sales["中小企業(百萬元)"] = numeric_series(sales["中小企業(百萬元)"])
    sales["大企業(百萬元)"] = numeric_series(sales["大企業(百萬元)"])
    sales["企業銷售額百萬元"] = sales[["中小企業(百萬元)", "大企業(百萬元)"]].sum(axis=1, min_count=1)
    sales_panel = (
        sales[sales["縣市別"].isin(COUNTIES)]
        .groupby(["縣市別", "年度"], as_index=False)["企業銷售額百萬元"]
        .sum()
        .rename(columns={"縣市別": "縣市"})
    )

    out = count_panel.merge(sales_panel, on=["縣市", "年度"], how="outer").sort_values(["縣市", "年度"])
    out["企業家數對數成長率"] = out.groupby("縣市")["企業家數"].transform(lambda s: np.log(s).diff())
    out["企業銷售額對數成長率"] = out.groupby("縣市")["企業銷售額百萬元"].transform(lambda s: np.log(s).diff())
    return out


def add_politics(panel: pd.DataFrame) -> pd.DataFrame:
    panel = panel.copy()
    panel["中央執政黨代碼"] = panel["年度"].apply(lambda y: central_party(int(y)))
    panel["中央執政黨"] = panel["中央執政黨代碼"].map(PARTY_LABEL)
    panel["地方首長黨籍代碼"] = panel.apply(lambda r: local_party(r["縣市"], int(r["年度"])), axis=1)
    panel["地方首長黨籍"] = panel["地方首長黨籍代碼"].map(PARTY_LABEL)
    panel["中央地方同黨"] = (
        (panel["中央執政黨代碼"] == panel["地方首長黨籍代碼"]) & panel["地方首長黨籍代碼"].isin(MAJOR_PARTIES)
    ).astype(int)
    panel["地方是否主要政黨"] = panel["地方首長黨籍代碼"].isin(MAJOR_PARTIES).astype(int)
    panel["地方國民黨執政"] = (panel["地方首長黨籍代碼"] == "KMT").astype(int)
    panel["地方民進黨執政"] = (panel["地方首長黨籍代碼"] == "DPP").astype(int)
    panel["六都"] = panel["縣市"].isin(SIX_MUNIS).astype(int)
    panel["特殊產業結構縣市"] = panel["縣市"].isin(SPECIAL_COUNTIES).astype(int)
    panel["離島縣市"] = panel["縣市"].isin(ISLAND_COUNTIES).astype(int)
    panel["任期年序"] = panel.apply(lambda r: tenure_year(r["縣市"], int(r["年度"])), axis=1)
    panel["地方政黨輪替"] = (
        panel.sort_values(["縣市", "年度"])
        .groupby("縣市")["地方首長黨籍代碼"]
        .transform(lambda s: (s != s.shift(1)).astype(int))
    )
    panel.loc[panel.groupby("縣市")["年度"].idxmin(), "地方政黨輪替"] = 0
    return panel


def tenure_year(county: str, year: int) -> int:
    if year == 1998:
        year = 1999
    active = [p for p in PARTY_PERIODS[county] if p.start_year <= year <= p.end_year][0]
    return year - active.start_year + 1


def build_panel() -> pd.DataFrame:
    income = read_income_panel()
    unemp = read_unemployment_panel()
    enterprise = read_enterprise_panel()
    panel = income.merge(unemp, on=["縣市", "年度"], how="left").merge(enterprise, on=["縣市", "年度"], how="left")
    panel = add_politics(panel)
    panel["失業率變動"] = panel.sort_values(["縣市", "年度"]).groupby("縣市")["失業率"].diff()
    return panel.sort_values(["縣市", "年度"])


def design_matrix(df: pd.DataFrame, x_cols: list[str], county_fe=True, year_fe=True, trend=False) -> tuple[np.ndarray, list[str]]:
    mats = []
    names = []
    mats.append(np.ones((len(df), 1)))
    names.append("const")
    for col in x_cols:
        mats.append(df[[col]].to_numpy(float))
        names.append(col)
    if county_fe:
        d = pd.get_dummies(df["縣市"], prefix="縣市", drop_first=True, dtype=float)
        mats.append(d.to_numpy())
        names.extend(d.columns.tolist())
    if year_fe:
        d = pd.get_dummies(df["年度"], prefix="年度", drop_first=True, dtype=float)
        mats.append(d.to_numpy())
        names.extend(d.columns.astype(str).tolist())
    if trend:
        base_year = df["年度"].min()
        for county in sorted(df["縣市"].unique())[1:]:
            names.append(f"{county}_線性趨勢")
            mats.append(((df["縣市"] == county).astype(float) * (df["年度"] - base_year)).to_numpy()[:, None])
    return np.hstack(mats), names


def ols_cluster(df: pd.DataFrame, outcome: str, x_col: str, specification: str, trend=False, filters=None) -> RegressionResult:
    work = df.copy()
    if filters is not None:
        work = work[filters(work)]
    work = work.dropna(subset=[outcome, x_col, "縣市", "年度"]).reset_index(drop=True)
    X, names = design_matrix(work, [x_col], trend=trend)
    y = work[outcome].to_numpy(float)
    beta = np.linalg.pinv(X.T @ X) @ (X.T @ y)
    resid = y - X @ beta
    bread = np.linalg.pinv(X.T @ X)

    meat = np.zeros((X.shape[1], X.shape[1]))
    for _, idx in work.groupby("縣市").groups.items():
        Xg = X[list(idx), :]
        ug = resid[list(idx)]
        score = Xg.T @ ug
        meat += np.outer(score, score)
    g = work["縣市"].nunique()
    n, k = X.shape
    correction = (g / (g - 1)) * ((n - 1) / max(n - k, 1)) if g > 1 else 1.0
    vcov = correction * bread @ meat @ bread
    j = names.index(x_col)
    se = float(math.sqrt(max(vcov[j, j], 0)))
    coef = float(beta[j])
    t = coef / se if se else np.nan
    return RegressionResult(
        outcome=outcome,
        specification=specification,
        n=len(work),
        counties=work["縣市"].nunique(),
        years=f"{int(work['年度'].min())}-{int(work['年度'].max())}",
        coefficient=coef,
        std_error=se,
        t_stat=float(t),
        p_value_normal=norm_pvalue(t) if np.isfinite(t) else np.nan,
        mean_outcome=float(work[outcome].mean()),
        notes="縣市與年度固定效果；標準誤依縣市聚類。非強因果估計。",
    )


def run_models(panel: pd.DataFrame) -> pd.DataFrame:
    outcomes = [
        ("所得相對成長率百分點", "所得相對成長率百分點"),
        ("失業率", "失業率"),
        ("失業率變動", "失業率變動"),
        ("企業家數對數成長率", "企業家數對數成長率"),
        ("企業銷售額對數成長率", "企業銷售額對數成長率"),
    ]
    specs = []
    for outcome, label in outcomes:
        specs.append(ols_cluster(panel, outcome, "中央地方同黨", f"{label}：基準 FE"))
        specs.append(ols_cluster(panel, outcome, "中央地方同黨", f"{label}：加入縣市線性趨勢", trend=True))
        specs.append(ols_cluster(panel, outcome, "中央地方同黨", f"{label}：排除六都", filters=lambda d: d["六都"] == 0))
        specs.append(ols_cluster(panel, outcome, "中央地方同黨", f"{label}：排除臺北市與新竹市", filters=lambda d: d["特殊產業結構縣市"] == 0))
        specs.append(ols_cluster(panel, outcome, "中央地方同黨", f"{label}：排除澎湖", filters=lambda d: d["離島縣市"] == 0))
    return pd.DataFrame([r.__dict__ for r in specs])


def build_event_study(panel: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    events = []
    for county, cdf in panel.sort_values("年度").groupby("縣市"):
        cdf = cdf.sort_values("年度")
        switches = cdf[(cdf["地方政黨輪替"] == 1) & cdf["地方首長黨籍代碼"].isin(MAJOR_PARTIES)]
        for _, sw in switches.iterrows():
            year0 = int(sw["年度"])
            old_party = cdf.loc[cdf["年度"] == year0 - 1, "地方首長黨籍代碼"]
            if old_party.empty or old_party.iloc[0] not in MAJOR_PARTIES:
                continue
            for rel in range(-window, window + 1):
                row = cdf[cdf["年度"] == year0 + rel]
                if row.empty:
                    continue
                events.append(
                    {
                        "縣市": county,
                        "輪替年度": year0,
                        "由": old_party.iloc[0],
                        "轉為": sw["地方首長黨籍代碼"],
                        "相對年度": rel,
                        "所得相對成長率百分點": float(row["所得相對成長率百分點"].iloc[0]),
                    }
                )
    event_df = pd.DataFrame(events)
    if event_df.empty:
        return event_df
    avg = (
        event_df.groupby("相對年度", as_index=False)
        .agg(平均所得相對成長率百分點=("所得相對成長率百分點", "mean"), 事件數=("所得相對成長率百分點", "count"))
    )
    return avg.merge(event_df, on="相對年度", how="left")


def match_cases(panel: pd.DataFrame) -> pd.DataFrame:
    baseline = panel[(panel["年度"] >= 1999) & (panel["年度"] <= 2002)].groupby("縣市").agg(
        基準所得=("平均每戶可支配所得", "mean"),
        基準失業率=("失業率", "mean"),
        基準所得波動=("所得相對成長率百分點", "std"),
    )
    long_cases = {
        "臺南市": "DPP",
        "屏東縣": "DPP",
        "新竹縣": "KMT",
        "南投縣": "KMT",
        "臺東縣": "KMT",
    }
    records = []
    for target, target_party in long_cases.items():
        donor_pool = []
        for county in COUNTIES:
            if county == target:
                continue
            cdf = panel[(panel["縣市"] == county) & (panel["年度"].between(1999, 2024))]
            opposite_share = (cdf["地方首長黨籍代碼"] != target_party).mean()
            if opposite_share < 0.35:
                continue
            donor_pool.append(county)
        b = baseline.loc[[target] + donor_pool].copy()
        for col in b.columns:
            std = b[col].std()
            b[col + "_z"] = (b[col] - b.loc[target, col]) / (std if std else 1)
        b["距離"] = np.sqrt((b[[c + "_z" for c in ["基準所得", "基準失業率", "基準所得波動"]]] ** 2).sum(axis=1))
        match = b.drop(index=target).sort_values("距離").index[0]
        for county, role in [(target, "處理縣市"), (match, "配對縣市")]:
            cdf = panel[panel["縣市"] == county].copy()
            base_income = cdf[cdf["年度"].between(1999, 2002)]["平均每戶可支配所得"].mean()
            cdf["所得指數_1999_2002_100"] = cdf["平均每戶可支配所得"] / base_income * 100
            cdf["案例縣市"] = target
            cdf["角色"] = role
            cdf["配對距離"] = float(b.loc[match, "距離"])
            records.append(cdf[["案例縣市", "角色", "縣市", "年度", "所得指數_1999_2002_100", "地方首長黨籍", "配對距離"]])
    return pd.concat(records, ignore_index=True)


def draw_event_chart(event_df: pd.DataFrame) -> None:
    avg = event_df[["相對年度", "平均所得相對成長率百分點", "事件數"]].drop_duplicates().sort_values("相對年度")
    w, h = 1300, 780
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    title_f, f, small = font(38), font(24), font(19)
    d.text((70, 45), "地方政黨輪替事件研究：所得相對成長率", font=title_f, fill=(28, 35, 45))
    d.text((70, 96), "輪替年 = 0；線為所有主要政黨輪替事件平均。", font=f, fill=(80, 90, 105))
    x0, y0, x1, y1 = 110, 155, 1220, 670
    d.rectangle([x0, y0, x1, y1], outline=(210, 218, 228), width=2)
    vals = avg["平均所得相對成長率百分點"].tolist()
    ymin, ymax = min(-8, min(vals)), max(8, max(vals))
    for tick in range(math.floor(ymin / 2) * 2, math.ceil(ymax / 2) * 2 + 1, 2):
        y = y1 - (tick - ymin) / (ymax - ymin) * (y1 - y0)
        d.line([x0, y, x1, y], fill=(225, 230, 236), width=1)
        d.text((48, y - 11), f"{tick:+d}", font=small, fill=(95, 106, 120))
    def px(rel): return x0 + (rel + 5) / 10 * (x1 - x0)
    def py(v): return y1 - (v - ymin) / (ymax - ymin) * (y1 - y0)
    d.line([px(0), y0, px(0), y1], fill=(120, 126, 134), width=3)
    points = [(px(int(r["相對年度"])), py(float(r["平均所得相對成長率百分點"]))) for _, r in avg.iterrows()]
    d.line(points, fill=(30, 80, 150), width=5)
    for x, y in points:
        d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(30, 80, 150))
    for rel in range(-5, 6):
        d.text((px(rel) - 10, y1 + 24), str(rel), font=small, fill=(95, 106, 120))
    d.text((x0, y1 + 65), "相對年度", font=small, fill=(80, 90, 105))
    d.text((x0, y0 - 35), "百分點", font=small, fill=(80, 90, 105))
    img.save(EVENT_PNG, quality=95)


def draw_match_chart(match_df: pd.DataFrame) -> None:
    cases = match_df["案例縣市"].drop_duplicates().tolist()
    w, h = 1600, 1150
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    title_f, f, small = font(38), font(23), font(17)
    d.text((70, 42), "長期單一政黨縣市：配對縣市所得指數比較", font=title_f, fill=(28, 35, 45))
    d.text((70, 94), "所得指數以 1999-2002 平均 = 100；配對依基準所得、失業率與所得波動距離選取。", font=f, fill=(80, 90, 105))
    cols, rows = 2, 3
    panel_w, panel_h = 690, 285
    left, top = 85, 160
    gapx, gapy = 65, 55
    for i, case in enumerate(cases):
        col, row = i % cols, i // cols
        x0, y0 = left + col * (panel_w + gapx), top + row * (panel_h + gapy)
        x1, y1 = x0 + panel_w, y0 + panel_h
        d.rectangle([x0, y0, x1, y1], outline=(210, 218, 228), width=2)
        cdf = match_df[match_df["案例縣市"] == case]
        d.text((x0 + 18, y0 + 13), case, font=f, fill=(28, 35, 45))
        years = sorted(cdf["年度"].unique())
        vals = cdf["所得指數_1999_2002_100"]
        ymin, ymax = math.floor(vals.min() / 10) * 10, math.ceil(vals.max() / 10) * 10
        px = lambda yr: x0 + 55 + (yr - min(years)) / (max(years) - min(years)) * (panel_w - 95)
        py = lambda v: y1 - 42 - (v - ymin) / (ymax - ymin) * (panel_h - 90)
        for tick in range(ymin, ymax + 1, 20):
            yy = py(tick)
            d.line([x0 + 55, yy, x1 - 40, yy], fill=(228, 233, 238), width=1)
            d.text((x0 + 8, yy - 10), str(tick), font=small, fill=(95, 106, 120))
        colors = {"處理縣市": (30, 80, 150), "配對縣市": (180, 80, 45)}
        for role, rdf in cdf.groupby("角色"):
            rdf = rdf.sort_values("年度")
            points = [(px(int(r["年度"])), py(float(r["所得指數_1999_2002_100"]))) for _, r in rdf.iterrows()]
            d.line(points, fill=colors[role], width=4)
            label = f"{role}：{rdf['縣市'].iloc[0]}"
            d.text((points[-1][0] - 190, points[-1][1] - (18 if role == "處理縣市" else -4)), label, font=small, fill=colors[role])
        for yr in [2000, 2008, 2016, 2024]:
            if yr in years:
                d.text((px(yr) - 18, y1 - 28), str(yr), font=small, fill=(95, 106, 120))
    img.save(MATCH_PNG, quality=95)


def write_memo(panel: pd.DataFrame, models: pd.DataFrame, event_df: pd.DataFrame, match_df: pd.DataFrame) -> None:
    key = models[(models["outcome"] == "所得相對成長率百分點") & (models["specification"].str.contains("基準"))].iloc[0]
    pre = event_df[event_df["相對年度"].isin([-3, -2, -1])][["相對年度", "平均所得相對成長率百分點"]].drop_duplicates()
    pre_mean = pre["平均所得相對成長率百分點"].mean()
    lines = [
        "# 中央地方執政黨一致性與縣市經濟發展研究備忘錄",
        "",
        "## 研究包內容",
        "",
        "- `party_alignment_county_year_panel.csv`：縣市年度面板，含所得、失業率、企業活動與政治變數。",
        "- `model_results.csv`：固定效果迴歸與穩健性規格。",
        "- `event_study_income.csv` / `event_study_income.png`：地方政黨輪替事件研究。",
        "- `matched_cases.csv` / `matched_cases_income_index.png`：長期單一政黨縣市與配對縣市比較。",
        "",
        "## 主要初步結果",
        "",
        f"- 基準固定效果模型中，同黨係數為 {key['coefficient']:.3f} 個百分點，縣市聚類標準誤 {key['std_error']:.3f}，樣本數 {int(key['n'])}。",
        f"- 輪替事件研究的前 3 年平均相對所得成長為 {pre_mean:.3f} 個百分點；若圖上可見明顯事前趨勢，應避免強因果解讀。",
        "- 企業活動資料自 2013 年起，適合作為輔助結果，不宜與 1999 起所得主模型混為同一長期證據。",
        "",
        "## 解讀限制",
        "",
        "- 這是準因果研究框架，不是隨機實驗。地方政黨與地方產業結構、都市化、選民偏好高度相關。",
        "- 主計總處不編製縣市別 GDP；本研究使用所得、失業與企業活動代理地方經濟表現。",
        "- 財政與人口接口已預留為後續擴充，但本版未把不穩定或不完整來源放入主模型。",
        "",
        "## 建議下一步",
        "",
        "- 從中選會補入縣市長勝選差距，加入接近勝選門檻樣本作穩健性檢查。",
        "- 從財政部國庫署整理普通/特別統籌分配款，檢驗同黨是否透過中央資源影響地方。",
        "- 將六都改制前後另作敏感性處理，特別是臺中、臺南、高雄 2010 年前後口徑。",
    ]
    MEMO_MD.write_text("\n".join(lines), encoding="utf-8")


def validate(panel: pd.DataFrame, models: pd.DataFrame, event_df: pd.DataFrame, match_df: pd.DataFrame) -> str:
    expected = set(range(1998, 2025))
    issues = []
    for county, cdf in panel.groupby("縣市"):
        missing = sorted(expected - set(cdf["年度"]))
        if missing:
            issues.append(f"{county}: 缺少年度 {missing}")
    lines = [
        "研究資料檢核報告",
        f"面板列數：{len(panel)}",
        f"縣市數：{panel['縣市'].nunique()}",
        f"年度範圍：{panel['年度'].min()}-{panel['年度'].max()}",
        f"所得非缺漏列：{panel['平均每戶可支配所得'].notna().sum()}",
        f"失業率非缺漏列：{panel['失業率'].notna().sum()}",
        f"企業家數非缺漏列：{panel['企業家數'].notna().sum()}",
        f"模型列數：{len(models)}",
        f"事件研究事件列數：{len(event_df)}",
        f"配對案例列數：{len(match_df)}",
        "",
        "年度完整性：",
        *(issues or ["20 縣市 1998-2024 皆有面板列。"]),
        "",
        "黨籍抽查：臺北市 2015-2022 無黨籍；高雄市 2019-2020 中國國民黨；新竹市 2023 起台灣民眾黨。",
    ]
    return "\n".join(lines)


def main() -> None:
    panel = build_panel()
    panel.to_csv(PANEL_CSV, index=False, encoding="utf-8-sig")

    models = run_models(panel)
    models.to_csv(MODEL_CSV, index=False, encoding="utf-8-sig")

    event_df = build_event_study(panel)
    event_df.to_csv(EVENT_CSV, index=False, encoding="utf-8-sig")
    draw_event_chart(event_df)

    match_df = match_cases(panel)
    match_df.to_csv(MATCH_CSV, index=False, encoding="utf-8-sig")
    draw_match_chart(match_df)

    write_memo(panel, models, event_df, match_df)
    VALIDATION_TXT.write_text(validate(panel, models, event_df, match_df), encoding="utf-8")

    print(PANEL_CSV)
    print(MODEL_CSV)
    print(EVENT_CSV)
    print(EVENT_PNG)
    print(MATCH_CSV)
    print(MATCH_PNG)
    print(MEMO_MD)
    print(VALIDATION_TXT)


if __name__ == "__main__":
    main()
