"""Generate report figures from experiment results."""
import json
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import pandas as pd
from pathlib import Path

matplotlib.rcParams.update({
    'font.size': 11,
    'font.family': 'sans-serif',
    'axes.titlesize': 13,
    'axes.labelsize': 11,
    'figure.dpi': 150,
})

OUT = Path(__file__).parent
DATA = Path(__file__).parent.parent / "output"

results = json.load(open(DATA / "all_results.json"))
df = pd.DataFrame(results)

# Parse variant
def split_task(t):
    for s in ['_guided', '_agent', '_reflect']:
        if t.endswith(s):
            return t.replace(s, ''), s[1:]
    return t, 'base'

df['base_task'] = df.task_type.apply(lambda t: split_task(t)[0])
df['variant'] = df.task_type.apply(lambda t: split_task(t)[1])
df['dataset'] = df.task_id.apply(lambda t: 'extended' if '/' in t else 'base')

MODELS = ['gemini-2.5-flash-lite', 'gemini-2.5-pro']
MODEL_LABELS = {'gemini-2.5-flash-lite': 'Flash Lite', 'gemini-2.5-pro': 'Pro'}
VARIANTS = ['base', 'guided', 'agent', 'reflect']
TASKS = ['nl2alloy', 'alloy2alloy', 'sketch2alloy']
TASK_LABELS = {'nl2alloy': 'NL → Alloy', 'alloy2alloy': 'Alloy → Alloy', 'sketch2alloy': 'Sketch → Alloy'}
COLORS = {'base': '#4C72B0', 'guided': '#55A868', 'agent': '#C44E52', 'reflect': '#8172B2'}


# ── Figure 1: Main results table-like grouped bar chart ──────────────────
# Paper-style: per-task pass rates, comparing models and variants
fig, axes = plt.subplots(1, 3, figsize=(14, 5), sharey=True)

for ax, task in zip(axes, TASKS):
    sub = df[df.base_task == task]
    x = np.arange(len(VARIANTS))
    width = 0.35
    for i, model in enumerate(MODELS):
        rates = []
        for v in VARIANTS:
            mask = (sub.model == model) & (sub.variant == v)
            if mask.sum() > 0:
                rates.append(sub[mask].passed.mean() * 100)
            else:
                rates.append(0)
        bars = ax.bar(x + i * width, rates, width, label=MODEL_LABELS[model],
                      color=['#4C72B0', '#C44E52'][i], alpha=0.85)
        for bar, rate in zip(bars, rates):
            if rate > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
                        f'{rate:.0f}', ha='center', va='bottom', fontsize=8)

    ax.set_title(TASK_LABELS[task], fontweight='bold')
    ax.set_xticks(x + width/2)
    ax.set_xticklabels([v.capitalize() for v in VARIANTS], rotation=30, ha='right')
    ax.set_ylim(0, 115)
    ax.axhline(y=100, color='gray', linestyle=':', alpha=0.3)

axes[0].set_ylabel('Pass Rate (%)')
axes[0].legend(loc='upper left', fontsize=9)
fig.suptitle('Pass Rates by Task, Variant, and Model', fontweight='bold', fontsize=14)
plt.tight_layout()
fig.savefig(OUT / 'fig1_main_results.png', bbox_inches='tight')
plt.close()
print('Saved fig1_main_results.png')


# ── Figure 2: Variant improvement over base (delta chart) ───────────────
fig, axes = plt.subplots(1, 2, figsize=(10, 5))

for ax, model in zip(axes, MODELS):
    for task in TASKS:
        base_rate = df[(df.model == model) & (df.base_task == task) & (df.variant == 'base')].passed.mean() * 100
        deltas = []
        labels = []
        for v in ['guided', 'agent', 'reflect']:
            mask = (df.model == model) & (df.base_task == task) & (df.variant == v)
            if mask.sum() > 0:
                rate = df[mask].passed.mean() * 100
                deltas.append(rate - base_rate)
                labels.append(v.capitalize())
            else:
                deltas.append(0)
                labels.append(v.capitalize())

        x = np.arange(len(labels))
        ax.bar(x + TASKS.index(task) * 0.25, deltas, 0.22,
               label=TASK_LABELS[task] if model == MODELS[0] else '',
               color=['#4C72B0', '#55A868', '#C44E52'][TASKS.index(task)], alpha=0.85)

    ax.set_title(MODEL_LABELS[model], fontweight='bold')
    ax.set_xticks(np.arange(3) + 0.25)
    ax.set_xticklabels(['Guided', 'Agent', 'Reflect'])
    ax.axhline(y=0, color='black', linewidth=0.5)
    ax.set_ylabel('Change in Pass Rate (pp)')
    ax.set_ylim(-15, 30)

