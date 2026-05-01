"""
pipeline/layer3_prompt_assembly.py

Layer 3 – Prompt Assembly.

Assembles the final prompt sent to the LLM using only the chunks that
passed the risk classification step. Applies structural guardrails and
instruction hardening (e.g., role anchoring, context delimiting) to
reduce the model's susceptibility to residual injection content.
"""
