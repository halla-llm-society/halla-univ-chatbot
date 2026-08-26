"""
Claude Provider implementation.

Anthropic Claude Messages API를 사용하는 Provider 구현체입니다.
OpenAI 형식 메시지를 Claude 형식으로 변환하여 호출합니다.
"""

import asyncio
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# apikey.env 파일 로드
_BASE_DIR = Path(__file__).resolve().parent.parent.parent  # app/
_DOTENV_PATH = _BASE_DIR / "apikey.env"
load_dotenv(_DOTENV_PATH)

try:
    from anthropic import Anthropic

    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    print("[WARNING] anthropic not installed. Claude Provider will not work.")

from .base import BaseLLMProvider
from .openai_to_claude_request import ContextConverter


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude API Provider."""

    DEFAULT_MAX_TOKENS = 1024

    def __init__(
        self,
        model_name: str,
        api_key: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Claude Provider를 초기화합니다.

        Args:
            model_name: Claude 모델 ID
            api_key: Anthropic API 키. 없으면 ANTHROPIC_API_KEY를 사용합니다.
            **kwargs: 추가 설정. default_max_tokens를 지원합니다.
        """
        if not CLAUDE_AVAILABLE:
            raise ImportError(
                "anthropic is not installed. "
                "Please install it: pip install anthropic"
            )

        super().__init__(model_name, **kwargs)

        resolved_api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not resolved_api_key:
            raise ValueError("ANTHROPIC_API_KEY is not configured.")

        self.client = Anthropic(api_key=resolved_api_key)
        self.converter = ContextConverter()
        self.default_max_tokens = kwargs.get(
            "default_max_tokens", self.DEFAULT_MAX_TOKENS
        )

    async def simple_completion(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> tuple[str, Dict[str, int]]:
        """
        OpenAI 형식 메시지로 Claude 텍스트 생성을 요청합니다.

        Returns:
            tuple: (생성된 텍스트, usage 정보)
        """
        try:
            output_text, usage = await asyncio.to_thread(
                self._create_message,
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            if usage:
                print(f"[ClaudeProvider] simple_completion usage: {usage}")

            return output_text, usage

        except Exception as error:
            print(f"[ClaudeProvider] simple_completion failed: {error}")
            raise

    async def structured_completion(
        self,
        messages: List[Dict[str, Any]],
        schema: Dict[str, Any],
        temperature: float = 1.0,
        **kwargs: Any,
    ) -> tuple[str, Dict[str, int]]:
        """
        JSON Schema에 맞는 구조화된 Claude 출력을 생성합니다.

        구조화된 출력은 이를 지원하는 Claude 모델에서만 사용할 수 있습니다.
        """
        try:
            output_config = {
                "format": {
                    "type": "json_schema",
                    "schema": schema,
                }
            }
            output_text, usage = await asyncio.to_thread(
                self._create_message,
                messages,
                temperature=temperature,
                max_tokens=kwargs.pop("max_tokens", None),
                output_config=output_config,
                **kwargs,
            )

            if usage:
                print(f"[ClaudeProvider] structured_completion usage: {usage}")

            return output_text, usage

        except Exception as error:
            print(f"[ClaudeProvider] structured_completion failed: {error}")
            raise

    async def structured_completion_with_tokens(
        self,
        messages: List[Dict[str, Any]],
        schema: Dict[str, Any],
        temperature: float = 1.0,
        **kwargs: Any,
    ) -> tuple[str, int]:
        """구조화된 출력을 생성하고 API가 반환한 실제 토큰 수를 함께 반환합니다."""
        output_text, usage = await self.structured_completion(
            messages,
            schema,
            temperature,
            **kwargs,
        )
        return output_text, usage.get("total_tokens", 0)

    def count_tokens(self, text: str) -> int:
        """Claude Token Counting API로 텍스트 토큰 수를 계산합니다."""
        try:
            response = self.client.messages.count_tokens(
                model=self.model_name,
                messages=[{"role": "user", "content": text],
            )
            return response.input_tokens
        except Exception as error:
            print(f"[ClaudeProvider] count_tokens failed: {error}")
            return len(text) // 4

    def _create_message(
        self,
        messages: List[Dict[str, Any]],
        *,
        temperature: float,
        max_tokens: Optional[int],
        output_config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> tuple[str, Dict[str, int]]:
        """동기 Claude Messages API 호출과 응답 정리를 수행합니다."""
        request = self.converter.openai_to_claude_request(messages)
        request.update(
            {
                "model": self.model_name,
                "max_tokens": (
                    max_tokens if max_tokens is not None else self.default_max_tokens
                ),
                "temperature": temperature,
            }
        )

        # Claude Messages API가 지원하는 생성 옵션만 전달한다.
        for option in ("top_p", "top_k", "stop_sequences", "service_tier"):
            if option in kwargs and kwargs[option] is not None:
                request[option] = kwargs[option]

        if output_config is not None:
            request["output_config"] = output_config

        response = self.client.messages.create(**request)
        output_text = self._extract_text(response.content)
        usage = self._extract_usage(response)
        return output_text, usage

    @staticmethod
    def _extract_text(content: Any) -> str:
        """Claude 응답 content에서 text block만 추출합니다."""
        text_blocks = [
            block.text
            for block in content
            if getattr(block, "type", None) == "text"
            and isinstance(getattr(block, "text", None), str)
        ]
        return "\n".join(text_blocks).strip()

    @staticmethod
    def _extract_usage(response: Any) -> Dict[str, int]:
        """Claude 응답 usage를 Provider 공통 형식으로 변환합니다."""
        usage = getattr(response, "usage", None)
        if usage is None:
            return {}

        input_tokens = getattr(usage, "input_tokens", 0)
        output_tokens = getattr(usage, "output_tokens", 0)

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            # Claude의 usage 객체에는 OpenAI의 reasoning_tokens 같은
            # 별도 thinking 토큰 필드가 없음 (thinking 토큰은 output_tokens에 포함되어 옴).
            "reasoning_tokens": 0,
            "total_tokens": input_tokens + output_tokens,
        }
