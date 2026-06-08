import json
import hashlib
from pathlib import Path

INPUT_PATH = Path("data/processed/chunks_metadata.json")
OUTPUT_PATH = Path("data/processed/chunks_metadata_dedup.json")

def hash_text(text):
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    chunks = json.load(f)

seen = set()
clean_chunks = []

for c in chunks:
    h = hash_text(c["text"])
    if h not in seen:
        seen.add(h)
        c["hash"] = h
        clean_chunks.append(c)

print("Original:", len(chunks))
print("Cleaned:", len(clean_chunks))
print("Removed:", len(chunks) - len(clean_chunks))

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(clean_chunks, f, indent=2)

print("Saved:", OUTPUT_PATH)