"""
Aegis RAG Pipeline - Chunk Processor with DeBERTa Scoring
Processes document chunks and runs DeBERTa-v3 model for prompt injection detection.
Generates JSON metadata with scores.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
import logging

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import pandas as pd
from tqdm import tqdm

# =====================================
# LOGGING
# =====================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChunkProcessor:
    """
    prompt injection scoring pipeline.
    """

    def __init__(self, model_name: str = "protectai/deberta-v3-base-prompt-injection-v2"):
        logger.info(f"Loading model: {model_name}")

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Device: {self.device}")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name).to(self.device)
        self.model.eval()

        logger.info(f"Model labels: {self.model.config.id2label}")

    def score_chunk(self, chunk_text: str) -> float:
        try:
            inputs = self.tokenizer(
                chunk_text,
                return_tensors="pt",
                truncation=True,
                max_length=512
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.softmax(outputs.logits, dim=-1)[0]

            injection_idx = 1  # correct for this model
            score = probs[injection_idx].item()

            return round(score, 4)

        except Exception as e:
            logger.error(f"Scoring failed: {e}")
            return 0.0

    def process_chunks_from_list(
        self,
        chunks: List[Dict[str, Any]],
        output_dir: str = "./output"
    ) -> List[Dict[str, Any]]:

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        metadata = []

        logger.info(f"Processing {len(chunks)} chunks...")

        for chunk in tqdm(chunks, desc="Scoring"):

            text = chunk.get("text", "")
            score = self.score_chunk(text)

            metadata.append({
                "chunk_id": chunk.get("chunk_id", ""),
                "document_id": chunk.get("document_id", ""),
                "file_name": chunk.get("file_name", ""),
                "source_type": chunk.get("source_type", ""),
                "classification": chunk.get("classification", ""),
                "chunk_index": chunk.get("chunk_index"),
                "total_chunks": chunk.get("total_chunks"),
                "text": text,
                "score_1": score
            })

            logger.info(f"{chunk.get('chunk_id')} -> score_1: {score}")

        output_path = os.path.join(output_dir, "chunks_metadata.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved: {output_path}")

        return metadata


def load_chunks_from_json(filepath: str) -> List[Dict[str, Any]]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data)} chunks")
        return data
    except Exception as e:
        logger.error(f"Load failed: {e}")
        return []


def main():
    logger.info("Aegis DeBERTa Scoring Pipeline Started")

    processor = ChunkProcessor()

    chunks_file = r"C:\Users\User\projects\Aegis\data\processed\chunked_data.json"
    output_dir = r"C:\Users\User\projects\Aegis\data\processed"

    chunks = load_chunks_from_json(chunks_file)

    if not chunks:
        logger.error("No chunks found. Exit.")
        return

    metadata = processor.process_chunks_from_list(chunks, output_dir)

    logger.info(f"Total chunks processed: {len(metadata)}")
    logger.info("Done.")
    

if __name__ == "__main__":
    main()