"""
pipeline/layer2_reranker.py

Layer 2 – Reranker (disabled).

Reranking is intentionally disabled. The pipeline uses FAISS similarity
scores only.

This module is kept for backward compatibility with notebooks/scripts
that still import `rerank_chunks`.

Flow:
    FAISS top-30 chunks
          ↓
    Normalize FAISS distances (per query)
          ↓
    Top-5 chunks (max 8)
          ↓
    Layer 3
"""


import numpy as np
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import (
    RERANK_TOP_K,
    RERANK_TOP_K_MAX,
)

from aegis_logging.logger import get_logger
logger = get_logger(__name__)


# ── Score normalization ───────────────────────────────────
def _distances_to_relevance(distances: list[float]) -> list[float]:
    """Convert FAISS L2 distances (lower is better) → relevance in [0,1] (higher is better)."""
    if not distances:
        return []
    min_d = float(min(distances))
    max_d = float(max(distances))
    denom = (max_d - min_d) + 1e-6
    return [1.0 - ((float(d) - min_d) / denom) for d in distances]


# ── Core reranking ────────────────────────────────────────
def rerank_chunks(query: str, chunks: list[dict], top_k: int = None) -> list[dict]:
    """
    Rerank step is disabled: uses FAISS distance only.

    Args:
        query  : user query string
        chunks : list of dicts from FAISS retrieval (should have 'faiss_distance')
        top_k  : how many chunks to return (default: RERANK_TOP_K from config)

    Returns:
        top-N chunks sorted by FAISS-derived relevance descending,
        each enriched with 'relevance_score' (0.0–1.0).
    """
    if not chunks:
        logger.warning("[Layer 2] No chunks to rerank.")
        return []

    k = min(top_k or RERANK_TOP_K, RERANK_TOP_K_MAX, len(chunks))

    # If relevance_score is already present (e.g., added during retrieval), keep it.
    if all("relevance_score" in c for c in chunks):
        scored_chunks = list(chunks)
    else:
        dists = [float(c.get("faiss_distance", 0.0)) for c in chunks]
        rels = _distances_to_relevance(dists)
        scored_chunks = [
            {**chunk, "relevance_score": round(float(rel), 4)}
            for chunk, rel in zip(chunks, rels)
        ]

    scored_chunks.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)
    top_chunks = scored_chunks[:k]

    if not top_chunks:
        logger.warning("[Layer 2] No chunks after reranking.")
        return []

    logger.info(
        f"[Layer 2] Rerank disabled — selected top {len(top_chunks)} of {len(chunks)} | "
        f"best={top_chunks[0]['relevance_score']:.4f} | "
        f"worst={top_chunks[-1]['relevance_score']:.4f}"
    )

    return top_chunks