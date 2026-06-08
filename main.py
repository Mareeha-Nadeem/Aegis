"""
main.py

<<<<<<< HEAD
Application Entry Point.

Parses command-line arguments and launches the appropriate mode:
  - 'serve'    : starts the hardened RAG pipeline as an interactive service
  - 'evaluate' : runs the evaluation harness against the benchmark suite
  - 'train'    : fine-tunes the SetFit chunk classifier
"""
=======
Aegis FastAPI Server.

Endpoints:
    POST /query  — run aegis or baseline pipeline
    GET  /health — health check
"""

import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.append(str(Path(__file__).parent))
from pipeline.rag_hardened import run_hardened_query
from pipeline.rag_baseline import run_baseline_query
from pipeline.phi_loader  import llm_is_loading, llm_is_ready, llm_load_error, warm_llm_async
from aegis_logging.logger  import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title       = "Aegis RAG API",
    description = "Hardened vs Baseline RAG pipeline comparison",
    version     = "1.0.0",
)


@app.on_event("startup")
def _warm_models():
    # Avoid the first /query call appearing to hang while HF downloads / loads weights.
    warm_llm_async()

# ── CORS — React frontend ke liye ────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ── Request model ─────────────────────────────────────────
class QueryRequest(BaseModel):
    query : str
    mode  : str = "aegis"   # "aegis" | "baseline"


# ── Endpoints ─────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status": "ok",
        "llm_ready": llm_is_ready(),
        "llm_loading": llm_is_loading(),
        "llm_error": llm_load_error(),
    }


@app.post("/query")
def query(request: QueryRequest):
    """
    Run aegis or baseline RAG pipeline.

    Body:
        query : user question
        mode  : "aegis" | "baseline"
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if request.mode not in ("aegis", "baseline"):
        raise HTTPException(status_code=400, detail="Mode must be 'aegis' or 'baseline'.")

    # If the LLM is still downloading/loading, return a fast, explicit response.
    if not llm_is_ready():
        if llm_is_loading():
            raise HTTPException(status_code=503, detail="LLM is loading (first run can take minutes on CPU). Try again shortly.")
        if llm_load_error():
            raise HTTPException(status_code=500, detail=f"LLM failed to load: {llm_load_error()}")

    logger.info(f"[API] mode={request.mode} | query='{request.query[:60]}'")

    if request.mode == "aegis":
        result = run_hardened_query(request.query)
        return {
            "answer":      result["answer"],
            "mode":        "aegis",
            "verdict":     result["verdict"],
            "score_3":     result["score_3"],
            "safe_chunks": result["safe_chunks"],
            "dropped":     result["dropped"],
            "latency_ms":  result["latency_ms"],
        }

    else:
        result = run_baseline_query(request.query)
        return {
            "answer":     result["answer"],
            "mode":       "baseline",
            "chunks":     result["chunks"],
            "latency_ms": result["latency_ms"],
        }


# ── Run ───────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
>>>>>>> 712ea001c4db72213d1f7679e9523872a5095070
