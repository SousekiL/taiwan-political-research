# 项目规范与标准总结（Project Principles & Standards）

本文档汇总项目过程中逐步确立的数据处理原则、可视化标准、报告编写规范等。

---

## 一、核心研究问题

| 编号 | 问题 | 说明 |
|------|------|------|
| **RQ0** | 长期单一政党执政对地方经济发展是好是坏？ | 核心问题，要求给出明确回答 |
| **RQ1** | 中央执政党与地方执政党相同/不同时，对地方经济发展有无影响？ | 垂直对齐效应（Vertical Alignment） |
| **RQ2** | 不同政党长期执政的县市，其经济发展表现是否存在差异？ | 水平政党效应（Horizontal Partisan Effect） |

**最终回答要求**：必须给出明确结论（好/坏），但允许从多维度展开解释。

---

## 二、数据处理原则

### 2.1 时间范围

| 项目 | 值 |
|------|-----|
| 面板数据跨度 | **1990–2024**（经济 + 选举面板） |
| 实际分析窗口 | **1996–2024**（1996 之前部分县市数据缺失） |
| 增长计算基准 | 1996 → 2024 |

### 2.2 核心变量定义

| 变量 | 定义 | 来源 |
|------|------|------|
| `per_capita_income` | 每人可支配所得（NTD） | 行政院主計總處家庭收支調查 |
| `log_income` | `ln(per_capita_income)` | 衍生变量 |
| `dpp_dummy` | =1 当地方首长为民进党 | 中選會選舉結果 |
| `kmt_dummy` | =1 当地方首长为国民党 | 中選會選舉結果 |
| `aligned` | =1 当地方首长政党 = 总统政党 | 衍生变量 |
| `party_alternation` | =1 在政党轮替后 4 年内 | 衍生变量，参考 Huang (2023) |
| `excess_growth_pct` | 县市增长率 − 全国平均增长率（百分点） | 衍生 |

### 2.3 长期单一政党执政的界定

- **阈值**：≥ **70%**（用户明确设定）
- 在 1996–2024（29 年）中，某政党执政 ≥ 20.3 年 → 判定为该政党优势县市
- **11 个县市达标**（不含金门、连江）：

| 县市 | 优势政党 | 占比 |
|------|---------|------|
| 屏東縣 | DPP | 100% |
| 花蓮縣 | KMT | 100%（含 2009–2017 无党籍年份，属泛蓝阵营） |
| 臺南市 | DPP | 97% |
| 新竹縣 | KMT | 83% |
| 嘉義縣 | DPP | 83% |
| 高雄市 | DPP | 79% |
| 南投縣 | KMT | 72% |
| 彰化縣 | KMT | 72% |
| 澎湖縣 | KMT | 72% |
| 臺中市 | KMT | 72% |
| 臺東縣 | KMT | 72% |

- **不达标的县市**（9 个）标注为 MIXED，不使用蓝/绿色

### 2.4 特殊处理

| 问题 | 处理方式 |
|------|---------|
| 台湾无县级 GDP | 以人均可支配所得 + 失业率 + 税课收入等多指标代理 |
| 2010 年五都改制等行政区划变动 | 在文中加 caveat，改用增长率而非原始排名进行比较 |
| 花蓮縣无党籍年份（傅崐萁 2009–2017） | 归入 KMT（属泛蓝阵营），不单独处理 |
| 金门、连江 | 排除在分析之外（政治生态特殊、数据有限） |

### 2.5 排名处理

- 排名仅作参考（因行政区划变动影响可比性）
- 核心指标改用 **相对全国平均的超额增长率**（excess growth）而非排名

---

## 三、可视化标准

### 3.1 颜色体系（铁律）

| 含义 | 色号 | 适用场景 |
|------|------|---------|
| **KMT（国民党）** | `#0052A5`（深蓝） | KMT 优势县市的政党标识 |
| **DPP（民进党）** | `#1B9431`（深绿） | DPP 优势县市的政党标识 |
| **MIXED / 非优势** | `#888888` 或 `#9ca3af`（灰） | 未达 70% 阈值的县市 |
| **Good（正面结论）** | `#dcfce7` 底 / `#16a34a` 字 | 判定为"好"的案例 |
| **Bad（负面结论）** | `#fee2e2` 底 / `#dc2626` 字 | 判定为"坏"的案例 |
| **Neutral（中性）** | `#eff6ff`（蓝）/ `#fffbeb`（黄） | Modest +/− |

- **绝对禁止**：非优势（MIXED）县市使用蓝色或绿色
- **代码层面**：所有颜色赋值必须有显式 `else` fallback，不允许裸三元表达式

### 3.2 中文字体

| 要求 | 值 |
|------|-----|
| 字体 | **PingFang TC（蘋方-繁）** |
| 查找路径 | `/System/Library/AssetsV2/com_apple_MobileAsset_Font8/.../PingFang.ttc` |
| matplotlib 配置 | `plt.rcParams['font.sans-serif'] = ['PingFang TC', ...]` |
| 备选字体 | `Arial Unicode MS`, `Helvetica` |

### 3.3 图表排版标准

