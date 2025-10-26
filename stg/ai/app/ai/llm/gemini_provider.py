"""
Google Gemini Provider implementation.

Google Gemini API를 사용하는 Provider 구현체입니다.
OpenAI 형식 메시지를 Gemini 형식으로 변환하여 호출합니다.
"""

import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# apikey.env 파일 로드
_BASE_DIR = Path(__file__).resolve().parent.parent.parent  # app/
_DOTENV_PATH = _BASE_DIR / "apikey.env"
load_dotenv(_DOTENV_PATH)

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("[WARNING] google-generativeai not installed. Gemini Provider will not work.")

from .base import BaseLLMProvider
from .context_converter import ContextConverter


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API Provider"""
    
    def __init__(
        self,
        model_name: str,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Gemini Provider 초기화
        
        Args:
            model_name: Gemini 모델 ID (gemini-1.5-flash, gemini-1.5-pro 등)
            api_key: Google API 키 (None이면 환경변수 사용)
            **kwargs: 추가 설정
        
        Raises:
            ImportError: google-generativeai가 설치되지 않은 경우
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai is not installed. "
                "Please install it: pip install google-generativeai"
            )
        
        super().__init__(model_name, **kwargs)
        
        # API 설정
        genai.configure(api_key=api_key or os.getenv("GOOGLE_API_KEY"))
        
        # 모델 이름 변환 (Gemini API는 models/ prefix 필요)
        # gemini-2.0-flash → models/gemini-2.0-flash
        # gemini-2.5-flash → models/gemini-2.5-flash
        # gemini-2.5-pro → models/gemini-2.5-pro
        actual_model_name = model_name
        if not model_name.startswith("models/"):
            actual_model_name = f"models/{model_name}"
        
        # 모델 초기화
        self.model = genai.GenerativeModel(actual_model_name)
        self.actual_model_name = actual_model_name
        
        # Context converter
        self.converter = ContextConverter()
    
    def simple_completion(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        단순 텍스트 생성 (Gemini API)
        
        OpenAI 형식 메시지를 Gemini 형식으로 변환하여 호출합니다.
        
        Args:
            messages: OpenAI 형식 메시지
            temperature: 생성 온도
            max_tokens: 최대 출력 토큰
            **kwargs: 추가 파라미터
        
        Returns:
            str: 생성된 텍스트
        """
        try:
            # OpenAI 형식 → Gemini 형식 변환
            gemini_messages = self.converter.openai_to_gemini(messages)
            
            # Generation config 설정
            generation_config = {
                "temperature": temperature,
                "top_p": kwargs.get("top_p", 0.95),
                "top_k": kwargs.get("top_k", 40),
            }
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens
            
            # Gemini API 호출
            response = self.model.generate_content(
                gemini_messages,
                generation_config=generation_config
            )
            
            # 응답 텍스트 추출
            return response.text.strip()
            
        except Exception as e:
            print(f"[GeminiProvider] simple_completion failed: {e}")
            raise
    
    def _clean_schema_for_gemini(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gemini API용 스키마 정리 (additionalProperties 등 제거)
        
        Args:
            schema: 원본 JSON 스키마
        
        Returns:
            Dict: Gemini 호환 스키마
        """
        cleaned = schema.copy()
        
        # additionalProperties 제거 (Gemini 미지원)
        if "additionalProperties" in cleaned:
            del cleaned["additionalProperties"]
        
        # properties 내부도 재귀적으로 정리
        if "properties" in cleaned:
            cleaned["properties"] = {
                key: self._clean_schema_for_gemini(val) if isinstance(val, dict) else val
                for key, val in cleaned["properties"].items()
            }
        
        # items 내부도 재귀적으로 정리 (배열의 경우)
        if "items" in cleaned and isinstance(cleaned["items"], dict):
            cleaned["items"] = self._clean_schema_for_gemini(cleaned["items"])
        
        return cleaned
    
    def structured_completion(
        self,
        messages: List[Dict[str, Any]],
        schema: Dict[str, Any],
        temperature: float = 1.0,
        **kwargs
    ) -> str:
        """
        JSON 스키마 기반 구조화된 출력 생성
        
        Gemini 1.5-pro는 response_schema를 지원합니다.
        gemini-1.5-flash는 지원 여부를 확인해야 합니다.
        
        Args:
            messages: OpenAI 형식 메시지
            schema: JSON 스키마
            temperature: 생성 온도
            **kwargs: 추가 파라미터
        
        Returns:
            str: JSON 형식 문자열
        
        Raises:
            NotImplementedError: 모델이 스키마 기반 출력을 지원하지 않을 때
        """
        try:
            # OpenAI 형식 → Gemini 형식 변환
            gemini_messages = self.converter.openai_to_gemini(messages)
            
            # 스키마 정리 (Gemini 호환)
            cleaned_schema = self._clean_schema_for_gemini(schema)
            
            # Generation config with schema
            generation_config = {
                "temperature": temperature,
                "response_mime_type": "application/json",
                "response_schema": cleaned_schema
            }
            
            # 스키마 지원 모델로 재초기화
            schema_model = genai.GenerativeModel(
                self.actual_model_name,
                generation_config=generation_config
            )
            
            # Gemini API 호출
            response = schema_model.generate_content(gemini_messages)
            
            # JSON 응답 추출
            return response.text.strip()
            
        except AttributeError as e:
            # response_schema 미지원 모델
            raise NotImplementedError(
                f"Model {self.model_name} does not support response_schema. "
                f"Use gemini-1.5-pro or higher. Error: {e}"
            )
        except Exception as e:
            print(f"[GeminiProvider] structured_completion failed: {e}")
            raise
    
    def structured_completion_with_tokens(
        self,
        messages: List[Dict[str, Any]],
        schema: Dict[str, Any],
        temperature: float = 1.0,
        **kwargs
    ) -> tuple[str, int]:
        """
        JSON 스키마 기반 구조화된 출력 생성 + 실제 토큰 수 반환
        
        Args:
            messages: OpenAI 형식 메시지
            schema: JSON 스키마
            temperature: 생성 온도
            **kwargs: 추가 파라미터
        
        Returns:
            tuple[str, int]: (JSON 응답, 실제 토큰 수)
        """
        try:
            # 기본 structured_completion 호출
            output_text = self.structured_completion(messages, schema, temperature, **kwargs)
            
            # 토큰 수 계산
            try:
                # 입력 토큰 계산
                prompt_text = "\n".join([
                    f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                    for msg in messages
                ])
                input_count = self.model.count_tokens(prompt_text).total_tokens
                
                # 출력 토큰 계산
                output_count = self.model.count_tokens(output_text).total_tokens
                
                total_tokens = input_count + output_count
                print(f"[GeminiProvider] 토큰 계산: 입력 {input_count} + 출력 {output_count} = {total_tokens}")
                return output_text, total_tokens
            except Exception as e:
                print(f"[GeminiProvider] token counting failed: {e}")
                return output_text, 0
                
        except Exception as e:
            print(f"[GeminiProvider] structured_completion_with_tokens failed: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """
        Gemini 토크나이저를 사용한 토큰 수 계산
        
        Args:
            text: 토큰을 계산할 텍스트
        
        Returns:
            int: 토큰 수
        """
        try:
            # Gemini 자체 토큰 카운터 사용
            token_count = self.model.count_tokens(text)
            return token_count.total_tokens
        except Exception as e:
            print(f"[GeminiProvider] count_tokens failed: {e}")
            # 폴백: 대략적인 추정 (1 토큰 ≈ 4 글자, Gemini는 조금 다를 수 있음)
            return len(text) // 4

