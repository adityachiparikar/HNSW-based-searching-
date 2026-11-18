from typing import Any, List, Union
import os
import threading
import hashlib
import re
from vector_utils import Vector, normalize, to_vector_batch, weighted_concat, zero_vector

model_name = "all-MiniLM-L6-v2"
model: Any = None
model_load_error: str | None = None
_model_lock = threading.Lock()
EMBEDDING_MODE = os.getenv("EMBEDDING_MODE", "hybrid").casefold().strip()
if os.getenv("USE_TRANSFORMER_MODEL", "0") == "1" and EMBEDDING_MODE == "fast":
    EMBEDDING_MODE = "hybrid"
TORCH_NUM_THREADS = int(os.getenv("TORCH_NUM_THREADS", str(min(8, max(2, os.cpu_count() or 2)))))
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "128"))
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "").strip()

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


def get_model() -> Any:
    global model, model_load_error
    if EMBEDDING_MODE not in {"transformer", "hybrid"}:
        return None
    if model is None:
        from sentence_transformers import SentenceTransformer
        try:
            import torch

            torch.set_num_threads(TORCH_NUM_THREADS)
            device = EMBEDDING_DEVICE or ("cuda" if torch.cuda.is_available() else "cpu")
        except Exception:
            device = EMBEDDING_DEVICE or None

        print(f"Loading embedding model: {model_name}...", flush=True)
        try:
            model = SentenceTransformer(model_name, device=device, local_files_only=True)
            model_load_error = None
            print(f"Embedding device: {device or 'default'}, torch threads: {TORCH_NUM_THREADS}", flush=True)
            print("Model loaded successfully.", flush=True)
        except Exception as e:
            model_load_error = str(e)
            if EMBEDDING_MODE == "transformer":
                raise
            print(f"Hybrid transformer unavailable; using hash fallback. Reason: {model_load_error}", flush=True)
    return model


def _hash_embedding(text: str, dimensions: int = 384) -> Vector:
    vector = zero_vector(dimensions)
    tokens = re.findall(r"[a-z0-9]+", str(text).casefold())
    if not tokens:
        return vector

    for token in tokens:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        bucket = int.from_bytes(digest[:4], "little") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += sign

    return normalize(vector)


def _transformer_embedding(text: Union[str, List[str]]) -> Union[Vector, List[Vector]]:
    with _model_lock:
        loaded_model = get_model()
        if loaded_model is None:
            if isinstance(text, list):
                return [zero_vector(384) for _ in text]
            return zero_vector(384)

        encoded = loaded_model.encode(
            text,
            batch_size=EMBEDDING_BATCH_SIZE,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
    vectors = to_vector_batch(encoded)
    return vectors if isinstance(text, list) else vectors[0]


def _combine_embeddings(hash_vectors: List[Vector], transformer_vectors: List[Vector]) -> List[Vector]:
    return [
        weighted_concat(hash_vector, 0.45, transformer_vector, 0.55)
        for hash_vector, transformer_vector in zip(hash_vectors, transformer_vectors)
    ]


def get_embedding_mode() -> str:
    return EMBEDDING_MODE


def get_embedding_info() -> dict:
    return {
        "mode": EMBEDDING_MODE,
        "batch_size": EMBEDDING_BATCH_SIZE,
        "torch_threads": TORCH_NUM_THREADS,
        "device": EMBEDDING_DEVICE or "auto",
        "transformer_available": model is not None,
        "transformer_error": model_load_error,
    }

def encode_text(text: Union[str, List[str]]) -> Union[Vector, List[Vector]]:
    """
    Converts text (or a list of texts) into vector embeddings.
    """
    if EMBEDDING_MODE not in {"fast", "transformer", "hybrid"}:
        raise ValueError("EMBEDDING_MODE must be one of: fast, transformer, hybrid")

    if EMBEDDING_MODE == "fast":
        if isinstance(text, list):
            return [_hash_embedding(item) for item in text]
        return _hash_embedding(text)

    if EMBEDDING_MODE == "transformer":
        return _transformer_embedding(text)

    if isinstance(text, list):
        hash_vectors = [_hash_embedding(item) for item in text]
    else:
        hash_vectors = [_hash_embedding(text)]

    transformer_vectors = _transformer_embedding(text)
    if not isinstance(text, list):
        transformer_vectors = [transformer_vectors]

    combined = _combine_embeddings(hash_vectors, transformer_vectors)
    return combined if isinstance(text, list) else combined[0]
