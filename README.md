# Aegis

AI/ML-based system focused on security and robustness against prompt injection
and data exfiltration in RAG pipelines.  Aegis implements a multi-layer
defence architecture — ingestion guard, chunk-level risk filtering, hardened
prompt assembly, and output validation — to improve LLM safety and
reliability.

---

## Project Structure

```
Aegis/
├── pipeline/
│   ├── __init__.py                  # Package initialisation
│   ├── layer1_ingestion_guard.py    # Layer 1 – sanitise documents at ingest time
│   ├── layer2_chunk_classifier.py   # Layer 2 – risk-score retrieved chunks
│   ├── layer3_prompt_assembly.py    # Layer 3 – build hardened LLM prompts
│   ├── layer4_output_validator.py   # Layer 4 – validate / redact LLM responses
│   ├── rag_baseline.py              # Unprotected RAG pipeline (baseline)
│   └── rag_hardened.py              # Security-hardened RAG pipeline
│
├── training/
│   ├── __init__.py
│   └── setfit_finetune.py           # Fine-tune SetFit chunk risk classifier
│
├── evaluation/
│   ├── __init__.py
│   ├── eval_harness.py              # End-to-end evaluation runner
│   └── metrics.py                   # ASR, DSR, faithfulness, latency metrics
│
├── logging/
│   ├── __init__.py
│   └── logger.py                    # Centralised structured logger
│
├── data/
│   ├── raw/                         # Original source documents
│   ├── processed/                   # Chunked / embedded data
│   └── documents/                   # Curated document corpus
│
├── models/
│   ├── setfit/                      # Saved SetFit model artifacts
│   └── faiss_index/                 # FAISS vector index files
│
├── notebooks/                       # Exploratory Jupyter notebooks
├── tests/                           # Unit and integration tests
├── logs/                            # Runtime log files
│
├── config.py                        # Global configuration & constants
├── main.py                          # CLI entry point
├── requirements.txt                 # Python dependencies
└── .gitignore
```

---

## Getting Started

```bash
# 1. Clone the repository
git clone https://github.com/Mareeha-Nadeem/Aegis.git
cd Aegis

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python main.py
```

---

## Roadmap

- [ ] Implement Layer 1 – Ingestion Guard
- [ ] Implement Layer 2 – Chunk Classifier (SetFit)
- [ ] Implement Layer 3 – Prompt Assembly
- [ ] Implement Layer 4 – Output Validator
- [ ] Build FAISS vector store and RAG baseline
- [ ] Assemble hardened RAG pipeline
- [ ] Fine-tune SetFit model on labelled chunk dataset
- [ ] Run evaluation harness and publish benchmark results
