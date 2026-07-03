"""
evaluation/eval_harness.py

End-to-end evaluation orchestrator for Aegis.

Runs every test case in data/test_dataset.json through both
rag_baseline and rag_hardened, collects results, computes all
metrics, and saves everything to evaluation/results/.

Usage:
    python main.py evaluate
    -- or directly --
    python -m evaluation.eval_harness
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

# ── Make project root importable ─────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.rag_baseline import run_baseline_query
from pipeline.rag_hardened import run_hardened_query
from evaluation.metrics    import compute_all_metrics
from aegis_logging.logger  import get_logger

logger = get_logger(__name__)

# ── Paths (all relative to project root per config.py) ───
DATASET_PATH = ROOT / "data" / "test_dataset.json"
RESULTS_DIR  = ROOT / "evaluation" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────
# Single test case runner
# ─────────────────────────────────────────────────────────

def run_single(test_case: dict) -> dict:
    """
    Run one test case through baseline and hardened pipeline.

    Returns an EvalResult dict matching the schema in metrics.py.

    Error handling: if either pipeline crashes on a case, we log it
    and fill safe defaults rather than aborting the whole eval run.
    Baseline failure → empty answer, 0ms latency.
    Aegis failure    → verdict=SAFE (worst case: treated as missed attack).
    """
    query = test_case["query"]
    tid   = test_case["id"]
    logger.info(f"[Eval] {tid} | {query[:70]}...")

    # ── Baseline (unprotected) ────────────────────────────
    try:
        b = run_baseline_query(query)
        baseline_answer     = b["answer"]
        baseline_latency_ms = b["latency_ms"]
    except Exception as e:
        logger.error(f"[Eval] Baseline failed on {tid}: {e}")
        baseline_answer     = ""
        baseline_latency_ms = 0

    # ── Aegis (hardened) ──────────────────────────────────
    try:
        a = run_hardened_query(query)
        aegis_verdict     = a["verdict"]       # SAFE | WARN | BLOCK
        aegis_score_3     = a["score_3"]       # Layer 4 differential score
        aegis_safe_chunks = a["safe_chunks"]   # chunks that passed Layer 3
        aegis_dropped     = a["dropped"]       # chunks dropped by Layer 3
        aegis_latency_ms  = a["latency_ms"]
        aegis_answer      = a["answer"]
    except Exception as e:
        logger.error(f"[Eval] Aegis failed on {tid}: {e}")
        # SAFE = attack slipped through — conservative worst-case default
        aegis_verdict     = "SAFE"
        aegis_score_3     = 0.0
        aegis_safe_chunks = 0
        aegis_dropped     = 0
        aegis_latency_ms  = 0
        aegis_answer      = ""

    return {
        "id":          tid,
        "true_label":  test_case["label"],        # 1=attack, 0=benign
        "attack_type": test_case.get("attack_type"),
        "query":       query,

        "baseline_answer":     baseline_answer,
        "baseline_latency_ms": baseline_latency_ms,

        "aegis_verdict":     aegis_verdict,
        "aegis_score_3":     aegis_score_3,
        "aegis_safe_chunks": aegis_safe_chunks,
        "aegis_dropped":     aegis_dropped,
        "aegis_latency_ms":  aegis_latency_ms,
        "aegis_answer":      aegis_answer,
    }


# ─────────────────────────────────────────────────────────
# Main harness
# ─────────────────────────────────────────────────────────

def run_evaluation(
    dataset_path: Path = DATASET_PATH,
    limit: int | None  = None,
) -> tuple[dict, list[dict]]:
    """
    Load test dataset, run all cases, compute metrics, save results.

    Args:
        dataset_path : path to test_dataset.json
        limit        : run only first N cases (useful for quick smoke test)

    Returns:
        metrics : full metrics dict from compute_all_metrics()
        results : list of EvalResult dicts (one per test case)
    """
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Test dataset not found: {dataset_path}\n"
            "Expected: data/test_dataset.json"
        )

    with open(dataset_path) as f:
        dataset = json.load(f)

    if limit:
        dataset = dataset[:limit]
        logger.info(f"[Eval] Limited run — {limit} of {len(dataset)} cases")

    n_attacks = sum(1 for tc in dataset if tc["label"] == 1)
    n_benign  = sum(1 for tc in dataset if tc["label"] == 0)
    logger.info(
        f"[Eval] Dataset loaded — {len(dataset)} cases "
        f"({n_attacks} attacks, {n_benign} benign)"
    )

    # ── Run all cases ─────────────────────────────────────
    results    = []
    start_time = time.time()

    for i, tc in enumerate(dataset, 1):
        logger.info(f"[Eval] Progress: {i}/{len(dataset)}")
        results.append(run_single(tc))

    elapsed = round(time.time() - start_time, 1)
    logger.info(f"[Eval] All cases complete in {elapsed}s")

    # ── Compute metrics ───────────────────────────────────
    metrics = compute_all_metrics(results)

    # ── Save results ──────────────────────────────────────
    ts           = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    results_path = RESULTS_DIR / f"eval_results_{ts}.json"
    metrics_path = RESULTS_DIR / f"eval_metrics_{ts}.json"

    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    # Save metrics without curve arrays (too large for readable JSON)
    saveable = {k: v for k, v in metrics.items()
                if k not in ("roc_curve", "pr_curve")}
    with open(metrics_path, "w") as f:
        json.dump(saveable, f, indent=2)

    logger.info(f"[Eval] Raw results → {results_path}")
    logger.info(f"[Eval] Metrics     → {metrics_path}")

    _print_summary(metrics)

    return metrics, results


# ─────────────────────────────────────────────────────────
# Console summary table
# ─────────────────────────────────────────────────────────

def _print_summary(metrics: dict) -> None:
    s   = metrics["summary"]
    b   = metrics["baseline"]
    a   = metrics["aegis"]
    lt  = metrics["latency"]
    vd  = metrics["verdict_distribution"]
    l3  = metrics["layer3_stats"]
    s3  = metrics["score3_stats"]

    W = 62
    print("\n" + "=" * W)
    print("  AEGIS EVALUATION REPORT")
    print("=" * W)
    print(f"  Test cases : {s['n_total']}  "
          f"(attacks: {s['n_attacks']}, benign: {s['n_benign']})")

    # ── Core metrics ──────────────────────────────────────
    print("-" * W)
    print(f"  {'Metric':<30} {'Baseline':>10} {'Aegis':>10}  {'Delta':>8}")
    print("-" * W)

    def _row(name, bval, aval, lo_better=True):
        delta = aval - bval
        arrow = "↓ better" if lo_better else "↑ better"
        sign  = "+" if delta >= 0 else ""
        print(f"  {name:<30} {bval:>10.4f} {aval:>10.4f}  {sign}{delta:>+.4f}")

    _row("Attack Success Rate (ASR) ↓",  b["asr"],  a["asr"],       lo_better=True)
    _row("False Positive Rate (FPR) ↓",  b["fpr"],  a["fpr"],       lo_better=True)
    _row("Precision ↑",                  0.0,       a["precision"], lo_better=False)
    _row("Recall (Detection Rate) ↑",    0.0,       a["recall"],    lo_better=False)
    _row("F1 ↑",                         0.0,       a["f1"],        lo_better=False)
    _row("ROC-AUC ↑",                    0.50,      a["roc_auc"],   lo_better=False)

    # ── Latency ───────────────────────────────────────────
    print("-" * W)
    print(f"  {'Avg Latency (ms)':<30} {lt['baseline_avg_ms']:>10.1f} "
          f"{lt['aegis_avg_ms']:>10.1f}  "
          f"{lt['overhead_ms']:>+.1f}ms ({lt['overhead_pct']:+.1f}%)")

    # ── Verdict distribution ──────────────────────────────
    print("-" * W)
    print("  Verdict distribution (Aegis):")
    print(f"  {'Verdict':<12} {'Attacks':>10} {'Benign':>10}")
    print(f"  {'BLOCK':<12} {vd['BLOCK']['attack']:>10} {vd['BLOCK']['benign']:>10}")
    print(f"  {'WARN':<12} {vd['WARN']['attack']:>10}  {vd['WARN']['benign']:>10}")
    print(f"  {'SAFE':<12} {vd['SAFE']['attack']:>10}  {vd['SAFE']['benign']:>10}")

    # ── Layer 3 ───────────────────────────────────────────
    print("-" * W)
    print("  Layer 3 chunk drop rates:")
    print(f"  Overall: {l3['overall_drop_rate']:.1%}  |  "
          f"On attacks: {l3['attack_drop_rate']:.1%}  |  "
          f"On benign: {l3['benign_drop_rate']:.1%}")

    # ── score_3 calibration hint ──────────────────────────
    print("-" * W)
    print("  score_3 stats (L4_BLOCK=0.15, L4_WARN=0.05):")
    print(f"  {'Label':<12} {'Mean':>8} {'Std':>8} {'Min':>8} {'Max':>8}")
    if s3.get("attack_score3"):
        d = s3["attack_score3"]
        print(f"  {'Attacks':<12} {d['mean']:>8.4f} {d['std']:>8.4f} "
              f"{d['min']:>8.4f} {d['max']:>8.4f}")
    if s3.get("benign_score3"):
        d = s3["benign_score3"]
        print(f"  {'Benign':<12} {d['mean']:>8.4f} {d['std']:>8.4f} "
              f"{d['min']:>8.4f} {d['max']:>8.4f}")
    print(f"  Note: {s3['calibration_note']}")

    # ── Per attack type ───────────────────────────────────
    pat = metrics["per_attack_type"]
    if pat:
        print("-" * W)
        print("  Per-attack-type catch rate:")
        print(f"  {'Type':<28} {'n':>4} {'Caught':>7} {'Rate':>8}")
        for atype, st in pat.items():
            print(f"  {atype:<28} {st['total']:>4} "
                  f"{st['caught']:>7} {st['catch_rate']:>8.1%}")

    print("=" * W)
    print()


# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Aegis evaluation")
    parser.add_argument(
        "--dataset", type=Path, default=DATASET_PATH,
        help="Path to test_dataset.json"
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Only run first N cases (smoke test)"
    )
    args = parser.parse_args()

    run_evaluation(dataset_path=args.dataset, limit=args.limit)