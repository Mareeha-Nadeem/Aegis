# Aegis

AI/ML-based system focused on security and robustness against indirect prompt injection and data exfiltration in RAG pipelines. It implements chunk-level risk filtering and output validation to improve LLM safety and reliability.

---

## Project Structure

```
Aegis/
├── config.py                         # Global runtime configuration
├── main.py                           # Application entry point (serve / evaluate / train)
├── requirements.txt                  # Python dependencies
│
├── pipeline/                         # Core RAG pipeline layers
│   ├── __init__.py
│   ├── layer1_ingestion_guard.py     # Layer 1 – screens documents at ingestion time
│   ├── layer2_chunk_classifier.py    # Layer 2 – classifies retrieved chunks by risk level
│   ├── layer3_prompt_assembly.py     # Layer 3 – assembles hardened prompts for the LLM
│   ├── layer4_output_validator.py    # Layer 4 – validates LLM responses before delivery
│   ├── rag_baseline.py               # Unprotected baseline RAG pipeline
│   └── rag_hardened.py               # Full Aegis-protected RAG pipeline
│
├── training/
│   └── setfit_finetune.py            # Fine-tunes the SetFit chunk-risk classifier
│
├── evaluation/
│   ├── eval_harness.py               # End-to-end evaluation orchestration
│   └── metrics.py                    # Security & performance metrics
│
├── logging/
│   └── logger.py                     # Centralised structured logger
│
├── data/
│   ├── raw/                          # Raw source documents (unprocessed)
│   ├── processed/                    # Pre-processed / chunked documents
│   └── documents/                    # Curated document store for the vector DB
│
├── models/
│   ├── setfit/                       # Trained SetFit model artefacts
│   └── faiss_index/                  # FAISS vector index files
│
├── notebooks/                        # Exploratory Jupyter notebooks
├── tests/                            # Unit and integration tests
└── logs/                             # Runtime log files
```

## Getting Started

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the hardened RAG service
python main.py serve

# 4. Run the evaluation harness
python main.py evaluate

# 5. Fine-tune the chunk classifier
python main.py train
```
