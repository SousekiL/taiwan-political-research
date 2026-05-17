#!/usr/bin/env python3
"""
Generate the ONE summary chart for the conclusion section.
Clean, academic, minimal — shows the key finding at a glance.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

font_path = None
for f in fm.findSystemFonts(fontext='ttc'):
    if 'com_apple' in f and 'PingFang' in f:
        font_path = f; break
if font_path:
    fm.fontManager.addfont(font_path)
    plt.rcParams['font.sans-serif'] = ['PingFang TC', 'Arial Unicode MS', 'Helvetica']
plt.rcParams['axes.unicode_minus'] = False

RESULTDIR = Path("/Users/sousekilyu/Documents/Github/taiwan-political-research/results")
RESULTDIR.mkdir(exist_ok=True)

df = pd.read_csv("../data/merged_panel.csv")
for c in ['per_capita_income','log_income','unemployment_rate','population','tax_revenue_per_capita']:
    df[c] = pd.to_numeric(df[c], errors='coerce')

df96 = df[(df['year'] >= 1996) & (df['year'] <= 2024)].copy()
counties = sorted([c for c in df96['county'].unique() if c not in ('金門縣','連江縣')])

# --- Core metric: income growth 1996-2024 relative to national average ---
natl_growth_96_24 = {}
for c in counties:
    cd = df96[df96['county'] == c]
    g = cd[cd['year'].isin([1996, 2024])].copy()
    natl = df96.groupby('year')['per_capita_income'].mean()
    avg_96 = natl.get(1996); avg_24 = natl.get(2024)
    natl_growth = avg_24/avg_96 - 1 if avg_96 else np.nan
    natl_growth_96_24[c] = natl_growth

# Party dominance
dom_party = {}; dominance = {}
for c in counties:
    cd = df96[df96['county'] == c]
    k = cd['kmt_dummy'].mean(); d = cd['dpp_dummy'].mean()
    dom_party[c] = 'KMT' if k > d else 'DPP' if d > k else 'MIXED'
    dominance[c] = max(k, d)

# Build summary
rows = []
for c in counties:
    cd = df96[df96['county'] == c]
    g = cd[cd['year'].isin([1996, 2024])]
    if len(g) < 2: continue
    g = g.set_index('year')
    v96 = g.loc[1996,'per_capita_income']; v24 = g.loc[2024,'per_capita_income']
    growth = v24/v96 - 1
    excess = growth - natl_growth_96_24[c]
    rows.append({
        'county': c, 'party': dom_party[c], 'dominance_pct': dominance[c]*100,
        'income_1996': v96, 'income_2024': v24, 'growth_pct': growth*100,
        'excess_growth_pct': excess*100, 'excess_growth_log': np.log(1+growth) - np.log(1+natl_growth_96_24[c])
    })
sdf = pd.DataFrame(rows).sort_values('excess_growth_pct')

print("Counties sorted by excess growth over national average:")
for _, r in sdf.iterrows():
    print(f"  {r['county']:6s} ({r['party']:4s} {r['dominance_pct']:.0f}% dom): "
          f"growth {r['growth_pct']:5.1f}% → excess {r['excess_growth_pct']:+5.1f}%")

# ========== THE ONE CHART ==========
fig, ax = plt.subplots(figsize=(12, 7))

colors = ['#0052A5' if p == 'KMT' else '#1B9431' if p == 'DPP' else '#888888' 
          for p in sdf['party']]
bars = ax.barh(range(len(sdf)), sdf['excess_growth_pct'], color=colors, height=0.65, edgecolor='white')

# Labels
for i, (_, r) in enumerate(sdf.iterrows()):
    label = f"{r['county']}   {r['growth_pct']:+.1f}%"
    xval = r['excess_growth_pct']
    if xval >= 0:
        ax.text(xval + 0.5, i, label, va='center', fontsize=10, color=colors[i])
    else:
        ax.text(xval - 0.5, i, label, va='center', ha='right', fontsize=10, color=colors[i])

ax.set_yticks([])
ax.axvline(x=0, color='black', linewidth=1.2, zorder=0)
ax.set_xlabel('Excess Growth Over National Average (percentage points)', fontsize=11)

# Annotation
ax.text(0.02, 0.98, '← Lagged behind nation    |    Outpaced nation →', 
        transform=ax.transAxes, fontsize=10, color='#78716c', va='top', ha='center')

# Legend with meaning
ax.text(0.01, 0.015, 'Per capita disposable income growth 1996–2024, relative to national average growth of '
        f'{natl_growth_96_24.get(counties[0],0)*100:.1f}%.  Administrative boundary changes (e.g., county mergers, '
        'special municipality upgrades) affect year-over-year comparability and are noted in the full discussion.',
        transform=ax.transAxes, fontsize=8, color='#a8a29e', va='bottom')

import matplotlib.patches as mpatches
ax.legend(handles=[
    mpatches.Patch(color='#0052A5', label='KMT-dominant'),
    mpatches.Patch(color='#1B9431', label='DPP-dominant'),
    mpatches.Patch(color='#888888', label='Mixed/Alternating'),
], loc='lower right', fontsize=9)

# Title
ax.set_title('Long-Term Party Rule and Local Economic Growth in Taiwan\n'
             'Per Capita Disposable Income Growth vs. National Average, 1996–2024',
             fontsize=13, fontweight='bold', pad=15)

plt.tight_layout()
fig.savefig(RESULTDIR / 'summary_conclusion.png', dpi=200, bbox_inches='tight')
fig.savefig(RESULTDIR / 'summary_conclusion.pdf', dpi=200, bbox_inches='tight')
print("\nSaved: summary_conclusion.png/pdf")

# Also save the key numbers
sdf.to_csv(RESULTDIR / 'county_excess_growth.csv', index=False, encoding='utf-8')
print("Saved: county_excess_growth.csv")

# ========== Key stats for report text ==========
dpp_avg = sdf[sdf['party'] == 'DPP']['excess_growth_pct'].mean()
kmt_avg = sdf[sdf['party'] == 'KMT']['excess_growth_pct'].mean()
print(f"\nDPP avg excess growth: {dpp_avg:+.1f} pp")
print(f"KMT avg excess growth: {kmt_avg:+.1f} pp")
