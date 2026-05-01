"""
pipeline/layer1_ingestion_guard.py

Layer 1 – Ingestion Guard.

Responsible for screening raw documents and data chunks at ingestion time.
Detects and filters out potentially malicious or adversarial content
(e.g., indirect prompt injection payloads, PII leakage triggers) before
they are stored in the vector database or passed further downstream.
"""
