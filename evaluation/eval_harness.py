"""
evaluation/eval_harness.py

Evaluation Harness.

Runs end-to-end evaluations of both the baseline and hardened RAG pipelines
against a suite of adversarial and benign test prompts.  Collects per-query
results and delegates metric computation to metrics.py.
"""
