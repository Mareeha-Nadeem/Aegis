
"""
evaluation/visualize.py

All evaluation visualizations for Aegis vs Baseline.

Generates 6 plots, saved to evaluation/results/plots/.

Plots:
    1. ROC curve
    2. Precision-Recall curve
    3. Metric comparison bar chart (Baseline vs Aegis)
    4. Confusion matrices side-by-side
    5. Per-attack-type catch rate
    6. score_3 distribution with L4_BLOCK / L4_WARN thresholds

Usage:
    # From eval_harness (automatic after eval run):
    from evaluation.visualize import plot_all
    plot_all(metrics)

    # From CLI — pass your eval_results JSON directly:
    python -m evaluation.visualize evaluation/results/eval_results_20260608_203831.json

    The file just needs to be a JSON dict that contains these top-level keys:
        summary, baseline, aegis, roc_curve, pr_curve,
        per_attack_type, score3_stats
    Both eval_results_*.json and any hand-built metrics dict work fine.
    No compute_all_metrics() call needed — just load and pass.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")   # headless — no display needed
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

ROOT = Path(__file__).resolve().parent.parent

# ── Config values (used for threshold lines on plot 6) ────
try:
    from config import L4_BLOCK, L4_WARN
except ImportError:
    L4_BLOCK = 0.15
    L4_WARN  = 0.05

# ── Output dir ─────────────────────────────────────────────
PLOTS_DIR = ROOT / "evaluation" / "results" / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Palette ────────────────────────────────────────────────
C_BASELINE = "#e74c3c"   # red   — baseline / bad
C_AEGIS    = "#27ae60"   # green — Aegis / good
C_WARN     = "#f39c12"   # orange
C_NEUTRAL  = "#95a5a6"   # grey
C_DARK     = "#2c3e50"   # text


def _save(fig: plt.Figure, name: str) -> Path:
    path = PLOTS_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [plot] saved → {path.name}")
    return path


def _gaussian(x: np.ndarray, mean: float, std: float) -> np.ndarray:
    """
    Evaluate a Gaussian PDF at each point in x.

    Used by plot_score3_distribution() to approximate attack and benign
    score_3 distributions from summary stats (mean + std) stored in
    metrics["score3_stats"], without requiring the raw per-row results list.
    """
    return np.exp(-0.5 * ((x - mean) / std) ** 2) / (std * np.sqrt(2 * np.pi))


# ──────────────────────────────────────────────────────────
# 1. ROC Curve
# ──────────────────────────────────────────────────────────

def plot_roc(metrics: dict) -> Path:
    """
    ROC curve for Aegis vs random baseline diagonal.

    X-axis = FPR (false alarms on benign queries)
    Y-axis = TPR (attacks caught)

    The bigger the gap between Aegis curve and the diagonal,
    the better the system discriminates attacks from benign.
    AUC = area under the curve (0.5 = random, 1.0 = perfect).
    """
    roc = metrics["roc_curve"]
    auc = metrics["aegis"]["roc_auc"]

    fig, ax = plt.subplots(figsize=(6, 5))

    ax.plot([0, 1], [0, 1], "--", color=C_BASELINE,
            linewidth=1.5, label="Baseline — random (AUC = 0.50)", zorder=1)

    ax.plot(roc["fpr"], roc["tpr"], color=C_AEGIS,
            linewidth=2.5, label=f"Aegis (AUC = {auc:.3f})", zorder=2)

    ax.fill_between(
        roc["fpr"], roc["tpr"], roc["fpr"],
        where=[t >= f for t, f in zip(roc["tpr"], roc["fpr"])],
        alpha=0.10, color=C_AEGIS, label="Improvement area",
    )

    ax.set_xlim(0, 1); ax.set_ylim(0, 1.02)
    ax.set_xlabel("False Positive Rate  (benign queries blocked)", fontsize=11)
    ax.set_ylabel("True Positive Rate  (attacks caught)",          fontsize=11)
    ax.set_title("ROC Curve — Aegis vs Baseline",
                 fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(alpha=0.25)
    ax.set_aspect("equal")

    return _save(fig, "1_roc_curve.png")


# ──────────────────────────────────────────────────────────
# 2. Precision-Recall Curve
# ──────────────────────────────────────────────────────────

def plot_pr_curve(metrics: dict) -> Path:
    """
    PR curve — preferred over ROC when classes are imbalanced
    (real deployments see far more benign than attack queries).

    Dashed line = random classifier baseline (= attack prevalence).
    """
    pr    = metrics["pr_curve"]
    s     = metrics["summary"]
    prior = s["n_attacks"] / s["n_total"]

    fig, ax = plt.subplots(figsize=(6, 5))

    ax.plot(pr["recall"], pr["precision"],
            color=C_AEGIS, linewidth=2.5, label="Aegis")
    ax.axhline(prior, linestyle="--", color=C_BASELINE, linewidth=1.5,
               label=f"Baseline — random (= {prior:.2f})")

    ax.fill_between(pr["recall"], pr["precision"], prior,
                    where=[p >= prior for p in pr["precision"]],
                    alpha=0.10, color=C_AEGIS)

    ax.set_xlim(0, 1); ax.set_ylim(0, 1.05)
    ax.set_xlabel("Recall  (fraction of attacks caught)", fontsize=11)
    ax.set_ylabel("Precision  (fraction of flags correct)", fontsize=11)
    ax.set_title("Precision-Recall Curve — Aegis",
                 fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(alpha=0.25)

    return _save(fig, "2_pr_curve.png")


# ──────────────────────────────────────────────────────────
# 3. Metric Comparison Bar Chart
# ──────────────────────────────────────────────────────────

def plot_metric_comparison(metrics: dict) -> Path:
    """
    Side-by-side bars: ASR, FPR, Precision, Recall, F1, ROC-AUC.

    Baseline has no classifier so Precision/Recall/F1/AUC = 0 / 0.5.
    The visual makes the improvement immediately obvious.
    """
    b = metrics["baseline"]
    a = metrics["aegis"]

    labels    = ["ASR ↓", "FPR ↓", "Precision ↑", "Recall ↑", "F1 ↑", "ROC-AUC ↑"]
    b_vals    = [b["asr"], b["fpr"], 0.0, 0.0, 0.0, 0.50]
    a_vals    = [a["asr"], a["fpr"], a["precision"], a["recall"], a["f1"], a["roc_auc"]]

    x     = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(11, 5))

    bars_b = ax.bar(x - width/2, b_vals, width,
                    color=C_BASELINE, alpha=0.82, label="Baseline", zorder=2)
    bars_a = ax.bar(x + width/2, a_vals, width,
                    color=C_AEGIS,    alpha=0.82, label="Aegis",    zorder=2)

    for bar in list(bars_b) + list(bars_a):
        h = bar.get_height()
        if h > 0.005:
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.015,
                    f"{h:.2f}", ha="center", va="bottom",
                    fontsize=8.5, color=C_DARK, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylim(0, 1.18)
    ax.set_ylabel("Score", fontsize=12)
    ax.set_title("Security Metrics — Baseline vs Aegis",
                 fontsize=13, fontweight="bold")
    ax.legend(fontsize=11)
    ax.grid(axis="y", alpha=0.25, zorder=0)
    ax.set_axisbelow(True)

    return _save(fig, "3_metric_comparison.png")


# ──────────────────────────────────────────────────────────
# 4. Confusion Matrices
# ──────────────────────────────────────────────────────────

def plot_confusion_matrices(metrics: dict) -> Path:
    """
    Side-by-side 2×2 confusion matrices.

    Baseline: FN = all attacks (nothing caught)
    Aegis:    TP should be high, FP low
    """
    def _draw(ax, cm, title, title_color):
        data   = [[cm["TN"], cm["FP"]],
                  [cm["FN"], cm["TP"]]]
        labels = [["TN\n(Benign correct)", "FP\n(Benign blocked)"],
                  ["FN\n(Attack missed)",  "TP\n(Attack caught)"]]
        bg     = [["#d5f5e3", "#fadbd8"],
                  ["#fadbd8", "#d5f5e3"]]

        for i in range(2):
            for j in range(2):
                ax.add_patch(
                    plt.Rectangle([j, 1-i], 1, 1,
                                  facecolor=bg[i][j],
                                  edgecolor="white", lw=2.5)
                )
                ax.text(j + 0.5, 1-i + 0.62, str(data[i][j]),
                        ha="center", va="center",
                        fontsize=22, fontweight="bold", color=C_DARK)
                ax.text(j + 0.5, 1-i + 0.28, labels[i][j],
                        ha="center", va="center",
                        fontsize=8, color="#555555")

        ax.set_xlim(0, 2); ax.set_ylim(0, 2)
        ax.set_xticks([0.5, 1.5])
        ax.set_xticklabels(["Predicted Benign", "Predicted Attack"], fontsize=9)
        ax.set_yticks([0.5, 1.5])
        ax.set_yticklabels(["Actual Attack", "Actual Benign"], fontsize=9)
        ax.set_title(title, fontsize=12, fontweight="bold",
                     color=title_color, pad=12)
        ax.tick_params(length=0)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    _draw(ax1, metrics["baseline"]["confusion_matrix"],
          "Baseline (Unprotected)", C_BASELINE)
    _draw(ax2, metrics["aegis"]["confusion_matrix"],
          "Aegis (Protected)", C_AEGIS)

    fig.suptitle("Confusion Matrices", fontsize=14, fontweight="bold", y=1.01)
    plt.tight_layout()
    return _save(fig, "4_confusion_matrices.png")


# ──────────────────────────────────────────────────────────
# 5. Per-Attack-Type Catch Rate
# ──────────────────────────────────────────────────────────

def plot_per_attack_type(metrics: dict) -> Path | None:
    """
    Horizontal bar chart — catch rate per attack category.

    Green  ≥ 80%  strong
    Orange 50-79% moderate
    Red    < 50%  weak — needs improvement
    """
    pat = metrics.get("per_attack_type", {})
    if not pat:
        print("  [plot] No per-attack-type data — skipping plot 5.")
        return None

    types   = sorted(pat.keys())
    rates   = [pat[t]["catch_rate"] for t in types]
    totals  = [pat[t]["total"]      for t in types]
    colours = [
        C_AEGIS    if r >= 0.80 else
        C_WARN     if r >= 0.50 else
        C_BASELINE
        for r in rates
    ]

    fig, ax = plt.subplots(figsize=(9, max(4, len(types) * 1.0)))

    bars = ax.barh(types, rates, color=colours, alpha=0.85,
                   edgecolor="white", linewidth=1.2, zorder=2)

    for bar, rate, total in zip(bars, rates, totals):
        ax.text(bar.get_width() + 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"{rate:.0%}  (n={total})",
                va="center", fontsize=10, color=C_DARK)

    ax.set_xlim(0, 1.35)
    ax.axvline(1.0, linestyle="--", color=C_NEUTRAL, linewidth=1, zorder=1)
    ax.set_xlabel("Catch Rate", fontsize=12)
    ax.set_title("Aegis Catch Rate by Attack Type",
                 fontsize=13, fontweight="bold")
    ax.grid(axis="x", alpha=0.25, zorder=0)
    ax.set_axisbelow(True)

    legend_patches = [
        mpatches.Patch(color=C_AEGIS,    label="≥ 80%  Strong"),
        mpatches.Patch(color=C_WARN,     label="50–79%  Moderate"),
        mpatches.Patch(color=C_BASELINE, label="< 50%   Needs work"),
    ]
    ax.legend(handles=legend_patches, fontsize=9, loc="lower right")
    plt.tight_layout()

    return _save(fig, "5_per_attack_type.png")


# ──────────────────────────────────────────────────────────
# 6. score_3 Distribution — Layer 4 Calibration
# ──────────────────────────────────────────────────────────

def plot_score3_distribution(metrics: dict) -> Path | None:
    """
    Overlapping Gaussian-approximated distributions of score_3 for
    attack vs benign queries.

    Previously this function required a raw results list to build
    histograms from per-row score_3 values.  The results file is no
    longer needed — instead we read pre-computed summary stats from
    metrics["score3_stats"] and reconstruct smooth Gaussian curves
    using _gaussian().  The visual information is identical; the only
    difference is we show smooth curves rather than jagged histogram
    bars (which is actually cleaner for a report).

    What metrics["score3_stats"] must contain:
        attack_score3 : {mean, std, min, max}
        benign_score3 : {mean, std, min, max}
        thresholds_used : {L4_BLOCK, L4_WARN}   (optional — falls back to config)

    Vertical lines at L4_WARN and L4_BLOCK from metrics or config.py.

    What to look for:
    - Good: attack curve sits clearly RIGHT of L4_WARN
    - Good: benign curve sits clearly LEFT of L4_WARN
    - Overlap zone = misclassification region — tune thresholds to minimise it
    - If attack mean < L4_WARN: lower your thresholds
    - If benign mean > L4_WARN: raise your thresholds
    """
    s3 = metrics.get("score3_stats")
    if not s3:
        print("  [plot] No score3_stats in metrics — skipping plot 6.")
        return None

    atk = s3["attack_score3"]
    ben = s3["benign_score3"]

    # Prefer thresholds embedded in the metrics file so the plot always
    # matches the run that produced it — fall back to config.py values.
    thresholds   = s3.get("thresholds_used", {})
    warn_line    = thresholds.get("L4_WARN",  L4_WARN)
    block_line   = thresholds.get("L4_BLOCK", L4_BLOCK)

    # x range: span both distributions plus a small margin
    lo = min(atk["min"], ben["min"]) - 0.03
    hi = max(atk["max"], ben["max"]) + 0.03
    x  = np.linspace(lo, hi, 300)

    atk_curve = _gaussian(x, atk["mean"], atk["std"])
    ben_curve = _gaussian(x, ben["mean"], ben["std"])

    n_atk = metrics["summary"]["n_attacks"]
    n_ben = metrics["summary"]["n_benign"]

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(x, atk_curve, color=C_BASELINE, linewidth=2.5,
            label=f"Attack queries  (n={n_atk}, mean={atk['mean']:.4f})")
    ax.fill_between(x, atk_curve, alpha=0.18, color=C_BASELINE)

    ax.plot(x, ben_curve, color=C_AEGIS, linewidth=2.5,
            label=f"Benign queries  (n={n_ben}, mean={ben['mean']:.4f})")
    ax.fill_between(x, ben_curve, alpha=0.18, color=C_AEGIS)

    # Percentile tick marks on x-axis to show where p25/median/p75 fall
    for stat_dict, color in [(atk, C_BASELINE), (ben, C_AEGIS)]:
        for pct_key in ("p25", "median", "p75"):
            val = stat_dict.get(pct_key)
            if val is not None:
                ax.axvline(val, color=color, linewidth=0.8,
                           linestyle=":", alpha=0.55)

    # Threshold lines from metrics (preferred) or config
    ax.axvline(warn_line,  linestyle="--", color=C_WARN,     linewidth=2,
               label=f"L4_WARN  = {warn_line}  (flag as suspicious)", zorder=3)
    ax.axvline(block_line, linestyle="--", color=C_BASELINE, linewidth=2,
               label=f"L4_BLOCK = {block_line}  (block response)",    zorder=3)

    # Shade WARN zone
    ax.axvspan(warn_line, block_line, alpha=0.06, color=C_WARN,
               label="WARN zone")
    # Shade BLOCK zone
    ax.axvspan(block_line, hi, alpha=0.06, color=C_BASELINE,
               label="BLOCK zone")

    # Calibration note from metrics if present
    cal_note = s3.get("calibration_note", "")
    if cal_note:
        ax.set_xlabel(
            f"score_3  =  inj_sim − benign_sim\n{cal_note}",
            fontsize=10,
        )
    else:
        ax.set_xlabel("score_3  =  inj_sim − benign_sim", fontsize=12)

    ax.set_ylabel("Density", fontsize=12)
    ax.set_title(
        "Layer 4  score_3 Distribution\n"
        "Use this to calibrate L4_BLOCK and L4_WARN thresholds",
        fontsize=12, fontweight="bold"
    )
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25)
    plt.tight_layout()

    return _save(fig, "6_score3_distribution.png")


# ──────────────────────────────────────────────────────────
# Master call
# ──────────────────────────────────────────────────────────

def plot_all(metrics: dict) -> list[Path]:
    """
    Generate all 6 plots from a metrics dict alone.

    Previously signature was plot_all(metrics, results).
    The results parameter has been removed — plot 6 now reads
    summary stats from metrics["score3_stats"] directly.

    Called automatically by eval_harness after a run:
        from evaluation.visualize import plot_all
        plot_all(metrics)

    Returns list of saved file paths.
    """
    print(f"\n[Visualize] Generating plots → {PLOTS_DIR}\n")
    paths = [
        plot_roc(metrics),
        plot_pr_curve(metrics),
        plot_metric_comparison(metrics),
        plot_confusion_matrices(metrics),
        plot_per_attack_type(metrics),
        plot_score3_distribution(metrics),   # no results arg
    ]
    saved = [p for p in paths if p is not None]
    print(f"\n[Visualize] {len(saved)} plots saved.\n")
    return saved


# ──────────────────────────────────────────────────────────
# CLI: python -m evaluation.visualize <metrics_file.json>
# ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Generate Aegis evaluation plots from a metrics JSON file.\n\n"
            "If no file is specified, auto-detects the latest eval_metrics_*.json\n"
            "or eval_results_*.json in evaluation/results/.\n\n"
            "Example:\n"
            "  python -m evaluation.viz\n"
            "  python -m evaluation.viz evaluation/results/eval_metrics_20260608_203831.json\n"
            "  python -m evaluation.viz eval_metrics_20260608_203831.json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "metrics_file", type=Path, nargs="?", default=None,
        help="Path to eval_results_*.json or eval_metrics_*.json (optional — auto-detects latest)"
    )
    args = parser.parse_args()

    # ── Auto-detect latest metrics file if not provided ─────────
    metrics_path = args.metrics_file

    if metrics_path is None:
        # Find latest eval_metrics_*.json (preferred over eval_results_*.json)
        results_dir = ROOT / "evaluation" / "results"
        
        # Prefer metrics files over results files
        candidates = sorted(
            results_dir.glob("eval_metrics_*.json"),
            key=lambda p: p.stem,
            reverse=True
        )
        
        if candidates:
            metrics_path = candidates[0]
            print(f"[Viz] Auto-detected latest metrics file: {metrics_path.name}")
        else:
            print(f"\n❌ No eval_metrics_*.json found in {results_dir}")
            print(f"\n💡 First run an evaluation:")
            print(f"   python main.py evaluate")
            print(f"\nAvailable files:")
            available = sorted(results_dir.glob("eval_*.json"), reverse=True)
            if available:
                for f in available[:5]:
                    print(f"     - {f.name}")
            sys.exit(1)
    else:
        # ── Smart path resolution for provided file ──────────────
        if not metrics_path.exists():
            # Try 2: Relative to evaluation/results/
            alt1 = ROOT / "evaluation" / "results" / metrics_path.name
            if alt1.exists():
                metrics_path = alt1
                print(f"[Viz] Found file at: {metrics_path}")
            else:
                # Try 3: Treat as relative to project root if not absolute
                if not metrics_path.is_absolute():
                    alt2 = ROOT / metrics_path
                    if alt2.exists():
                        metrics_path = alt2
                        print(f"[Viz] Found file at: {metrics_path}")

        if not metrics_path.exists():
            print(f"\n❌ File not found: {args.metrics_file}")
            print(f"\nSearched in:")
            print(f"  1. {args.metrics_file.resolve()}")
            print(f"  2. {ROOT / 'evaluation' / 'results' / args.metrics_file.name}")
            if not args.metrics_file.is_absolute():
                print(f"  3. {ROOT / args.metrics_file}")
            print(f"\n💡 Available metrics files in {ROOT / 'evaluation' / 'results'}:")
            results_dir = ROOT / "evaluation" / "results"
            if results_dir.exists():
                files = sorted(results_dir.glob("eval_*.json"), reverse=True)
                if files:
                    for f in files[:5]:  # Show last 5
                        print(f"     - {f.name}")
                else:
                    print("     (none found)")
            sys.exit(1)

    with open(metrics_path) as f:
        metrics = json.load(f)

    print(f"[Viz] Loaded metrics from: {metrics_path}\n")
    plot_all(metrics)