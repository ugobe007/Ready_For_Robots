import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.patches import FancyBboxPatch
import matplotlib.gridspec as gridspec

# Color palette
NAVY = '#0F172A'
DARK_NAVY = '#1E293B'
EMERALD = '#10B981'
LIGHT_BLUE = '#38BDF8'
VIOLET = '#818CF8'
SLATE = '#64748B'
LIGHT_SLATE = '#94A3B8'
WHITE = '#FFFFFF'
OFF_WHITE = '#F8FAFC'
AMBER = '#F59E0B'
RED = '#EF4444'
TEAL = '#14B8A6'

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.facecolor'] = OFF_WHITE
plt.rcParams['figure.facecolor'] = WHITE

# ─────────────────────────────────────────────
# CHART 1: Top 12 Robots — Index Score Bar Chart
# ─────────────────────────────────────────────
robots = [
    'Dexmate Vega', 'Agibot A2', 'Agibot G5',
    'Tesla Optimus Gen 2', 'Tesla Optimus Gen 1',
    'Noble Machines', 'Deep Robotics DR02',
    'Figure 02', 'Figure 03', 'Figure 01',
    'Fourier GR-3C Cosmo', 'Fourier GR-3'
]
scores = [77.0, 77.0, 77.0, 75.0, 75.0, 73.0, 70.8, 68.8, 68.8, 68.8, 68.8, 66.8]
tiers = [
    'Commercial', 'Commercial', 'PoC/Trial',
    'PoC/Trial', 'Demo Only', 'Active Pilot',
    'Active Pilot', 'Active Pilot', 'Demo Only', 'Demo Only',
    'Active Pilot', 'Commercial'
]

tier_colors = {
    'Commercial': EMERALD,
    'Active Pilot': LIGHT_BLUE,
    'PoC/Trial': VIOLET,
    'Demo Only': AMBER
}

bar_colors = [tier_colors[t] for t in tiers]

fig, ax = plt.subplots(figsize=(12, 7))
fig.patch.set_facecolor(WHITE)
ax.set_facecolor('#F1F5F9')

# Horizontal bars
y_pos = np.arange(len(robots))
bars = ax.barh(y_pos, scores, color=bar_colors, height=0.65, zorder=3, alpha=0.92)

# Add score labels
for i, (bar, score) in enumerate(zip(bars, scores)):
    ax.text(score + 0.3, i, f'{score}', va='center', ha='left',
            fontsize=10, fontweight='bold', color=NAVY)

# Styling
ax.set_yticks(y_pos)
ax.set_yticklabels([f'#{i+1}  {r}' for i, r in enumerate(robots)],
                   fontsize=10, color=NAVY)
ax.set_xlabel('HEIR Index Score (0–100)', fontsize=11, color=SLATE, labelpad=10)
ax.set_title('Top 12 Humanoids — HEIR Index Score', fontsize=14, fontweight='bold',
             color=NAVY, pad=15)
ax.set_xlim(0, 90)
ax.axvline(x=70, color=SLATE, linestyle='--', alpha=0.4, linewidth=1, zorder=2)
ax.text(70.3, 11.6, 'Threshold 70', fontsize=8, color=SLATE, alpha=0.7)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#CBD5E1')
ax.spines['bottom'].set_color('#CBD5E1')
ax.tick_params(colors=SLATE)
ax.xaxis.label.set_color(SLATE)
ax.grid(axis='x', alpha=0.3, color='#CBD5E1', zorder=1)
ax.invert_yaxis()

# Legend
legend_patches = [mpatches.Patch(color=c, label=t) for t, c in tier_colors.items()]
ax.legend(handles=legend_patches, loc='lower right', fontsize=9,
          framealpha=0.9, edgecolor='#E2E8F0', title='Deployment Tier',
          title_fontsize=9)

plt.tight_layout()
plt.savefig('/home/ubuntu/humanoid_report/chart_index_scores.png', dpi=150, bbox_inches='tight',
            facecolor=WHITE)
plt.close()
print("Chart 1 saved")

# ─────────────────────────────────────────────
# CHART 2: Deployment Funnel (fixed)
# ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor(WHITE)
ax.set_facecolor(WHITE)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

funnel_data = [
    (103, 'Total Indexed', '100%',  LIGHT_BLUE),
    (56,  'PoC-or-Better Evidence', '54.4%', VIOLET),
    (19,  'Commercial Deployments > 0', '18.4%', EMERALD),
    (10,  'Fleet-Scale Signals', '9.7%', AMBER),
]

# All boxes share the same full width; tapering is shown via decreasing alpha
full_width = 0.82
x_left     = (1 - full_width) / 2
row_h      = 0.14
gap        = 0.06
top_y      = 0.90
alphas     = [0.95, 0.80, 0.70, 0.60]   # lighter = smaller funnel stage

