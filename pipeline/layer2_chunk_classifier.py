"""
pipeline/layer2_chunk_classifier.py

Layer 2 – Chunk Classifier.

Takes retrieved document chunks and classifies each one by risk level using
a fine-tuned SetFit model. High-risk chunks are flagged or excluded before
they are included in the prompt context, preventing injection content from
reaching the LLM.
"""
