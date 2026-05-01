"""
evaluation/eval_harness.py

Evaluation Harness.

Orchestrates end-to-end evaluation of both the baseline and hardened RAG
pipelines against a benchmark suite of adversarial and benign queries.
Collects predictions and ground-truth labels, then delegates to metrics.py
for scoring.
"""
