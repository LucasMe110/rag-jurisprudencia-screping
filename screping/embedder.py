from sentence_transformers import SentenceTransformer


def generate_embeddings(records: list[dict]) -> list[dict]:
    model = SentenceTransformer("intfloat/multilingual-e5-base")
    texts = [f"passage: {r.get('decisao') or ''}" for r in records]
    vectors = model.encode(texts, batch_size=256, normalize_embeddings=True)
    for record, vector in zip(records, vectors):
        record["embedding"] = vector.tolist()
    return records
