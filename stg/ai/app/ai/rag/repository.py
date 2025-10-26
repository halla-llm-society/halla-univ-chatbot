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

    def fetch_chunks(self, chunk_ids: Sequence[Any]) -> list[dict]:
        self._debug(
            f"repository.fetch_chunks: requested_ids={len(chunk_ids)} sample={list(chunk_ids)[:5]}"
        )
        if not chunk_ids:
            return []
        if not self._mongo_available:
            self._debug("repository.fetch_chunks: Mongo unavailable -> returning []")
            return []

        results: list[dict] = []
        hits = 0
        misses = 0

        for chunk_id in chunk_ids:
            try:
                if isinstance(chunk_id, str) and len(chunk_id) == 24:
                    object_id = ObjectId(chunk_id)
                    self._debug(f"  - converted '{chunk_id}' to ObjectId")
                else:
                    object_id = chunk_id
                    self._debug(f"  - using id '{chunk_id}' without conversion (type={type(chunk_id).__name__})")
            except errors.InvalidId as exc:
                self._debug(
                    f"  - ObjectId conversion failed for '{chunk_id}' ({exc}); using raw value"
                )
                object_id = chunk_id

            try:
                document = self._collection.find_one({"_id": object_id})
            except Exception as exc:  # pragma: no cover - defensive logging
                self._debug(f"    -> Mongo query error for _id={chunk_id}: {exc}")
                continue

            if document:
                results.append(document)
                hits += 1
                text_value = document.get("text")
                text_len = len(text_value) if isinstance(text_value, str) else 0
                self._debug(
                    f"    -> hit: _id={document.get('_id')} text_length={text_len}"
                )
            else:
                misses += 1
                self._debug(f"    -> miss: _id={chunk_id}")

        self._debug(
            f"repository.fetch_chunks summary: hits={hits} misses={misses} returned={len(results)}"
        )
        return results
