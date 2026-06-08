"""
build_faiss_index.py

Reads chunks_metadata_dedup.json, embeds text using sentence-transformers,
builds FAISS index, and saves index + metadata to models/faiss_index/
"""

import json
import pickle
import numpy as np
import faiss
import sys
from sentence_transformers import SentenceTransformer
from pathlib import Path

# ── Config import ─────────────────────────────────────────
sys.path.append(str(Path(__file__).parent.parent))
from config import FAISS_INDEX_PATH, FAISS_META_PATH, EMBEDDER_MODEL

# ── Paths ─────────────────────────────────────────────────
CHUNKS_PATH = Path("data/processed/chunks_metadata_dedup.json")
INDEX_DIR   = FAISS_INDEX_PATH.parent
INDEX_PATH  = FAISS_INDEX_PATH
META_PATH   = FAISS_META_PATH

# ── Load chunks ───────────────────────────────────────────
print("Loading chunks...")
with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"Loaded {len(chunks)} chunks")

# ── Embed ─────────────────────────────────────────────────
print("Loading embedding model...")
model = SentenceTransformer(EMBEDDER_MODEL)

texts = [c["text"] for c in chunks]

print("Embedding chunks... (this may take a few minutes)")
embeddings = model.encode(texts, batch_size=64, show_progress_bar=True)
embeddings = np.array(embeddings).astype("float32")

print(f"Embeddings shape: {embeddings.shape}")

# ── Build FAISS index ─────────────────────────────────────
print("Building FAISS index...")
dim = embeddings.shape[1]  # 384 for MiniLM

INDEX_DIR.mkdir(parents=True, exist_ok=True)
index = faiss.IndexFlatL2(dim)
index.add(embeddings)

print(f"Index size: {index.ntotal} vectors")

# ── Save ──────────────────────────────────────────────────
faiss.write_index(index, str(INDEX_PATH))
print(f"FAISS index saved → {INDEX_PATH}")

with open(META_PATH, "wb") as f:
    pickle.dump(chunks, f)
print(f"Metadata saved → {META_PATH}")

print("\nDone! FAISS index ready.")