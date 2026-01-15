"""
Base abstract interface for LLM providers.

모든 LLM Provider는 이 인터페이스를 구현해야 합니다.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseLLMProvider(ABC):
    """LLM Provider 추상 인터페이스"""
    
    def __init__(self, model_name: str, **kwargs):
        """
        LLM Provider 초기화
        
        Args:
            model_name: 사용할 모델 ID
            **kwargs: 추가 설정 (api_key, temperature 등)
        """
        self.model_name = model_name
        self.config = kwargs
    
    @abstractmethod
    async def simple_completion(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> tuple[str, Dict[str, int]]:
        """
        단순 텍스트 생성

        OpenAI Responses API 형식의 메시지를 받아 텍스트 응답을 반환합니다.
        Provider 내부에서 필요 시 메시지 포맷을 변환합니다.

        Args:
            messages: OpenAI Responses API 형식 메시지 리스트
                     예: [{"role": "user", "content": [{"type": "input_text", "text": "..."}]}]
            temperature: 생성 온도 (0.0 ~ 2.0)
            max_tokens: 최대 출력 토큰 수 (None이면 모델 기본값)
            **kwargs: 추가 파라미터

        Returns:
            tuple: (생성된 텍스트, usage 정보)
                  usage = {
                      "input_tokens": int,
                      "output_tokens": int,
                      "reasoning_tokens": int,
                      "total_tokens": int
                  }

        Raises:
            Exception: API 호출 실패 시
        """
        pass

    @abstractmethod
    async def structured_completion(
        self,
        messages: List[Dict[str, Any]],
        schema: Dict[str, Any],
        temperature: float = 1.0,
        **kwargs
    ) -> tuple[str, Dict[str, int]]:
        """
        JSON 스키마 기반 구조화된 출력 생성

        Args:
            messages: OpenAI Responses API 형식 메시지 리스트
            schema: JSON 스키마 (type, properties, required 등)
            temperature: 생성 온도
            **kwargs: 추가 파라미터

        Returns:
            tuple: (JSON 형식의 문자열, usage 정보)
                  usage = {
                      "input_tokens": int,
                      "output_tokens": int,
                      "reasoning_tokens": int,
                      "total_tokens": int
                  }

        Raises:
            NotImplementedError: 해당 Provider가 스키마 기반 출력을 지원하지 않을 때
            Exception: API 호출 실패 시
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        텍스트의 토큰 수 계산
        
        Provider별로 다른 토크나이저를 사용할 수 있습니다.
        
        Args:
            text: 토큰 수를 계산할 텍스트
        
        Returns:
            int: 토큰 수
        """
        pass
    
    def get_model_name(self) -> str:
        """
        현재 사용 중인 모델 이름 반환
        
        Returns:
            str: 모델 ID
        """
        return self.model_name
    
    def get_provider_name(self) -> str:
        """
        Provider 이름 반환 (openai, gemini 등)
        
        Returns:
            str: Provider 이름
        """
        return self.__class__.__name__.replace("Provider", "").lower()

