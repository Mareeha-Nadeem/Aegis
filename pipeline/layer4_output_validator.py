"""
pipeline/layer4_output_validator.py

Layer 4 – Output Validator.

Validates LLM output against injection attack patterns using
dual-centroid differential scoring.

score_3 = cosine(output, injection_centroid)
        - cosine(output, benign_centroid)

Decision (in priority order):
    1. Leakage keywords present → BLOCK immediately (no score check needed)
    2. score_3 > effective_block → BLOCK
    3. score_3 > effective_warn  → WARN  (sanitized output, not raw)
    4. else                      → SAFE

effective_block and effective_warn are tightened when Layer 3 already
flagged many suspicious chunks (drop_ratio > 0), so the system is more
aggressive about blocking outputs that followed a suspicious retrieval.

NOTE: L4_BLOCK and L4_WARN are uncalibrated placeholders.
Calibrate after running eval on benign + attack output distributions.
Expected real score range: approximately -0.25 to +0.25

CHANGES (v2):
    - Leakage keywords now trigger a hard BLOCK instead of log-only.
    - WARN no longer returns raw output — returns a hedged prefix + 300-char
      truncated output so attacked responses are not silently passed through.
    - run_output_validator() accepts drop_ratio and max_score_1_dropped from
      Layer 3 and uses them to compute context-aware effective thresholds.
    - block_reason field added to log_record to distinguish leakage blocks
      from score-based blocks in downstream analysis.
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


# ── Leakage check ─────────────────────────────────────────
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

    If the LLM output echoes injection-style language back to the user,
    the injection likely succeeded at the prompt level even if score_3
    looks borderline. We treat this as a hard BLOCK signal.
    """
    output_lower = output.lower()
    matched      = [kw for kw in LEAKAGE_KEYWORDS if kw in output_lower]

    return {
        "leakage_flag":     len(matched) > 0,
        "matched_keywords": matched,
    }


# ── Effective threshold computation ──────────────────────
def _compute_effective_thresholds(
    drop_ratio: float,
    max_score_1_dropped: float,
) -> tuple[float, float]:
    """
    Tighten L4 thresholds when Layer 3 already saw suspicious chunks.

    Logic:
        drop_ratio          → how much of the retrieved context was flagged.
                              A high ratio means the retrieval set itself was
                              contaminated, making the output more suspect.
        max_score_1_dropped → severity of the worst chunk seen.
                              A very high score_1 means a strongly injected
                              chunk was present, even if Layer 3 caught it.

    Both signals independently reduce the thresholds so Layer 4 blocks
    more aggressively when the upstream environment looked hostile.

    Caps:
        Block threshold floor : L4_BLOCK - 0.05  (never drops below this)
        Warn  threshold floor : L4_WARN  - 0.04
    """
    # drop_ratio contribution: scale 0.0→1.0 to 0.0→0.03 threshold reduction
    drop_ratio_adj = 0.03 * drop_ratio

    # max_score_1 contribution: scale 0.0→1.0 to 0.0→0.02 threshold reduction
    score1_adj = 0.02 * min(max_score_1_dropped, 1.0)

    total_adj = drop_ratio_adj + score1_adj

    effective_block = max(L4_BLOCK - total_adj, L4_BLOCK - 0.05)
    effective_warn  = max(L4_WARN  - total_adj, L4_WARN  - 0.04)

    logger.debug(
        f"[Layer 4] Threshold adjustment — "
        f"drop_ratio={drop_ratio:.3f} | "
        f"max_score_1={max_score_1_dropped:.4f} | "
        f"total_adj={total_adj:.4f} | "
        f"effective_block={effective_block:.4f} | "
        f"effective_warn={effective_warn:.4f}"
    )

    return effective_block, effective_warn


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


# ── WARN sanitizer ────────────────────────────────────────
_WARN_PREFIX = (
    "I found relevant information but I'm not fully confident in this "
    "response. Please verify with an authoritative source: "
)

