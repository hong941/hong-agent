import math
from collections import Counter
from typing import Any

from sqlalchemy.orm import Session

from ..database import engine
from ..models import KnowledgeItem, Patient, TriageConversation
from ..services.embeddings import get_embedder
from ..services.pgvector_store import search_pgvector
from ..services.text_utils import tokenize


class KnowledgeService:
    def __init__(self, db: Session) -> None:
        self.items = db.query(KnowledgeItem).order_by(KnowledgeItem.id).all()
        self.index: dict[str, list[tuple[int, int]]] = {}
        self.doc_freq: Counter[str] = Counter()
        self.doc_lengths: list[int] = []
        self.embedder = get_embedder()
        self.embeddings: dict[int, list[float]] = {}
        self.item_id_to_doc: dict[int, int] = {}
        self._build_index()

    def _build_index(self) -> None:
        for doc_id, item in enumerate(self.items):
            self.item_id_to_doc[item.id] = doc_id
            tokens = tokenize(
                f"{item.title} {item.title} {item.title} "
                f"{item.category} {item.content} {' '.join(item.tags or [])}"
            )
            self.doc_lengths.append(len(tokens))
            counts = Counter(tokens)
            for token, count in counts.items():
                self.index.setdefault(token, []).append((doc_id, count))
                self.doc_freq[token] += 1
            self.embeddings[doc_id] = item.embedding or self.embedder.embed(
                f"{item.title} {item.category} {item.content} {' '.join(item.tags or [])}"
            )

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if not norm_a or not norm_b:
            return 0.0
        return dot / (norm_a * norm_b)

    def _vector_scores(self, query: str) -> dict[int, float]:
        query_vector = self.embedder.embed(query)
        scores: dict[int, float] = {}
        if engine.dialect.name == "postgresql":
            try:
                for item_id, similarity in search_pgvector(query_vector, 20):
                    doc_id = self.item_id_to_doc.get(item_id)
                    if doc_id is not None:
                        scores[doc_id] = max(0.0, (similarity + 1) / 2)
                return scores
            except Exception:
                pass
        for doc_id, vector in self.embeddings.items():
            similarity = self._cosine(query_vector, vector)
            scores[doc_id] = max(0.0, (similarity + 1) / 2)
        return scores

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if not self.items:
            return []
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        n_docs = len(self.items)
        avg_len = sum(self.doc_lengths) / n_docs
        scores = [0.0] * n_docs
        for token in set(query_tokens):
            df = self.doc_freq.get(token, 0)
            if not df:
                continue
            idf = math.log((n_docs - df + 0.5) / (df + 0.5) + 1)
            for doc_id, tf in self.index.get(token, []):
                length = self.doc_lengths[doc_id]
                denom = tf + 1.5 * (1 - 0.75 + 0.75 * length / avg_len)
                scores[doc_id] += idf * (tf / denom if denom else 0)

        bm25_ranked = sorted(
            range(n_docs), key=lambda i: scores[i], reverse=True
        )[: max(10, top_k * 2)]
        vector_scores = self._vector_scores(query)
        vector_ranked = sorted(
            vector_scores, key=vector_scores.get, reverse=True
        )[: max(10, top_k * 2)]

        fused: dict[int, float] = {}
        for rank, doc_id in enumerate(bm25_ranked):
            fused[doc_id] = fused.get(doc_id, 0.0) + 2.0 / (60 + rank + 1)
        for rank, doc_id in enumerate(vector_ranked):
            fused[doc_id] = fused.get(doc_id, 0.0) + 1.0 / (60 + rank + 1)

        ranked = sorted(fused, key=fused.get, reverse=True)[:top_k]
        results = []
        for doc_id in ranked:
            item = self.items[doc_id]
            results.append(
                {
                    "id": item.id,
                    "title": item.title,
                    "category": item.category,
                    "content": item.content,
                    "source": item.source,
                    "tags": item.tags or [],
                    "score": round(fused[doc_id], 4),
                }
            )
        return results

    def search_for_patient(
        self,
        patient: Patient,
        conversation: TriageConversation | None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        parts = [patient.chief_complaint or ""]
        parts.extend(patient.symptoms or [])
        if conversation:
            user_messages = [
                item.get("content", "")
                for item in (conversation.messages or [])
                if item.get("role") == "user"
            ]
            parts.extend(user_messages)
        return self.search(" ".join(parts), top_k=top_k)
