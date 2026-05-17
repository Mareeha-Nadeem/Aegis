from pathlib import Path
import json
import hashlib

BASE_DIR = Path(__file__).resolve().parents[1]



INPUT_FILE = BASE_DIR / "data" / "documents" / "all_parsed.json"

OUTPUT_FILE = BASE_DIR / "data" / "processed" / "chunked_data.json"


# =====================================
# CHUNK FUNCTION
# =====================================

def chunk_text(text, chunk_size=250, overlap=60):

    words = text.split()

    chunks = []

    start = 0

    while start < len(words):

        end = start + chunk_size

        chunk = " ".join(words[start:end])

        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


# =====================================
# LOAD PARSED JSON
# =====================================

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    documents = json.load(f)


# =====================================
# CREATE CHUNKS
# =====================================



def make_chunk_id(doc_id, idx, text):
    short_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
    return f"doc_{doc_id}_chunk_{idx}_{short_hash}"
chunked_data = []


for doc in documents:

    chunks = chunk_text(doc["content"])

    total_chunks = len(chunks)

    for idx, chunk in enumerate(chunks, start=1):

        chunked_data.append({

            # "chunk_id": f"doc{doc['id']}_chunk{idx}",
            "chunk_id": make_chunk_id(doc['id'], idx, chunk),

            "document_id": f"doc_{doc['id']}",

            "source_type": Path(doc["file_name"]).suffix.replace(".", ""),

            "chunk_index": idx,

            "total_chunks": total_chunks,

            "text": chunk
        })


# =====================================
# SAVE
# =====================================

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(chunked_data, f, indent=2, ensure_ascii=False)


print("Chunked data saved:", OUTPUT_FILE)