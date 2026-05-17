#!/usr/bin/env python3
"""
Complete Re-Analysis: Fixed Chinese fonts, national rank trajectories,
extended time range (1996+), all new charts.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# FONT SETUP
# ============================================================
# Find PingFang TC font
font_path = None
for f in fm.findSystemFonts(fontext='ttc'):
    if 'com_apple' in f and 'PingFang' in f:
        font_path = f
        break
if not font_path:
    # Fallback: SourceHanSans
    for f in fm.findSystemFonts():
        if 'SourceHanSans' in f and 'Regular' in f:
            font_path = f
            break
if font_path:
    font_prop = fm.FontProperties(fname=font_path)
    print(f"Using font: {font_prop.get_name()} ({font_path})")
else:
    font_prop = None
    print("WARNING: No CJK font found!")

plt.rcParams['font.family'] = 'sans-serif'
if font_prop:
    fm.fontManager.addfont(font_path)
    plt.rcParams['font.sans-serif'] = [font_prop.get_name(), 'PingFang TC', 'Arial Unicode MS', 'Helvetica']
plt.rcParams['axes.unicode_minus'] = False

RESULTDIR = Path("/Users/sousekilyu/Documents/Github/taiwan-political-research/results")
RESULTDIR.mkdir(exist_ok=True)

# ============================================================
# 1. Load and prepare data
# ============================================================
df = pd.read_csv("data/merged_panel.csv")
df['per_capita_income'] = pd.to_numeric(df['per_capita_income'], errors='coerce')
df['log_income'] = pd.to_numeric(df['log_income'], errors='coerce')
df['unemployment_rate'] = pd.to_numeric(df['unemployment_rate'], errors='coerce')
df['population'] = pd.to_numeric(df['population'], errors='coerce')
df['tax_revenue_per_capita'] = pd.to_numeric(df['tax_revenue_per_capita'], errors='coerce')

# Extended analysis period: 1996-2024
BASE_YEAR = 1996
END_YEAR = 2024
df_analysis = df[(df['year'] >= BASE_YEAR) & (df['year'] <= END_YEAR)].copy()
df_analysis = df_analysis.sort_values(['county', 'year'])
counties = sorted(df_analysis['county'].unique())
print(f"Analysis range: {BASE_YEAR}-{END_YEAR}, {len(counties)} counties, {len(df_analysis)} obs")

# ============================================================
# 2. NATIONAL RANK ANALYSIS BY YEAR
# ============================================================
def compute_ranks(df, metric='per_capita_income'):
    """Compute national ranking (1=highest income) for each county each year."""
    ranks = {}
    for year in sorted(df['year'].unique()):
        year_data = df[df['year'] == year][['county', metric]].dropna()
        if len(year_data) < 15:
            continue
        year_data = year_data.sort_values(metric, ascending=False).reset_index(drop=True)
        year_data['rank'] = range(1, len(year_data) + 1)
        ranks[year] = dict(zip(year_data['county'], year_data['rank']))
    return ranks

income_ranks = compute_ranks(df_analysis, 'per_capita_income')
unemp_ranks = compute_ranks(df_analysis, 'unemployment_rate')
# For unemployment, rank 1 = lowest unemployment (best)
unemp_ranks_inverted = {}
for year in unemp_ranks:
    max_r = max(unemp_ranks[year].values()) if unemp_ranks[year] else 20
    unemp_ranks_inverted[year] = {c: max_r - r + 1 for c, r in unemp_ranks[year].items()}

# Build rank dataframe
rank_rows = []
for year in sorted(income_ranks.keys()):
    for county in counties:
        ir = income_ranks.get(year, {}).get(county, np.nan)
        ur = unemp_ranks_inverted.get(year, {}).get(county, np.nan)
        rank_rows.append({'year': year, 'county': county, 'income_rank': ir, 'unemp_rank': ur})
rank_df = pd.DataFrame(rank_rows)

# Merge party info
party_info = df_analysis.groupby('county')[['local_party', 'aligned', 'dpp_dummy', 'kmt_dummy']].last()
county_dom_party = {}
for c in counties:
    cdata = df_analysis[df_analysis['county'] == c]
    kmt_pct = cdata['kmt_dummy'].mean()
    dpp_pct = cdata['dpp_dummy'].mean()
    county_dom_party[c] = 'KMT' if kmt_pct > dpp_pct else 'DPP' if dpp_pct > kmt_pct else 'MIXED'

rank_df['dominant_party'] = rank_df['county'].map(county_dom_party)

# ============================================================
# 3. LONG-TERM GROWTH (1996-2024)
# ============================================================
growth_stats = {}
for c in counties:
    cdata = df_analysis[df_analysis['county'] == c]
    val1996 = cdata[cdata['year'] == 1996]['per_capita_income'].values
    val2024 = cdata[cdata['year'] == 2024]['per_capita_income'].values
    # Also compute periodic growth
    val2000 = cdata[cdata['year'] == 2000]['per_capita_income'].values
    val2010 = cdata[cdata['year'] == 2010]['per_capita_income'].values
    
    rank1996 = income_ranks.get(1996, {}).get(c, np.nan)
    rank2024 = income_ranks.get(2024, {}).get(c, np.nan)
    
    if len(val1996) > 0 and len(val2024) > 0:
        growth_stats[c] = {
            'income_1996': val1996[0],
            'income_2024': val2024[0],
            'growth_1996_2024': val2024[0] / val1996[0] - 1,
            'rank_1996': rank1996,
            'rank_2024': rank2024,
            'rank_change': rank1996 - rank2024 if not np.isnan(rank1996) and not np.isnan(rank2024) else np.nan,
            # positive rank_change = improved ranking (moved up)
            'dominant_party': county_dom_party[c],
            'dpp_pct': cdata['dpp_dummy'].mean(),
            'kmt_pct': cdata['kmt_dummy'].mean(),
        }

growth_df = pd.DataFrame(growth_stats).T
growth_df['county'] = growth_df.index
growth_df = growth_df.reset_index(drop=True)

# ============================================================
# 4. RANK TRAJECTORY BY PARTY RULE PERIODS
# ============================================================
# For key counties, trace rank changes under each party's rule period
def trace_county_rank_trajectory(county_name):
    """Return rank trajectory for a county, annotated with ruling party changes."""
    cdata = rank_df[rank_df['county'] == county_name].sort_values('year')
    
    # Get party transitions
    elec = df_analysis[df_analysis['county'] == county_name]
    party_changes = []
    prev_party = None
    for _, row in elec.iterrows():
        if prev_party and row['local_party'] != prev_party:
            party_changes.append({
                'year': row['year'],
                'from': prev_party,
                'to': row['local_party']
            })
        prev_party = row['local_party']
    
    return cdata, party_changes

# ============================================================
# 5. SCM with 1996 baseline
# ============================================================
def synthetic_control_v2(df_all, treated_county, treatment_year, donor_counties,
                          outcome_var="log_income", start_year=1996, end_year=2024):
    """SCM with robust handling of sparse/missing data."""
    years_pre = list(range(start_year, treatment_year))
    years_post = list(range(treatment_year, end_year + 1))
    
    treated_data = df_all[(df_all['county'] == treated_county) & 
                          (df_all['year'].between(start_year, end_year))].set_index('year')
    
    available_years = treated_data.index.tolist()
    actual_pre = [y for y in years_pre if y in available_years]
    actual_post = [y for y in years_post if y in available_years]
    
    if len(actual_pre) < 2:
        return None
    
    Y1_pre = treated_data.loc[actual_pre, outcome_var].values
    if np.any(pd.isna(Y1_pre)):
        return None
    
    donor_data = {}
    valid_donors = []
    for c in donor_counties:
        if c == treated_county:
            continue
        cdata = df_all[(df_all['county'] == c) & (df_all['year'].between(start_year, end_year))].set_index('year')
        c_avail = cdata.index.tolist()
        c_pre = [y for y in actual_pre if y in c_avail]
        if len(c_pre) < len(actual_pre):
            continue
        Yj_pre = cdata.loc[actual_pre, outcome_var].values
        if np.any(pd.isna(Yj_pre)):
            continue
        donor_data[c] = cdata
        valid_donors.append(c)
    
    if len(valid_donors) < 2:
        return None
    
    J = len(valid_donors)
    T0 = len(actual_pre)
    Z0 = np.zeros((T0, J))
    for j, c in enumerate(valid_donors):
        Z0[:, j] = donor_data[c].loc[actual_pre, outcome_var].values
    
    def objective(w):
        return np.sum((Y1_pre - Z0 @ w) ** 2)
    
    result = minimize(objective, np.ones(J) / J, method='SLSQP',
                      bounds=[(0, 1) for _ in range(J)],
                      constraints=[{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}],
                      options={'maxiter': 5000, 'ftol': 1e-12})
    
    W = result['x']
    W[W < 0.001] = 0
    W = W / W.sum()
    
    all_avail = sorted(actual_pre + actual_post)
    Y_synth = np.zeros(len(all_avail))
    Y_actual = np.zeros(len(all_avail))
    for j, c in enumerate(valid_donors):
        Y_synth += W[j] * donor_data[c].loc[all_avail, outcome_var].values
    Y_actual = treated_data.loc[all_avail, outcome_var].values
    
    gaps = Y_actual - Y_synth
    gap_df = pd.DataFrame({'year': all_avail, 'treated': Y_actual, 'synthetic': Y_synth, 'gap': gaps})
    
    post_gaps = gap_df[gap_df['year'] >= treatment_year]
    avg_gap = np.mean(post_gaps['gap'])
    pre_msp = np.mean(gap_df[gap_df['year'] < treatment_year]['gap']**2)
    post_msp = np.mean(post_gaps['gap']**2)
    ratio = post_msp / pre_msp if pre_msp > 0 else np.nan
    
    return {
        'county': treated_county, 'treatment_year': treatment_year,
        'gaps': gap_df, 'avg_gap': avg_gap, 'ratio': ratio,
        'donor_weights': {valid_donors[i]: W[i] for i in range(J) if W[i] > 0.005},
    }

# Run SCM with 1996 baseline
cases_v2 = [
    ("臺南市", 1997, "DPP"), ("高雄市", 1998, "DPP"),
    ("屏東縣", 1996, "DPP"), ("嘉義縣", 2001, "DPP"),
    ("花蓮縣", 1996, "KMT"), ("南投縣", 2005, "KMT"),
    ("臺北市", 1998, "KMT"), ("苗栗縣", 2005, "KMT"),
    ("臺東縣", 1996, "KMT"), ("新竹縣", 2001, "KMT"),
    ("宜蘭縣", 2005, "MIXED"),  # KMT takeover in 2005 after long DPP
    ("彰化縣", 2005, "MIXED"),  # Frequent alternation
]

all_results = []
for county, t_year, party in cases_v2:
    if t_year <= 1996 + 2:
        # Ensure minimum pre-period
        if county == "花蓮縣" or county == "臺東縣" or county == "屏東縣":
            # These were already governed by same party in 1996 — no pre-period
            # Use them only for descriptive, not SCM
            continue
    res = synthetic_control_v2(df_analysis, county, t_year, counties,
                                start_year=BASE_YEAR, end_year=END_YEAR)
    if res:
        res['party'] = party
        all_results.append(res)
        print(f"  SCM {county}: avg_gap={res['avg_gap']:.4f}")

print(f"SCM cases: {len(all_results)}")

# ============================================================
# 6. CHART 1: RANK TRAJECTORIES — Key Counties
# ============================================================
KEY_COUNTIES = ['臺南市', '高雄市', '花蓮縣', '南投縣', '臺北市', '臺中市', '屏東縣', '臺東縣']
PARTY_COLORS = {'KMT': '#0052A5', 'DPP': '#1B9431', 'IND': '#888888', 'MIXED': '#666666'}

fig, axes = plt.subplots(3, 3, figsize=(20, 18))
axes = axes.flatten()

for idx, county in enumerate(KEY_COUNTIES):
    ax = axes[idx]
    cdata, changes = trace_county_rank_trajectory(county)
    
    years = cdata['year'].values
    ranks = cdata['income_rank'].values
    
    # Color by ruling party at each point
    party_colors_line = []
    for y in years:
        pdata = df_analysis[(df_analysis['county'] == county) & (df_analysis['year'] == y)]
        if len(pdata) == 1:
            p = pdata.iloc[0]['local_party']
            party_colors_line.append(PARTY_COLORS.get(p, '#999999'))
        else:
            party_colors_line.append('#999999')
    
    # Bar chart: rank (lower bar = better rank, i.e., higher income)
    bar_colors = ['#0052A5' if pc == PARTY_COLORS['KMT'] else 
                  '#1B9431' if pc == PARTY_COLORS['DPP'] else '#999999'
                  for pc in party_colors_line]
    
    ax.bar(years, ranks, color=bar_colors, width=0.8, alpha=0.85)
    
    # Mark party transitions
    for ch in changes:
        if ch['year'] in years:
            ax.axvline(x=ch['year'] - 0.5, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
            ax.text(ch['year'], 1, f"{ch['from']}→{ch['to']}", 
                    fontsize=8, color='red', rotation=90, va='bottom', ha='left')
    
    ax.set_title(f"{county}\nRank {cdata.iloc[0]['income_rank']:.0f} ({cdata.iloc[0]['year']:.0f}) → {cdata.iloc[-1]['income_rank']:.0f} ({cdata.iloc[-1]['year']:.0f})",
                 fontsize=11, fontweight='bold')
    ax.set_ylabel('Income Rank (1=highest)', fontsize=9)
    ax.invert_yaxis()  # rank 1 at top
    ax.set_ylim(20, 0.5)
    ax.set_xlim(BASE_YEAR - 1, END_YEAR + 1)
    ax.grid(axis='y', alpha=0.3)

# Legend
p1 = plt.Rectangle((0,0),1,1, facecolor='#0052A5', alpha=0.85)
p2 = plt.Rectangle((0,0),1,1, facecolor='#1B9431', alpha=0.85)
p3 = plt.Rectangle((0,0),1,1, facecolor='#999999', alpha=0.85)
axes[0].legend([p1, p2, p3], ['KMT ruled', 'DPP ruled', 'Other/IND'], 
               loc='upper left', fontsize=8, ncol=3)

# Hide extra subplot
axes[8].set_visible(False)

plt.suptitle('County Income Rank Trajectories (1996–2024)\nRed dashed lines = party transition; Blue = KMT, Green = DPP',
             fontsize=14, fontweight='bold', y=0.99)
plt.tight_layout()
fig.savefig(RESULTDIR / 'rank_trajectories.pdf', dpi=200, bbox_inches='tight')
fig.savefig(RESULTDIR / 'rank_trajectories.png', dpi=200, bbox_inches='tight')
print("Saved: rank_trajectories.pdf/png")
plt.close()

# ============================================================
# 7. CHART 2: Rank Change vs Party Dominance scatter
# ============================================================
fig2, axes2 = plt.subplots(1, 2, figsize=(16, 7))

# Panel A: Rank change vs party dominance
ax = axes2[0]
for _, row in growth_df.iterrows():
    color = '#0052A5' if row['dominant_party'] == 'KMT' else '#1B9431' if row['dominant_party'] == 'DPP' else '#888888'
    marker = 'o' if row['dominant_party'] == 'KMT' else 's' if row['dominant_party'] == 'DPP' else 'D'
    ax.scatter(row['kmt_pct'] * 100 if row['dominant_party'] == 'KMT' else row['dpp_pct'] * 100,
               row['rank_change'], s=200, c=color, marker=marker, edgecolors='white', linewidth=1.5)
    ax.annotate(row['county'],
                (row['kmt_pct'] * 100 if row['dominant_party'] == 'KMT' else row['dpp_pct'] * 100,
                 row['rank_change']),
                xytext=(6, 6), textcoords='offset points', fontsize=9)
ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
ax.set_xlabel('Dominant Party Control (% of 1996-2024)', fontsize=12)
ax.set_ylabel('Rank Change 1996→2024\n(positive = improved)', fontsize=12)
ax.set_title('A. National Income Rank Change vs. Party Dominance', fontsize=13, fontweight='bold')
p1 = plt.Rectangle((0,0),1,1, facecolor='#0052A5')
p2 = plt.Rectangle((0,0),1,1, facecolor='#1B9431')
p3 = plt.Rectangle((0,0),1,1, facecolor='#888888')
ax.legend([p1, p2, p3], ['KMT-dominant', 'DPP-dominant', 'Mixed'], loc='lower left', fontsize=10)

# Panel B: Rank change by party group
ax = axes2[1]
dpp_rank_changes = growth_df[growth_df['dominant_party'] == 'DPP']['rank_change'].dropna()
kmt_rank_changes = growth_df[growth_df['dominant_party'] == 'KMT']['rank_change'].dropna()

categories = ['DPP-dominant\ncounties', 'KMT-dominant\ncounties']
means = [dpp_rank_changes.mean(), kmt_rank_changes.mean()]
colors_b = ['#1B9431', '#0052A5']

bars = ax.bar(categories, means, color=colors_b, width=0.5, edgecolor='white')
ax.axhline(y=0, color='black', linewidth=1)
ax.set_ylabel('Average Rank Change 1996→2024', fontsize=12)
ax.set_title('B. Average Rank Change by Dominant Party\n(positive = rank improved)', fontsize=13, fontweight='bold')

# Add value labels
for bar, val in zip(bars, means):
    ax.text(bar.get_x() + bar.get_width()/2, val + 0.1 if val >= 0 else val - 0.4,
            f'{val:+.1f}', ha='center', fontsize=14, fontweight='bold',
            color='#166534' if val >= 0 else '#dc2626')

plt.tight_layout()
fig2.savefig(RESULTDIR / 'rank_change_analysis.pdf', dpi=200, bbox_inches='tight')
fig2.savefig(RESULTDIR / 'rank_change_analysis.png', dpi=200, bbox_inches='tight')
print("Saved: rank_change_analysis.pdf/png")
plt.close()

# ============================================================
# 8. CHART 3: Detailed before/after rank table chart
# ============================================================
fig3, ax3 = plt.subplots(figsize=(14, 7))

# Sort by rank change (most improved first)
growth_sorted = growth_df.dropna(subset=['rank_change']).sort_values('rank_change', ascending=False)

colors_bars = ['#1B9431' if r['dominant_party'] == 'DPP' else '#0052A5' for _, r in growth_sorted.iterrows()]
x_labels = [f"{r['county']}\n({r['dominant_party']})" for _, r in growth_sorted.iterrows()]

x_pos = np.arange(len(growth_sorted))
ax.bar(x_pos, growth_sorted['rank_change'], color=colors_bars, width=0.7, edgecolor='white')

# Annotate with before/after ranks
for i, (_, r) in enumerate(growth_sorted.iterrows()):
    label = f"#{int(r['rank_1996'])}→#{int(r['rank_2024'])}"
    if r['rank_change'] >= 0:
        ax.text(i, r['rank_change'] + 0.2, label, ha='center', fontsize=8, fontweight='bold', color='#166534')
    else:
        ax.text(i, r['rank_change'] - 0.3, label, ha='center', fontsize=8, fontweight='bold', color='#dc2626')

ax.set_xticks(x_pos)
ax.set_xticklabels(x_labels, fontsize=9, rotation=45, ha='right')
ax.axhline(y=0, color='black', linewidth=1)
ax.set_ylabel('Rank Change (positive = improved)', fontsize=12)
ax.set_title('National Income Rank Change 1996→2024 by County\n(rank 1 = highest per capita income)', 
             fontsize=13, fontweight='bold')
ax.grid(axis='y', alpha=0.2)

p1 = plt.Rectangle((0,0),1,1, facecolor='#0052A5')
p2 = plt.Rectangle((0,0),1,1, facecolor='#1B9431')
ax.legend([p1, p2], ['KMT-dominant', 'DPP-dominant'], loc='lower left', fontsize=10)

plt.tight_layout()
fig3.savefig(RESULTDIR / 'rank_change_bars.pdf', dpi=200, bbox_inches='tight')
fig3.savefig(RESULTDIR / 'rank_change_bars.png', dpi=200, bbox_inches='tight')
print("Saved: rank_change_bars.pdf/png")
plt.close()

# ============================================================
# 9. CHART 4: SCM treatment effects (updated)
# ============================================================
fig4, ax4 = plt.subplots(figsize=(12, 6))

scm_df = pd.DataFrame([{
    'county': r['county'], 'gap': r['avg_gap'], 'party': r['party']
} for r in all_results])
scm_df = scm_df.sort_values('gap')

colors_scm = ['#0052A5' if p == 'KMT' else '#1B9431' for p in scm_df['party']]
bars = ax4.barh(np.arange(len(scm_df)), scm_df['gap'], color=colors_scm, height=0.7)

# Labels
for i, (_, r) in enumerate(scm_df.iterrows()):
    label = f"{r['county']} ({r['party']})"
    if r['gap'] >= 0:
        ax4.text(r['gap'] + 0.001, i, label, va='center', fontsize=10, fontweight='bold', color=colors_scm[i])
    else:
        ax4.text(r['gap'] - 0.003, i, label, va='center', ha='right', fontsize=10, fontweight='bold', color=colors_scm[i])

ax4.set_yticks([])
ax4.axvline(x=0, color='black', linewidth=1.5)
ax4.set_xlabel('SCM Estimated Gap (log points)', fontsize=12)
ax4.set_title('Synthetic Control Method: Actual vs. Counterfactual Income\n(positive = outperformed counterfactual)', 
              fontsize=13, fontweight='bold')
ax4.text(0.5, 0.02, '← Underperformed    |    Outperformed →', transform=ax4.transAxes,
         fontsize=10, color='gray', ha='center')

p1 = plt.Rectangle((0,0),1,1, facecolor='#0052A5')
p2 = plt.Rectangle((0,0),1,1, facecolor='#1B9431')
ax4.legend([p1, p2], ['KMT-rule case', 'DPP-rule case'], loc='lower right', fontsize=10)

plt.tight_layout()
fig4.savefig(RESULTDIR / 'scm_effects_1996.pdf', dpi=200, bbox_inches='tight')
fig4.savefig(RESULTDIR / 'scm_effects_1996.png', dpi=200, bbox_inches='tight')
print("Saved: scm_effects_1996.pdf/png")
plt.close()

# ============================================================
# 10. CHART 5: Party-specific growth timeline for key cases
# ============================================================
fig5, axes5 = plt.subplots(2, 4, figsize=(22, 10))
axes5 = axes5.flatten()

CASE_LIST = ['臺南市', '高雄市', '花蓮縣', '南投縣', '臺北市', '屏東縣', '苗栗縣', '臺東縣']

for idx, county in enumerate(CASE_LIST):
    ax = axes5[idx]
    cdata = df_analysis[df_analysis['county'] == county]
    
    # Plot income with party-colored segments
    for i in range(1, len(cdata)):
        x = [cdata.iloc[i-1]['year'], cdata.iloc[i]['year']]
        y = [cdata.iloc[i-1]['per_capita_income'] / 10000, cdata.iloc[i]['per_capita_income'] / 10000]
        color = '#0052A5' if cdata.iloc[i-1]['local_party'] == 'KMT' else '#1B9431'
        ax.plot(x, y, linewidth=2.5, color=color, alpha=0.7)
    
    # Mark party transitions
    prev_p = None
    for _, row in cdata.iterrows():
        if prev_p and row['local_party'] != prev_p:
            ax.axvline(x=row['year'] - 0.5, color='red', linestyle='--', 
                      linewidth=1.2, alpha=0.6)
        prev_p = row['local_party']
    
    # National average for reference
    natl_avg = df_analysis.groupby('year')['per_capita_income'].mean() / 10000
    ax.plot(natl_avg.index, natl_avg.values, 'k--', linewidth=1, alpha=0.3, label='National Avg')
    
    dom_p = county_dom_party[county]
    rank_start = income_ranks.get(1996, {}).get(county, '?')
    rank_end = income_ranks.get(2024, {}).get(county, '?')
    
    ax.set_title(f"{county} ({dom_p}, #{rank_start}→#{rank_end})", 
                 fontsize=10, fontweight='bold')
    ax.set_ylabel('Income (NTD 10k)', fontsize=8)
    ax.set_xlim(BASE_YEAR - 0.5, END_YEAR + 0.5)

plt.suptitle('Per Capita Disposable Income Trajectories (1996–2024)\nBlue = KMT rule, Green = DPP rule, Red dashed = party change',
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
fig5.savefig(RESULTDIR / 'income_trajectories.pdf', dpi=200, bbox_inches='tight')
fig5.savefig(RESULTDIR / 'income_trajectories.png', dpi=200, bbox_inches='tight')
print("Saved: income_trajectories.pdf/png")
plt.close()

# ============================================================
# 11. Panel FE (re-run on 1996-2024)
# ============================================================
import statsmodels.api as sm

df_fe = df_analysis.dropna(subset=['log_income', 'dpp_dummy', 'kmt_dummy', 
                                     'aligned', 'party_alternation', 'unemployment_rate'])
X = df_fe[['dpp_dummy', 'aligned', 'party_alternation', 'unemployment_rate', 'tax_revenue_per_capita']]
X = X.copy()
X['tax_revenue_per_capita'] = X['tax_revenue_per_capita'] / 10000
X = sm.add_constant(X)

cty_dummies = pd.get_dummies(df_fe['county'], prefix='c', drop_first=True)
yr_dummies = pd.get_dummies(df_fe['year'], prefix='y', drop_first=True)
X_full = pd.concat([X, cty_dummies, yr_dummies], axis=1)

model = sm.OLS(df_fe['log_income'].astype(float), X_full.astype(float))
results = model.fit()

print("\n===== Panel FE (1996-2024) =====")
print(f"N={len(df_fe)}, R²={results.rsquared:.3f}")
for var in ['dpp_dummy', 'aligned', 'party_alternation', 'unemployment_rate']:
    coef = results.params[var]
    se = results.bse[var]
    pv = results.pvalues[var]
    sig = '***' if pv < 0.01 else '**' if pv < 0.05 else '*' if pv < 0.1 else ''
    print(f"  {var}: {coef:.4f} ({se:.4f}) p={pv:.4f} {sig}")

# Save summary stats
summary_stats = {
    'analysis_period': f'{BASE_YEAR}-{END_YEAR}',
    'n_observations': int(len(df_fe)),
    'r_squared': round(results.rsquared, 4),
    'dpp_coef': round(results.params['dpp_dummy'], 4),
    'dpp_pvalue': round(results.pvalues['dpp_dummy'], 4),
    'dpp_significant': bool(results.pvalues['dpp_dummy'] < 0.05),
    'aligned_coef': round(results.params['aligned'], 4),
    'aligned_pvalue': round(results.pvalues['aligned'], 4),
    'aligned_significant': bool(results.pvalues['aligned'] < 0.05),
    'alternation_coef': round(results.params['party_alternation'], 4),
    'alternation_pvalue': round(results.pvalues['party_alternation'], 4),
    'alternation_significant': bool(results.pvalues['party_alternation'] < 0.05),
    'dpp_avg_rank_change': round(growth_df[growth_df['dominant_party']=='DPP']['rank_change'].mean(), 1),
    'kmt_avg_rank_change': round(growth_df[growth_df['dominant_party']=='KMT']['rank_change'].mean(), 1),
    'n_scm_cases': len(all_results),
}
import json
with open(RESULTDIR / 'summary_stats.json', 'w', encoding='utf-8') as f:
    json.dump(summary_stats, f, ensure_ascii=False, indent=2)

# Save key tables
growth_df.to_csv(RESULTDIR / 'county_growth_rank.csv', index=False, encoding='utf-8')
rank_df.to_csv(RESULTDIR / 'county_rank_panel.csv', index=False, encoding='utf-8')

print("\n====== ALL DONE ======")
print(f"Growth stats: {len(growth_df)} counties")
print(f"Rank panel: {len(rank_df)} county-years")
print(f"SCM results: {len(all_results)} cases")
print("\n=== KEY FINDINGS ===")
print(f"DPP avg rank change: {summary_stats['dpp_avg_rank_change']:+.1f}")
print(f"KMT avg rank change: {summary_stats['kmt_avg_rank_change']:+.1f}")
print(f"DPP dummy p-value: {summary_stats['dpp_pvalue']:.4f}")
print(f"Aligned p-value: {summary_stats['aligned_pvalue']:.4f}")
