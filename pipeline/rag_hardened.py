"""
pipeline/rag_hardened.py

Aegis Hardened RAG Pipeline.

Flow:
    User query
          ↓
    FAISS retrieval (top-30)
          ↓
    CrossEncoder reranking → relevance_score updated
          ↓
    Layer 3 — DROP/DEMOTE/ALLOW → safe_chunks
          ↓
        LLM → raw output
          ↓
    Layer 4 — score_3 → BLOCK/WARN/SAFE
              (thresholds tightened by Layer 3 drop_ratio signal)
          ↓
    log_event()
          ↓
    final_output

CHANGES (v2):
    - CrossEncoder reranking re-added between FAISS retrieval and Layer 3.
      FAISS L2 distances are a weak relevance proxy; the CrossEncoder reads
      (query, chunk) jointly and produces a much stronger relevance score.
      This makes the Layer 3 RELEVANCE_FLOOR filter actually meaningful.
    - drop_ratio and max_score_1_dropped from Layer 3 are now forwarded to
      Layer 4 so it can tighten its decision thresholds when retrieval was
      already suspicious.
    - CrossEncoder is loaded as a singleton (same pattern as embedder/FAISS)
      so it is only loaded once per process.
"""

import pickle
import time
import numpy as np
import faiss
import sys
from pipeline.phi_loader import call_llm
from pathlib import Path
from sentence_transformers import SentenceTransformer, CrossEncoder


sys.path.append(str(Path(__file__).parent.parent))
from config import (
    FAISS_INDEX_PATH,
    FAISS_META_PATH,
    EMBEDDER_MODEL,
    TOP_K,
    PHI_MODEL,
)
from pipeline.layer3_prompt_assembly  import run_prompt_assembly
from pipeline.layer4_output_validator import run_output_validator
from aegis_logging.logger             import get_logger, log_event

logger = get_logger(__name__)


# ── Singletons ────────────────────────────────────────────
_faiss_index    = None
_metadata       = None
_embedder       = None
_cross_encoder  = None  # NEW


# ── Cross-encoder model name ──────────────────────────────
# ms-marco-MiniLM-L-6-v2 is fast (~50ms/query on CPU for 30 chunks)
# and meaningfully stronger than raw FAISS distances for relevance ranking.
# Swap for a larger model (e.g. ms-marco-MiniLM-L-12-v2) if latency permits.
CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


# ── Loaders ───────────────────────────────────────────────
def get_faiss():
    global _faiss_index, _metadata
    if _faiss_index is None:
        if not FAISS_INDEX_PATH.exists():
            raise FileNotFoundError(
                "FAISS index not found. Run notebooks/build_faiss_index.py first."
            )
        logger.info("[Hardened] Loading FAISS index...")
        _faiss_index = faiss.read_index(str(FAISS_INDEX_PATH))
        with open(FAISS_META_PATH, "rb") as f:
            _metadata = pickle.load(f)
        logger.info(f"[Hardened] FAISS loaded — {_faiss_index.ntotal} vectors.")
    return _faiss_index, _metadata


def get_embedder():
    global _embedder
    if _embedder is None:
        logger.info("[Hardened] Loading embedder...")
        _embedder = SentenceTransformer(EMBEDDER_MODEL)
        logger.info("[Hardened] Embedder loaded.")
    return _embedder


def get_cross_encoder() -> CrossEncoder:
    """
    Singleton loader for the CrossEncoder reranker.

    The CrossEncoder is a bi-encoder alternative that takes (query, passage)
    pairs and scores them jointly. It cannot be used for retrieval (no separate
    embeddings to index), but it is much more accurate than cosine similarity
    for ranking a small candidate set — exactly our use case after FAISS
    narrows down to top-30.
    """
    global _cross_encoder
    if _cross_encoder is None:
        logger.info(f"[Hardened] Loading CrossEncoder: {CROSS_ENCODER_MODEL}")
        _cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL)
        logger.info("[Hardened] CrossEncoder loaded.")
    return _cross_encoder


# ── Reranking ─────────────────────────────────────────────
def rerank_chunks(query: str, chunks: list[dict]) -> list[dict]:
    """
    Replace FAISS-derived relevance_score with CrossEncoder scores.

    CrossEncoder.predict() takes a list of (query, text) pairs and returns
    a score per pair. Higher score = more relevant. We normalize the scores
    to [0, 1] across the candidate set and write them back into each chunk's
    relevance_score field so Layer 3's RELEVANCE_FLOOR filter operates on
    a meaningful signal rather than noisy L2 distances.

    Args:
        query  : user question
        chunks : list of chunk dicts with at least a "text" field

    Returns:
        Same chunks list, sorted descending by updated relevance_score.
    """
    if not chunks:
        return chunks
    chunks = [
    c for c in chunks
    if c.get("classification", "").lower() != "restricted"
]
    ce     = get_cross_encoder()
    pairs  = [(query, chunk.get("text", "")) for chunk in chunks]
    scores = ce.predict(pairs)          # returns np.ndarray of raw logits

    # Normalize to [0, 1] across this candidate set so RELEVANCE_FLOOR
    # (which was designed for a 0–1 range) stays meaningful.
    min_s = float(scores.min())
    max_s = float(scores.max())
    denom = (max_s - min_s) + 1e-6

    for chunk, raw_score in zip(chunks, scores):
        normalized               = (float(raw_score) - min_s) / denom
        chunk["relevance_score"] = round(normalized, 4)
        chunk["ce_raw_score"]    = round(float(raw_score), 4)  # keep raw for debug

    # Sort best-first so Layer 3 sees highest-relevance chunks at top
    reranked = sorted(chunks, key=lambda c: c["relevance_score"], reverse=True)

    logger.info(
        f"[Hardened] CrossEncoder reranking complete — "
        f"{len(reranked)} chunks | "
        f"top relevance={reranked[0]['relevance_score']:.4f} | "
        f"bottom relevance={reranked[-1]['relevance_score']:.4f}"
    )
    return reranked


