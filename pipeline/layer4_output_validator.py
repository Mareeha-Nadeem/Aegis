"""
pipeline/layer4_output_validator.py

Layer 4 – Output Validator.

Validates LLM output against injection attack patterns using
dual-centroid differential scoring.

score_3 = cosine(output, injection_centroid)
        - cosine(output, benign_centroid)

Decision:
    score_3 > L4_BLOCK → BLOCK + log
    score_3 > L4_WARN  → WARN  + log
    else               → SAFE

Leakage check → logged only, not part of decision.

NOTE: L4_BLOCK and L4_WARN are uncalibrated placeholders.
Calibrate after running eval on benign + attack output distributions.
Expected real score range: approximately -0.25 to +0.25
"""

import pickle

import numpy as np
import sys
from datetime import datetime
from pathlib import Path
from sentence_transformers import SentenceTransformer

sys.path.append(str(Path(__file__).parent.parent))
from config import (
    EMBEDDER_MODEL,
    CENTROIDS_PATH,
    L4_BLOCK,
    L4_WARN,
)

from aegis_logging.logger import get_logger, log_event
logger = get_logger(__name__)


# ── Model + centroid loading (singleton) ──────────────────
_embedder           = None
_injection_centroid = None
_benign_centroid    = None


def get_embedder():
    global _embedder
    if _embedder is None:
        logger.info(f"[Layer 4] Loading embedder: {EMBEDDER_MODEL}")
        _embedder = SentenceTransformer(EMBEDDER_MODEL)
        logger.info("[Layer 4] Embedder loaded.")
    return _embedder


def get_centroids() -> tuple[np.ndarray, np.ndarray]:
    global _injection_centroid, _benign_centroid
    if _injection_centroid is None or _benign_centroid is None:
        if not CENTROIDS_PATH.exists():
            raise FileNotFoundError(
                f"Centroids not found at {CENTROIDS_PATH}. "
                "Run notebooks/build_centroids.py first."
            )
        logger.info(f"[Layer 4] Loading centroids from {CENTROIDS_PATH}...")
        with open(CENTROIDS_PATH, "rb") as f:
            data = pickle.load(f)

        # Embedding model consistency check
        saved_model = data.get("model", "")
        if saved_model and saved_model != EMBEDDER_MODEL:
            raise ValueError(
                f"Centroid built with '{saved_model}' "
                f"but config uses '{EMBEDDER_MODEL}'. "
                "Rebuild centroids with matching model."
            )

        _injection_centroid = data["injection_centroid"]
        _benign_centroid    = data["benign_centroid"]
        logger.info("[Layer 4] Centroids loaded.")

    return _injection_centroid, _benign_centroid


# ── Cosine similarity (no sklearn) ───────────────────────
def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Direct normalized dot product — no sklearn overhead."""
    return float(
        np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)
    )


# ── Leakage check (log only) ──────────────────────────────
LEAKAGE_KEYWORDS = [
    "ignore", "forget", "disregard", "override",
    "bypass", "you are now", "act as", "pretend",
    "system prompt", "reveal", "repeat after",
    "do not follow", "new instructions",
    "unrestricted", "no restrictions",
]


def compute_leakage(output: str) -> dict:
    """
    Lightweight keyword leakage check.
    For logging/debug only — not used in decision.
    """
    output_lower = output.lower()
    matched      = [kw for kw in LEAKAGE_KEYWORDS if kw in output_lower]

    return {
        "leakage_flag":     len(matched) > 0,
        "matched_keywords": matched,
    }


# ── Core scoring ──────────────────────────────────────────
def compute_score_3(output: str) -> tuple[float, float, float]:
    """
    Dual-centroid differential score.

    Returns:
        score_3    : inj_sim - benign_sim
        inj_sim    : cosine similarity to injection centroid
        benign_sim : cosine similarity to benign centroid
    """
    if not output or not output.strip():
        logger.warning("[Layer 4] Empty output, returning score_3=1.0")
        return 1.0, 1.0, 0.0

    embedder                            = get_embedder()
    injection_centroid, benign_centroid = get_centroids()

    try:
        output_emb = embedder.encode(
            [output],
            convert_to_numpy=True,
        ).astype("float32")[0]

        # Normalize output embedding
        output_emb = output_emb / (np.linalg.norm(output_emb) + 1e-8)

        inj_sim    = _cosine(output_emb, injection_centroid)
        benign_sim = _cosine(output_emb, benign_centroid)
        score_3    = round(inj_sim - benign_sim, 4)

        logger.debug(
            f"[Layer 4] inj_sim={inj_sim:.4f} | "
            f"benign_sim={benign_sim:.4f} | "
            f"score_3={score_3:.4f}"
        )

        return score_3, inj_sim, benign_sim

    except Exception as e:
        logger.error(f"[Layer 4] Scoring failed: {e}")
        return 0.0, 0.0, 0.0


# ── Main Layer 4 function ─────────────────────────────────
def run_output_validator(
    output: str,
    query: str,
    safe_chunks: list[dict],
    drop_log: list[dict],
) -> dict:
    """
    Validate LLM output for injection patterns.

    Args:
        output      : raw LLM output string
        query       : original user query
        safe_chunks : ALLOW chunks from Layer 3
        drop_log    : drop records from Layer 3

    Returns:
        dict:
            verdict      : BLOCK | WARN | SAFE
            score_3      : differential centroid score
            final_output : response to return to user
            log_record   : full record for logging
    """
    if not output or not output.strip():
        logger.warning("[Layer 4] Empty LLM output.")
        return {
            "verdict":      "BLOCK",
            "score_3":      1.0,
            "final_output": "I'm unable to provide a response to this query.",
            "log_record":   None,
        }

    score_3, inj_sim, benign_sim = compute_score_3(output)
    leakage                      = compute_leakage(output)

    # ── Decision ──────────────────────────────────────────
    if score_3 > L4_BLOCK:
        verdict      = "BLOCK"
        final_output = "I'm unable to provide a response to this query."
    elif score_3 > L4_WARN:
        verdict      = "WARN"
        final_output = output
    else:
        verdict      = "SAFE"
        final_output = output

    # ── Log record ────────────────────────────────────────
    log_record = {
        "verdict":          verdict,
        "score_3":          score_3,
        "inj_sim":          round(inj_sim, 4),
        "benign_sim":       round(benign_sim, 4),
        "query":            query,
        "leakage_flag":     leakage["leakage_flag"],
        "leakage_keywords": leakage["matched_keywords"],
        "dropped_chunks":   len(drop_log),
        "safe_chunks":      len(safe_chunks),
        "layer":            "L4",
        "timestamp":        datetime.utcnow().isoformat(),
    }

    if verdict == "BLOCK":
        logger.warning(
            f"[Layer 4] BLOCK | score_3={score_3:.4f} | "
            f"query='{query[:60]}'"
        )
    elif verdict == "WARN":
        logger.warning(
            f"[Layer 4] WARN  | score_3={score_3:.4f} | "
            f"query='{query[:60]}'"
        )
    else:
        logger.debug(f"[Layer 4] SAFE  | score_3={score_3:.4f}")

    return {
        "verdict":      verdict,
        "score_3":      score_3,
        "final_output": final_output,
        "log_record":   log_record,
    }