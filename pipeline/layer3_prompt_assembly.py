"""
pipeline/layer3_prompt_assembly.py

Layer 3 – Prompt Assembly.

Constructs the final prompt sent to the LLM by combining the user query with
safe, validated context chunks.  Applies templating, token-budget management,
and instruction hardening to minimise the attack surface for prompt injection.
"""
