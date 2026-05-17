#!/usr/bin/env python3
"""Generate dashboard chart for report opening using actual data with 70% threshold."""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

DOCS_DIR = Path(__file__).resolve().parents[1]

# Font
font_path = None
for f in fm.findSystemFonts(fontext='ttc'):
    if 'com_apple' in f and 'PingFang' in f:
        font_path = f; break
if font_path:
    fm.fontManager.addfont(font_path)
    plt.rcParams['font.sans-serif'] = ['PingFang TC', 'Arial Unicode MS', 'Helvetica']
plt.rcParams['axes.unicode_minus'] = False

RESULTDIR = DOCS_DIR / "results"
df = pd.read_csv(DOCS_DIR / "data" / "merged_panel.csv")
for c in ['per_capita_income','log_income','unemployment_rate','population','tax_revenue_per_capita']:
    df[c] = pd.to_numeric(df[c], errors='coerce')
df96 = df[(df['year'] >= 1996) & (df['year'] <= 2024)].copy()

# === Dominance calc ===
counties_all = sorted([c for c in df96['county'].unique() if c not in ('金門縣','連江縣')])
dom = {}
for c in counties_all:
    cd = df96[df96['county'] == c]
    k = cd['kmt_dummy'].mean(); d = cd['dpp_dummy'].mean()
    dom[c] = {'KMT': k, 'DPP': d, 'max_pct': max(k,d), 'party': 'KMT' if k>d else 'DPP'}

THRESHOLD = 0.70

# Hualien now classified as KMT (IND years = pan-Blue/KMT-aligned)
qualifying = {c: d for c, d in dom.items() if d['max_pct'] >= THRESHOLD}

print(f"Qualifying counties (≥{THRESHOLD:.0%}): {len(qualifying)}")
for c in sorted(qualifying.keys()):
    d = qualifying[c]
    print(f"  {c}: {d['party']} {d['max_pct']:.0%}")

# === Key metrics per county ===
natl_growth = df96.groupby('year')['per_capita_income'].mean()
natl_96 = natl_growth.get(1996); natl_24 = natl_growth.get(2024)
natl_tot_growth = natl_24/natl_96 - 1

metrics = {}
for c in qualifying:
    cd = df96[df96['county'] == c]
    g = cd[cd['year'].isin([1996, 2024])].set_index('year')
    v96 = g.loc[1996,'per_capita_income']; v24 = g.loc[2024,'per_capita_income']
    growth = v24/v96 - 1
    excess = growth - natl_tot_growth
    
    # Unemployment
    ue_early = cd[cd['year'].isin([2019,2020,2021,2022,2023,2024])]['unemployment_rate'].mean()
    ue_change = cd[cd['year'].isin([1996,1997,1998,1999,2000])]['unemployment_rate'].mean() - ue_early
    
    # Population growth
    p96 = cd[cd['year']==1996]['population'].values
    p24 = cd[cd['year']==2024]['population'].values
    pop_g = p24[0]/p96[0]-1 if len(p96)>0 and len(p24)>0 else np.nan
    
    metrics[c] = {
        'growth': growth, 'excess_pp': excess*100,
        'income_96': v96, 'income_24': v24,
        'unemp_late': ue_early, 'unemp_change': ue_change,
        'pop_growth': pop_g,
        'party': qualifying[c]['party'],
        'pct': qualifying[c]['max_pct'],
        'borderline': qualifying[c].get('borderline', False),
    }

# Sort: Good cases first (by excess growth desc)
sorted_cases = sorted(metrics.items(), key=lambda x: x[1]['excess_pp'], reverse=True)
labels = [c for c, _ in sorted_cases]

# === Verdict categories ===
def verdict(excess):
    if excess >= 5: return ('Good ✓', '#dcfce7', '#16a34a')
    elif excess >= 0: return ('Modest +', '#eff6ff', '#2563eb')
    elif excess >= -5: return ('Modest −', '#fffbeb', '#d97706')
    else: return ('Bad ✗', '#fee2e2', '#dc2626')

# ===== BUILD THE DASHBOARD =====
N = len(sorted_cases)
fig = plt.figure(figsize=(20, 7 + N * 0.55))
gs = fig.add_gridspec(1, 1, left=0.06, right=0.98, top=0.93, bottom=0.04)
ax = fig.add_subplot(gs[0, 0])
ax.set_xlim(0, 100)
ax.set_ylim(0, N * 5 + 3)
ax.axis('off')

