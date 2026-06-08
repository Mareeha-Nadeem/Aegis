import pickle
from collections import Counter

with open("models/faiss_index/metadata.pkl", "rb") as f:
    chunks = pickle.load(f)

texts = [c["text"] for c in chunks]

counts = Counter(texts)

dupes = {k:v for k,v in counts.items() if v > 1}

print("Duplicate unique texts:", len(dupes))
print("Total duplicates:", sum(v-1 for v in dupes.values()))