import json
import sys
from pathlib import Path

sys.path.insert(0, '.')
from evaluation.metrics import compute_all_metrics, compute_roc_auc, compute_pr_curve
from evaluation.viz import plot_all
import matplotlib.pyplot as plt

# Load existing eval_metrics (DO NOT MODIFY)
metrics_file = Path('evaluation/results/eval_metrics_20260610_030104.json')
with open(metrics_file) as f:
    metrics = json.load(f)

print(f'[Gen] Loaded metrics from {metrics_file.name} (NOT MODIFIED)')

# Load eval_results separately to compute ONLY ROC & PR curves
results_file = Path('evaluation/results/eval_results_20260610_030104.json')
with open(results_file) as f:
    results = json.load(f)

print(f'[Gen] Loaded {len(results)} results from {results_file.name}')

# Compute ROC and PR curves from results
auc, fpr_curve, tpr_curve = compute_roc_auc(results)
pr_p, pr_r, pr_t = compute_pr_curve(results)

# Inject curves into metrics dict (in memory only, don't save)
metrics['roc_curve'] = {'fpr': fpr_curve, 'tpr': tpr_curve}
metrics['pr_curve'] = {'precision': pr_p, 'recall': pr_r, 'thresholds': pr_t}

print(f'[Gen] ✓ Computed ROC & PR curves from eval_results (metrics file unchanged)')
print(f'     - ROC AUC: {auc:.4f} ({len(fpr_curve)} points)')
print(f'     - PR points: {len(pr_p)}')

# Generate all plots
print(f'\n[Gen] Generating plots...')
plot_all(metrics)
print(f'[Gen] ✓ All plots generated! (NO FILES MODIFIED)')
