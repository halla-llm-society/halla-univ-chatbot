"""
RAG 문서 조립기 (Document Assembler)

이 파일의 책임(무엇을 하는가):
1) 검색기(retriever)가 준 매치(hits)와 문서 조각 ID(chunk_ids)를 받아,
2) 우선 MongoDB에서 실제 본문을 찾아 이어 붙여 컨텍스트 문자열을 만들고,
3) Mongo에서 못 찾았을 경우 Pinecone 메타데이터에 들어있는 미리보기(preview) 문장으로 임시 컨텍스트를 구성하며,
4) 둘 다 없으면 컨텍스트를 만들지 않습니다(None).

출력에는 컨텍스트 문자열과 함께 "어떤 경로로 만들었는지(source)" 및 개수 통계(document_count, preview_count), 검색문서의 메타데이터를 함께 담아
다음 단계(응답 생성을 위한 프롬프트 결합)에서 참고할 수 있도록 합니다.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Sequence

from .repository import MongoChunkRepository


@dataclass(slots=True)
class RagDocumentPackage:
    """RAG 검색된 문서 패키지 (텍스트 + 메타데이터 + 통계)"""
    # merged_documents_text: MongoDB 문서들의 text 필드를 병합한 최종 텍스트 (없으면 None)
    merged_documents_text: str | None
    # source: 컨텍스트 출처
    #  - "mongo": DB에서 실제 문서 본문을 성공적으로 이어 붙였음
    #  - "preview": DB에서 못 찾았고, Pinecone 메타데이터의 미리보기(preview)로 구성함
    #  - "none": 만들 수 있는 자료가 없었음
    source: str
    # document_count: MongoDB에서 성공적으로 불러와 이어 붙인 문서 조각 수
    document_count: int = 0
    # preview_count: 미리보기 문장을 사용했다면 그 개수
    preview_count: int = 0
    # source_documents: 검색된 문서들의 메타데이터 (law_article_id, source_file, title)
    source_documents: list[dict] = None
    
    def __post_init__(self):
        if self.source_documents is None:
            self.source_documents = []


class ContextBuilder:
    """Mongo 문서 또는 Pinecone 미리보기로부터 컨텍스트 문자열을 조립합니다."""

    def __init__(
        self,
        repository: MongoChunkRepository,
        *,
        joiner: str = "\n\n",
        debug_fn: Callable[[str], None] | None = None,
    ) -> None:
        self._repository = repository
        self._joiner = joiner
        self._debug = debug_fn or (lambda _: None)

    def build(self, hits: Sequence[Any], chunk_ids: Sequence[Any]) -> RagDocumentPackage:
        # 디버그: 입력으로 받은 매치/청크ID 개수 로그
        self._debug(
            f"context_builder.build: 히트 수={len(hits)} 청크ID 수={len(chunk_ids)}"
        )
        if not chunk_ids:
            # 청크 ID가 하나도 없으면 컨텍스트를 만들 수 없습니다.
            self._debug("context_builder.build: 청크ID 없음 -> 컨텍스트 없음(None)")
            return RagDocumentPackage(merged_documents_text=None, source="none")

        retrieved_chunks = self._repository.fetch_chunks(chunk_ids)
        if retrieved_chunks:
            extracted_texts = [chunk.get("text", "") for chunk in retrieved_chunks]
            merged_text = self._joiner.join(filter(None, extracted_texts))
            
            # 출처 문서 메타데이터 추출
            source_docs = []
            for chunk in retrieved_chunks:
                # MongoDB 문서 구조: 최상위 레벨에 law_article_id, source_file, title이 있음
                # metadata 필드가 있다면 그것도 체크
                metadata = chunk.get("metadata", {})
                
                source_doc = {
                    "law_article_id": chunk.get("law_article_id") or metadata.get("law_article_id", ""),
                    "source_file": chunk.get("source_file") or metadata.get("source_file", ""),
                    "title": chunk.get("title") or metadata.get("title", ""),
                }
                
                # 디버그: 추출된 메타데이터 확인
                self._debug(f"  문서 메타데이터: {source_doc}")
                source_docs.append(source_doc)
            
            # 디버그: Mongo 본문으로 컨텍스트를 구성했을 때, 길이/문서개수 로그
            self._debug(
                f"context_builder.build: 컨텍스트 결합 글자수={len(merged_text)} 문서 수={len(retrieved_chunks)}"
            )
            final_merged_text = merged_text.strip()
            return RagDocumentPackage(
                merged_documents_text=final_merged_text or None,
                source="mongo",
                document_count=len(retrieved_chunks),
                source_documents=source_docs,
            )

        # MongoDB에서 문서를 찾지 못했을 때는 Pinecone 매치의 metadata.text_preview를 모아 임시 컨텍스트로 사용합니다.
        previews: list[str] = []
        for hit in hits:
            metadata = getattr(hit, "metadata", {}) or {}
            preview = metadata.get("text_preview")
            if isinstance(preview, str) and preview.strip():
                previews.append(preview.strip())

        if previews:
            fallback = self._joiner.join(previews)
            # 디버그: 미리보기 기반 컨텍스트 구성 로그
            self._debug(
                f"context_builder.build: 미리보기 사용 개수={len(previews)} 글자수={len(fallback)}"
            )
            return RagDocumentPackage(
                merged_documents_text=fallback,
                source="preview",
                preview_count=len(previews),
            )

        # Mongo 문서도, 미리보기 텍스트도 없을 때
        self._debug("context_builder.build: 문서/미리보기 없음 -> 컨텍스트 없음(None)")
        return RagDocumentPackage(merged_documents_text=None, source="none")