ROW_H = 4.5
START_Y = N * ROW_H + 1

# Title
ax.text(0.5, START_Y + 1.5, 'Summary Dashboard: Long-Term Single-Party Rule & Local Economic Outcomes', 
        fontsize=16, fontweight='bold', ha='center', va='center', color='#111827')
ax.text(0.5, START_Y, f'Per capita disposable income growth 1996–2024 relative to national average ({natl_tot_growth*100:.1f}%).  '
        f'Only counties with ≥{THRESHOLD:.0%} single-party control included.  '
        f'Hualien (69%) included as borderline — IND years KMT-aligned.',
        fontsize=9, ha='center', va='center', color='#6b7280')

# Column headers (x positions as %)
col_x = {
    'county': 3, 'rule': 13, 'verdict': 21, 'tw_gap': 29,
    'income': 45, 'unemp': 61, 'pop': 75, 'alignment': 88
}
for name, x in col_x.items():
    labels_h = {'county': 'County', 'rule': 'Rule Mix\n(% years)', 'verdict': 'Verdict',
                'tw_gap': 'TW Growth\nGap (pp)', 'income': 'Income Change\n(NTD 10k, 1996→2024)',
                'unemp': 'Unemployment\n(avg 2019–24)', 'pop': 'Population\n(%Δ 1996→2024)',
                'alignment': 'Political\nAlignment'}
    ax.text(x, START_Y - 1.5, labels_h[name], fontsize=8, fontweight='bold', 
            ha='center', va='center', color='#475569')

ax.axhline(y=START_Y - 2.5, xmin=0.02, xmax=0.98, color='#d1d5db', linewidth=0.8)

