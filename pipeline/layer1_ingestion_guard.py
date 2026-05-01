"""
pipeline/layer1_ingestion_guard.py

Layer 1 – Ingestion Guard.

Responsible for scanning and sanitising raw documents before they enter the
RAG knowledge base.  Will detect and block prompt-injection payloads,
malicious instructions, and exfiltration attempts embedded in source
documents at ingest time.
"""
