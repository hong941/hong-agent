from sqlalchemy import text

from ..config import get_settings
from ..database import engine


def _active() -> bool:
    return engine.dialect.name == "postgresql"


def _vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"


def ensure_pgvector() -> None:
    if not _active():
        return
    dim = get_settings().embedding_dim
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS knowledge_embeddings (
                    knowledge_item_id integer PRIMARY KEY
                        REFERENCES knowledge_items(id) ON DELETE CASCADE,
                    embedding vector(:dim)
                )
                """
            ),
            {"dim": dim},
        )
        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_hnsw
                ON knowledge_embeddings USING hnsw (embedding vector_cosine_ops)
                """
            )
        )


def upsert_embedding(item_id: int, vector: list[float]) -> None:
    if not _active() or not vector:
        return
    ensure_pgvector()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO knowledge_embeddings (knowledge_item_id, embedding)
                VALUES (:item_id, :vector::vector)
                ON CONFLICT (knowledge_item_id)
                DO UPDATE SET embedding = EXCLUDED.embedding
                """
            ),
            {"item_id": item_id, "vector": _vector_literal(vector)},
        )


def search_pgvector(query_vector: list[float], top_k: int) -> list[tuple[int, float]]:
    if not _active() or not query_vector:
        return []
    ensure_pgvector()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT knowledge_item_id,
                       1 - (embedding <=> :query::vector) AS similarity
                FROM knowledge_embeddings
                ORDER BY embedding <=> :query::vector
                LIMIT :top_k
                """
            ),
            {"query": _vector_literal(query_vector), "top_k": top_k},
        ).all()
    return [(int(row[0]), float(row[1])) for row in rows]


def sync_knowledge_embeddings(db) -> None:
    from ..models import KnowledgeItem

    if not _active():
        return
    ensure_pgvector()
    items = db.query(KnowledgeItem).all()
    for item in items:
        if item.embedding:
            upsert_embedding(item.id, item.embedding)