def _sanitize_warn_output(raw_output: str) -> str:
    """
    For WARN verdicts, never return the raw LLM output unchanged.

    We truncate to 300 characters and prepend a hedging prefix so the user
    gets partial utility while the suspicious content is contained.
    Returning raw output on a WARN verdict was the original bug: 48 attack
    responses were being silently passed through.
    """
    truncated = raw_output.strip()[:300]
    if len(raw_output.strip()) > 300:
        truncated += "…"
    return _WARN_PREFIX + truncated


# ── Main Layer 4 function ─────────────────────────────────
def run_output_validator(
    output: str,
    query: str,
    safe_chunks: list[dict],
    drop_log: list[dict],
    drop_ratio: float = 0.0,           # NEW — from Layer 3
    max_score_1_dropped: float = 0.0,  # NEW — from Layer 3
) -> dict:
    """
    Validate LLM output for injection patterns.

    Args:
        output               : raw LLM output string
        query                : original user query
        safe_chunks          : ALLOW chunks from Layer 3
        drop_log             : drop records from Layer 3
        drop_ratio           : fraction of retrieved chunks that Layer 3 dropped
                               → used to tighten effective thresholds
        max_score_1_dropped  : highest score_1 among safety/demote drops
                               → used to tighten effective thresholds

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

    # ── Compute context-aware thresholds ──────────────────
    effective_block, effective_warn = _compute_effective_thresholds(
        drop_ratio, max_score_1_dropped
    )

    # ── Decision (priority order) ─────────────────────────

    # Priority 1: leakage keywords → hard BLOCK regardless of score_3.
    # If the LLM is echoing injection-style language, the attack likely
    # succeeded at the prompt level. No score threshold can save this.
    if leakage["leakage_flag"]:
        verdict      = "BLOCK"
        final_output = "I'm unable to provide a response to this query."
        block_reason = "leakage_keyword"
        logger.warning(
            f"[Layer 4] BLOCK (leakage) | "
            f"keywords={leakage['matched_keywords']} | "
            f"query='{query[:60]}'"
        )

    # Priority 2: score above effective block threshold
    elif score_3 > effective_block:
        verdict      = "BLOCK"
        final_output = "I'm unable to provide a response to this query."
        block_reason = "score_3"
        logger.warning(
            f"[Layer 4] BLOCK (score) | score_3={score_3:.4f} | "
            f"effective_block={effective_block:.4f} | "
            f"query='{query[:60]}'"
        )

    # Priority 3: score above effective warn threshold.
    # Do NOT return raw output — sanitize it.
    # The original code returned raw output here, which meant 48 attack
    # responses were silently passed through on WARN verdicts.
    elif score_3 > effective_warn:
        verdict      = "WARN"
        final_output = _sanitize_warn_output(output)
        block_reason = None
        logger.warning(
            f"[Layer 4] WARN  | score_3={score_3:.4f} | "
            f"effective_warn={effective_warn:.4f} | "
            f"query='{query[:60]}'"
        )

    # Priority 4: safe
    else:
        verdict      = "SAFE"
        final_output = output
        block_reason = None
        logger.debug(f"[Layer 4] SAFE  | score_3={score_3:.4f}")

    # ── Log record ────────────────────────────────────────
    log_record = {
        "verdict":              verdict,
        "score_3":              score_3,
        "inj_sim":              round(inj_sim, 4),
        "benign_sim":           round(benign_sim, 4),
        "query":                query,
        "leakage_flag":         leakage["leakage_flag"],
        "leakage_keywords":     leakage["matched_keywords"],
        "block_reason":         block_reason,          # NEW: leakage_keyword | score_3 | None
        "dropped_chunks":       len(drop_log),
        "safe_chunks":          len(safe_chunks),
        "drop_ratio":           round(drop_ratio, 4),  # NEW
        "max_score_1_dropped":  round(max_score_1_dropped, 4),  # NEW
        "effective_block":      round(effective_block, 4),      # NEW
        "effective_warn":       round(effective_warn, 4),       # NEW
        "layer":                "L4",
        "timestamp":            datetime.utcnow().isoformat(),
    }

    return {
        "verdict":      verdict,
        "score_3":      score_3,
        "final_output": final_output,
        "log_record":   log_record,
    }