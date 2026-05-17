#!/usr/bin/env python3
"""
Complete analysis: SCM, panel FE, and summary visualization
for Taiwan county-level political economy study.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

RESULTDIR = Path("/Users/sousekilyu/Documents/Github/taiwan-political-research/results")
RESULTDIR.mkdir(exist_ok=True)

# ============================================
# 1. Load data
# ============================================
df = pd.read_csv("../data/merged_panel.csv")
print(f"Loaded: {len(df)} rows, {df['county'].nunique()} counties")
print(f"Years: {df['year'].min()}-{df['year'].max()}")

# ============================================
# 2. Synthetic Control Method (Python implementation)
# ============================================

def synthetic_control(df, treated_county, treatment_year, donor_counties,
                       outcome_var="log_income", start_year=1990, end_year=2024):
    """
    Python implementation of Abadie-Gardeazabal (2003) synthetic control.
    Uses constrained quadratic programming to find donor weights.
    """
    years_pre = list(range(start_year, treatment_year))
    years_post = list(range(treatment_year, end_year + 1))
    
    if len(years_pre) < 3:
        print(f"  WARNING: Only {len(years_pre)} pre-treatment years. Skipping {treated_county}.")
        return None
    
    # Get treated unit pre-treatment outcome
    treated_data = df[(df['county'] == treated_county) & (df['year'].between(start_year, end_year))]
    treated_data = treated_data.set_index('year')
    
    # Find actual available years for treated unit
    available_years = treated_data.index.tolist()
    actual_pre = [y for y in years_pre if y in available_years]
    actual_post = [y for y in years_post if y in available_years]
    
    if len(actual_pre) < 2:
        print(f"  WARNING: Only {len(actual_pre)} pre-treatment years available for {treated_county}. Skipping.")
        return None
    
    Y1_pre = treated_data.loc[actual_pre, outcome_var].values
    if np.any(pd.isna(Y1_pre)):
        print(f"  WARNING: Missing pre-treatment data for {treated_county}. Skipping.")
        return None
    
    # Get donor data
    donor_data = {}
    valid_donors = []
    for c in donor_counties:
        if c == treated_county:
            continue
        cdata = df[(df['county'] == c) & (df['year'].between(start_year, end_year))]
        cdata = cdata.set_index('year')
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
        print(f"  WARNING: Only {len(valid_donors)} valid donors for {treated_county}. Skipping.")
        return None
    
    J = len(valid_donors)
    T0 = len(actual_pre)
    
    # Build Z0 matrix (T0 x J) - donor pre-treatment outcomes
    Z0 = np.zeros((T0, J))
    for j, c in enumerate(valid_donors):
        Z0[:, j] = donor_data[c].loc[actual_pre, outcome_var].values
    
    # Constrained optimization
    def objective(w):
        return np.sum((Y1_pre - Z0 @ w) ** 2)
    
    constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
    bounds = [(0, 1) for _ in range(J)]
    x0 = np.ones(J) / J
    
    result = minimize(objective, x0, method='SLSQP', bounds=bounds,
                      constraints=constraints, options={'maxiter': 5000, 'ftol': 1e-12})
    
    W = result['x']
    W[W < 0.001] = 0
    W = W / W.sum()
    
    # Compute synthetic path using ALL available post-treatment years
    all_avail_years = sorted(actual_pre + actual_post)
    Y_synth = np.zeros(len(all_avail_years))
    Y_actual = np.zeros(len(all_avail_years))
    
    for j, c in enumerate(valid_donors):
        cdata_dep = donor_data[c].loc[all_avail_years, outcome_var].values
        Y_synth += W[j] * cdata_dep
    
    Y_actual = treated_data.loc[all_avail_years, outcome_var].values
    
    gaps = Y_actual - Y_synth
    gap_df = pd.DataFrame({
        'year': all_avail_years,
        'treated': Y_actual,
        'synthetic': Y_synth,
        'gap': gaps
    })
    
    pre_gaps = gap_df[gap_df['year'] < treatment_year]
    post_gaps = gap_df[gap_df['year'] >= treatment_year]
    
    pre_msp = np.mean(pre_gaps['gap']**2) if len(pre_gaps) > 0 else np.nan
    post_msp = np.mean(post_gaps['gap']**2) if len(post_gaps) > 0 else np.nan
    ratio = post_msp / pre_msp if (pre_msp and pre_msp > 0) else np.nan
    avg_gap = np.mean(post_gaps['gap'])
    
    donor_weights = {valid_donors[i]: W[i] for i in range(J) if W[i] > 0.005}
    
    print(f"  {treated_county}: avg_gap={avg_gap:.4f}, ratio={ratio:.2f}" if not np.isnan(ratio) else f"  {treated_county}: avg_gap={avg_gap:.4f}", 
          f"donors: {list(donor_weights.keys())[:5]}...")
    
    return {
        'county': treated_county,
        'treatment_year': treatment_year,
        'gaps': gap_df,
        'avg_gap': avg_gap,
        'pre_msp': pre_msp,
        'post_msp': post_msp,
        'ratio': ratio,
        'donor_weights': donor_weights,
    }


# ============================================
# Run SCM for all candidate cases
# ============================================
all_counties = sorted(df['county'].unique())
all_counties = [c for c in all_counties if c not in ('金門縣', '連江縣')]

cases = [
    # DPP strongholds
    ("臺南市", 1997, "DPP"),
    ("高雄市", 1998, "DPP"),
    ("屏東縣", 1993, "DPP"),
    ("嘉義縣", 2001, "DPP"),
    # KMT strongholds
    ("花蓮縣", 1990, "KMT"),
    ("南投縣", 2005, "KMT"),
    ("臺北市", 1998, "KMT"),
    ("苗栗縣", 2005, "KMT"),
    ("臺東縣", 1990, "KMT"),
    ("新竹縣", 2001, "KMT"),
]

all_results = []
for county, t_year, party in cases:
    # For treatment year = start_year, use slightly later to have some pre-period
    effective_start = 1990
    if t_year <= effective_start + 2:
        effective_start = 1990
        # For cases starting almost at beginning, use "always-treated" design
        # We use all available donors (not other long-term single-party)
        use_treatment = t_year
    else:
        use_treatment = t_year
    
    res = synthetic_control(df, county, use_treatment, all_counties,
                            start_year=1990, end_year=2024)
    if res:
        res['party'] = party
        all_results.append(res)

print(f"\nSuccessfully analyzed {len(all_results)} cases")

# Save results
import json
pd.DataFrame([{
    'county': r['county'], 'party': r['party'],
    'treatment_year': r['treatment_year'], 'avg_gap': r['avg_gap'],
    'ratio': r['ratio']
} for r in all_results]).to_csv(RESULTDIR / 'scm_summary.csv', index=False)

# ============================================
# 3. Summary Visualization
# ============================================
# For each county, compute long-term growth and party dominance metrics

# Compute 5-year growth rates per county
df_sorted = df.sort_values(['county', 'year'])
df_sorted['income_growth_5yr'] = df_sorted.groupby('county')['per_capita_income'].transform(
    lambda x: x.pct_change(periods=5)
)

# Overall income growth: (2024 income / 1998 income - 1) per county
income_growth = {}
for c in all_counties:
    cdata = df_sorted[df_sorted['county'] == c]
    val1998 = cdata[cdata['year'] == 1998]['per_capita_income'].values
    val2024 = cdata[cdata['year'] == 2024]['per_capita_income'].values
    if len(val1998) > 0 and len(val2024) > 0:
        income_growth[c] = val2024[0] / val1998[0] - 1

# Compute party dominance: fraction of 1990-2024 that party governed
party_dominance = {}
for c in all_counties:
    cdata = df_sorted[df_sorted['county'] == c]
    kmt_pct = cdata['kmt_dummy'].mean()
    dpp_pct = cdata['dpp_dummy'].mean()
    party_dominance[c] = (kmt_pct, dpp_pct)

# Determine "dominant party" and strength
dominant_party = {}
dominance_pct = {}
for c in all_counties:
    k, d = party_dominance[c]
    if k > d:
        dominant_party[c] = 'KMT'
        dominance_pct[c] = k
    elif d > k:
        dominant_party[c] = 'DPP'
        dominance_pct[c] = d
    else:
        dominant_party[c] = 'MIXED'
        dominance_pct[c] = 0.5

# Build summary dataframe for visualization
summary_rows = []
for c in all_counties:
    if c in income_growth:
        avg_income_2024 = df_sorted[(df_sorted['county'] == c) & (df_sorted['year'] == 2024)]['per_capita_income'].values[0]
        avg_unemp = df_sorted[(df_sorted['county'] == c) & (df_sorted['year'].between(2019, 2024))]['unemployment_rate'].mean()
        pop_growth = (df_sorted[(df_sorted['county'] == c) & (df_sorted['year'] == 2024)]['population'].values[0] /
                      df_sorted[(df_sorted['county'] == c) & (df_sorted['year'] == 2000)]['population'].values[0] - 1)
        
        summary_rows.append({
            'county': c,
            'dominant_party': dominant_party[c],
            'dominance_ratio': dominance_pct[c],
            'income_growth': income_growth[c],
            'income_2024': avg_income_2024,
            'unemp_2019_2024': avg_unemp,
            'pop_growth_2000_2024': pop_growth,
            'kmt_pct': party_dominance[c][0],
            'dpp_pct': party_dominance[c][1],
        })

summary_df = pd.DataFrame(summary_rows)
# Assign SCM gap for each county (from results)
gap_map = {r['county']: r['avg_gap'] for r in all_results}
summary_df['scm_gap'] = summary_df['county'].map(gap_map)

# ============================================
# 3A. MAIN FIGURE: Party-Colored Growth vs Dominance
# ============================================
fig, axes = plt.subplots(2, 2, figsize=(16, 14))

# ---- Panel A: Growth vs Dominance ----
ax = axes[0, 0]
for _, row in summary_df.iterrows():
    color = '#1B9431' if row['dominant_party'] == 'DPP' else '#0052A5' if row['dominant_party'] == 'KMT' else '#888888'
    ax.scatter(row['dominance_ratio']*100, row['income_growth']*100, 
               s=200, c=color, edgecolors='white', linewidth=1.5, 
               alpha=0.85, zorder=5)
    # Label selected counties
    if row['county'] in ['臺南市', '高雄市', '花蓮縣', '南投縣', '臺北市', '屏東縣', '臺東縣']:
        ax.annotate(row['county'], (row['dominance_ratio']*100, row['income_growth']*100),
                    xytext=(8, 8), textcoords='offset points', fontsize=9,
                    fontproperties='Arial Unicode MS')
ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
ax.set_xlabel('Party Dominance (%)', fontsize=12)
ax.set_ylabel('Income Growth 1998-2024 (%)', fontsize=12)
ax.set_title('A. Income Growth vs. Party Dominance', fontsize=13, fontweight='bold')
# Legends
p1 = mpatches.Patch(color='#0052A5', label='KMT-dominant')
p2 = mpatches.Patch(color='#1B9431', label='DPP-dominant')
p3 = mpatches.Patch(color='#888888', label='Mixed')
ax.legend(handles=[p1, p2, p3], loc='lower right', fontsize=10)

# ---- Panel B: Income Level by Party ----
ax = axes[0, 1]
dpp_counties = summary_df[summary_df['dominant_party'] == 'DPP'].sort_values('income_2024')
kmt_counties = summary_df[summary_df['dominant_party'] == 'KMT'].sort_values('income_2024')

y_pos_dpp = np.arange(len(dpp_counties))
y_pos_kmt = np.arange(len(kmt_counties)) + len(dpp_counties) + 1

all_bars = pd.concat([dpp_counties, kmt_counties])
colors = ['#1B9431'] * len(dpp_counties) + ['#0052A5'] * len(kmt_counties)
all_y = list(y_pos_dpp) + list(y_pos_kmt)

bars = ax.barh(all_y, all_bars['income_2024']/10000, color=colors, height=0.7)
# Labels
labels = list(dpp_counties['county']) + list(kmt_counties['county'])
ax.set_yticks(all_y)
ax.set_yticklabels(labels, fontsize=10)
ax.set_xlabel('Per Capita Disposable Income 2024 (NTD 10,000)', fontsize=12)
ax.set_title('B. 2024 Income Level by Dominant Party', fontsize=13, fontweight='bold')
ax.axvline(x=summary_df['income_2024'].mean()/10000, color='red', linestyle='--', 
           alpha=0.5, label='National Average')
ax.legend(fontsize=10)

# ---- Panel C: Unemployment vs Growth ----
ax = axes[1, 0]
for _, row in summary_df.iterrows():
    color = '#1B9431' if row['dominant_party'] == 'DPP' else '#0052A5' if row['dominant_party'] == 'KMT' else '#888888'
    ax.scatter(row['unemp_2019_2024'], row['income_growth']*100, 
               s=200, c=color, edgecolors='white', linewidth=1.5, alpha=0.85)
    if row['county'] in ['臺南市', '高雄市', '花蓮縣', '南投縣', '臺北市', '屏東縣', '臺東縣']:
        ax.annotate(row['county'], (row['unemp_2019_2024'], row['income_growth']*100),
                    xytext=(8, 8), textcoords='offset points', fontsize=9)
ax.set_xlabel('Avg Unemployment Rate 2019-2024 (%)', fontsize=12)
ax.set_ylabel('Income Growth 1998-2024 (%)', fontsize=12)
ax.set_title('C. Growth vs. Unemployment', fontsize=13, fontweight='bold')
ax.legend(handles=[p1, p2, p3], loc='upper right', fontsize=10)

# ---- Panel D: SCM Gaps (estimated treatment effects) ----
ax = axes[1, 1]
scm_data = summary_df.dropna(subset=['scm_gap']).sort_values('scm_gap')
colors_d = ['#1B9431' if r['dominant_party'] == 'DPP' else '#0052A5' for _, r in scm_data.iterrows()]

bars = ax.barh(np.arange(len(scm_data)), scm_data['scm_gap'], 
               color=colors_d, height=0.7)
ax.set_yticks(np.arange(len(scm_data)))
ax.set_yticklabels(scm_data['county'], fontsize=10)
ax.axvline(x=0, color='black', linewidth=1)
ax.set_xlabel('SCM Estimated Gap (log points)', fontsize=12)
ax.set_title('D. SCM Treatment Effect (Actual - Synthetic)', fontsize=13, fontweight='bold')

# Positive = outperformed counterfactual (good)
# Negative = underperformed (bad)
ax.text(0.02, 0.02, '← Underperformed | Outperformed →', transform=ax.transAxes,
        fontsize=10, color='gray', ha='center')
ax.legend(handles=[p1, p2], loc='lower right', fontsize=10)

plt.tight_layout(pad=3)
fig.savefig(RESULTDIR / 'summary_quad.pdf', dpi=200, bbox_inches='tight')
fig.savefig(RESULTDIR / 'summary_quad.png', dpi=200, bbox_inches='tight')
print("Saved: summary_quad.pdf/png")
plt.close()

# ============================================
# 3B. ALIGNMENT ANALYSIS: How central-local alignment affects outcomes
# ============================================
fig2, axes2 = plt.subplots(1, 2, figsize=(16, 6))

# Compute aligned vs unaligned growth rates
align_growth = []
for c in all_counties:
    cdata = df_sorted[df_sorted['county'] == c]
    aligned_data = cdata[cdata['aligned'] == 1]
    unaligned_data = cdata[cdata['aligned'] == 0]
    
    if len(aligned_data) > 5 and len(unaligned_data) > 5:
        aligned_growth = aligned_data['per_capita_income'].pct_change(periods=3).mean()
        unaligned_growth = unaligned_data['per_capita_income'].pct_change(periods=3).mean()
        align_growth.append({
            'county': c,
            'aligned_growth': aligned_growth * 100,
            'unaligned_growth': unaligned_growth * 100,
            'diff': (aligned_growth - unaligned_growth) * 100,
            'dominant_party': dominant_party[c],
        })

align_df = pd.DataFrame(align_growth).sort_values('diff')

ax = axes2[0]
colors_a = ['#1B9431' if r['dominant_party'] == 'DPP' else '#0052A5' for _, r in align_df.iterrows()]
ax.barh(np.arange(len(align_df)), align_df['diff'], color=colors_a, height=0.7)
ax.set_yticks(np.arange(len(align_df)))
ax.set_yticklabels(align_df['county'], fontsize=9)
ax.axvline(x=0, color='black', linewidth=1)
ax.set_xlabel('Aligned - Unaligned Growth Differential (pp)', fontsize=12)
ax.set_title('A. Alignment Premium by County\n(Positive = aligned period grew faster)', fontsize=13, fontweight='bold')
ax.legend(handles=[p1, p2], loc='lower right', fontsize=10)

ax = axes2[1]
# Average by party
avg_dpp = align_df[align_df['dominant_party'] == 'DPP']['diff'].mean()
avg_kmt = align_df[align_df['dominant_party'] == 'KMT']['diff'].mean()
ax.bar(['DPP-dominant\ncounties', 'KMT-dominant\ncounties'], [avg_dpp, avg_kmt],
       color=['#1B9431', '#0052A5'], width=0.5)
ax.axhline(y=0, color='black', linewidth=1)
ax.set_ylabel('Alignment Growth Premium (pp)', fontsize=12)
ax.set_title('B. Average Alignment Effect by Dominant Party', fontsize=13, fontweight='bold')
for i, (v, p) in enumerate(zip([avg_dpp, avg_kmt], ['#1B9431', '#0052A5'])):
    ax.text(i, v + (0.1 if v >= 0 else -0.3), f'{v:.2f}', ha='center', fontweight='bold', 
            fontsize=12, color=p)

plt.tight_layout()
fig2.savefig(RESULTDIR / 'alignment_analysis.pdf', dpi=200, bbox_inches='tight')
fig2.savefig(RESULTDIR / 'alignment_analysis.png', dpi=200, bbox_inches='tight')
print("Saved: alignment_analysis.pdf/png")
plt.close()

# ============================================
# 3C. SEPARATE PARTY-SPECIFIC GROWTH VS DOMINANCE CHARTS
# ============================================
fig3, axes3 = plt.subplots(1, 3, figsize=(18, 6))

# Panel A: All counties, party-colored
ax = axes3[0]
for _, row in summary_df.iterrows():
    color = '#1B9431' if row['dominant_party'] == 'DPP' else '#0052A5'
    marker = 's' if row['dominant_party'] == 'DPP' else 'o'
    ax.scatter(row['dominance_ratio']*100, row['income_growth']*100,
               s=180, c=color, marker=marker, edgecolors='white', linewidth=1.2)
    if row['county'] in ['臺南市', '高雄市', '花蓮縣', '南投縣', '臺北市']:
        ax.annotate(row['county'], (row['dominance_ratio']*100, row['income_growth']*100),
                    xytext=(8, 8), textcoords='offset points', fontsize=9)
ax.axhline(y=np.mean(summary_df['income_growth']*100), color='gray', linestyle='--', alpha=0.5)
ax.set_xlabel('Party Dominance (% years ruled)', fontsize=11)
ax.set_ylabel('Income Growth 1998-2024 (%)', fontsize=11)
ax.set_title('A. All Counties', fontsize=13, fontweight='bold')
ax.legend(handles=[p1, p2], loc='lower right')

# Panel B: KMT-dominant only
ax = axes3[1]
kdf = summary_df[summary_df['dominant_party'] == 'KMT']
avg_kmt_growth = np.mean(kdf['income_growth'] * 100)
for _, row in kdf.iterrows():
    ax.scatter(row['dominance_ratio']*100, row['income_growth']*100,
               s=200, c='#0052A5', edgecolors='white', linewidth=1.5)
    ax.annotate(row['county'], (row['dominance_ratio']*100, row['income_growth']*100),
                xytext=(6, 6), textcoords='offset points', fontsize=10)
ax.axhline(y=avg_kmt_growth, color='#0052A5', linestyle='--', alpha=0.5,
           label=f'KMT Avg: {avg_kmt_growth:.1f}%')
ax.set_xlabel('KMT Dominance (% years)', fontsize=11)
ax.set_ylabel('Income Growth 1998-2024 (%)', fontsize=11)
ax.set_title('B. KMT-Dominant Counties Only', fontsize=13, fontweight='bold')
ax.legend(fontsize=10)

# Panel C: DPP-dominant only
ax = axes3[2]
ddf = summary_df[summary_df['dominant_party'] == 'DPP']
avg_dpp_growth = np.mean(ddf['income_growth'] * 100)
for _, row in ddf.iterrows():
    ax.scatter(row['dominance_ratio']*100, row['income_growth']*100,
               s=200, c='#1B9431', marker='s', edgecolors='white', linewidth=1.5)
    ax.annotate(row['county'], (row['dominance_ratio']*100, row['income_growth']*100),
                xytext=(6, 6), textcoords='offset points', fontsize=10)
ax.axhline(y=avg_dpp_growth, color='#1B9431', linestyle='--', alpha=0.5,
           label=f'DPP Avg: {avg_dpp_growth:.1f}%')
ax.set_xlabel('DPP Dominance (% years)', fontsize=11)
ax.set_ylabel('Income Growth 1998-2024 (%)', fontsize=11)
ax.set_title('C. DPP-Dominant Counties Only', fontsize=13, fontweight='bold')
ax.legend(fontsize=10)

plt.tight_layout()
fig3.savefig(RESULTDIR / 'party_split_growth.pdf', dpi=200, bbox_inches='tight')
fig3.savefig(RESULTDIR / 'party_split_growth.png', dpi=200, bbox_inches='tight')
print("Saved: party_split_growth.pdf/png")
plt.close()

# ============================================
# 4. Panel FE Regression Summary
# ============================================
import statsmodels.api as sm

# Simple FE check
df_fe = df.dropna(subset=['log_income', 'dpp_dummy', 'kmt_dummy', 'aligned', 
                            'party_alternation', 'unemployment_rate'])
df_fe = df_fe.copy()
df_fe['county_code'] = df_fe['county'].astype('category').cat.codes
df_fe['year_f'] = df_fe['year'].astype(str)

X = df_fe[['dpp_dummy', 'aligned', 'party_alternation', 'unemployment_rate', 
            'tax_revenue_per_capita']]
X = sm.add_constant(X)
X['tax_revenue_per_capita'] = X['tax_revenue_per_capita'] / 10000  # scale

# Add county FE
county_dummies = pd.get_dummies(df_fe['county'], prefix='cty')
# Add year FE
year_dummies = pd.get_dummies(df_fe['year'], prefix='yr')

X_full = pd.concat([X, county_dummies.iloc[:, 1:], year_dummies.iloc[:, 1:]], axis=1)

model = sm.OLS(df_fe['log_income'].astype(float), X_full.astype(float))
results = model.fit()

print("\n===== Panel FE Regression =====")
print(f"N={len(df_fe)}, R²={results.rsquared:.3f}")
print(f"DPP dummy: {results.params['dpp_dummy']:.4f} (p={results.pvalues['dpp_dummy']:.4f})")
print(f"Aligned:   {results.params['aligned']:.4f} (p={results.pvalues['aligned']:.4f})")
print(f"Alternation: {results.params['party_alternation']:.4f} (p={results.pvalues['party_alternation']:.4f})")

# Save regression table
reg_table = pd.DataFrame({
    'Variable': ['DPP dummy', 'Aligned (central=local)', 'Party Alternation', 
                 'Unemployment Rate', 'Tax Revenue per capita'],
    'Coefficient': [results.params['dpp_dummy'], results.params['aligned'],
                    results.params['party_alternation'], results.params['unemployment_rate'],
                    results.params['tax_revenue_per_capita']],
    'Std_Error': [results.bse['dpp_dummy'], results.bse['aligned'],
                  results.bse['party_alternation'], results.bse['unemployment_rate'],
                  results.bse['tax_revenue_per_capita']],
    'P_value': [results.pvalues['dpp_dummy'], results.pvalues['aligned'],
                results.pvalues['party_alternation'], results.pvalues['unemployment_rate'],
                results.pvalues['tax_revenue_per_capita']],
})
reg_table.to_csv(RESULTDIR / 'panel_fe_results.csv', index=False)
print("Saved: panel_fe_results.csv")

# Save summary_df for report integration
summary_df.to_csv(RESULTDIR / 'county_summary.csv', index=False, encoding='utf-8')
print("Saved: county_summary.csv")

# ============================================
# 5. Key Finding Print
# ============================================
print("\n" + "="*60)
print("KEY FINDINGS FOR REPORT")
print("="*60)
print(f"\nDPP-dominant counties avg growth: {avg_dpp_growth:.1f}%")
print(f"KMT-dominant counties avg growth: {avg_kmt_growth:.1f}%")
print(f"DPP alignment premium: {avg_dpp:.2f} pp")
print(f"KMT alignment premium: {avg_kmt:.2f} pp")
print(f"Panel FE DPP coefficient: {results.params['dpp_dummy']:.4f} (p={results.pvalues['dpp_dummy']:.4f})")
print(f"Panel FE Aligned coefficient: {results.params['aligned']:.4f} (p={results.pvalues['aligned']:.4f})")
print("="*60)
