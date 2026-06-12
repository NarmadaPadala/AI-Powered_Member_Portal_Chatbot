from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec

from src.documents import KBDocument, batches
from src.local_hybrid import char_ngrams, cosine, lexical_score, source_boost, tokenize
from src.settings import Settings


def get_client(settings: Settings) -> Pinecone:
    return Pinecone(api_key=settings.pinecone_api_key)


def get_openai_client(settings: Settings) -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key)


def ensure_index(pc: Pinecone, settings: Settings) -> None:
    if pc.has_index(settings.index_name):
        return

    pc.create_index(
        name=settings.index_name,
        vector_type="dense",
        dimension=settings.embedding_dimension,
        metric="cosine",
        spec=ServerlessSpec(cloud=settings.cloud, region=settings.region),
    )


def _dense_embedding(openai_client: OpenAI, settings: Settings, texts: list[str]) -> list[list[float]]:
    response = openai_client.embeddings.create(
        model=settings.embedding_model,
        input=texts,
        dimensions=settings.embedding_dimension,
    )
    return [item.embedding for item in response.data]


def _query_dense_embedding(openai_client: OpenAI, settings: Settings, query: str) -> list[float]:
    response = openai_client.embeddings.create(
        model=settings.embedding_model,
        input=[query],
        dimensions=settings.embedding_dimension,
    )
    return response.data[0].embedding


def upsert_documents(
    pc: Pinecone,
    settings: Settings,
    documents: list[KBDocument],
    batch_size: int = 20,
) -> int:
    index = pc.Index(settings.index_name)
    openai_client = get_openai_client(settings)
    count = 0

    for batch in batches(documents, batch_size):
        texts = [doc.text for doc in batch]
        dense_vectors = _dense_embedding(openai_client, settings, texts)

        vectors = []
        for doc, dense in zip(batch, dense_vectors):
            vectors.append(
                {
                    "id": doc.id,
                    "values": dense,
                    "metadata": doc.metadata,
                }
            )

        index.upsert(vectors=vectors, namespace=settings.namespace)
        count += len(vectors)

    return count


def query_hybrid(
    pc: Pinecone,
    settings: Settings,
    query: str,
    member_id: str,
    plan_id: str,
    top_k: int = 5,
    alpha: float = 0.55,
) -> dict:
    if not 0 <= alpha <= 1:
        raise ValueError("alpha must be between 0 and 1")

    openai_client = get_openai_client(settings)
    dense = _query_dense_embedding(openai_client, settings, query)

    metadata_filter = {
        "$and": [
            {
                "$or": [
                    {"member_id": {"$eq": member_id}},
                    {"member_id": {"$eq": "ALL"}},
                ]
            },
            {
                "$or": [
                    {"plan_id": {"$eq": plan_id}},
                    {"plan_id": {"$eq": "ALL"}},
                ]
            },
        ]
    }

    index = pc.Index(settings.index_name)
    candidate_k = max(top_k * 4, 20)
    response = index.query(
        namespace=settings.namespace,
        vector=dense,
        top_k=candidate_k,
        include_metadata=True,
        filter=metadata_filter,
    )
    result = response.to_dict() if hasattr(response, "to_dict") else response
    result["matches"] = rerank_hybrid(query, result.get("matches", []), top_k=top_k, alpha=alpha)
    return result


def rerank_hybrid(query: str, matches: list[dict], top_k: int, alpha: float) -> list[dict]:
    if not matches:
        return []

    max_dense = max(float(match.get("score", 0)) for match in matches) or 1.0
    query_tokens = tokenize(query)
    query_chars = char_ngrams(query)
    reranked = []

    for match in matches:
        metadata = match.get("metadata", {})
        combined_text = " ".join(
            [
                metadata.get("title", ""),
                metadata.get("source_type", ""),
                metadata.get("text", ""),
            ]
        )
        dense_score = float(match.get("score", 0)) / max_dense
        lexical = lexical_score(query_tokens, tokenize(combined_text))
        fuzzy = cosine(query_chars, char_ngrams(combined_text))
        keyword_score = max(lexical, fuzzy) + source_boost(query, metadata.get("source_type", ""))
        hybrid_score = (alpha * dense_score) + ((1 - alpha) * keyword_score)

        updated = dict(match)
        updated["dense_score"] = round(dense_score, 4)
        updated["keyword_score"] = round(keyword_score, 4)
        updated["score"] = round(hybrid_score, 4)
        reranked.append(updated)

    return sorted(reranked, key=lambda item: item["score"], reverse=True)[:top_k]


def summarize_matches(result: dict, min_confidence: float = 0.38) -> dict:
    matches = result.get("matches", [])
    best_score = matches[0]["score"] if matches else 0
    should_escalate = best_score < min_confidence

    return {
        "best_score": best_score,
        "should_escalate": should_escalate,
        "matches": matches,
    }
