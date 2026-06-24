"""
Step 3: RAG Pipeline - embed code chunks and retrieve similar context from Qdrant.

Uses OpenAI text-embedding-3-small to embed method source code, stores in
Qdrant, then retrieves top-K similar chunks as context for prompt building.
"""
import logging
from typing import Dict, Any, List

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import OpenAI
import hashlib

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)
EMBEDDING_DIM = 768  # text-embedding-004 dimension

def _get_qdrant_client() -> QdrantClient:
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def _get_openai_client() -> OpenAI:
    return OpenAI(
        api_key=settings.effective_api_key,
        base_url=settings.effective_api_base
    )


def _ensure_collection(client: QdrantClient):
    """Create the Qdrant collection if it doesn't exist."""
    collections = [c.name for c in client.get_collections().collections]
    if settings.qdrant_collection not in collections:
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
        logger.info(f"Created Qdrant collection: {settings.qdrant_collection}")


def _embed_text(openai_client: OpenAI, text: str) -> List[float]:
    """Get embedding vector for a text string."""
    response = openai_client.embeddings.create(
        model=settings.effective_embedding_model,
        input=text[:8000],  # Truncate to fit model limits
    )
    return response.data[0].embedding


def _text_to_id(text: str) -> str:
    """Generate a deterministic point ID from text content."""
    return hashlib.md5(text.encode()).hexdigest()


def embed_and_retrieve(code_model: Dict[str, Any], top_k: int = 3) -> Dict[str, str]:
    """
    For each method:
      1. Embed the method source code
      2. Upsert to Qdrant
      3. Query for similar methods as RAG context

    Returns: dict mapping "ClassName.methodName" -> concatenated RAG context
    """
    if not settings.effective_api_key or settings.effective_api_key == "sk-your-key-here":
        logger.warning("No LLM API key configured, skipping RAG pipeline")
        return _empty_contexts(code_model)

    try:
        qdrant = _get_qdrant_client()
        openai_client = _get_openai_client()
        _ensure_collection(qdrant)
    except Exception as e:
        logger.warning(f"Could not connect to Qdrant/OpenAI: {e}, returning empty contexts")
        return _empty_contexts(code_model)

    # Phase 1: Embed and upsert all methods
    points = []
    method_keys = []

    for cls in code_model.get("classes", []):
        class_name = cls.get("name", "Unknown")
        for method in cls.get("methods", []):
            method_name = method.get("name", "unknown")
            key = f"{class_name}.{method_name}"
            source = method.get("source", "")
            if not source:
                continue

            try:
                embedding = _embed_text(openai_client, source)
                point_id = _text_to_id(key)
                # Qdrant requires integer or UUID ids
                int_id = int(hashlib.md5(key.encode()).hexdigest()[:15], 16)
                points.append(PointStruct(
                    id=int_id,
                    vector=embedding,
                    payload={
                        "class_name": class_name,
                        "method_name": method_name,
                        "source": source[:4000],  # Limit payload size
                    },
                ))
                method_keys.append((key, embedding))
            except Exception as e:
                logger.warning(f"Failed to embed {key}: {e}")

    # Batch upsert
    if points:
        try:
            qdrant.upsert(
                collection_name=settings.qdrant_collection,
                points=points,
            )
            logger.info(f"Upserted {len(points)} code chunks to Qdrant")
        except Exception as e:
            logger.warning(f"Qdrant upsert failed: {e}")

    # Phase 2: Retrieve similar context for each method
    contexts = {}
    for key, embedding in method_keys:
        try:
            results = qdrant.search(
                collection_name=settings.qdrant_collection,
                query_vector=embedding,
                limit=top_k + 1,  # +1 because the method itself will match
            )
            # Filter out the method itself and build context
            context_parts = []
            for hit in results:
                hit_key = f"{hit.payload.get('class_name')}.{hit.payload.get('method_name')}"
                if hit_key != key and hit.score > 0.5:
                    context_parts.append(
                        f"// Similar method: {hit_key} (similarity: {hit.score:.2f})\n"
                        f"{hit.payload.get('source', '')}"
                    )
                if len(context_parts) >= top_k:
                    break
            contexts[key] = "\n\n".join(context_parts)
        except Exception as e:
            logger.warning(f"Qdrant search failed for {key}: {e}")
            contexts[key] = ""

    return contexts


def _empty_contexts(code_model: Dict[str, Any]) -> Dict[str, str]:
    """Return empty context for all methods when RAG is unavailable."""
    contexts = {}
    for cls in code_model.get("classes", []):
        class_name = cls.get("name", "Unknown")
        for method in cls.get("methods", []):
            key = f"{class_name}.{method.get('name', 'unknown')}"
            contexts[key] = ""
    return contexts
