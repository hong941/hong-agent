import hashlib
import math

from ..config import get_settings
from .text_utils import tokenize


class LocalHashEmbedder:
    """Deterministic offline embedder used until a remote embedding API is configured."""

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        for token in tokenize(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dim
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm:
            vector = [value / norm for value in vector]
        return vector


def get_embedder() -> LocalHashEmbedder:
    settings = get_settings()
    return LocalHashEmbedder(dim=settings.embedding_dim)


def ensure_knowledge_embeddings(db) -> None:
    from ..models import KnowledgeItem
    from .pgvector_store import sync_knowledge_embeddings

    embedder = get_embedder()
    items = db.query(KnowledgeItem).all()
    changed = False
    for item in items:
        if not item.embedding:
            item.embedding = embedder.embed(
                f"{item.title} {item.category} {item.content} {' '.join(item.tags or [])}"
            )
            changed = True
    if changed:
        db.commit()
    sync_knowledge_embeddings(db)