| 项目 | 标准 |
|------|------|
| 最小字号 | **8pt** |
| 图表分辨率 | **150–200 DPI** |
| 嵌入方式 | base64 内嵌于 HTML（自包含）|
| 图片格式 | PNG（报告嵌图）+ PDF（学术引用） |

### 3.4 Dashboard（文章首页总览图）设计规范

- 位置：cover 之后、§1 之前
- 结构（从左到右）：
    1. 县市名称
    2. 规则混合（Rule Mix）：优势政党名称 + 占比 %
    3. 判定（Verdict）：带颜色的标签（Good/Bad/Modest）
    4. TW Growth Gap：相对全国平均的增长差距条形图
    5. 收入变化（NTD 万，1996→2024）
    6. 失业率（2019–2024 平均）
    7. 人口变化（1996→2024 %）
    8. 政治对齐（% 年份中央=地方）
- 仅展示 ≥70% 的案件
- 每行交替灰白底色以便阅读

### 3.5 Figures in §2–§3

| 图号 | 位置 | 内容 |
|------|------|------|
| Figure 1 | §2（结论部分）| 超额增长率条形图（20 县市） |
| Figure 2 | §3（方法部分）| 8 个关键县市收入走勢图 |
| Figure 3 | §3（方法部分）| SCM 处理效应图 |

---

## 四、报告写作规范

### 4.1 语言与排版

| 要求 | 说明 |
|------|------|
| 主语言 | **English** |
| 专有名词 | 标注 **繁体中文**（Taiwan Traditional Chinese） |
| 段落风格 | **自然段落**，避免 bullet points / 过多小标题 |
| 学术风格 | 严谨、客观、紧凑 |

### 4.2 报告结构（6 章节）

| 序号 | 章节 | 定位 |
|------|------|------|
| 1 | Background and Motivation | 研究背景、数据来源说明、阈值定义 |
| 2 | **Findings and Conclusions** | **结论先行** — 摘要框 + 核心图 + 机制分析 |
| 3 | Data and Methods | 数据源表格 + SCM + Panel FE 说明 |
| 4 | Related Literature | 三段体文献综述 |
| 5 | Limitations | 研究限制 |
| 6 | References | 17 篇参考文献 |

### 4.3 政治中立性要求（铁律）

| 要求 | 实现方式 |
|------|---------|
| 不偏向任何政党 | 案例对称选取（KMT/DDP 各若干），以数据说话 |
| 零假设被严肃对待 | 明确写出 "The null hypothesis of no party effect is a valid and potentially correct answer" |
| 研究者立场声明 | §1 末尾附 Positionality Statement |
| 判定标准对称 | 两个政党都用同一套指标和阈值评判 |
| 语言不带倾向性 | 不出现"某党更好/更差"的预设立场 |

---

## 五、技术实现规范

### 5.1 分析脚本

| 脚本 | 功能 | 语言 |
|------|------|------|
| `fetch_data.py` | 经济数据采集 | Python |
| `build_election_data.py` | 选举数据构建 | Python |
| `run_analysis_v2.py` | SCM + Panel FE + 全部图表 | Python |
| `make_dashboard.py` | Dashboard 总结图表 | Python |
| `make_summary_chart.py` | Figure 1 超额增长率图 | Python |
| `build_final_report.py` | 组装最终 HTML 报告 | Python |
| `run_scm.R` | R 版 SCM（备选） | R |

### 5.2 SCM 实现方案

| 组件 | 方案 |
|------|------|
| 优化方法 | `scipy.optimize.minimize` (SLSQP) |
| 约束条件 | weights ∈ [0,1], Σ weights = 1 |
| 目标函数 | minimise Σ (Y_treated − Y_synthetic)² |
| 后处理 | weights < 0.001 → 归零 → 重新归一化 |

### 5.3 代码鲁棒性要求

| 要求 | 说明 |
|------|------|
| 显式 else fallback | 颜色赋值不允许裸三元 |
| 常量集中定义 | `THRESHOLD`, 色号等放在脚本顶部 |
| 处理缺失数据 | SCM 跳过 pre-treatment 数据不足的县市 |

---

## 六、项目文件清单

```
taiwan-political-research/
├── .gitignore
├── README.md
├── index.html                   # GitHub Pages 入口（= 报告最终版）
├── research-design-report.html  # 报告主文件
├── fetch_data.py                # 经济数据采集
├── build_election_data.py       # 选举数据构建
├── run_analysis_v2.py           # 主分析流程
├── make_dashboard.py            # Dashboard 总结图
├── make_summary_chart.py        # Figure 1 超额增长率图
├── build_final_report.py        # 报告组装
├── run_analysis.py              # 早期版本（保留）
├── run_scm.R                    # R 版 SCM
├── data/                        # CSV 面板数据（.gitignore）
└── results/                     # 生成的图表（.gitignore）
```

---

## 七、关键经验教训

1. **先定阈值再分析**：70% 标准明确后再筛选案例，避免事后挑选
2. **颜色就是信号**：图表颜色体系一旦确定，不可随意混用
3. **结论在前，方法在后**：学术报告不等于方法说明书
4. **排名不等于真相**：行政区划变动会扭曲排名信号
5. **代码要有防御性**：else fallback 不是可选项，是必选项
