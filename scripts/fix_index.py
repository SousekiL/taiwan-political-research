#!/usr/bin/env python3
import re

with open('/Users/sousekilyu/Documents/Github/taiwan-political-research/docs/index.html', 'r') as f:
    content = f.read()

# === Edit A: Wrap Figure 1 (first margin:22px 0 div) ===
# Replace opening div with figure
content = content.replace(
    '  <div style="text-align:center; margin:22px 0;">',
    '  <figure id="fig-1" style="text-align:center; margin:22px 0;">',
    1
)
# Add alt to the img inside fig-1
content = content.replace(
    '      src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAACwsAAAVd',
    '  <img alt="Figure 1: Excess per capita disposable income growth by county, 1996–2024. Blue bars show KMT-dominant counties, green bars show DPP-dominant counties." src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAACwsAAAVd',
    1
)
# Replace caption p with figcaption
content = content.replace(
    '  <p style="font-size:11px; color:var(--muted); margin-top:6px;"><strong>Figure 1. Excess Income Growth by County',
    '  <figcaption style="font-size:11px; color:var(--muted); margin-top:6px;"><strong>Figure 1. Excess Income Growth by County',
    1
)
# Find "not statistically distinguishable.</p>" and replace the </p> that follows with </figcaption>
# Instead use the first occurrence after "not statistically distinguishable."
pidx = content.find('not statistically distinguishable.')
if pidx > 0:
    next_p = content.find('</p>', pidx)
    if next_p > 0:
        content = content[:next_p] + '</figcaption>' + content[next_p+4:]

# Replace the </div> immediately following </figcaption>
fcidx = content.find('</figcaption>')
if fcidx > 0:
    next_div = content.find('</div>', fcidx)
    if next_div > 0:
        content = content[:next_div] + '</figure>' + content[next_div+6:]


# === Edit B: Wrap Figure 2 (first remaining margin:18px 0 div) ===
content = content.replace(
    '  <div style="text-align:center; margin:18px 0;">',
    '  <figure id="fig-2" style="text-align:center; margin:18px 0;">',
    1
)
# Add alt to the img inside fig-2 - it starts with data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAERs...
content = content.replace(
    '  <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAERsAAAfr',
    '  <img alt="Figure 2: Per capita disposable income trajectories for eight key counties (1996–2024), showing party-colored segments and national average." src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAERsAAAfr',
    1
)
# Replace caption
content = content.replace(
    '  <p style="font-size:11px; color:var(--muted); margin-top:6px;"><strong>Figure 2. Per Capita Disposable Income Trajectories',
    '  <figcaption style="font-size:11px; color:var(--muted); margin-top:6px;"><strong>Figure 2. Per Capita Disposable Income Trajectories',
    1
)
# Find the </p> after Figure 2 caption
pidx2 = content.find('dominant party.</p>')
if pidx2 > 0:
    next_p2 = content.find('</p>', pidx2)
    if next_p2 > 0:
        content = content[:next_p2] + '</figcaption>' + content[next_p2+4:]

# Replace the </div> immediately following </figcaption>
fcidx2 = content.find('</figcaption>', fcidx + 1)
if fcidx2 > fcidx:
    next_div2 = content.find('</div>', fcidx2)
    if next_div2 > 0:
        content = content[:next_div2] + '</figure>' + content[next_div2+6:]


# === Edit C: Wrap Figure 3 (second remaining margin:18px 0 div) ===
content = content.replace(
    '  <div style="text-align:center; margin:18px 0;">',
    '  <figure id="fig-3" style="text-align:center; margin:18px 0;">',
    1
)
# Add alt to the img inside fig-3 - it starts with data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAACTY...
content = content.replace(
    '  <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAACTYAAASW',
    '  <img alt="Figure 3: SCM treatment effect estimates — the average post-treatment gap between actual and synthetic income in log points." src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAACTYAAASW',
    1
)
# Replace caption
content = content.replace(
    '  <p style="font-size:11px; color:var(--muted); margin-top:6px;"><strong>Figure 3. SCM Treatment Effects (1996 baseline).',
    '  <figcaption style="font-size:11px; color:var(--muted); margin-top:6px;"><strong>Figure 3. SCM Treatment Effects (1996 baseline).',
    1
)
# Find the </p> after Figure 3 caption
pidx3 = content.find('on both sides of zero.</p>')
if pidx3 > 0:
    next_p3 = content.find('</p>', pidx3)
    if next_p3 > 0:
        content = content[:next_p3] + '</figcaption>' + content[next_p3+4:]

# Replace the </div> immediately following </figcaption>
fcidx3 = content.find('</figcaption>', fcidx2 + 1)
if fcidx3 > fcidx2:
    next_div3 = content.find('</div>', fcidx3)
    if next_div3 > 0:
        content = content[:next_div3] + '</figure>' + content[next_div3+6:]


# === Edit D: Cross-reference "Figure 1" → #fig-1 ===
content = content.replace(
    'Figure 1 shows',
    '<a href="#fig-1">Figure 1</a> shows',
    1
)
# === Edit E: Cross-reference "Figure 2" → #fig-2 ===
content = content.replace(
    'Figure 2 illustrates',
    '<a href="#fig-2">Figure 2</a> illustrates',
    1
)
# === Edit F: Cross-reference "Figure 3" → #fig-3 ===
content = content.replace(
    'Figure 3 presents',
    '<a href="#fig-3">Figure 3</a> presents',
    1
)


# === Edit G: Add <abbr> tags for SCM after its definition ===
# Replace "The Synthetic Control Method analysis" with "The <abbr title=\"Synthetic Control Method\">SCM</abbr> analysis"
content = content.replace(
    'The Synthetic Control Method analysis, which constructs counterfactuals',
    'The <abbr title="Synthetic Control Method">SCM</abbr> analysis, which constructs counterfactuals',
    1
)

# Replace "both show positive SCM gaps" with abbr
# First find "panel FE finding" - wrap FE
content = content.replace(
    'panel FE finding on alternation effects',
    'panel <abbr title="Fixed Effects">FE</abbr> finding on alternation effects',
    1
)

# Fix FE in section 5 limitations text
content = content.replace(
    'panel FE model',
    'panel <abbr title="Fixed Effects">FE</abbr> model',
    1
)


with open('/Users/sousekilyu/Documents/Github/taiwan-political-research/docs/index.html', 'w') as f:
    f.write(content)

print("✅ HTML edits applied successfully!")
print("  - Wrapped Figure 1, 2, 3 in <figure> + <figcaption> + alt + anchor IDs")
print("  - Added cross-reference links (Figure 1→#fig-1, etc.)")
print("  - Added <abbr> for SCM, FE")
