import os
import torch
from sentence_transformers import SentenceTransformer

# Textos jurídicos podem ter milhares de chars, mas o modelo trunca em 512 tokens.
# Pré-truncar para ~2000 chars evita tokenização desnecessária e reduz tempo em CPU.
_MAX_CHARS = 2000
_BATCH_SIZE = 32  # seguro para runners 2-CPU/7GB RAM


def generate_embeddings(records: list[dict]) -> list[dict]:
    torch.set_num_threads(os.cpu_count() or 2)
    model = SentenceTransformer("intfloat/multilingual-e5-base")
    texts = [f"passage: {(r.get('decisao') or '')[:_MAX_CHARS]}" for r in records]
    vectors = model.encode(
        texts,
        batch_size=_BATCH_SIZE,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    for record, vector in zip(records, vectors):
        record["embedding"] = vector.tolist()
    return records
