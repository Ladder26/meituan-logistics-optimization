"""Fix Figure 3: title/legend aligned with Fig 1/2 style."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

import matplotlib.pyplot as plt
import numpy as np

from optimization.inventory_optimizer import calculate_city_total_cost

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 9

COLOR_STORAGE = '#E07A5F'
COLOR_TRANSPORT = '#3D405B'
COLOR_TOTAL = '#81B29A'

fig, ax = plt.subplots(figsize=(7, 5), dpi=300)

T_range = np.arange(1, 8)
storage = []
transport = []
total = []
for T in T_range:
    res = calculate_city_total_cost('A', T)
    storage.append(res['storage_cost'])
    transport.append(res['transport_cost'])
    total.append(res['total_cost'])

ax.plot(T_range, storage, 'o-', color=COLOR_STORAGE, label='Storage Cost', linewidth=2, markersize=8)
ax.plot(T_range, transport, 's-', color=COLOR_TRANSPORT, label='Transport Cost', linewidth=2, markersize=8)
ax.plot(T_range, total, '^--', color=COLOR_TOTAL, label='Total Cost', linewidth=2.5, markersize=10)

# Optimal marker
opt_T = 1
opt_total = total[0]
ax.axvline(x=opt_T, color='gray', linestyle='--', alpha=0.6, linewidth=1.2)
ax.annotate('Optimal\nT=1', xy=(opt_T, opt_total), xytext=(opt_T + 0.6, opt_total + 2500),
            fontsize=10, color='green', fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='green', lw=1.2))

# Axis labels
ax.set_xlabel('Replenishment Cycle T (days)', fontsize=10)
ax.set_ylabel('Daily Cost (CNY)', fontsize=10)
ax.set_xticks(T_range)

# Tick hierarchy
ax.tick_params(axis='y', labelsize=8, colors='dimgray')
ax.tick_params(axis='x', labelsize=9, colors='black')
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x):,}'))

# Spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_linewidth(0.8)
ax.spines['left'].set_bounds(0, 20000)
ax.spines['bottom'].set_linewidth(0.8)

# Title top-left
ax.text(0.02, 0.98, '(c) Cost Sensitivity to Replenishment Cycle (City A)',
        transform=ax.transAxes, fontsize=10, fontweight='bold', va='top', ha='left')

# Legend top-right
ax.legend(loc='upper right', frameon=False, fontsize=9, bbox_to_anchor=(1.0, 1.0))

ax.set_ylim(0, 23000)

plt.tight_layout()
plt.savefig('figures/fig3_t_sensitivity.pdf', bbox_inches='tight', pad_inches=0.05)
plt.savefig('figures/fig3_t_sensitivity.png', dpi=300, bbox_inches='tight', pad_inches=0.05)
plt.close()
print('Fig 3 fixed and saved.')
