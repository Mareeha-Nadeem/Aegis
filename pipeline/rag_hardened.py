"""
pipeline/rag_hardened.py

Aegis Hardened RAG Pipeline.

Flow:
    User query
          ↓
    FAISS retrieval (top-30)
          ↓
    Layer 3 — DROP/DEMOTE/ALLOW → safe_chunks
          ↓
        LLM → raw output
          ↓
    Layer 4 — score_3 → BLOCK/WARN/SAFE
          ↓
    log_event()
          ↓
    final_output
"""

import pickle
import time
import numpy as np
import faiss
import sys
from pipeline.phi_loader import call_llm
from pathlib import Path
from sentence_transformers import SentenceTransformer


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
_faiss_index   = None
_metadata      = None
_embedder      = None



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




# ── FAISS retrieval ───────────────────────────────────────
def retrieve_chunks(query: str, top_k: int = TOP_K) -> list[dict]:
    """Embed query and retrieve top-K chunks from FAISS."""
    embedder        = get_embedder()
    index, metadata = get_faiss()

    query_emb          = embedder.encode([query], convert_to_numpy=True).astype("float32")
    distances, indices = index.search(query_emb, top_k)

    # Convert FAISS L2 distances (lower is better) into a normalized relevance score (higher is better)
    # This keeps Layer 3's relevance gate functional without a CrossEncoder.
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
        chunk                   = dict(metadata[idx])
        chunk["faiss_distance"] = round(float(dist), 4)
        # relevance_score in [0,1] where 1.0 is most similar (smallest distance)
        denom = (max_d - min_d) + 1e-6
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

    # ── Step 2 — Layer 3: Prompt assembly ─────────────────
    # No CrossEncoder reranking — use FAISS-derived relevance_score only.
    layer3   = run_prompt_assembly(query, retrieved)
    prompt   = layer3["prompt"]
    drop_log = layer3["drop_log"]

    # ── Step 4 — LLM ──────────────────────────────────────
    raw_output = call_llm(prompt)

    # ── Step 5 — Layer 4: Output validation ───────────────
    layer4 = run_output_validator(
        output      = raw_output,
        query       = query,
        safe_chunks = layer3["safe_chunks"],
        drop_log    = drop_log,
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