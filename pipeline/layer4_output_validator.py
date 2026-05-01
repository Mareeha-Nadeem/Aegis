"""
pipeline/layer4_output_validator.py

Layer 4 – Output Validator.

Post-processes LLM responses to detect signs of successful prompt injection,
sensitive data leakage, or policy violations.  Can redact, flag, or block
responses that fail validation before they are returned to the user.
"""
