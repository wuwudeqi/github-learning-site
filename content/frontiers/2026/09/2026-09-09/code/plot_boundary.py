"""Replot author-reported results, arXiv:2609.04482v1 abstract and section 6.
Optional dependency: matplotlib 3.11.1. This is NOT a training reproduction.
Run from anywhere: output is relative to this file.
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'svg.fonttype': 'none', 'font.size': 12})
fig, axes = plt.subplots(1, 2, figsize=(9, 4.5), layout='constrained')
fig.set_facecolor('#f2f6f6')
for ax, values, title in zip(axes, [[32.94,4.16],[91.88,87.72]],
                           ['Benign over-refusal (lower is better)', 'Harmful refusal (higher is better)']):
    ax.set_facecolor('#f2f6f6')
    bars=ax.bar(['Control', '+ benign boundary data'], values, color=['#8b9baa','#16877e'],width=.6)
    ax.bar_label(bars, labels=[f'{v:.2f}%' for v in values],padding=5)
    ax.set_ylim(0,105);ax.set_ylabel('Rate (%)');ax.set_title(title, fontsize=12)
    ax.tick_params(axis='x',labelsize=9)
    ax.spines[['top','right']].set_visible(False)
fig.suptitle('Refusal boundary: report both sides',weight='bold')
fig.supxlabel('Source: arXiv:2609.04482v1 · matched boundary-pair comparison · not reproduced',fontsize=9)
out=Path(__file__).resolve().parent.parent/'images'
fig.savefig(out/'boundary-results.svg')
fig.savefig('/tmp/boundary-results-0909.png',dpi=130)
