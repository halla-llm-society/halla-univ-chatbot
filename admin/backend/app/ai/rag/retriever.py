"""Pinecone retriever component for the RAG pipeline.

This module encapsulates the vector search logic that previously lived on
`ChatbotStream.search_similar_chunks`. It keeps the behaviour identical while
making the implementation injectable and easier to test.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Sequence

from app.ai.data import get_embedding, index

# ID 추출 우선순위 (앞에 있을수록 우선)
ID_KEYS_PRIORITY: tuple[str, ...] = ("mongo_id", "id", "ID", "default")


@dataclass(slots=True)
class RetrieverResult:
        """Container for retriever outputs.

        - hits: Pinecone 검색에서 반환된 "매치 객체" 목록입니다.
            include_metadata=True 로 질의하므로, 각 항목은 대체로 다음 정보를 가집니다:
                * score: 유사도 점수(0~1)
                * id: 벡터 고유 ID(업서트 시 생성된 UUID)
                * metadata: 업로드 시 넣어둔 보조정보(dict). 예: mongo_id, text_preview, sub_index 등
            → 이 목록은 threshold(기본 0.4) 미만 점수는 걸러진 상태로 반환됩니다.

        - chunk_ids: 실제 MongoDB에서 본문을 재조회하기 위해 추출한 문서 조각 ID들의 모음입니다.
            우선순위는 metadata.mongo_id → metadata.id → metadata.ID → metadata.default 순서로 사용합니다.
        """

        hits: Sequence[Any]
        chunk_ids: Sequence[Any]


class PineconeRetriever:
    """Wrapper around the Pinecone index used for similarity search."""

    def __init__(
        self,
        index_client=index,
        embed_fn: Callable[[str], Iterable[float]] | None = None,
        *,
        namespaces: Sequence[str] | None = None,
        top_k: int = 5,
        debug_fn: Callable[[str], None] | None = None,
    ) -> None:
        self._index = index_client
        self._embed = embed_fn or get_embedding
        self._namespaces = list(namespaces or ("law_articles", "appendix_tables"))
        self._top_k = top_k
        self._debug = debug_fn or (lambda _: None)

    def search(self, query: str, *, threshold: float = 0.4) -> RetrieverResult:
        start_ts = time.time()
        self._debug(
            f"retriever.search: query='{query[:80]}' namespaces={self._namespaces} top_k={self._top_k} threshold={threshold}"
        )
        embedding = self._embed(query)

        # all_hits: 네임스페이스별 Pinecone 질의에서 얻은 "매치 객체"(score/id/metadata 포함)들을 전부 모아둔 임시 바구니
        #            이후 threshold(점수 하한)로 필터링해 최종 hits 로 돌려줍니다.
        all_hits: list[Any] = []
        # all_chunk_ids: 각 매치의 metadata에서 문서 조각 ID를 뽑아 모아둔 리스트
        #               → 나중에 MongoDB에서 실제 본문을 가져올 때 사용합니다.
        all_chunk_ids: list[Any] = []

        for namespace in self._namespaces:
            self._debug(f"  - querying namespace='{namespace}'")
            # include_metadata=True: 업로드 시 저장해둔 metadata(mongo_id, text_preview, sub_index 등)를 함께 받아옵니다.
            response = self._index.query(
                namespace=namespace,
                top_k=self._top_k,
                include_metadata=True,
                vector=embedding,
            )
            matches = getattr(response, "matches", []) or []
            self._debug(f"    -> returned_matches={len(matches)}")

            for match in matches:
                # 매치 전체 객체 자체를 보관합니다(점수, id, metadata를 다 들고 있음)
                all_hits.append(match)
                metadata = getattr(match, "metadata", {}) or {}

                # 우선순위에 따라 첫 번째로 발견되는 유효한 ID를 선택
                id_source, id_value = next(
                    (
                        (k, metadata[k])
                        for k in ID_KEYS_PRIORITY
                        if k in metadata and metadata[k] is not None
                    ),
                    (None, None),
                )

                score = getattr(match, "score", None)
                if id_value is not None:
                    # Mongo 재조회용으로 청크 ID만 따로 수집합니다.
                    all_chunk_ids.append(id_value)
                    self._debug(f"      match: id(source={id_source})={id_value} score={score}")
                else:
                    self._debug(
                        f"      match: missing id score={score} metadata_keys={list(metadata.keys())}"
                    )

        filtered_hits = [hit for hit in all_hits if getattr(hit, "score", 0) >= threshold]
        duration = time.time() - start_ts
        self._debug(
            "retriever.search summary: total_hits={} filtered_hits={} unique_ids={} duration={:.3f}s".format(
                len(all_hits), len(filtered_hits), len(set(all_chunk_ids)), duration
            )
        )

        # 결과: 임계값 이상인 매치들만 hits 로, 추출된 청크 ID 모음을 chunk_ids 로 반환합니다.
        return RetrieverResult(hits=filtered_hits, chunk_ids=all_chunk_ids)