def retrieve_chunks(query: str, top_k: int = TOP_K) -> list[dict]:
    """Embed query and retrieve top-K chunks from FAISS."""
    embedder        = get_embedder()
    index, metadata = get_faiss()

    query_emb          = embedder.encode([query], convert_to_numpy=True).astype("float32")
    distances, indices = index.search(query_emb, top_k)

    dists = distances[0]
    valid_dists = [float(d) for d, idx in zip(dists, indices[0]) if idx != -1]
    if valid_dists:
        min_d = min(valid_dists)
        max_d = max(valid_dists)
    else:
        min_d = 0.0
        max_d = 0.0

    chunks = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        chunk = dict(metadata[idx])

        # ── ACCESS CONTROL: skip restricted chunks ────────
        if chunk.get("classification", "").lower() == "restricted":
            logger.info(
                f"[Hardened] Skipping restricted chunk: {chunk.get('chunk_id', 'unknown')}"
            )
            continue
        # ──────────────────────────────────────────────────

        chunk["faiss_distance"] = round(float(dist), 4)

        # Preliminary FAISS-based relevance — will be overwritten by CrossEncoder.
        # Kept here so the field always exists even if reranking is skipped.
        denom     = (max_d - min_d) + 1e-6
        relevance = 1.0 - ((float(dist) - min_d) / denom)
        chunk["relevance_score"] = round(float(relevance), 4)

        chunks.append(chunk)

    logger.info(f"[Hardened] Retrieved {len(chunks)} chunks from FAISS.")
    return chunks


# ── Main hardened query function ──────────────────────────
def run_hardened_query(query: str) -> dict:
    """
    Full Aegis hardened RAG pipeline.

    Args:
        query : user question

    Returns:
        dict:
            answer       : final response to user
            verdict      : SAFE | WARN | BLOCK
            score_3      : Layer 4 differential score
            safe_chunks  : number of ALLOW chunks
            dropped      : number of dropped chunks
            latency_ms   : total pipeline latency
    """
    start = time.time()

    # ── Step 1 — FAISS retrieval ──────────────────────────
    retrieved = retrieve_chunks(query)

    if not retrieved:
        logger.warning("[Hardened] No chunks retrieved.")
        return {
            "answer":      "I could not find relevant information to answer your query.",
            "verdict":     "SAFE",
            "score_3":     0.0,
            "safe_chunks": 0,
            "dropped":     0,
            "latency_ms":  int((time.time() - start) * 1000),
        }

    # ── Step 2 — CrossEncoder reranking ───────────────────
    # Replaces the raw FAISS relevance_score with a much stronger signal.
    # This makes Layer 3's RELEVANCE_FLOOR filter reliable.
    # Latency cost: ~50ms on CPU for 30 chunks — well within our budget.
    reranked = rerank_chunks(query, retrieved)

    # ── Step 3 — Layer 3: Prompt assembly ─────────────────
    layer3   = run_prompt_assembly(query, reranked)
    prompt   = layer3["prompt"]
    drop_log = layer3["drop_log"]

    # ── Step 4 — LLM ──────────────────────────────────────
    raw_output = call_llm(prompt)

    # ── Step 5 — Layer 4: Output validation ───────────────
    # Pass Layer 3 suspicion signals so Layer 4 can tighten its thresholds
    # when the retrieval environment looked hostile.
    layer4 = run_output_validator(
        output               = raw_output,
        query                = query,
        safe_chunks          = layer3["safe_chunks"],
        drop_log             = drop_log,
        drop_ratio           = layer3["drop_ratio"],           # NEW
        max_score_1_dropped  = layer3["max_score_1_dropped"],  # NEW
    )

    # ── Step 6 — Log ──────────────────────────────────────
    if layer4["log_record"]:
        log_event(layer4["log_record"])

    for entry in drop_log:
        log_event(entry)

    latency = int((time.time() - start) * 1000)
    logger.info(
        f"[Hardened] Done — verdict={layer4['verdict']} | "
        f"score_3={layer4['score_3']} | latency={latency}ms"
    )

    return {
        "answer":      layer4["final_output"],
        "verdict":     layer4["verdict"],
        "score_3":     layer4["score_3"],
        "safe_chunks": len(layer3["safe_chunks"]),
        "dropped":     len(drop_log),
        "latency_ms":  latency,
    }