for i, (val, label, pct, color) in enumerate(funnel_data):
    y_top = top_y - i * (row_h + gap)
    y_bot = y_top - row_h
    y_mid = (y_top + y_bot) / 2

    rect = FancyBboxPatch(
        (x_left, y_bot), full_width, row_h,
        boxstyle="round,pad=0.008",
        facecolor=color, alpha=alphas[i],
        edgecolor='white', linewidth=1.5,
        transform=ax.transAxes, zorder=3, clip_on=False
    )
    ax.add_patch(rect)

    combined = f"{val}   ·   {label}   ·   {pct}"
    ax.text(0.5, y_mid, combined,
            transform=ax.transAxes, ha='center', va='center',
            fontsize=11, fontweight='bold', color=NAVY, zorder=5,
            clip_on=False)

    if i < len(funnel_data) - 1:
        ax.annotate(
            '', xy=(0.5, y_bot - gap + 0.004),
            xytext=(0.5, y_bot - 0.004),
            xycoords='axes fraction', textcoords='axes fraction',
            arrowprops=dict(arrowstyle='->', color=SLATE, lw=1.8)
        )

ax.set_title('Deployment Funnel — 103 Robots Indexed', fontsize=14,
             fontweight='bold', color=NAVY, pad=14)

plt.tight_layout()
plt.savefig('/home/ubuntu/humanoid_report/chart_funnel.png', dpi=150, bbox_inches='tight',
            facecolor=WHITE)
plt.close()
print("Chart 2 saved")

# ─────────────────────────────────────────────
# CHART 3: Radar Chart — HEIF Dimensions (Top 5)
# ─────────────────────────────────────────────
categories = ['Mobility', 'Manipulation', 'Cognition', 'Safety', 'Data Pipeline', 'Production']
N = len(categories)
angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]

robots_radar = {
    'Dexmate Vega': [2.5, 3.5, 3.0, 3.0, 3.0, 3.5],
    'Agibot A2': [3.0, 3.5, 3.0, 2.0, 4.0, 3.0],
    'Tesla Optimus Gen 2': [3.0, 2.5, 3.0, 2.0, 3.5, 4.0],
    'Noble Machines': [3.0, 3.5, 3.0, 3.5, 2.5, 2.0],
    'Figure 02': [2.5, 3.0, 3.5, 2.0, 3.5, 2.0],
}

radar_colors = [EMERALD, LIGHT_BLUE, VIOLET, AMBER, TEAL]

fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
fig.patch.set_facecolor(WHITE)
ax.set_facecolor('#F8FAFC')

for i, (robot, values) in enumerate(robots_radar.items()):
    vals = values + values[:1]
    ax.plot(angles, vals, 'o-', linewidth=2, color=radar_colors[i], label=robot, alpha=0.9)
    ax.fill(angles, vals, alpha=0.08, color=radar_colors[i])

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, size=11, color=NAVY, fontweight='bold')
ax.set_ylim(0, 4)
ax.set_yticks([1, 2, 3, 4])
ax.set_yticklabels(['1', '2', '3', '4'], size=8, color=SLATE)
ax.grid(color='#CBD5E1', alpha=0.5)
ax.spines['polar'].set_color('#CBD5E1')

ax.set_title('HEIF Dimension Comparison — Top 5 Robots', size=14,
             fontweight='bold', color=NAVY, pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.15), fontsize=9,
          framealpha=0.9, edgecolor='#E2E8F0')

plt.tight_layout()
plt.savefig('/home/ubuntu/humanoid_report/chart_radar.png', dpi=150, bbox_inches='tight',
            facecolor=WHITE)
plt.close()
print("Chart 3 saved")

# ─────────────────────────────────────────────
# CHART 4: Vendor Comparison — Deployments Bar
# ─────────────────────────────────────────────
vendors = [
    'Unitree Robotics', 'Agibot\n(Zhiyuan)', 'Agility Robotics',
    'Fourier Robotics', 'UBTECH Robotics', 'Dexmate',
    'Apptronik', 'Noble Machines', 'Figure AI', 'Engineered Arts'
]
deployments = [80, 20, 20, 15, 15, 10, 10, 5, 5, 0]
poc_pct = [100, 100, 100, 100, 100, 100, 33.3, 100, 33.3, 100]

fig, ax1 = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor(WHITE)
ax1.set_facecolor('#F1F5F9')

x = np.arange(len(vendors))
bars = ax1.bar(x, deployments, color=EMERALD, alpha=0.85, width=0.55, zorder=3, label='Deployments')

ax2 = ax1.twinx()
ax2.plot(x, poc_pct, 'o--', color=VIOLET, linewidth=2, markersize=8, label='PoC+ Rate (%)', zorder=4)

