"""
pipeline/rag_baseline.py

Baseline RAG Pipeline (unprotected).

No security layers — raw retrieval directly to LLM.
Used as comparison baseline against Aegis hardened pipeline.

Flow:
    User query
          ↓
    FAISS retrieval (top-5)
          ↓
    Plain prompt assembly
          ↓
    LLM → output
          ↓
    Return to user
"""
from pipeline.phi_loader import call_llm
import pickle
import time
import numpy as np
import faiss
import sys

from pathlib import Path
from sentence_transformers import SentenceTransformer


sys.path.append(str(Path(__file__).parent.parent))
from config import (
    FAISS_INDEX_PATH,
    FAISS_META_PATH,
    EMBEDDER_MODEL,
    RERANK_TOP_K,
    PHI_MODEL,
)
from aegis_logging.logger import get_logger

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
        logger.info("[Baseline] Loading FAISS index...")
        _faiss_index = faiss.read_index(str(FAISS_INDEX_PATH))
        with open(FAISS_META_PATH, "rb") as f:
            _metadata = pickle.load(f)
        logger.info(f"[Baseline] FAISS loaded — {_faiss_index.ntotal} vectors.")
    return _faiss_index, _metadata


def get_embedder():
    global _embedder
    if _embedder is None:
        logger.info("[Baseline] Loading embedder...")
        _embedder = SentenceTransformer(EMBEDDER_MODEL)
        logger.info("[Baseline] Embedder loaded.")
    return _embedder



# ── FAISS retrieval ───────────────────────────────────────
def retrieve_chunks(query: str) -> list[dict]:
    """Embed query and retrieve top-K chunks — no filtering."""
    embedder        = get_embedder()
    index, metadata = get_faiss()

    query_emb          = embedder.encode([query], convert_to_numpy=True).astype("float32")
    distances, indices = index.search(query_emb, RERANK_TOP_K)

    chunks = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        chunk                   = dict(metadata[idx])
        chunk["faiss_distance"] = round(float(dist), 4)
        chunks.append(chunk)

    logger.info(f"[Baseline] Retrieved {len(chunks)} chunks.")
    return chunks


# ── Plain prompt assembly ─────────────────────────────────
def assemble_prompt(query: str, chunks: list[dict]) -> str:
    """
    No security structure — plain context + question.
    Exactly what a standard RAG pipeline does.
    """
    lines = []

    lines.append("You are a helpful assistant.")
    lines.append("Answer the question using the context below.")
    lines.append("")
    lines.append("Context:")

    for i, chunk in enumerate(chunks, 1):
        lines.append(f"[{i}] {chunk['text'].strip()}")
        lines.append("") 

    lines.append("Question:")
    lines.append(query.strip())

    return "\n".join(lines)




# ── Main baseline query function ──────────────────────────
def run_baseline_query(query: str) -> dict:
    """
    Unprotected RAG pipeline — no defenses.

    Args:
        query : user question

    Returns:
        dict:
            answer     : LLM response
            chunks     : number of chunks used
            latency_ms : total pipeline latency
    """
    start = time.time()

    # ── Retrieve ──────────────────────────────────────────
    chunks = retrieve_chunks(query)

    if not chunks:
        logger.warning("[Baseline] No chunks retrieved.")
        return {
            "answer":     "I could not find relevant information to answer your query.",
            "chunks":     0,
            "latency_ms": int((time.time() - start) * 1000),
        }

    # ── Assemble prompt ───────────────────────────────────
    prompt = assemble_prompt(query, chunks)

    # ── LLM ───────────────────────────────────────────────
    answer = call_llm(prompt)

    latency = int((time.time() - start) * 1000)
    logger.info(f"[Baseline] Done — latency={latency}ms")

    return {
        "answer":     answer,
        "chunks":     len(chunks),
        "latency_ms": latency,
    }