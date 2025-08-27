# Minimal no-embedding placeholder implementations to avoid heavy local ML deps.
# These enable API-only LLM usage while keeping vector DB endpoints no-ops.

from .config import settings


def load_documents(directory_path=None):
    # Skip heavy embedding/ingest; acknowledge the call
    return {"status": "disabled", "reason": "Embeddings disabled in API-only mode"}


async def search_documents(query, k=5):
    # No vector search in API-only mode; return empty context
    return []


async def add_document(content, metadata=None):
    # No-op in API-only mode
    return {"status": "disabled", "reason": "Embeddings disabled in API-only mode"}