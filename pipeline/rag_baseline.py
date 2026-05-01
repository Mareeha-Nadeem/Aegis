"""
pipeline/rag_baseline.py

RAG Baseline Pipeline.

Implements a standard, unprotected Retrieval-Augmented Generation pipeline
used as a performance and safety baseline.  Retrieves top-k chunks from the
FAISS index and passes them directly to the LLM without any hardening layers.
"""
