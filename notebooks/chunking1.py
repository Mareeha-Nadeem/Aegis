<<<<<<< HEAD
# from pathlib import Path
# import json
# import hashlib

# BASE_DIR = Path(__file__).resolve().parents[1]



# INPUT_FILE = BASE_DIR / "data" / "documents" / "all_parsed.json"

# OUTPUT_FILE = BASE_DIR / "data" / "processed" / "chunked_data.json"


# # =====================================
# # CHUNK FUNCTION
# # =====================================

# def chunk_text(text, chunk_size=250, overlap=60):

#     words = text.split()

#     chunks = []

#     start = 0

#     while start < len(words):

#         end = start + chunk_size

#         chunk = " ".join(words[start:end])

#         chunks.append(chunk)

#         start += chunk_size - overlap

#     return chunks


# # =====================================
# # LOAD PARSED JSON
# # =====================================

# with open(INPUT_FILE, "r", encoding="utf-8") as f:
#     documents = json.load(f)


# # =====================================
# # CREATE CHUNKS
# # =====================================



# def make_chunk_id(doc_id, idx, text):
#     short_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
#     return f"doc_{doc_id}_chunk_{idx}_{short_hash}"
# chunked_data = []


# for doc in documents:

#     chunks = chunk_text(doc["content"])

#     total_chunks = len(chunks)

#     for idx, chunk in enumerate(chunks, start=1):

#         chunked_data.append({

#             # "chunk_id": f"doc{doc['id']}_chunk{idx}",
#             "chunk_id": make_chunk_id(doc['id'], idx, chunk),

#             "document_id": f"doc_{doc['id']}",

#             "source_type": Path(doc["file_name"]).suffix.replace(".", ""),

#             "chunk_index": idx,

#             "total_chunks": total_chunks,

#             "text": chunk
#         })


# # =====================================
# # SAVE
# # =====================================

# with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
#     json.dump(chunked_data, f, indent=2, ensure_ascii=False)


# print("Chunked data saved:", OUTPUT_FILE)

=======
>>>>>>> 712ea001c4db72213d1f7679e9523872a5095070
from pathlib import Path
import json
import hashlib

BASE_DIR = Path(__file__).resolve().parents[1]

<<<<<<< HEAD
INPUT_FILE = BASE_DIR / "data" / "documents" / "all_parsed.json"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "chunked_data.json"

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
=======


INPUT_FILE = BASE_DIR / "data" / "documents" / "all_parsed.json"

OUTPUT_FILE = BASE_DIR / "data" / "processed" / "chunked_data.json"

>>>>>>> 712ea001c4db72213d1f7679e9523872a5095070

# =====================================
# CHUNK FUNCTION
# =====================================

def chunk_text(text, chunk_size=250, overlap=60):
<<<<<<< HEAD
    words = text.split()

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])

        if chunk.strip():
            chunks.append(chunk)
=======

    words = text.split()

    chunks = []

    start = 0

    while start < len(words):

        end = start + chunk_size

        chunk = " ".join(words[start:end])

        chunks.append(chunk)
>>>>>>> 712ea001c4db72213d1f7679e9523872a5095070

        start += chunk_size - overlap

    return chunks

<<<<<<< HEAD
=======

>>>>>>> 712ea001c4db72213d1f7679e9523872a5095070
# =====================================
# LOAD PARSED JSON
# =====================================

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    documents = json.load(f)

<<<<<<< HEAD
# =====================================
# CHUNK ID GENERATOR
# =====================================

def make_chunk_id(doc_id, idx, text):
    short_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
    return f"doc_{doc_id}_chunk_{idx}_{short_hash}"
=======
>>>>>>> 712ea001c4db72213d1f7679e9523872a5095070

# =====================================
# CREATE CHUNKS
# =====================================

<<<<<<< HEAD
chunked_data = []

for doc in documents:

    content = doc.get("content", "")
    doc_id = doc.get("id")
    file_name = doc.get("file_name", "")

    if not content:
        continue

    chunks = chunk_text(content)
=======


def make_chunk_id(doc_id, idx, text):
    short_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
    return f"doc_{doc_id}_chunk_{idx}_{short_hash}"
chunked_data = []


for doc in documents:

    chunks = chunk_text(doc["content"])

>>>>>>> 712ea001c4db72213d1f7679e9523872a5095070
    total_chunks = len(chunks)

    for idx, chunk in enumerate(chunks, start=1):

        chunked_data.append({
<<<<<<< HEAD
            "chunk_id": make_chunk_id(doc_id, idx, chunk),
            "document_id": f"doc_{doc_id}",
            "file_name": file_name,
            "source_type": Path(file_name).suffix.replace(".", ""),
            "classification": doc.get("classification", "general"),
            "chunk_index": idx,
            "total_chunks": total_chunks,
            "text": chunk
        })

# =====================================
# SAVE OUTPUT
=======

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
>>>>>>> 712ea001c4db72213d1f7679e9523872a5095070
# =====================================

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(chunked_data, f, indent=2, ensure_ascii=False)

<<<<<<< HEAD
=======

>>>>>>> 712ea001c4db72213d1f7679e9523872a5095070
print("Chunked data saved:", OUTPUT_FILE)