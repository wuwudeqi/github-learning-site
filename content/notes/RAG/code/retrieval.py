"""Real dense retrieval and an inspectable sparse baseline. No labels enter this module."""
from dataclasses import dataclass, replace
from collections import defaultdict
import re
import uuid
import numpy as np
from qdrant_client import QdrantClient, models
from rank_bm25 import BM25Okapi
from chunking import Chunk


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float
    method: str


def lexical_tokens(text: str) -> list[str]:
    """Keep identifiers whole; Chinese bigrams are a transparent baseline, not a trained tokenizer."""
    words = re.findall(r"[a-zA-Z0-9_./:-]+|[\u4e00-\u9fff]+", text.lower())
    result = []
    for word in words:
        if re.fullmatch(r"[\u4e00-\u9fff]+", word):
            result.extend(word[i:i + 2] for i in range(max(1, len(word) - 1)))
        else:
            result.append(word)
    return result


class BGEEncoder:
    model_name = "BAAI/bge-small-zh-v1.5"
    revision = "7999e1d3359715c523056ef9478215996d62a620"
    query_instruction = "为这个句子生成表示以用于检索相关文章："

    def __init__(self, model_name: str | None = None):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name or self.model_name, device="cpu",
                                         revision=None if model_name else self.revision)
        self.model.max_seq_length = 512
        self.tokenizer = self.model.tokenizer

    def documents(self, texts: list[str]) -> np.ndarray:
        if any(len(self.tokenizer.encode(text)) > self.model.max_seq_length for text in texts):
            raise ValueError("document exceeds embedding token limit; fix chunking instead of truncating silently")
        return self.model.encode(texts, batch_size=16, normalize_embeddings=True, show_progress_bar=False)

    def query(self, text: str) -> np.ndarray:
        prompt = self.query_instruction + text
        if len(self.tokenizer.encode(prompt)) > self.model.max_seq_length:
            raise ValueError("query/history exceeds embedding token limit; resolve the follow-up before retrieval")
        return self.model.encode(prompt, normalize_embeddings=True, show_progress_bar=False)


def rrf(rankings: list[list[Hit]], limit: int = 8, constant: int = 60) -> list[Hit]:
    scores, entries = defaultdict(float), {}
    for ranking in rankings:
        seen = set()
        for rank, hit in enumerate(ranking, 1):
            key = hit.chunk.chunk_id
            if key in seen:
                continue
            seen.add(key)
            scores[key] += 1 / (constant + rank)
            entries[key] = hit
    ids = sorted(scores, key=lambda key: (-scores[key], key))[:limit]
    return [Hit(entries[key].chunk, scores[key], "rrf") for key in ids]


class HybridRetriever:
    def __init__(self, chunks: list[Chunk], encoder, client: QdrantClient | None = None):
        if not chunks:
            raise ValueError("empty corpus")
        self.chunks, self.encoder = chunks, encoder
        self.client = client or QdrantClient(":memory:")
        self.collection = "wiki_chunks"
        self.by_id = {c.chunk_id: c for c in chunks}
        vectors = encoder.documents([c.text for c in chunks])
        self.client.create_collection(self.collection, vectors_config=models.VectorParams(
            size=len(vectors[0]), distance=models.Distance.COSINE))
        self.client.upsert(self.collection, points=[models.PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, c.chunk_id)), vector=v.tolist(),
            payload={"chunk_id": c.chunk_id, "status": c.metadata.get("status", "active"),
                     "version": c.metadata.get("version", "2.0"),
                     "system": c.metadata.get("system", "cross")})
            for c, v in zip(chunks, vectors)], wait=True)
        self.bm25 = BM25Okapi([lexical_tokens(c.text) for c in chunks])

    @staticmethod
    def allowed(chunk: Chunk, filters: dict | None) -> bool:
        return all(chunk.metadata.get(key) in values for key, values in (filters or {}).items())

    def dense(self, query: str, limit: int, filters: dict | None = None) -> list[Hit]:
        conditions = [models.FieldCondition(key=key, match=models.MatchAny(any=values))
                      for key, values in (filters or {}).items()]
        result = self.client.query_points(self.collection, query=self.encoder.query(query).tolist(),
                                         query_filter=models.Filter(must=conditions) if conditions else None,
                                         limit=limit)
        return [Hit(self.by_id[p.payload["chunk_id"]], p.score, "dense") for p in result.points]

    def sparse(self, query: str, limit: int, filters: dict | None = None) -> list[Hit]:
        scores = self.bm25.get_scores(lexical_tokens(query))
        ranked = sorted(range(len(scores)), key=lambda i: (-scores[i], self.chunks[i].chunk_id))
        return [Hit(self.chunks[i], float(scores[i]), "bm25") for i in ranked
                if scores[i] > 0 and self.allowed(self.chunks[i], filters)][:limit]

    def search(self, query: str, mode: str = "hybrid", limit: int = 8,
               filters: dict | None = None, candidates: int = 20) -> list[Hit]:
        if mode == "dense":
            return self.dense(query, limit, filters)
        if mode == "bm25":
            return self.sparse(query, limit, filters)
        if mode != "hybrid":
            raise ValueError(f"unknown retrieval mode: {mode}")
        return rrf([self.dense(query, candidates, filters), self.sparse(query, candidates, filters)], limit)

    def close(self):
        self.client.close()


class CrossEncoderReranker:
    """Scores only the supplied candidates. Download and run explicitly; never enabled silently."""
    revision = "2cfc18c9415c912f9d8155881c133215df768a70"
    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(model_name, device="cpu", max_length=512,
                                  revision=self.revision if model_name == "BAAI/bge-reranker-base" else None)

    def rerank(self, query: str, hits: list[Hit], limit: int = 5) -> list[Hit]:
        if not hits:
            return []
        if any(len(self.model.tokenizer(query, hit.chunk.text, truncation=False)["input_ids"]) > 512 for hit in hits):
            raise ValueError("query + passage exceeds reranker token limit; shorten/split explicitly")
        scores = self.model.predict([(query, hit.chunk.text) for hit in hits],
                                    activation_fn=lambda logits: logits, show_progress_bar=False)
        rescored = [replace(hit, score=float(score), method="cross_encoder") for hit, score in zip(hits, scores)]
        return sorted(rescored, key=lambda h: (-h.score, h.chunk.chunk_id))[:limit]