ax1.set_xticks(x)
ax1.set_xticklabels(vendors, fontsize=9.5, color=NAVY, rotation=0, ha='center')
ax1.set_ylabel('Catalog Deployments', fontsize=11, color=EMERALD, labelpad=10)
ax2.set_ylabel('PoC-or-Better Rate (%)', fontsize=11, color=VIOLET, labelpad=10)
ax1.set_ylim(0, 100)
ax2.set_ylim(0, 130)
ax1.set_title('Vendor Comparison — Deployments & PoC Rate', fontsize=14,
              fontweight='bold', color=NAVY, pad=15)

# Add value labels on bars
for bar, val in zip(bars, deployments):
    if val > 0:
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                 str(val), ha='center', va='bottom', fontsize=9, fontweight='bold', color=NAVY)

ax1.spines['top'].set_visible(False)
ax2.spines['top'].set_visible(False)
ax1.spines['left'].set_color('#CBD5E1')
ax1.spines['bottom'].set_color('#CBD5E1')
ax1.grid(axis='y', alpha=0.3, color='#CBD5E1', zorder=1)
ax1.tick_params(colors=SLATE)
ax2.tick_params(colors=SLATE)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=9,
           framealpha=0.9, edgecolor='#E2E8F0')

plt.tight_layout()
plt.savefig('/home/ubuntu/humanoid_report/chart_vendors.png', dpi=150, bbox_inches='tight',
            facecolor=WHITE)
plt.close()
print("Chart 4 saved")

# ─────────────────────────────────────────────
# CHART 5: HEIF Dimension Leaders — Horizontal
# ─────────────────────────────────────────────
dimensions = ['Mobility', 'Manipulation', 'Cognition', 'Safety', 'Data Pipeline', 'Production']
leaders = ['Boston Dynamics Atlas', 'Dexmate Vega', 'Figure 02', 'Noble Machines', 'Agibot A2', 'Tesla Optimus Gen 2']
heif_scores = [4.0, 3.5, 3.5, 3.5, 4.0, 4.0]
index_scores = [100.0, 87.5, 87.5, 87.5, 100.0, 100.0]
dim_colors = [LIGHT_BLUE, EMERALD, VIOLET, AMBER, TEAL, '#F97316']

fig, ax = plt.subplots(figsize=(11, 5))
fig.patch.set_facecolor(WHITE)
ax.set_facecolor('#F1F5F9')
ax.axis('off')

col_widths = [0.14, 0.30, 0.12, 0.12]
col_x = [0.01, 0.16, 0.50, 0.64]
headers = ['Dimension', 'Leader Robot', 'HEIF Score', 'Index Score']

# Header row
for j, (hdr, x) in enumerate(zip(headers, col_x)):
    ax.text(x, 0.93, hdr, transform=ax.transAxes, fontsize=10,
            fontweight='bold', color=WHITE,
            bbox=dict(boxstyle='round,pad=0.3', facecolor=NAVY, edgecolor='none'))

# Data rows
for i, (dim, leader, heif, idx, color) in enumerate(zip(
        dimensions, leaders, heif_scores, index_scores, dim_colors)):
    y = 0.80 - i * 0.135
    bg = '#F8FAFC' if i % 2 == 0 else '#EFF6FF'

    # Row background
    rect = FancyBboxPatch((0.0, y - 0.055), 0.78, 0.115,
                          boxstyle="round,pad=0.005",
                          facecolor=bg, edgecolor='#E2E8F0', linewidth=0.5,
                          transform=ax.transAxes, zorder=2)
    ax.add_patch(rect)

    # Dimension pill
    ax.text(col_x[0] + 0.065, y, dim, transform=ax.transAxes, fontsize=9.5,
            fontweight='bold', color=WHITE, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor=color, edgecolor='none'))

    ax.text(col_x[1], y, leader, transform=ax.transAxes, fontsize=9.5,
            color=NAVY, va='center', fontweight='semibold')

    ax.text(col_x[2] + 0.06, y, f'{heif}/4.0', transform=ax.transAxes, fontsize=10,
            color=EMERALD, va='center', ha='center', fontweight='bold')

    ax.text(col_x[3] + 0.06, y, f'{idx:.0f}', transform=ax.transAxes, fontsize=10,
            color=NAVY, va='center', ha='center', fontweight='bold')

ax.set_title('HEIF Dimension Leaders', fontsize=14, fontweight='bold',
             color=NAVY, pad=10, y=1.02)

plt.tight_layout()
plt.savefig('/home/ubuntu/humanoid_report/chart_dimension_leaders.png', dpi=150,
            bbox_inches='tight', facecolor=WHITE)
plt.close()
print("Chart 5 saved")

print("\nAll charts generated successfully!")
