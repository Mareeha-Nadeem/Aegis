"""
Aegis RAG Pipeline - Chunk Processor with DeBERTa Scoring
Processes document chunks, runs DeBERTa-v3 model for prompt injection detection,
and generates JSON metadata and CSV files.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
import logging

# Check and warn about missing dependencies
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import pandas as pd
    from tqdm import tqdm
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install transformers torch pandas tqdm")
    exit(1)

# =====================================
# CONFIGURE LOGGING
# =====================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChunkProcessor:
    """
    Processes document chunks with DeBERTa-v3 model for prompt injection scoring.
    """

    def __init__(self, model_name: str = "protectai/deberta-v3-base-prompt-injection-v2"):
        """
        Initialize the processor with the specified DeBERTa model.
        """
        logger.info(f"Starting model initialization: {model_name}")
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using system hardware device: {self.device}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name).to(self.device)
        self.model.eval()
        
        logger.info("DeBERTa Model loaded successfully into memory")

    def score_chunk(self, chunk_text: str) -> float:
        """
        Score a single chunk for prompt injection risk using DeBERTa.
        """
        try:
            inputs = self.tokenizer(
                chunk_text,
                return_tensors="pt",
                truncation=True,
                max_length=512
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                # Extracting probability of the "injection" class (index 1)
                score = torch.softmax(logits, dim=-1)[0, 1].item()

            return round(score, 4)
        except Exception as e:
            logger.error(f"Failed to score chunk due to an error: {e}")
            return 0.0

    def process_chunks_from_list(
        self,
        chunks: List[Dict[str, Any]],
        output_dir: str = "./output"
    ) -> tuple:
        """
        Process a list of chunks and generate corrected JSON + CSV files.
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        metadata = []
        csv_rows = []

        logger.info(f"Beginning scoring pipeline for {len(chunks)} text chunks...")

        for chunk in tqdm(chunks, desc="Scoring progress"):
            chunk_text = chunk.get("text", "")
            score = self.score_chunk(chunk_text)

            # Updated keys to align seamlessly with your chunked_data.json schema
            metadata_entry = {
                "chunk_id": chunk.get("chunk_id", ""),
                "document_id": chunk.get("document_id", ""),
                "source_type": chunk.get("source_type", ""),
                "chunk_index": chunk.get("chunk_index", None),
                "total_chunks": chunk.get("total_chunks", None),
                "text": chunk_text,
                "deberta_score": score,
                "risk_level": self._classify_risk(score),
                "timestamp": pd.Timestamp.now().isoformat()
            }
            metadata.append(metadata_entry)

            # Created matching structured record for the dataset output
            csv_row = {
                "chunk_id": chunk.get("chunk_id", ""),
                "chunk_text": chunk_text,
                "label": "safe"  # Pre-labeled as safe per pipeline design parameters
            }
            csv_rows.append(csv_row)

        logger.info("Completed processing framework across all nodes.")

        # Export outputs
        json_path = os.path.join(output_dir, "chunks_metadata.json")
        self._save_json(metadata, json_path)

        csv_path = os.path.join(output_dir, "chunks_dataset.csv")
        self._save_csv(csv_rows, csv_path)

        return metadata, csv_rows

    def _classify_risk(self, score: float) -> str:
        """
        Classify risk level based on operational threshold benchmarks.
        """
        if score > 0.8:
            return "critical"
        elif score > 0.6:
            return "high"
        elif score > 0.4:
            return "medium"
        elif score > 0.2:
            return "low"
        else:
            return "minimal"

    def _save_json(self, data: List[Dict], filepath: str) -> None:
        """Save structured data output array to target JSON path."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ Target JSON metadata saved: {filepath}")
        except Exception as e:
            logger.error(f"Failed writing json export payload: {e}")

    def _save_csv(self, rows: List[Dict], filepath: str) -> None:
        """Save chunk data matrix to target CSV path."""
        try:
            df = pd.DataFrame(rows)
            df.to_csv(filepath, index=False, encoding='utf-8')
            logger.info(f"✓ Target CSV dataset saved: {filepath}")
        except Exception as e:
            logger.error(f"Failed building pandas tabular CSV export: {e}")


def load_chunks_from_json(filepath: str) -> List[Dict[str, Any]]:
    """
    Safely locate and unpack raw text chunks from input JSON.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        logger.info(f"Loaded {len(chunks)} items successfully from path file data matrix.")
        return chunks
    except Exception as e:
        logger.error(f"Aborted loading configuration file layout matching path criteria: {e}")
        return []


def main():
    """
    Main orchestration function block.
    """
    logger.info("=" * 60)
    logger.info("AEGIS CHUNK PROCESSOR - DeBERTa Scoring Pipeline")
    logger.info("=" * 60)

    # Initialize the processor engine
    processor = ChunkProcessor()

    # Fixed path evaluation variables matching system directory environments
    chunks_file = "C:\\Users\\User\\Desktop\\Aegis\\Aegis\\data\\processed\\chunked_data.json"
    output_directory = "C:\\Users\\User\\Desktop\\Aegis\\Aegis\\data\\processed"

    # Read records mapping matching dataset schema rules
    chunks = load_chunks_from_json(chunks_file)

    if not chunks:
        logger.error("No valid documents found. Stopping operational loop execution.")
        return

    # Trigger model scoring lifecycle pipeline
    metadata, csv_data = processor.process_chunks_from_list(chunks, output_directory)

    # Output executive pipeline summaries directly across logging console channels
    logger.info("\n" + "=" * 60)
    logger.info("PROCESSING SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total chunks evaluated: {len(metadata)}")
    logger.info(f"Output Target Directory: {output_directory}")
    logger.info("Generated Pipeline Objects:")
    logger.info("  1. chunks_metadata.json -> Deep analytical JSON containing metrics & source maps.")
    logger.info("  2. chunks_dataset.csv  -> Flat corpus extraction file emphasizing explicit safety tags.")


if __name__ == "__main__":
    main()