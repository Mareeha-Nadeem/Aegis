# Aegis

> A multi-layer adversarial defense framework for Retrieval-Augmented Generation (RAG) pipelines, designed to detect and neutralize indirect prompt injection attacks at ingestion, retrieval, generation, and output stages.

---

## Overview

Large Language Models deployed in RAG architectures are vulnerable to indirect prompt injection — adversarial instructions embedded within retrieved documents that hijack LLM behavior. Aegis addresses this by introducing a four-layer defense pipeline that intercepts, scores, and filters malicious context before it reaches the model, and validates generated outputs before they reach the user.

---

## System Architecture
```
┌─────────────────────────────────────────────────────────┐
│                     AEGIS PIPELINE                      │
├─────────────────────────────────────────────────────────┤
│  INGESTION                                              │
│  Document → [Layer 1: Ingestion Guard] → FAISS Store    │
│             DeBERTa-v3 · score_1 ∈ [0,1]               │
├─────────────────────────────────────────────────────────┤
│  RETRIEVAL                                              │
│  Query → Top-K Chunks → [Layer 2: Chunk Classifier]     │
│          SetFit · score_2 ∈ [0,1]                       │
│          combined = 0.4 × score_1 + 0.6 × score_2       │
│          combined > 0.8 → DROP                          │
│          combined > 0.5 → DEMOTE  (weight = 0.3)        │
│          combined ≤ 0.5 → ALLOW   (weight = 1.0)        │
├─────────────────────────────────────────────────────────┤
│  GENERATION                                             │
│  [Layer 3: Prompt Assembly]                             │
│  [SYSTEM] + [TRUSTED CONTEXT] +                         │
│  [UNVERIFIED CONTEXT] + [USER QUERY] → Phi SLM          │
├─────────────────────────────────────────────────────────┤
│  VALIDATION                                             │
│  [Layer 4: Output Validator]                            │
│  Leakage Detection + Cosine Similarity                  │
│  score_3 > 0.7 → BLOCK                                  │
│  score_3 > 0.4 → WARN                                   │
│  score_3 ≤ 0.4 → SAFE                                   │
└─────────────────────────────────────────────────────────┘
```
---

## Layer Specification

| Layer | Stage | Component | Model / Tool | Output |
|-------|-------|-----------|-------------|--------|
| 1 | Ingestion | Ingestion Guard | `protectai/deberta-v3-base-prompt-injection-v2` | `score_1 ∈ [0,1]` |
| 2 | Retrieval | Chunk Classifier | SetFit fine-tuned on `deepset/prompt-injections` | `score_2 ∈ [0,1]` |
| 3 | Generation | Prompt Assembly | LangChain + Phi SLM | Structured hardened prompt |
| 4 | Output | Output Validator | FAISS + `sentence-transformers` + cosine similarity | BLOCK / WARN / SAFE |

---

## Project Structure
```
Aegis/
├── config.py                         # Global runtime configuration
├── main.py                           # Entry point — serve / evaluate / train
├── requirements.txt                  # Pinned Python dependencies
│
├── pipeline/
│   ├── __init__.py
│   ├── layer1_ingestion_guard.py     # DeBERTa-v3 injection scoring at ingestion
│   ├── layer2_chunk_classifier.py    # SetFit chunk-level risk classification
│   ├── layer3_prompt_assembly.py     # Hardened prompt construction with trust separation
│   ├── layer4_output_validator.py    # Leakage detection and semantic similarity validation
│   ├── rag_baseline.py               # Unprotected vanilla RAG pipeline (eval baseline)
│   └── rag_hardened.py               # Full Aegis-protected RAG pipeline
│
├── training/
│   └── setfit_finetune.py            # SetFit fine-tuning on prompt injection dataset
│
├── evaluation/
│   ├── eval_harness.py               # End-to-end evaluation orchestration
│   └── metrics.py                    # ASR, FPR, FNR, RAG Utility Score, latency
│
├── data/
│   ├── raw/                          # Raw source documents
│   ├── processed/                    # Chunked and preprocessed documents
│   └── documents/                    # Curated vector store document corpus
│
├── models/
│   ├── setfit/                       # Fine-tuned SetFit model artifacts
│   └── faiss_index/                  # Serialized FAISS vector index
│
├── notebooks/                        # Exploratory and experimental notebooks
├── tests/                            # Unit and integration test suite
└── logs/                             # Structured runtime logs (JSONL)
```
---

## Installation

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.11.x |
| RAM | 16 GB recommended |
| GPU | Optional (CPU inference supported) |

### Setup

```bash
# Clone the repository
git clone https://github.com/Mareeha-Nadeem/Aegis.git
cd Aegis

# Create and activate virtual environment
py -3.11 -m venv rag_env
rag_env\Scripts\activate        # Windows
source rag_env/bin/activate     # Linux / macOS

# Install PyTorch (CPU build)
pip install torch==2.3.1 torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
pip install -r requirements.txt
```

---

## Usage

```bash
# Fine-tune the SetFit chunk-risk classifier
python main.py train

# Run the Aegis-hardened RAG service
python main.py serve

# Execute the evaluation harness
python main.py evaluate
```

---

## Evaluation Metrics

| Metric | Description |
|--------|-------------|
| **ASR** | Attack Success Rate — proportion of injections that reached the user |
| **FPR** | False Positive Rate — legitimate queries incorrectly blocked |
| **FNR** | False Negative Rate — attacks that bypassed all four layers |
| **RAG Utility Score** | Answer quality on clean, non-adversarial queries |
| **Latency Overhead** | Additional inference time introduced by the four-layer pipeline |
| **Layer Attribution** | Per-layer breakdown of detected and blocked attacks |

---

## Tech Stack

| Category | Libraries |
|----------|-----------|
| ML Framework | PyTorch, HuggingFace Transformers |
| NLP Models | DeBERTa-v3, SetFit, Phi SLM, sentence-transformers |
| Vector Store | FAISS |
| RAG Framework | LangChain |
| Classical ML | scikit-learn |
| Data | HuggingFace Datasets |

---

## Author

**Mareeha Nadeem**  
 
[linkedin.com/in/mareeha-nadeem](https://linkedin.com/in/mareeha-nadeem) 
[github.com/Mareeha-Nadeem](https://github.com/Mareeha-Nadeem)