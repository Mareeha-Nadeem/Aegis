"""
pipeline/layer2_chunk_classifier.py

Layer 2 – Chunk Classifier.

Uses a fine-tuned SetFit model to assign a risk score to every text chunk
retrieved from the vector store.  High-risk chunks are filtered or quarantined
before being forwarded to the prompt assembly stage.
"""
