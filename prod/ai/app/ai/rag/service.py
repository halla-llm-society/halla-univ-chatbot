"""RAG service orchestrating the modular Phase 2 components."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Optional, Sequence

from .RagDocumentPackage import RagDocumentPackage, ContextBuilder
from .gate import GateDecision, RegulationGate
from .repository import MongoChunkRepository
from .mongo_vector_retriever import MongoVectorRetriever, RetrieverResult

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RagResult:
        """
        RAG 처리 결과를 담아 돌려주는 상자.

        - context_source 값 설명(어디서 자료를 가져왔는지):
            * "mongo": 데이터베이스에서 실제 문서 본문을 찾아 이어 붙였음
            * "preview": DB에서 못 찾았을 때, 벡터검색 결과에 들어있는 짧은 미리보기 문장을 모아 붙였음
            * "none": 쓸만한 자료를 찾지 못함 (또는 규정 질문이 아니라서 검색을 안 함)
        """

        merged_documents_text: Optional[str]  # MongoDB 문서들의 text 필드를 병합한 최종 텍스트 (없으면 None)
        hits: Sequence[Any]          # 벡터검색에서 찾아온 결과 목록(점수 등 포함). 화면에는 보통 직접 노출하지 않음
        chunk_ids: Sequence[Any]     # 검색 결과와 연결된 문서 조각(청크) ID 모음
        gate_reason: Optional[str] = None  # "규정 질문인지" 판정 이유(간단한 글)
        is_regulation: bool = False        # 질문이 규정 관련인지 여부(True/False)
        context_source: str = "none"       # 위 주석의 세 값 중 하나: mongo | preview | none
        document_count: int = 0            # DB에서 불러온 문서 조각 개수
        preview_count: int = 0             # 미리보기 문장을 사용했다면 그 개수
        source_documents: list = None      # 검색된 문서들의 메타데이터 (law_article_id, source_file, title)
        
        def __post_init__(self):
            if self.source_documents is None:
                object.__setattr__(self, 'source_documents', [])


class RagService:
    """Coordinate gate, retriever, repository, and context builder."""

    def __init__(
        self,
        *,
        retriever: MongoVectorRetriever | None = None,
        repository: MongoChunkRepository | None = None,
        context_builder: ContextBuilder | None = None,
        gate: RegulationGate | None = None,
        debug_fn: Callable[[str], None] | None = None,
        token_counter=None,
    ) -> None:
        self._debug = debug_fn or (lambda _: None)
        self._repository = repository or MongoChunkRepository(debug_fn=self._debug)

        # MongoDB Vector Search 사용
        if retriever is not None:
            self._retriever = retriever
        else:
            self._debug("RagService: Using MongoVectorRetriever")
            self._retriever = MongoVectorRetriever(top_k=5, debug_fn=self._debug)

        self._use_mongo_vector = True
        self._context_builder = context_builder or ContextBuilder(
            self._repository, debug_fn=self._debug
        )
        self._gate = gate or RegulationGate(debug_fn=self._debug, token_counter=token_counter)
        self._last_result: RagResult | None = None

    def _make_result(
        self,
        *,
        merged_documents_text: str | None,
        hits: Sequence[Any],
        chunk_ids: Sequence[Any],
        gate_reason: str | None,
        is_regulation: bool,
        context_source: str,
        document_count: int = 0,
        preview_count: int = 0,
        source_documents: list = None,
    ) -> RagResult:
        """RagResult 생성 및 캐시 저장 헬퍼 (중복 코드 제거용)"""
        result = RagResult(
            merged_documents_text=merged_documents_text,
            hits=hits,
            chunk_ids=chunk_ids,
            gate_reason=gate_reason,
            is_regulation=is_regulation,
            context_source=context_source,
            document_count=document_count,
            preview_count=preview_count,
            source_documents=source_documents or [],
        )
        self._last_result = result
        return result

    async def retrieve_context(self, question: str) -> RagResult:
        """
        질문을 받아 RAG 검색 및 컨텍스트 조회 전 과정을 수행합니다.
        
        처리 흐름:
        1) 규정 질문 여부 판정 (gate) → 아니면 즉시 종료
        2) 벡터 검색 수행 (retriever) → 결과 없으면 종료
        3) 청크 ID 추출 확인 → 없으면 종료
        4) MongoDB 본문 조회 + 컨텍스트 조립 (context_builder)
        5) 최종 결과 반환 (컨텍스트 문자열 + 메타데이터)
        """
        # 1단계: 규정 질문 여부 판정
        self._debug("rag_service.retrieve_context: 레그검사 시작")
        decision: GateDecision = await self._gate.decide(question)
        
        if not decision.is_regulation:
            self._debug("rag_service.retrieve_context: 규정 질문 아님 → 검색 생략")
            logger.info("학사 규정 관련이 아님 → RAG 검색 안 함")
            return self._make_result(
                merged_documents_text=None,
                hits=[],
                chunk_ids=[],
                gate_reason=decision.reason,
                is_regulation=False,
                context_source="none",
            )

        # 2단계: 벡터 검색 수행
        self._debug("rag_service.retrieve_context: 레그 검사 통과 → 벡터검색 수행")
        retrieval: RetrieverResult = await self._retriever.search(question)
        hits, chunk_ids = retrieval.hits, retrieval.chunk_ids

        if not hits:
            self._debug("rag_service.retrieve_context: 벡터검색 결과 없음")
            engine = "MongoDB Vector Search" if self._use_mongo_vector else "Pinecone"
            logger.info(f"{engine}에서 유사 데이터 없음")
            return self._make_result(
                merged_documents_text=None,
                hits=[],
                chunk_ids=[],
                gate_reason=decision.reason,
                is_regulation=True,
                context_source="none",
            )

        # 3단계: 청크 ID 확인
        if not chunk_ids:
            self._debug("rag_service.retrieve_context: 청크ID 추출 실패")
            engine = "MongoDB Vector Search" if self._use_mongo_vector else "Pinecone"
            logger.info(f"{engine} 결과에 id 없음")
            return self._make_result(
                merged_documents_text=None,
                hits=hits,
                chunk_ids=[],
                gate_reason=decision.reason,
                is_regulation=True,
                context_source="none",
            )

        # 4단계: MongoDB 본문 조회 + 문서 패키지 조립
        self._debug("rag_service.retrieve_context: 문서 패키지 조립 시작")
        doc_package: RagDocumentPackage = await self._context_builder.build(hits, chunk_ids)
        
        if doc_package.source in {"preview", "none"}:
            logger.info("MongoDB에서 매칭된 문서 없음")
        if doc_package.merged_documents_text is None:
            self._debug("rag_service.retrieve_context: 문서 패키지 조립 결과 없음(None)")

        # 5단계: 최종 결과 반환
        return self._make_result(
            merged_documents_text=doc_package.merged_documents_text,
            hits=hits,
            chunk_ids=chunk_ids,
            gate_reason=decision.reason,
            is_regulation=True,
            context_source=doc_package.source,
            document_count=doc_package.document_count,
            preview_count=doc_package.preview_count,
            source_documents=doc_package.source_documents,
        )

    def is_regulation(self, question: str) -> bool:
        decision = self._gate.decide(question)
        return decision.is_regulation

    def search(self, question: str, threshold: float = 0.4):
        result = self._retriever.search(question, threshold=threshold)
        return result.hits, result.chunk_ids

    @property
    def last_result(self) -> RagResult | None:
        return self._last_result
