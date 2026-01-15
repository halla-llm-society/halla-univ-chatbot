"""MongoDB Vector Search retriever component for the RAG pipeline.

This module replaces PineconeRetriever with MongoDB Atlas Vector Search.
It provides the same interface (RetrieverResult) for seamless integration.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Iterable, List, Sequence

from openai import OpenAI
from dotenv import load_dotenv

from app.ai.data import collection, MONGO_AVAILABLE

# Load API key
load_dotenv("apikey.env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)


def get_embedding(text: str) -> List[float]:
    """OpenAI text-embedding-3-small을 사용하여 임베딩 생성"""
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding


@dataclass(slots=True)
class RetrieverResult:
    """Container for retriever outputs.

    - hits: Vector Search에서 반환된 매치 목록 (score, document 포함)
    - chunk_ids: MongoDB _id 목록 (하위 호환성 유지)
    - documents: 전체 문서 목록 (Vector Search는 문서를 직접 반환)
    """
    hits: Sequence[Any]
    chunk_ids: Sequence[Any]
    documents: List[dict] = None  # MongoDB Vector Search는 문서를 직접 반환

    def __post_init__(self):
        if self.documents is None:
            self.documents = []


class MongoVectorRetriever:
    """MongoDB Atlas Vector Search based retriever.

    Replaces PineconeRetriever with MongoDB's native vector search capability.
    Requires:
    - MongoDB Atlas M10+ tier
    - Vector Search Index named 'vector_index' on 'embedding' field
    - Documents with 'embedding' field (1536 dimensions, OpenAI text-embedding-3-small)
    """

    def __init__(
        self,
        mongo_collection=None,
        embed_fn: Callable[[str], Iterable[float]] | None = None,
        *,
        index_name: str = "vector_index",
        top_k: int = 5,
        debug_fn: Callable[[str], None] | None = None,
    ) -> None:
        self._collection = mongo_collection or collection
        self._embed = embed_fn or get_embedding
        self._index_name = index_name
        self._top_k = top_k
        self._debug = debug_fn or (lambda _: None)

    async def search(self, query: str, *, threshold: float = 0.4) -> RetrieverResult:
        """Execute vector search on MongoDB.

        Args:
            query: 검색할 쿼리 텍스트
            threshold: 최소 유사도 점수 (0~1, cosine similarity)

        Returns:
            RetrieverResult: hits, chunk_ids, documents를 포함한 검색 결과
        """
        start_ts = time.time()
        self._debug(
            f"mongo_retriever.search: query='{query[:80]}' index={self._index_name} "
            f"top_k={self._top_k} threshold={threshold}"
        )

        # 1. 쿼리 임베딩 생성
        try:
            embedding = self._embed(query)
            if isinstance(embedding, list):
                query_vector = embedding
            else:
                query_vector = list(embedding)
        except Exception as e:
            self._debug(f"mongo_retriever.search: embedding failed: {e}")
            return RetrieverResult(hits=[], chunk_ids=[], documents=[])

        # 2. MongoDB Vector Search 파이프라인
        pipeline = [
            {
                "$vectorSearch": {
                    "index": self._index_name,
                    "path": "embedding",
                    "queryVector": query_vector,
                    "numCandidates": self._top_k * 10,  # 후보군 확대
                    "limit": self._top_k,
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "text": 1,
                    "metadata": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            }
        ]

        # 3. 검색 실행
        try:
            import asyncio
            results = await asyncio.to_thread(
                lambda: list(self._collection.aggregate(pipeline))
            )
        except Exception as e:
            self._debug(f"mongo_retriever.search: aggregation failed: {e}")
            return RetrieverResult(hits=[], chunk_ids=[], documents=[])

        # 4. threshold 필터링 및 결과 구성
        filtered_results = []
        chunk_ids = []
        documents = []

        for doc in results:
            score = doc.get("score", 0)
            if score >= threshold:
                # Hit 객체 생성 (PineconeRetriever 호환)
                hit = {
                    "id": str(doc["_id"]),
                    "score": score,
                    "metadata": doc.get("metadata", {}),
                }
                filtered_results.append(type("Hit", (), hit)())  # 간단한 객체로 변환
                chunk_ids.append(str(doc["_id"]))  # ObjectId를 문자열로 변환

                # 전체 문서 저장 (MongoDB는 한 번에 조회 가능)
                documents.append({
                    "_id": str(doc["_id"]),  # ObjectId를 문자열로 변환
                    "text": doc.get("text", ""),
                    "metadata": doc.get("metadata", {}),
                    "score": score,
                })

                self._debug(
                    f"  hit: _id={doc['_id']} score={score:.4f} "
                    f"text_len={len(doc.get('text', ''))}"
                )
            else:
                self._debug(f"  filtered: _id={doc['_id']} score={score:.4f} < {threshold}")

        duration = time.time() - start_ts
        self._debug(
            f"mongo_retriever.search summary: total={len(results)} "
            f"filtered={len(filtered_results)} duration={duration:.3f}s"
        )

        return RetrieverResult(
            hits=filtered_results,
            chunk_ids=chunk_ids,
            documents=documents,
        )


# Factory function for creating retriever
def create_retriever(**kwargs) -> MongoVectorRetriever:
    """Create a MongoVectorRetriever instance.

    Args:
        **kwargs: Retriever 생성자에 전달할 인자

    Returns:
        MongoVectorRetriever instance
    """
    return MongoVectorRetriever(**kwargs)