axes[0].legend(fontsize=9)
fig.suptitle('Improvement Over Base Variant (percentage points)', fontweight='bold', fontsize=13)
plt.tight_layout()
fig.savefig(OUT / 'fig2_variant_delta.png', bbox_inches='tight')
plt.close()
print('Saved fig2_variant_delta.png')


# ── Figure 3: Error breakdown stacked bar ────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

error_types = ['Syntax Error', 'Type Error', 'Counterexample']
error_colors = ['#e74c3c', '#f39c12', '#3498db']

for ax, model in zip(axes, MODELS):
    sub = df[(df.model == model) & (~df.passed)]
    task_types = sorted(df.task_type.unique())

    bottoms = np.zeros(len(task_types))
    for err, color in zip(error_types, error_colors):
        counts = []
        for tt in task_types:
            counts.append(((sub.task_type == tt) & (sub.error == err)).sum())
        ax.barh(range(len(task_types)), counts, left=bottoms, color=color, label=err, alpha=0.85)
        bottoms += counts

    ax.set_yticks(range(len(task_types)))
    short_labels = [t.replace('alloy2alloy', 'a2a').replace('nl2alloy', 'nl2a').replace('sketch2alloy', 's2a') for t in task_types]
    ax.set_yticklabels(short_labels, fontsize=8)
    ax.set_title(MODEL_LABELS[model], fontweight='bold')
    ax.set_xlabel('Number of Failures')
    ax.invert_yaxis()

axes[1].legend(loc='lower right', fontsize=9)
fig.suptitle('Error Type Breakdown', fontweight='bold', fontsize=13)
plt.tight_layout()
fig.savefig(OUT / 'fig3_error_breakdown.png', bbox_inches='tight')
plt.close()
print('Saved fig3_error_breakdown.png')


# ── Figure 4: Per-property heatmap (base tasks only, like the paper) ─────
fig, axes = plt.subplots(1, 3, figsize=(15, 7), gridspec_kw={'wspace': 0.3})

base_props = [p for p in df.task_id.unique() if '/' not in p]
base_props = sorted(base_props)

for ax, task in zip(axes, TASKS):
    sub = df[(df.base_task == task) & (df.variant == 'base') & (df.task_id.isin(base_props))]
    if sub.empty:
        ax.set_visible(False)
        continue

    pivot = sub.pivot_table(values='passed', index='task_id', columns='model', aggfunc='mean')
    pivot = pivot.reindex(base_props)
    pivot = pivot[MODELS] if all(m in pivot.columns for m in MODELS) else pivot

    im = ax.imshow(pivot.values * 100, cmap='RdYlGn', vmin=0, vmax=100, aspect='auto')
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([MODEL_LABELS.get(m, m) for m in pivot.columns], rotation=45, ha='right')
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index if task == TASKS[0] else [])
    ax.set_title(TASK_LABELS[task], fontweight='bold')

    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j] * 100
            if not np.isnan(val):
                ax.text(j, i, f'{val:.0f}%', ha='center', va='center', fontsize=9,
                        color='white' if val < 40 else 'black')

cbar = fig.colorbar(im, ax=axes, shrink=0.5, pad=0.02, label='Pass Rate (%)')
fig.suptitle('Pass Rate by Property (Base Dataset, Base Variant)', fontweight='bold', fontsize=14, y=1.01)
fig.savefig(OUT / 'fig4_property_heatmap.png', bbox_inches='tight')
plt.close()
print('Saved fig4_property_heatmap.png')


# ── Figure 5: Base vs Extended domain comparison ─────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))

domains = {'base': 'Base (11)', 'graph': 'Graph (5)', 'social_network': 'Social Net (7)',
           'production_line': 'Prod. Line (9)', 'trash': 'Trash (9)'}

df['domain'] = df.task_id.apply(lambda t: t.split('/')[0] if '/' in t else 'base')

x = np.arange(len(domains))
width = 0.35
for i, model in enumerate(MODELS):
    rates = []
    for domain in domains:
        mask = (df.model == model) & (df.domain == domain) & (df.variant == 'base')
        if mask.sum() > 0:
            rates.append(df[mask].passed.mean() * 100)
        else:
            rates.append(0)
    bars = ax.bar(x + i * width, rates, width, label=MODEL_LABELS[model],
                  color=['#4C72B0', '#C44E52'][i], alpha=0.85)
    for bar, rate in zip(bars, rates):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{rate:.0f}%', ha='center', va='bottom', fontsize=9)

ax.set_xticks(x + width/2)
ax.set_xticklabels(domains.values())
ax.set_ylabel('Pass Rate (%)')
ax.set_ylim(0, 115)
ax.axhline(y=100, color='gray', linestyle=':', alpha=0.3)
ax.legend()
ax.set_title('Pass Rate by Domain (Base Variant)', fontweight='bold')
plt.tight_layout()
fig.savefig(OUT / 'fig5_domain_comparison.png', bbox_inches='tight')
plt.close()
print('Saved fig5_domain_comparison.png')

print('\nAll figures generated!')
