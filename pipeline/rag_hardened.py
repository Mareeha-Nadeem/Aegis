"""
pipeline/rag_hardened.py

Hardened RAG Pipeline.

Orchestrates all four Aegis defence layers (ingestion guard, chunk classifier,
prompt assembly, output validator) around the core RAG retrieval loop to
produce a security-hardened question-answering pipeline.
"""
