"""
config.py
Global Configuration for Aegis.
"""

from pathlib import Path

# ── Project root ──────────────────────────────────────────
BASE_DIR = Path(__file__).parent

# ── Data paths ────────────────────────────────────────────
DATA_DIR             = BASE_DIR / "data"
CHUNKS_METADATA_PATH = DATA_DIR / "processed" / "chunks_metadata.json"
CHUNKS_CSV_PATH      = DATA_DIR / "processed" / "chunks_dataset.csv"

# ── Model paths ───────────────────────────────────────────
MODELS_DIR          = BASE_DIR / "models"
FAISS_INDEX_PATH    = MODELS_DIR / "faiss_index" / "index.faiss"
FAISS_META_PATH     = MODELS_DIR / "faiss_index" / "metadata.pkl"
SETFIT_MODEL_PATH   = MODELS_DIR / "setfit"
CENTROIDS_PATH      = MODELS_DIR / "centroids.pkl"
EMBEDDER_MODEL      = "all-MiniLM-L6-v2"
CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-12-v2"
PHI_MODEL           = "Qwen/Qwen2.5-0.5B-Instruct"

# ── LLM generation ───────────────────────────────────────
# Keep defaults conservative for CPU-only environments.
MAX_NEW_TOKENS      = 512

# ── Chunking ──────────────────────────────────────────────
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

# ── FAISS retrieval ───────────────────────────────────────
TOP_K = 12

# ── Reranker ──────────────────────────────────────────────
RERANK_TOP_K      = 5
RERANK_TOP_K_MAX  = 8
RERANK_BATCH_SIZE = 12

# ── Layer 3 thresholds ────────────────────────────────────
THRESHOLD_DROP   = 0.8
THRESHOLD_DEMOTE = 0.5
RELEVANCE_FLOOR  = 0.15
CHUNK_MAX_CHARS  = 1200

# ── Layer 4 thresholds ────────────────────────────────────
# WARNING: uncalibrated placeholders
# Calibrate after eval. Expected range: -0.25 to +0.25
L4_BLOCK = 0.15
L4_WARN  = 0.05

# ── Logging ───────────────────────────────────────────────
LOGS_DIR  = BASE_DIR / "logs"
LOG_LEVEL = "INFO"