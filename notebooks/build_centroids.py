"""
notebooks/build_centroids.py

One-time script to build injection and benign centroids
from deepset/prompt-injections dataset.

Saves: models/centroids.pkl
    {
        "injection_centroid": np.ndarray,
        "benign_centroid":    np.ndarray,
        "model":              str,
    }
"""

import pickle
import logging
import numpy as np
import sys
from pathlib import Path
from datasets import load_dataset
from sentence_transformers import SentenceTransformer

sys.path.append(str(Path(__file__).parent.parent))
from config import EMBEDDER_MODEL, CENTROIDS_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Injection keywords (filter weak samples) ──────────────
INJECTION_KEYWORDS = [
    "ignore",
    "forget",
    "disregard",
    "override",
    "bypass",
    "you are now",
    "act as",
    "pretend",
    "system prompt",
    "reveal",
    "repeat after",
    "do not follow",
    "new instructions",
    "jailbreak",
    "dan",
    "unrestricted",
    "no restrictions",
    "without restrictions",
]


def is_strong_injection(text: str) -> bool:
    """Keep only clear instruction override / role hijack attempts."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in INJECTION_KEYWORDS)


# ── Load dataset ──────────────────────────────────────────
logger.info("Loading deepset/prompt-injections dataset...")
dataset = load_dataset("deepset/prompt-injections", split="train")
logger.info(f"Total samples: {len(dataset)}")

# ── Split and filter ──────────────────────────────────────
injection_texts = []
benign_texts    = []

for sample in dataset:
    text  = sample["text"].strip()
    label = sample["label"]  # 1 = injection, 0 = benign

    if not text:
        continue

    if label == 1:
        if is_strong_injection(text):
            injection_texts.append(text)
    else:
        benign_texts.append(text)

logger.info(f"Strong injections kept : {len(injection_texts)}")
logger.info(f"Benign samples kept    : {len(benign_texts)}")

if len(injection_texts) < 10:
    raise ValueError(
        "Too few injection samples after filtering. "
        "Check INJECTION_KEYWORDS or dataset."
    )

# ── Embed ─────────────────────────────────────────────────
logger.info(f"Loading embedder: {EMBEDDER_MODEL}")
embedder = SentenceTransformer(EMBEDDER_MODEL)

logger.info("Embedding injection samples...")
injection_embeddings = embedder.encode(
    injection_texts,
    batch_size=64,
    show_progress_bar=True,
    convert_to_numpy=True,
).astype("float32")

logger.info("Embedding benign samples...")
benign_embeddings = embedder.encode(
    benign_texts,
    batch_size=64,
    show_progress_bar=True,
    convert_to_numpy=True,
).astype("float32")

# ── Compute + normalize centroids ────────────────────────
injection_centroid = injection_embeddings.mean(axis=0).astype("float32")
benign_centroid    = benign_embeddings.mean(axis=0).astype("float32")

injection_centroid = injection_centroid / np.linalg.norm(injection_centroid)
benign_centroid    = benign_centroid    / np.linalg.norm(benign_centroid)

logger.info(f"Injection centroid shape : {injection_centroid.shape}")
logger.info(f"Benign centroid shape    : {benign_centroid.shape}")

# ── Save ──────────────────────────────────────────────────
CENTROIDS_PATH.parent.mkdir(parents=True, exist_ok=True)

with open(CENTROIDS_PATH, "wb") as f:
    pickle.dump({
        "injection_centroid": injection_centroid,
        "benign_centroid":    benign_centroid,
        "model":              EMBEDDER_MODEL,
    }, f)

logger.info(f"Centroids saved → {CENTROIDS_PATH}")
logger.info("Done.")