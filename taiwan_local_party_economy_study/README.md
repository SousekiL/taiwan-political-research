# 臺灣縣市所得成長與地方執政黨區塊圖

本資料視覺化以行政院主計總處「家庭收支調查-平均每戶可支配所得按區域別分」作為地方所得面代理指標。主計總處目前不編製縣市別 GDP，因此本圖不是官方縣市 GDP 圖。

## 產出

- `outputs/taiwan_county_income_party_growth.png`：20 縣市小多圖 PNG。
- `outputs/taiwan_county_income_party_growth.csv`：整理後長表資料，含可支配所得、對數成長率、全國對數成長率、相對成長率與縣市首長黨籍。
- `outputs/validation_report.txt`：年度完整性與黨籍區塊抽查報告。

## 指標

年度對數成長率：

```text
ln(本年可支配所得) - ln(前一年可支配所得)
```

相對成長率：

```text
縣市年度對數成長率 - 臺灣地區年度對數成長率
```

圖上以百分點呈現。正值代表該縣市所得成長高於臺灣地區，負值代表低於臺灣地區。

## 重跑

```bash
/Users/sousekilyu/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/make_taiwan_income_party_chart.py
```

## 重要限制

- 資料集不含金門縣、連江縣。
- 直轄市改制前採同名縣市或主要前身之民選首長黨籍。
- 黨籍區塊採當選時政黨；代理、停權、退黨不另切。

## 中央地方同黨研究包

執行：

```bash
/Users/sousekilyu/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/run_party_alignment_study.py
```

研究包產出位於 `study_outputs/`：

- `party_alignment_county_year_panel.csv`：縣市年度面板，含所得、失業率、企業活動與政治變數。
- `model_results.csv`：縣市固定效果 + 年度固定效果模型，以及排除六都、排除特殊縣市等穩健性規格。
- `event_study_income.csv` 與 `event_study_income.png`：地方政黨輪替事件研究。
- `matched_cases.csv` 與 `matched_cases_income_index.png`：長期單一政黨縣市的配對案例比較。
- `research_memo.md`：保守解讀的研究備忘錄。
- `study_validation_report.txt`：資料完整性檢核。
- `party_alignment_report.html`：完整英文 HTML 報告；假設與結論置於文首，臺灣專有名詞附繁體中文，並納入國際文獻脈絡。
- `long_term_party_rule_case_report.html`：聚焦高雄、臺南、花蓮、南投的長期單一政黨執政案例報告，直接回答「長期執政是否有利地方發展」。
- `dominant_party_outcome_matrix.svg`：按優勢政黨分組的結論矩陣圖，藍色為國民黨優勢案例，綠色為民進黨優勢案例。
- `long_term_party_rule_summary_dashboard.svg`：多指標結論儀表板，合併所得、排名、失業率、企業活動、配對差距與中央地方同黨占比。

本版納入官方可穩定取得的所得、縣市別失業率、企業家數與企業銷售額；人口與財政資料接口保留為後續擴充，不納入主模型。

## 目錄結構

- `scripts/`：資料整理、研究分析與報告生成腳本。
- `data/`：原始 CSV、XLS 與資料來源備查 HTML。
- `outputs/`：第一階段縣市所得成長圖與驗證檔。
- `study_outputs/`：中央地方同黨研究與案例報告產出。
