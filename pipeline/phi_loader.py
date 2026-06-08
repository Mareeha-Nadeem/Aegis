"""
pipeline/phi_loader.py

Shared LLM loader.

Singleton pattern — model loads once, reused by both
rag_hardened.py and rag_baseline.py.
"""

import threading
import torch
import sys
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM

sys.path.append(str(Path(__file__).parent.parent))
from config import PHI_MODEL, MAX_NEW_TOKENS
from aegis_logging.logger import get_logger

logger = get_logger(__name__)

# ── Singleton ─────────────────────────────────────────────
_llm_model     = None
_llm_tokenizer = None

_llm_lock         = threading.Lock()
_llm_loading      = False
_llm_load_error   = None
_llm_loaded_event = threading.Event()


def llm_is_ready() -> bool:
    return _llm_model is not None and _llm_tokenizer is not None


def llm_is_loading() -> bool:
    return _llm_loading


def llm_load_error() -> str | None:
    return _llm_load_error


def warm_llm_async() -> None:
    """Kick off model loading in a background thread (non-blocking)."""
    with _llm_lock:
        if llm_is_ready() or _llm_loading:
            return

    def _runner():
        try:
            get_llm()
        except Exception as e:
            logger.exception("[LLM] Background load failed")

    threading.Thread(target=_runner, daemon=True, name="aegis-llm-warmup").start()


def get_phi():
    """Backward-compatible alias for `get_llm()` (kept to avoid refactors)."""
    return get_llm()


def get_llm():
    """Load the configured instruct model once and reuse across pipelines."""
    global _llm_model, _llm_tokenizer
    with _llm_lock:
        if llm_is_ready():
            return _llm_model, _llm_tokenizer

        # If another thread is already loading, wait for it.
        if _llm_loading:
            event = _llm_loaded_event
        else:
            globals()["_llm_loading"] = True
            _llm_loaded_event.clear()
            event = None

    if event is not None:
        event.wait()
        if llm_is_ready():
            return _llm_model, _llm_tokenizer
        raise RuntimeError(_llm_load_error or "LLM failed to load")

    # This thread is responsible for loading.
    try:
        has_cuda = torch.cuda.is_available()
        device_map = "auto" if has_cuda else "cpu"
        torch_dtype = torch.float16 if has_cuda else torch.float32

        logger.info(
            f"[LLM] Loading model: {PHI_MODEL} | device_map={device_map} | dtype={torch_dtype}"
        )

        tokenizer = AutoTokenizer.from_pretrained(PHI_MODEL, use_fast=True)
        model = AutoModelForCausalLM.from_pretrained(
            PHI_MODEL,
            torch_dtype=torch_dtype,
            device_map=device_map,
            low_cpu_mem_usage=True,
        )
        model.eval()

        if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
            tokenizer.pad_token_id = tokenizer.eos_token_id

        with _llm_lock:
            _llm_model = model
            _llm_tokenizer = tokenizer
            globals()["_llm_load_error"] = None

        logger.info("[LLM] Model loaded.")
        return _llm_model, _llm_tokenizer

    except Exception as e:
        with _llm_lock:
            globals()["_llm_load_error"] = f"{type(e).__name__}: {e}"
        raise

    finally:
        with _llm_lock:
            globals()["_llm_loading"] = False
            _llm_loaded_event.set()


def call_llm(prompt: str) -> str:
    """Generate response using the configured instruct model."""
    model, tokenizer = get_llm()

    try:
        with torch.inference_mode():
            inputs = tokenizer(prompt, return_tensors="pt")
            device = next(model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}

            outputs = model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )

        # Return only the continuation (not the echoed prompt).
        prompt_len = inputs["input_ids"].shape[1]
        generated = outputs[0][prompt_len:]
        return tokenizer.decode(generated, skip_special_tokens=True).strip()
    except Exception as e:
        logger.error(f"[LLM] Generation failed: {e}")
        return ""