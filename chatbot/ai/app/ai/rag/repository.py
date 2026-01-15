"""MongoDB repository for retrieving RAG chunks."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Sequence

from bson import ObjectId, errors

from app.ai.data import MONGO_AVAILABLE, collection


@dataclass(slots=True)
class RepositoryStats:
    hits: int
    misses: int


class MongoChunkRepository:
    """Repository responsible for fetching chunk documents from MongoDB."""

    def __init__(
        self,
        mongo_collection=collection,
        *,
        mongo_available: bool = MONGO_AVAILABLE,
        debug_fn: Callable[[str], None] | None = None,
    ) -> None:
        self._collection = mongo_collection
        self._mongo_available = mongo_available
        self._debug = debug_fn or (lambda _: None)

    async def fetch_chunks(self, chunk_ids: Sequence[Any]) -> list[dict]:
        self._debug(
            f"repository.fetch_chunks: requested_ids={len(chunk_ids)} sample={list(chunk_ids)[:5]}"
        )
        if not chunk_ids:
            return []
        if not self._mongo_available:
            self._debug("repository.fetch_chunks: Mongo unavailable -> returning []")
            return []

        # ObjectId 변환 및 유효성 검증
        object_ids: list[Any] = []
        id_mapping: dict[str, Any] = {}  # 원본 chunk_id -> ObjectId 매핑
        
        for chunk_id in chunk_ids:
            try:
                if isinstance(chunk_id, str) and len(chunk_id) == 24:
                    object_id = ObjectId(chunk_id)
                    self._debug(f"  - converted '{chunk_id}' to ObjectId")
                else:
                    object_id = chunk_id
                    self._debug(f"  - using id '{chunk_id}' without conversion (type={type(chunk_id).__name__})")
                
                object_ids.append(object_id)
                id_mapping[str(object_id)] = chunk_id
            except errors.InvalidId as exc:
                self._debug(
                    f"  - ObjectId conversion failed for '{chunk_id}' ({exc}); skipping"
                )
                continue

        if not object_ids:
            self._debug("repository.fetch_chunks: No valid ObjectIds to query")
            return []

        # $in 연산자로 한 번에 조회 (성능 개선: N번 쿼리 → 1번 쿼리)
        try:
            import asyncio
            self._debug(f"  - querying MongoDB with $in operator for {len(object_ids)} ids")
            documents = await asyncio.to_thread(
                lambda: list(self._collection.find({"_id": {"$in": object_ids}}))
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            self._debug(f"    -> Mongo bulk query error: {exc}")
            return []

        # 결과 처리 및 통계
        results: list[dict] = []
        found_ids = set()
        
        for document in documents:
            results.append(document)
            found_ids.add(str(document.get("_id")))
            text_value = document.get("text")
            text_len = len(text_value) if isinstance(text_value, str) else 0
            self._debug(
                f"    -> hit: _id={document.get('_id')} text_length={text_len}"
            )

        # 못 찾은 ID 로깅
        hits = len(found_ids)
        misses = len(object_ids) - hits
        
        for obj_id_str in id_mapping:
            if obj_id_str not in found_ids:
                original_id = id_mapping[obj_id_str]
                self._debug(f"    -> miss: _id={original_id}")

        self._debug(
            f"repository.fetch_chunks summary: hits={hits} misses={misses} returned={len(results)}"
        )
        return results
