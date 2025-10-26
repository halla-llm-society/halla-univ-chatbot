"""
챗봇 응답 메타데이터 클래스들

RAG 검색 결과, 함수 호출 결과 등의 메타데이터를 구조화하여 관리합니다.
프론트엔드는 이 메타데이터를 통해 챗봇의 추론 근거와 검색 결과를 확인할 수 있습니다.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class RagMetadata:
    """RAG 검색 결과 메타데이터
    
    규정 문서 검색 결과와 관련된 모든 정보를 포함합니다.
    """
    
    # 기본 정보
    is_regulation: bool
    """규정 질문 여부 (gate 판단 결과)"""
    
    gate_reason: str
    """gate 판단 근거 (LLM 추론 또는 키워드 매칭)"""
    
    # 컨텍스트 소스
    context_source: str
    """컨텍스트 출처
    - "mongo": DB 본문에서 가져옴
    - "preview": Pinecone 미리보기에서 가져옴
    - "none": 자료를 찾지 못함
    """
    
    # 검색 통계
    hits_count: int
    """Pinecone 검색 히트 수"""
    
    document_count: int
    """MongoDB에서 가져온 문서 수"""
    
    preview_count: int
    """Pinecone 미리보기 사용 수 (fallback)"""
    
    # 원본 데이터 (디버그/관리자용)
    chunk_ids: Optional[List[str]] = None
    """MongoDB 청크 ID 목록"""
    
    source_documents: Optional[List[Dict[str, str]]] = None
    """검색된 문서들의 출처 정보 (law_article_id, source_file, title)"""
    
    raw_context: Optional[str] = None
    """원본 RAG 컨텍스트 (요약 전 MongoDB에서 가져온 원문)"""
    
    condensed_context: Optional[str] = None
    """요약된 컨텍스트 (LLM으로 가공된 버전)"""

    def to_dict(self) -> Dict[str, Any]:
        """JSON 직렬화용 딕셔너리 변환
        
        Returns:
            메타데이터를 담은 딕셔너리
        """
        return {
            "is_regulation": self.is_regulation,
            "gate_reason": self.gate_reason,
            "context_source": self.context_source,
            "hits_count": self.hits_count,
            "document_count": self.document_count,
            "preview_count": self.preview_count,
            "chunk_ids": self.chunk_ids,
            "source_documents": self.source_documents or [],  # 출처 문서 정보
            "has_raw_context": bool(self.raw_context),
            "raw_context": self.raw_context,  # 원본 컨텍스트 전체 포함
            "has_condensed_context": bool(self.condensed_context),
            "condensed_context": self.condensed_context,  # 요약된 컨텍스트 전체 포함
            "condensed_context_length": len(self.condensed_context) if self.condensed_context else 0,
        }


@dataclass
class FunctionCallMetadata:
    """함수 호출 결과 메타데이터
    
    웹 검색, 학식 메뉴, 공지사항 등 함수 호출 결과를 담습니다.
    """
    
    name: str
    """함수 이름 (예: search_internet, get_halla_cafeteria_menu)"""
    
    arguments: Dict[str, Any]
    """함수 인자"""
    
    output: str
    """함수 실행 결과"""
    
    call_id: str
    """호출 ID (OpenAI API에서 제공)"""
    
    is_fallback: bool = False
    """보강 호출 여부
    
    True: LLM이 아닌 규칙 기반으로 호출됨 (예: 학식 키워드 감지)
    False: LLM이 분석하여 호출함
    """
    
    reasoning: Optional[str] = None
    """함수 선택 근거 (LLM이 생성한 판단 이유)"""

    def to_dict(self) -> Dict[str, Any]:
        """JSON 직렬화용 딕셔너리 변환
        
        Returns:
            메타데이터를 담은 딕셔너리 (output은 200자로 축약)
        """
        # output이 너무 길면 축약
        output_preview = self.output
        if len(output_preview) > 200:
            output_preview = output_preview[:200] + "..."
        
        result = {
            "name": self.name,
            "arguments": self.arguments,
            "output": output_preview,
            "output_length": len(self.output),
            "call_id": self.call_id,
            "is_fallback": self.is_fallback,
        }
        
        # reasoning이 있으면 추가
        if self.reasoning:
            result["reasoning"] = self.reasoning
        
        return result


@dataclass
class ToolReasoningMetadata:
    """도구 선택 추론 메타데이터
    
    LLM이 도구를 선택한 이유를 담습니다.
    """
    
    reasoning: str
    """LLM이 생성한 추론 과정"""
    
    selected_tools: List[str]
    """선택된 도구 이름 목록"""
    
    def to_dict(self) -> Dict[str, Any]:
        """JSON 직렬화용 딕셔너리 변환"""
        return {
            "reasoning": self.reasoning,
            "selected_tools": self.selected_tools,
        }


@dataclass
class TokenUsageMetadata:
    """토큰 사용량 및 비용 메타데이터
    
    tiktoken 기반 토큰 계산 결과와 비용을 담습니다.
    """
    
    input_tokens: int
    """입력 토큰 수 (시스템 프롬프트 + 사용자 메시지 + RAG 컨텍스트)"""
    
    output_tokens: int
    """출력 토큰 수 (LLM 응답)"""
    
    function_tokens: int
    """함수 호출 토큰 수 (함수 정의 + 인자 + 결과)"""
    
    rag_tokens: int
    """RAG 컨텍스트 토큰 수 (MongoDB 원문 + 요약)"""
    
    total_tokens: int
    """총 토큰 수"""
    
    input_cost_usd: float
    """입력 비용 (USD)"""
    
    output_cost_usd: float
    """출력 비용 (USD)"""
    
    total_cost_usd: float
    """총 비용 (USD)"""
    
    currency: str = "USD"
    """통화 단위"""
    
    model: str = ""
    """사용된 모델 이름"""
    
    preset: Optional[str] = None
    """현재 활성 프리셋 이름 (예: balanced, budget, premium)
    
    각 LLM 업체마다 비용/토큰이 다르므로 프리셋 정보를 통해
    어떤 Provider 조합을 사용했는지 파악할 수 있습니다.
    """
    
    role_breakdown: Optional[Dict[str, Dict[str, int]]] = None
    """역할별 토큰 상세 분석
    
    예: {
        "gate": {"input": 150, "output": 30},
        "condense": {"input": 3000, "output": 500},
        "category": {"input": 50, "output": 20},
        "search_rewrite": {"input": 100, "output": 30},
        "function_analyze": {"input": 200, "output": 50},
        "streaming": {"input": 4000, "output": 300}
    }
    """
    
    def to_dict(self) -> Dict[str, Any]:
        """JSON 직렬화용 딕셔너리 변환"""
        result = {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "function_tokens": self.function_tokens,
            "rag_tokens": self.rag_tokens,
            "total_tokens": self.total_tokens,
            "input_cost_usd": self.input_cost_usd,
            "output_cost_usd": self.output_cost_usd,
            "total_cost_usd": self.total_cost_usd,
            "currency": self.currency,
            "model": self.model,
        }
        
        # preset이 있으면 추가
        if self.preset:
            result["preset"] = self.preset
        
        # role_breakdown이 있으면 추가
        if self.role_breakdown:
            result["role_breakdown"] = self.role_breakdown
        
        return result


@dataclass
class ChatMetadata:
    """챗봇 응답 전체 메타데이터
    
    RAG 검색 결과와 함수 호출 결과를 모두 포함하는 컨테이너입니다.
    """
    
    rag: Optional[RagMetadata] = None
    """RAG 검색 메타데이터 (규정 질문인 경우만 존재)"""
    
    functions: List[FunctionCallMetadata] = field(default_factory=list)
    """함수 호출 메타데이터 목록"""
    
    web_search_status: Optional[str] = None
    """웹검색 상태
    
    - "ok": 검색 성공
    - "empty-or-error": 결과 없음 또는 오류
    - "not-run": 실행 안 함
    """
    
    tool_reasoning: Optional[ToolReasoningMetadata] = None
    """도구 선택 추론 메타데이터 (LLM이 도구를 선택한 이유)"""
    
    token_usage: Optional[TokenUsageMetadata] = None
    """토큰 사용량 및 비용 메타데이터"""
    
    def to_dict(self) -> Dict[str, Any]:
        """JSON 직렬화용 딕셔너리 변환
        
        Returns:
            전체 메타데이터를 담은 딕셔너리
        """
        return {
            "rag": self.rag.to_dict() if self.rag else None,
            "functions": [f.to_dict() for f in self.functions],
            "functions_count": len(self.functions),
            "web_search_status": self.web_search_status,
            "tool_reasoning": self.tool_reasoning.to_dict() if self.tool_reasoning else None,
            "token_usage": self.token_usage.to_dict() if self.token_usage else None,
        }
    
    def add_function(self, func_meta: FunctionCallMetadata) -> None:
        """함수 호출 메타데이터 추가
        
        Args:
            func_meta: 추가할 함수 호출 메타데이터
        """
        self.functions.append(func_meta)
    
    def has_rag(self) -> bool:
        """RAG 검색 결과가 있는지 확인
        
        Returns:
            RAG 메타데이터 존재 여부
        """
        return self.rag is not None
    
    def has_functions(self) -> bool:
        """함수 호출 결과가 있는지 확인
        
        Returns:
            함수 호출 메타데이터 존재 여부
        """
        return len(self.functions) > 0
