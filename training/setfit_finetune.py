"""
training/setfit_finetune.py

SetFit Fine-tuning Script.

Fine-tunes a SetFit (few-shot text classification) model on labelled examples
of safe vs. injected/malicious document chunks. Produces the trained model
artifact used by Layer 2 (Chunk Classifier) to score retrieval results at
inference time.
"""
