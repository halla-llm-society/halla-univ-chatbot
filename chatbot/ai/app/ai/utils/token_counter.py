"""
토큰 카운팅 모듈

provider별 실제 토큰 계산 방식을 사용하여 토큰 수를 추적합니다.
- OpenAI: tiktoken
- Gemini: model.count_tokens()
입력/출력/함수/RAG 토큰을 분리하여 집계합니다.
"""

import tiktoken
import threading
import json
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app.ai.llm.base import BaseLLMProvider


class TokenCounter:
    """토큰 카운터
    
    Provider별 실제 토큰 계산 방식을 사용합니다.
    - 입력 토큰: 시스템/사용자 메시지, 지침
    - 출력 토큰: 어시스턴트 응답 (스트리밍 델타 누적)
    - 함수 토큰: 함수 정의 (tools)
    - RAG 토큰: 검색된 컨텍스트
    
    스레드세이프하며, 배치 인코딩으로 성능을 최적화합니다.
    """
    
    def __init__(self, model: str = "gpt-4"):
        """토큰 카운터 초기화

        Args:
            model: 모델 ID (예: "gpt-4", "gemini-2.0-flash")
                   OpenAI 모델은 tiktoken, Gemini는 폴백
        """
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # 폴백: cl100k_base (gpt-4, gpt-3.5-turbo 공통)
            self.encoding = tiktoken.get_encoding("cl100k_base")
            logger.debug(f"[TokenCounter] 모델 {model}의 encoding이 없어 cl100k_base 사용")

        self.model = model

        # 카테고리별 토큰 누적
        self.input_tokens = 0
        self.output_tokens = 0
        self.function_tokens = 0
        self.rag_tokens = 0
        self.reasoning_tokens = 0  # o3-mini 등 추론 토큰

        # 역할별 세부 추적
        self._role_breakdown: Dict[str, Dict[str, int]] = {}

        # 역할별 모델 추적 (비용 계산용)
        self._role_model_map: Dict[str, str] = {}

        self._delta_buffer = []
        self._lock = threading.Lock()

        # 프로바이더 설정 및 토큰 추적 설정 로드
        config = self._load_full_config()
        self.provider_overheads = config.get("provider_config", {})
        self._tracking_config = config.get("token_tracking", {})
        self._tracking_mode = self._tracking_config.get("mode", "tiktoken_only")

        logger.debug(f"[TokenCounter] 토큰 추적 모드: {self._tracking_mode}")

        # Provider별 실제 토큰 수 추적 (Gemini 등)
        self._provider_tokens = {
            "input": {},    # {role: actual_tokens}
            "output": {},   # {role: actual_tokens}
            "rag": {}       # {role: actual_tokens}
        }

        # API usage 캐시 (hybrid 모드에서 비교용)
        self._api_usage_cache: Dict[str, Dict[str, int]] = {}
    
    def count_openai_chat_input_tokens(self, messages: List[Dict[str, str]]) -> int:
        """OpenAI Chat API 입력 토큰 수 계산 (API 포맷 오버헤드 포함)
        
        OpenAI Chat API의 공식 토큰 계산 방식을 따릅니다:
        - 각 메시지마다 +3 토큰 (role, content 구조 오버헤드)
        - name 필드가 있으면 +1 토큰
        - reply priming용 +3 토큰
        
        Reference: https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
        
        Args:
            messages: OpenAI API 메시지 리스트
                     예: [{"role": "system", "content": "..."},
                          {"role": "user", "content": "..."}]
        
        Returns:
            int: 계산된 토큰 수 (OpenAI API가 실제로 청구하는 토큰)
        """
        with self._lock:
            num_tokens = 0
            for message in messages:
                num_tokens += 3  # role, content 구조 오버헤드
                for key, value in message.items():
                    num_tokens += len(self.encoding.encode(str(value)))
                    if key == "name":
                        num_tokens += 1
            num_tokens += 3  # reply priming
            self.input_tokens += num_tokens
            return num_tokens
    
    def count_output(self, text: str) -> int:
        """출력 텍스트 토큰 계산
        
        Args:
            text: 어시스턴트 응답 텍스트
        
        Returns:
            int: 계산된 토큰 수
        """
        with self._lock:
            num_tokens = len(self.encoding.encode(text))
            self.output_tokens += num_tokens
            return num_tokens
    
    def count_output_delta(self, delta: str, role: str = "streaming") -> None:
        """스트리밍 델타 청크 누적 (배치 인코딩)

        성능 최적화를 위해 10개 청크마다 배치로 인코딩합니다.
        개별 청크를 바로 인코딩하는 것보다 효율적입니다.

        Args:
            delta: 스트리밍 응답 델타 청크
            role: 역할 이름 (기본: "streaming")
        """
        with self._lock:
            self._delta_buffer.append(delta)
            if len(self._delta_buffer) >= 10:
                batch_text = "".join(self._delta_buffer)
                num_tokens = len(self.encoding.encode(batch_text))
                self.output_tokens += num_tokens

                # role_breakdown에도 추가
                if role not in self._role_breakdown:
                    self._role_breakdown[role] = {"input": 0, "output": 0, "reasoning": 0}
                self._role_breakdown[role]["output"] += num_tokens

                self._delta_buffer.clear()

    def flush_delta_buffer(self, role: str = "streaming") -> None:
        """남은 델타 버퍼 처리 (스트리밍 완료 시)

        스트리밍 완료 후 버퍼에 남은 청크를 처리합니다.

        Args:
            role: 역할 이름 (기본: "streaming")
        """
        with self._lock:
            if self._delta_buffer:
                batch_text = "".join(self._delta_buffer)
                num_tokens = len(self.encoding.encode(batch_text))
                self.output_tokens += num_tokens

                # role_breakdown에도 추가
                if role not in self._role_breakdown:
                    self._role_breakdown[role] = {"input": 0, "output": 0, "reasoning": 0}
                self._role_breakdown[role]["output"] += num_tokens

                self._delta_buffer.clear()
    
    def count_openai_tools_tokens(self, tools: List[Dict[str, Any]]) -> int:
        """OpenAI API tools 파라미터 토큰 계산
        
        OpenAI Chat API의 tools 파라미터 (함수 정의)의 토큰 수를 계산합니다.
        함수 스키마를 JSON으로 직렬화한 후 tiktoken으로 인코딩합니다.
        
        Args:
            tools: OpenAI tools 정의 리스트
                  예: [{"type": "function", "name": "...", "parameters": {...}}]
        
        Returns:
            int: 계산된 토큰 수
        """
        with self._lock:
            num_tokens = 0
            for tool in tools:
                # function 스키마를 JSON 문자열로 변환 후 인코딩
                json_str = json.dumps(tool, ensure_ascii=False)
                num_tokens += len(self.encoding.encode(json_str))
            self.function_tokens += num_tokens
            return num_tokens
    
    def count_function_call(self, function_name: str, arguments: Dict[str, Any], result: str) -> int:
        """개별 함수 호출 토큰 계산
        
        함수 이름, 인자, 결과를 모두 합쳐서 토큰을 계산합니다.
        
        Args:
            function_name: 함수 이름
            arguments: 함수 인자
            result: 함수 실행 결과
        
        Returns:
            int: 계산된 토큰 수
        """
        with self._lock:
            # 함수 호출 전체를 하나의 텍스트로 구성
            call_text = f"{function_name}({json.dumps(arguments, ensure_ascii=False)})\n결과: {result}"
            num_tokens = len(self.encoding.encode(call_text))
            self.function_tokens += num_tokens
            return num_tokens
    
    def count_rag(self, context: str, actual_tokens: Optional[int] = None, role: str = "condense") -> int:
        """RAG 컨텍스트 토큰 계산
        
        Args:
            context: RAG 검색 결과 텍스트
            actual_tokens: Provider에서 제공한 실제 토큰 수 (Gemini 등)
            role: 토큰을 사용한 역할 (예: "condense", "gate")
        
        Returns:
            int: 계산된 토큰 수
        """
        with self._lock:
            if actual_tokens is not None:
                # Provider가 제공한 실제 토큰 수 사용
                num_tokens = actual_tokens
                self._provider_tokens["rag"][role] = actual_tokens
                logger.debug(f"[TokenCounter] RAG ({role}): {actual_tokens} 토큰 (provider 실제값)")
            else:
                # tiktoken 폴백
                num_tokens = len(self.encoding.encode(context))
                logger.debug(f"[TokenCounter] RAG ({role}): {num_tokens} 토큰 (tiktoken 추정)")
            
            self.rag_tokens += num_tokens
            return num_tokens
    
    def count_rag_with_provider(
        self,
        output_text: str,
        provider: Any,
        input_text: Optional[str] = None,
        role: str = "condense"
    ) -> int:
        """
        Provider를 사용하여 RAG 토큰 계산
        
        Provider의 타입에 따라 자동으로 적절한 토큰 계산 방식을 선택합니다.
        - Gemini: model.count_tokens() 사용 (실제값)
        - OpenAI: tiktoken 사용 (추정값)
        - 기타: tiktoken 폴백
        
        Args:
            output_text: 출력 텍스트 (LLM 응답)
            provider: LLM Provider 인스턴스
            input_text: 입력 텍스트 (프롬프트, 선택)
            role: 역할 (예: "condense", "gate")
        
        Returns:
            int: 계산된 토큰 수
        """
        with self._lock:
            provider_name = provider.get_provider_name()
            
            # Provider별 토큰 계산 방식 선택
            match provider_name:
                case "gemini":
                    # Gemini 실제 토큰 계산
                    try:
                        output_tokens = provider.count_tokens(output_text)
                        input_tokens = provider.count_tokens(input_text) if input_text else 0
                        total_tokens = input_tokens + output_tokens
                        
                        logger.debug(f"[TokenCounter] {role} (Gemini 실제): "
                              f"입력 {input_tokens} + 출력 {output_tokens} = {total_tokens}")
                        
                        self._provider_tokens["rag"][role] = total_tokens
                        self.rag_tokens += total_tokens
                        return total_tokens
                    except Exception as e:
                        logger.debug(f"[TokenCounter] Gemini 토큰 계산 실패: {e}, tiktoken 폴백")
                        # 폴백으로 계속 진행
                
                case "openai":
                    # OpenAI tiktoken 사용
                    output_tokens = len(self.encoding.encode(output_text))
                    input_tokens = len(self.encoding.encode(input_text)) if input_text else 0
                    total_tokens = input_tokens + output_tokens
                    
                    logger.debug(f"[TokenCounter] {role} (OpenAI tiktoken): "
                          f"입력 {input_tokens} + 출력 {output_tokens} = {total_tokens}")
                    
                    self.rag_tokens += total_tokens
                    return total_tokens
                
                case _:
                    # 기타 Provider 또는 폴백: tiktoken 사용
                    output_tokens = len(self.encoding.encode(output_text))
                    input_tokens = len(self.encoding.encode(input_text)) if input_text else 0
                    total_tokens = input_tokens + output_tokens
                    
                    logger.debug(f"[TokenCounter] {role} ({provider_name} → tiktoken 폴백): "
                          f"입력 {input_tokens} + 출력 {output_tokens} = {total_tokens}")
                    
            self.rag_tokens += total_tokens
            return total_tokens
    
    def get_role_breakdown(self) -> Dict[str, Dict[str, int]]:
        """역할별 토큰 세부 분석 반환
        
        Returns:
            Dict: 역할별 토큰 통계
                {
                    "gate": {"input": 150, "output": 30},
                    "condense": {"input": 3000, "output": 500},
                    ...
                }
        """
        with self._lock:
            return dict(self._role_breakdown)
    
    def get_total(self) -> Dict[str, int]:
        """누적 토큰 통계 반환

        Returns:
            Dict: 토큰 통계
                {
                    "input_tokens": int,
                    "output_tokens": int,
                    "function_tokens": int,
                    "rag_tokens": int,
                    "reasoning_tokens": int,
                    "total_tokens": int
                }
        """
        with self._lock:
            return {
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "function_tokens": self.function_tokens,
                "rag_tokens": self.rag_tokens,
                "reasoning_tokens": self.reasoning_tokens,
                "total_tokens": (
                    self.input_tokens +
                    self.output_tokens +
                    self.function_tokens +
                    self.rag_tokens +
                    self.reasoning_tokens
                ),
            }
    
    def reset(self) -> None:
        """카운터 초기화

        대화 완료 후 카운터를 리셋합니다.
        """
        with self._lock:
            self.input_tokens = 0
            self.output_tokens = 0
            self.function_tokens = 0
            self.rag_tokens = 0
            self.reasoning_tokens = 0
            self._delta_buffer.clear()
            self._role_breakdown.clear()
            self._role_model_map.clear()
            self._api_usage_cache.clear()
    
    def _load_full_config(self) -> Dict[str, Any]:
        """llm_config.yaml에서 전체 설정 로드

        Returns:
            Dict: 전체 설정 (provider_config, token_tracking 등)
        """
        try:
            config_path = Path(__file__).parent.parent.parent / "config" / "llm_config.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            provider_config = config.get("provider_config", {})
            logger.debug(f"[TokenCounter] Provider config loaded: {provider_config}")
            return config
        except Exception as e:
            logger.debug(f"[TokenCounter] Failed to load config: {e}")
            # 폴백: 기본값 사용
            return {
                "provider_config": {
                    "openai": {
                        "message_overhead": 3,
                        "reply_priming_overhead": 3,
                        "name_field_overhead": 1
                    },
                    "gemini": {
                        "message_overhead": 0,
                        "reply_priming_overhead": 0,
                        "name_field_overhead": 0
                    }
                },
                "token_tracking": {
                    "mode": "tiktoken_only",
                    "fallback_to_tiktoken": True,
                    "track_reasoning_tokens": False
                }
            }
    
    def _calculate_openai_overhead(self, messages: List[Dict[str, Any]]) -> int:
        """OpenAI 메시지 구조 오버헤드 계산
        
        Args:
            messages: OpenAI 형식 메시지 리스트
        
        Returns:
            int: 오버헤드 토큰 수
        """
        overheads = self.provider_overheads.get("openai", {})
        message_overhead = overheads.get("message_overhead", 3)
        reply_priming = overheads.get("reply_priming_overhead", 3)
        name_field_overhead = overheads.get("name_field_overhead", 1)
        
        total_overhead = 0
        
        # 각 메시지마다 오버헤드
        for message in messages:
            total_overhead += message_overhead
            if "name" in message:
                total_overhead += name_field_overhead
        
        # Reply priming
        total_overhead += reply_priming
        
        return total_overhead
    
    def count_with_provider(
        self,
        provider: 'BaseLLMProvider',
        input_text: str,
        output_text: str,
        role: str,
        category: str = "input"
    ) -> Dict[str, int]:
        """프로바이더를 사용한 통합 토큰 계산
        
        Args:
            provider: LLM Provider 인스턴스
            input_text: 입력 텍스트 (프롬프트)
            output_text: 출력 텍스트 (응답)
            role: 역할 이름 (gate, condense, streaming 등)
            category: 토큰 카테고리 (input, output, rag, function)
        
        Returns:
            Dict: {"input": X, "output": Y, "total": Z}
        """
        with self._lock:
            # 1. Provider의 count_tokens() 사용
            input_tokens = provider.count_tokens(input_text)
            output_tokens = provider.count_tokens(output_text)
            
            # 2. 프로바이더별 오버헤드 적용 (OpenAI만)
            # 주의: 여기서는 단순 텍스트 토큰만 계산. 
            # 메시지 구조 오버헤드는 count_openai_chat_input_tokens에서 처리
            
            # 3. 카테고리별 누적
            if category == "rag":
                self.rag_tokens += (input_tokens + output_tokens)
            elif category == "function":
                self.function_tokens += (input_tokens + output_tokens)
            else:
                # 기본적으로 input/output에 각각 누적
                self.input_tokens += input_tokens
                self.output_tokens += output_tokens
            
            # 4. 역할별 세부 추적
            if role not in self._role_breakdown:
                self._role_breakdown[role] = {"input": 0, "output": 0, "reasoning": 0}
            self._role_breakdown[role]["input"] += input_tokens
            self._role_breakdown[role]["output"] += output_tokens
            
            return {
                "input": input_tokens,
                "output": output_tokens,
                "total": input_tokens + output_tokens
            }
    
    def count_openai_streaming_tokens(self, context: List[Dict[str, Any]], role: str = "streaming") -> int:
        """OpenAI 스트리밍 응답용 입력 토큰 계산

        Args:
            context: OpenAI API 메시지 컨텍스트
            role: 역할 이름 (기본: "streaming")

        Returns:
            int: 계산된 토큰 수
        """
        tokens = self.count_openai_chat_input_tokens(context)

        # 역할별 추적 (input_tokens는 이미 count_openai_chat_input_tokens에서 누적됨)
        with self._lock:
            if role not in self._role_breakdown:
                self._role_breakdown[role] = {"input": 0, "output": 0, "reasoning": 0}
            self._role_breakdown[role]["input"] += tokens

        return tokens

    def update_from_api_usage(
        self,
        usage: Dict[str, int],
        role: str,
        model: str,
        category: str = "input",
        replace: bool = False
    ) -> None:
        """OpenAI API response.usage로 토큰 카운터 갱신

        API가 반환한 실제 usage 정보를 사용하여 카운터를 업데이트합니다.
        api_first 또는 hybrid 모드에서 사용됩니다.

        Args:
            usage: API response의 usage 객체
                   {"input_tokens": N, "output_tokens": M, "reasoning_tokens": K, "total_tokens": T}
            role: 역할 이름 (gate, condense, function_analyze 등)
            model: 사용한 모델 ID (예: "o3-mini", "gpt-4.1")
            category: 토큰 카테고리 (input, output, rag, function)
            replace: True일 때 기존 role의 토큰을 제거하고 새 값으로 교체 (streaming 등에서 사용)
        """
        with self._lock:
            input_tok = usage.get("input_tokens", 0)
            output_tok = usage.get("output_tokens", 0)
            reasoning_tok = usage.get("reasoning_tokens", 0)

            # 모드별 처리
            if self._tracking_mode == "api_first":
                # API usage를 실제값으로 사용
                pass
            elif self._tracking_mode == "hybrid":
                # 비교를 위해 캐시에 저장
                self._api_usage_cache[role] = usage.copy()
                logger.debug(f"[TokenCounter][hybrid] {role} API usage: {usage}")

            # replace 모드: 기존 role의 토큰을 제거
            if replace and role in self._role_breakdown:
                old_tokens = self._role_breakdown[role]

                # 카테고리별 기존 토큰 제거
                if category == "rag":
                    self.rag_tokens -= (old_tokens["input"] + old_tokens["output"])
                elif category == "function":
                    self.function_tokens -= (old_tokens["input"] + old_tokens["output"])
                else:
                    self.input_tokens -= old_tokens["input"]
                    self.output_tokens -= old_tokens["output"]

                # reasoning tokens 제거
                self.reasoning_tokens -= old_tokens["reasoning"]

                logger.debug(f"[TokenCounter] {role} 기존 토큰 제거 (replace=True): "
                      f"input={old_tokens['input']}, output={old_tokens['output']}, reasoning={old_tokens['reasoning']}")

                # role_breakdown 초기화
                self._role_breakdown[role] = {"input": 0, "output": 0, "reasoning": 0}

            # 카테고리별 누적
            if category == "rag":
                self.rag_tokens += (input_tok + output_tok)
            elif category == "function":
                self.function_tokens += (input_tok + output_tok)
            else:
                self.input_tokens += input_tok
                self.output_tokens += output_tok

            # reasoning tokens 누적
            if reasoning_tok > 0:
                self.reasoning_tokens += reasoning_tok

            # 역할별 세부 추적
            if role not in self._role_breakdown:
                self._role_breakdown[role] = {"input": 0, "output": 0, "reasoning": 0}

            self._role_breakdown[role]["input"] += input_tok
            self._role_breakdown[role]["output"] += output_tok
            self._role_breakdown[role]["reasoning"] += reasoning_tok

            # 역할별 모델 추적 (비용 계산용)
            self._role_model_map[role] = model

            logger.debug(f"[TokenCounter] {role} ({model}) API usage 반영 (replace={replace}): "
                  f"input={input_tok}, output={output_tok}, reasoning={reasoning_tok}")

    def get_role_usage_for_cost_calc(self) -> List[Dict[str, any]]:
        """비용 계산용 role별 사용량 데이터 생성

        CostCalculator.calculate_batch()에 전달할 형식으로 데이터를 반환합니다.
        각 role에서 사용한 모델과 토큰 수를 포함합니다.

        Returns:
            List: 사용량 리스트
                 예: [
                     {"model": "o3-mini", "input_tokens": 638, "output_tokens": 55},
                     {"model": "gpt-4.1-nano", "input_tokens": 4195, "output_tokens": 287},
                     ...
                 ]
        """
        with self._lock:
            usage_list = []

            for role, tokens in self._role_breakdown.items():
                model = self._role_model_map.get(role, self.model)  # 기본값: streaming 모델

                usage_list.append({
                    "role": role,
                    "model": model,
                    "input_tokens": tokens["input"],
                    "output_tokens": tokens["output"],
                    "reasoning_tokens": tokens.get("reasoning", 0),
                })

            return usage_list

    def get_tracking_mode(self) -> str:
        """현재 토큰 추적 모드 반환

        Returns:
            str: 추적 모드 (api_first, tiktoken_only, hybrid)
        """
        return self._tracking_mode


# ============================================================
# DEPRECATED / LESS USED METHODS
# 아래 메서드들은 현재 사용되지 않거나 레거시 지원용으로 보관
# 새로운 코드에서는 count_with_provider() 사용을 권장
# ============================================================

# count_openai_tools_tokens: 현재 사용처 없음
# count_function_call: analyzer.py에서 제한적으로 사용 중
# count_rag, count_rag_with_provider: count_with_provider()로 대체 권장
