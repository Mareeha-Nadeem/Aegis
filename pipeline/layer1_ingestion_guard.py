"""
pipeline/layer1_ingestion_guard.py

Layer 1 – Ingestion Guard.

<<<<<<< HEAD
Responsible for screening raw documents and data chunks at ingestion time.
Detects and filters out potentially malicious or adversarial content
(e.g., indirect prompt injection payloads, PII leakage triggers) before
they are stored in the vector database or passed further downstream.
"""
=======
Screens raw document chunks at ingestion time using a fine-tuned
SetFit model. Assigns score_1 to each chunk and stores in FAISS
with metadata.

Score_1: 0.0 = safe, 1.0 = injection
"""

import pickle
import logging
import numpy as np
import faiss
from datetime import datetime
from setfit import SetFitModel
from sentence_transformers import SentenceTransformer
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config import (
    SETFIT_MODEL_PATH,
    EMBEDDER_MODEL,
    FAISS_INDEX_PATH,
    FAISS_META_PATH,
)

from aegis_logging.logger import get_logger, log_event
logger = get_logger(__name__)

# ── Model loading (singleton) ─────────────────────────────
_setfit_model = None
_embedder     = None


def get_setfit_model():
    """Load SetFit model once and reuse."""
    global _setfit_model
    if _setfit_model is None:
        if not Path(SETFIT_MODEL_PATH).exists():
            raise FileNotFoundError(
                f"SetFit model not found at {SETFIT_MODEL_PATH}. "
                "Run training/setfit_finetune.py first."
            )
        logger.info(f"[Layer 1] Loading SetFit model from {SETFIT_MODEL_PATH}...")
        _setfit_model = SetFitModel.from_pretrained(str(SETFIT_MODEL_PATH))
        logger.info("[Layer 1] SetFit model loaded.")
    return _setfit_model


def get_embedder():
    """Load sentence embedder once and reuse."""
    global _embedder
    if _embedder is None:
        logger.info("[Layer 1] Loading sentence embedder...")
        _embedder = SentenceTransformer(EMBEDDER_MODEL)
        logger.info("[Layer 1] Embedder loaded.")
    return _embedder


# ── Core scoring ──────────────────────────────────────────
def score_chunk(chunk_text: str, model=None) -> float:
    """
    Score a single chunk for injection risk using SetFit.
    Returns score_1 between 0.0 (safe) and 1.0 (injection).
    """
    if not chunk_text or not chunk_text.strip():
        logger.warning("[Layer 1] Empty chunk received, returning score_1=0.0")
        return 0.0

    mdl = model or get_setfit_model()

    try:
        probs   = mdl.predict_proba([chunk_text])  # shape: (1, 2)
        score_1 = float(probs[0][1])               # index 1 = injection class
        return round(score_1, 4)
    except Exception as e:
        logger.error(f"[Layer 1] Scoring failed: {e}")
        return 0.0


def run_ingestion_guard(chunks: list[str], model=None) -> list[dict]:
    """
    Score a list of raw text chunks at ingestion time.

    Returns:
        list of dicts:
            text      : original chunk text
            score_1   : injection risk score (0.0 – 1.0)
            timestamp : ISO timestamp of scoring
    """
    if not chunks:
        logger.warning("[Layer 1] No chunks provided.")
        return []

    mdl     = model or get_setfit_model()
    results = []

    for i, chunk in enumerate(chunks):
        score_1 = score_chunk(chunk, mdl)
        results.append({
            "text":      chunk,
            "score_1":   score_1,
            "timestamp": datetime.utcnow().isoformat(),
        })
        logger.debug(
            f"[Layer 1] Chunk {i+1}/{len(chunks)} | score_1={score_1:.4f}"
        )

    high_risk = sum(1 for r in results if r["score_1"] > 0.5)
    logger.info(
        f"[Layer 1] Ingestion complete — "
        f"{len(results)} chunks scored, {high_risk} high-risk (score_1 > 0.5)"
    )

    return results


# ── FAISS update (new documents ke liye) ─────────────────
def add_to_faiss_index(new_chunks: list[dict]) -> None:
    """
    Embed new scored chunks and add to existing FAISS index.
    new_chunks: output of run_ingestion_guard() — dicts with 'text' and 'score_1'.
    """
    if not new_chunks:
        logger.warning("[Layer 1] add_to_faiss_index: no chunks to add.")
        return

    if not FAISS_INDEX_PATH.exists() or not FAISS_META_PATH.exists():
        raise FileNotFoundError(
            "FAISS index not found. Run notebooks/build_faiss_index.py first."
        )

    # Load existing index + metadata
    index = faiss.read_index(str(FAISS_INDEX_PATH))
    with open(FAISS_META_PATH, "rb") as f:
        metadata: list = pickle.load(f)

    # Embed new chunks
    embedder   = get_embedder()
    texts      = [c["text"] for c in new_chunks]
    embeddings = embedder.encode(texts, batch_size=64, show_progress_bar=False)
    embeddings = np.array(embeddings).astype("float32")

    # Add to FAISS
    index.add(embeddings)
    metadata.extend(new_chunks)

    # Persist
    faiss.write_index(index, str(FAISS_INDEX_PATH))
    with open(FAISS_META_PATH, "wb") as f:
        pickle.dump(metadata, f)

    logger.info(
        f"[Layer 1] {len(new_chunks)} chunks added to FAISS. "
        f"Total vectors: {index.ntotal}"
    )
>>>>>>> 712ea001c4db72213d1f7679e9523872a5095070
