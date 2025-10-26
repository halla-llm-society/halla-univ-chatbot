"""
OpenAI Provider implementation.

OpenAI Responses API를 사용하는 Provider 구현체입니다.
"""

import os
import tiktoken
from typing import List, Dict, Any, Optional
from openai import OpenAI

from .base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Responses API Provider"""
    
    def __init__(
        self,
        model_name: str,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        OpenAI Provider 초기화
        
        Args:
            model_name: OpenAI 모델 ID (gpt-4.1, o3-mini 등)
            api_key: OpenAI API 키 (None이면 환경변수 사용)
            **kwargs: 추가 설정
        """
        super().__init__(model_name, **kwargs)
        
        # API 클라이언트 초기화
        self.client = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            max_retries=kwargs.get("max_retries", 1)
        )
        
        # Tiktoken 인코더 초기화
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            # 모델명이 tiktoken에 없으면 cl100k_base 사용
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def simple_completion(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        단순 텍스트 생성 (OpenAI Responses API)
        
        Args:
            messages: OpenAI 형식 메시지 (변환 불필요)
            temperature: 생성 온도
            max_tokens: 최대 출력 토큰
            **kwargs: 추가 파라미터
        
        Returns:
            str: 생성된 텍스트
        """
        try:
            # Responses API 호출
            response = self.client.responses.create(
                model=self.model_name,
                input=messages,
                text={"format": {"type": "text"}},
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=kwargs.get("top_p", 1),
                **self._filter_kwargs(kwargs)
            )
            
            # 응답 텍스트 추출
            output_text = getattr(response, "output_text", "").strip()
            return output_text
            
        except Exception as e:
            print(f"[OpenAIProvider] simple_completion failed: {e}")
            raise
    
    def structured_completion(
        self,
        messages: List[Dict[str, Any]],
        schema: Dict[str, Any],
        temperature: float = 1.0,
        **kwargs
    ) -> str:
        """
        JSON 스키마 기반 구조화된 출력 생성
        
        Args:
            messages: OpenAI 형식 메시지
            schema: JSON 스키마
            temperature: 생성 온도
            **kwargs: 추가 파라미터
        
        Returns:
            str: JSON 형식 문자열
        """
        try:
            # 디버그 로깅
            print(f"[OpenAIProvider] structured_completion called:")
            print(f"  model: {self.model_name}")
            print(f"  schema: {schema}")
            print(f"  strict: {kwargs.get('strict', True)}")
            
            # Responses API 호출 (JSON 스키마 사용)
            response = self.client.responses.create(
                model=self.model_name,
                input=messages,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": kwargs.get("schema_name", "response_schema"),
                        "schema": schema,
                        "strict": kwargs.get("strict", True)
                    }
                },
                temperature=temperature,
                **self._filter_kwargs(kwargs)
            )
            
            # JSON 응답 추출
            output_text = getattr(response, "output_text", "").strip()
            print(f"[OpenAIProvider] structured_completion output: {output_text[:100]}...")
            
            # 빈 응답 체크
            if not output_text:
                raise ValueError(f"Empty output from model {self.model_name}")
            
            # JSON 유효성 검사
            import json
            try:
                json.loads(output_text)
            except json.JSONDecodeError as je:
                raise ValueError(f"Invalid JSON output from model {self.model_name}: {je}")
            
            print(f"[OpenAIProvider] structured_completion success!")
            return output_text
            
        except Exception as e:
            print(f"[OpenAIProvider] structured_completion failed: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """
        Tiktoken을 사용한 토큰 수 계산
        
        Args:
            text: 토큰을 계산할 텍스트
        
        Returns:
            int: 토큰 수
        """
        try:
            tokens = self.encoding.encode(text)
            return len(tokens)
        except Exception as e:
            print(f"[OpenAIProvider] count_tokens failed: {e}")
            # 폴백: 대략적인 추정 (1 토큰 ≈ 4 글자)
            return len(text) // 4
    
    def _filter_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Responses API에서 허용하지 않는 kwargs 필터링
        
        Args:
            kwargs: 원본 kwargs
        
        Returns:
            Dict: 필터링된 kwargs
        """
        # Responses API에서 허용하는 파라미터만 전달
        allowed_params = {
            "top_p", "store", "reasoning", "tools", "tool_choice"
        }
        return {k: v for k, v in kwargs.items() if k in allowed_params}

