"""
training/setfit_finetune.py

SetFit Fine-tuning Script.

Fine-tunes a SetFit (few-shot text classification) model on labelled examples
of safe vs. injected/malicious document chunks. Produces the trained model
artifact used by Layer 2 (Chunk Classifier) to score retrieval results at
inference time.
"""

from datasets import load_dataset, concatenate_datasets, Dataset
from setfit import SetFitModel, Trainer, TrainingArguments
import pandas as pd
import os

# ── 1. Load deepset dataset ──────────────────────────────────────────
print("[Training] Loading deepset/prompt-injections dataset...")
deepset_data = load_dataset("deepset/prompt-injections", split="train")

# ── 2. Load your custom CSV (placeholder) ────────────────────────────
CUSTOM_CSV_PATH = "data/raw/custom_dataset.csv"  # 👈 replace with your actual filename

if os.path.exists(CUSTOM_CSV_PATH):
    print(f"[Training] Loading custom dataset from {CUSTOM_CSV_PATH}...")
    custom_df = pd.read_csv(CUSTOM_CSV_PATH)
    custom_data = Dataset.from_pandas(custom_df[["text", "label"]])
    combined = concatenate_datasets([deepset_data, custom_data])
    print(f"[Training] Combined dataset size: {len(combined)}")
else:
    print("[Training] No custom dataset found, using deepset only.")
    combined = deepset_data
    print(f"[Training] Dataset size: {len(combined)}")

# ── 3. Load base SetFit model ─────────────────────────────────────────
print("[Training] Loading base SetFit model...")
model = SetFitModel.from_pretrained("sentence-transformers/paraphrase-mpnet-base-v2")

# ── 4. Training arguments ─────────────────────────────────────────────
args = TrainingArguments(
    batch_size=2,
    num_epochs=1,
    num_iterations=1,
    evaluation_strategy="no",
    save_strategy="no",
    logging_steps=1,
)
trainer = Trainer(
    model=model,
    args=args,
    train_dataset=combined,
    eval_dataset=combined,
    column_mapping={"text": "text", "label": "label"}
)


# ── 6. Train ──────────────────────────────────────────────────────────
print("[Training] Starting fine-tuning...")
try:
    trainer.train()
    print("[Training] Fine-tuning complete!")
except Exception as e:
    print(f"[ERROR] Training failed: {e}")
    traceback.print_exc()

# ── 7. Save model ─────────────────────────────────────────────────────
os.makedirs("models/setfit", exist_ok=True)
model.save_pretrained("models/setfit")
print("[Training] Model saved to models/setfit/")
import traceback