# === Draw each case row ===
for i, (county, m) in enumerate(sorted_cases):
    y_base = START_Y - 3 - i * ROW_H
    y_mid = y_base - ROW_H / 2 + 0.3
    
    # Row background
    facecolor = '#f9fafb' if i % 2 == 0 else 'white'
    rect = FancyBboxPatch((1, y_base - ROW_H + 0.2), 98, ROW_H - 0.4,
                          boxstyle="round,pad=0.02", facecolor=facecolor, 
                          edgecolor='#e5e7eb', linewidth=0.5, zorder=0)
    ax.add_patch(rect)
    
    # 1) County name
    party_color = '#2563eb' if m['party'] == 'KMT' else '#16a34a' if m['party'] == 'DPP' else '#9ca3af'
    note = ''
    ax.text(col_x['county'], y_mid, f"{county}{note}", fontsize=12, fontweight='bold',
            ha='left', va='center', color=party_color)
    
    # 2) Rule mix: pill with party + %
    pill_w = 6
    pill_x = col_x['rule'] - 1
    pct_str = f"{m['pct']:.0f}%"
    # Dominant party pill
    ax.add_patch(FancyBboxPatch((pill_x, y_mid - 0.7), pill_w, 1.4,
                                boxstyle="round,pad=0.4", facecolor=party_color, 
                                edgecolor='none', alpha=0.9))
    ax.text(pill_x + pill_w/2, y_mid, f"{m['party']}", fontsize=9, fontweight='bold',
            ha='center', va='center', color='white')
    # Percentage
    ax.text(pill_x + pill_w + 1.5, y_mid, pct_str, fontsize=10, 
            ha='left', va='center', color='#374151')
    
    # 3) Verdict pill
    v_text, v_bg, v_edge = verdict(m['excess_pp'])
    vx = col_x['verdict'] - 1
    ax.add_patch(FancyBboxPatch((vx, y_mid - 0.7), 6, 1.4,
                                boxstyle="round,pad=0.4", facecolor=v_bg,
                                edgecolor=v_edge, linewidth=1.5))
    ax.text(vx + 3, y_mid, v_text, fontsize=9, fontweight='bold',
            ha='center', va='center', color=v_edge)
    
    # 4) TW Growth Gap bar
    gap = m['excess_pp']
    bar_x_start = col_x['tw_gap'] + 0
    bar_center = col_x['tw_gap'] + 7
    bar_h = 0.7
    
    # Background track
    ax.add_patch(FancyBboxPatch((bar_x_start, y_mid - bar_h/2), 14, bar_h,
                                boxstyle="round,pad=0.1", facecolor='#f1f5f9',
                                edgecolor='#cbd5e1', linewidth=0.5))
    # Zero line
    ax.axvline(x=bar_center, ymin=(y_mid - bar_h)/100, ymax=(y_mid + bar_h)/100,
              color='#64748b', linewidth=1.5, zorder=3)
    # Fill bar
    bar_width = min(abs(gap) / 20 * 7, 7)  # scale: ±20pp maps to ±7 units
    if gap >= 0:
        bar_left = bar_center
        bar_c = '#16a34a' if gap >= 5 else '#22c55e'
    else:
        bar_left = bar_center - bar_width
        bar_c = '#dc2626' if gap <= -5 else '#ef4444'
    if abs(gap) > 0.2:
        ax.add_patch(FancyBboxPatch((bar_left, y_mid - bar_h/2 + 0.05), bar_width, bar_h - 0.1,
                                    boxstyle="round,pad=0.05", facecolor=bar_c,
                                    edgecolor='none', alpha=0.85, zorder=2))
    # Gap label
    ax.text(bar_x_start + 15, y_mid, f'{gap:+.1f}', fontsize=10, fontweight='bold',
            ha='left', va='center', color='#111827')
    
    # 5) Income change
    inc_96 = m['income_96'] / 10000
    inc_24 = m['income_24'] / 10000
    ax.text(col_x['income'], y_mid + 0.2, f'{inc_96:.1f} → {inc_24:.1f}', fontsize=10,
            ha='center', va='center', color='#111827')
    ax.text(col_x['income'], y_mid - 0.8, f'({m["growth"]*100:+.1f}%)', fontsize=8,
            ha='center', va='center', color='#6b7280')
    
    # 6) Unemployment
    ue_val = m['unemp_late']
    ue_color = '#16a34a' if ue_val < 3.5 else '#d97706' if ue_val < 4.0 else '#dc2626'
    ax.text(col_x['unemp'], y_mid, f'{ue_val:.1f}%', fontsize=11, fontweight='bold',
            ha='center', va='center', color=ue_color)
    
    # 7) Population
    pop_val = m['pop_growth'] * 100
    pop_color = '#16a34a' if pop_val > 0 else '#dc2626'
    ax.text(col_x['pop'], y_mid, f'{pop_val:+.1f}%', fontsize=11, fontweight='bold',
            ha='center', va='center', color=pop_color)
    
    # 8) Alignment: simple bar or percentage
    # Compute % of years aligned
    cd2 = df96[df96['county'] == county]
    aligned_pct = cd2['aligned'].mean()
    align_w = aligned_pct * 5  # scale: 100% → 5 units
    ax.add_patch(FancyBboxPatch((col_x['alignment'] - 2.5, y_mid - 0.5), 5, 1.0,
                                boxstyle="round,pad=0.1", facecolor='#f1f5f9',
                                edgecolor='#cbd5e1', linewidth=0.5))
    if align_w > 0.1:
        align_color = '#2563eb' if m['party'] == 'KMT' else '#16a34a'
        ax.add_patch(FancyBboxPatch((col_x['alignment'] - 2.5, y_mid - 0.5), align_w, 1.0,
                                    boxstyle="round,pad=0.1", facecolor=align_color,
                                    edgecolor='none', alpha=0.7))
    ax.text(col_x['alignment'] + 3, y_mid, f'{aligned_pct:.0%}', fontsize=10,
            ha='left', va='center', color='#374151')

# Footer
ax.text(50, 0.8, f'Analysis period: 1996–2024.  Dominance threshold: ≥{THRESHOLD:.0%} single-party control.  '
        f'Administrative boundary changes (2010 reform, mergers) affect year-over-year comparability but not growth-rate-based metrics.',
        fontsize=8, ha='center', va='center', color='#9ca3af')

fig.savefig(RESULTDIR / 'dashboard.png', dpi=150, bbox_inches='tight')
fig.savefig(RESULTDIR / 'dashboard.pdf', dpi=150, bbox_inches='tight')
print("Saved: dashboard.png/pdf")

# Base64 encode
import base64
b64 = base64.b64encode(open(RESULTDIR / 'dashboard.png', 'rb').read()).decode()
open(RESULTDIR / 'dashboard_b64.b64', 'w').write(b64)
print(f"dashboard b64: {len(b64)} chars")
