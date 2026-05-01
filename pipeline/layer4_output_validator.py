"""
pipeline/layer4_output_validator.py

Layer 4 – Output Validator.

Validates the LLM's generated response before it is returned to the user.
Checks for signs of successful prompt injection, data exfiltration patterns,
policy violations, and unexpected instruction-following that deviates from
the intended task.
"""
