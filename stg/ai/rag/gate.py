"""Regulation gate logic for RAG."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable

from app.ai.chatbot import character
from app.ai.chatbot.config import client, model

# LLM Manager import
from app.ai.llm import get_provider


@dataclass(slots=True)
class GateDecision:
    is_regulation: bool
    reason: str | None = None


class RegulationGate:
    """RAG 여부를 판단하는 책임을 가집니다. 레그여부와 자신의 판단이유를 반환하는역할입니다."""

    def __init__(
        self,
        *,
        openai_client=client,
        model_name: str | None = None,
        debug_fn: Callable[[str], None] | None = None,
        token_counter=None,
    ) -> None:
        self._client = openai_client
        self._model_name = model_name or model.advanced
        self._debug = debug_fn or (lambda _: None)
        self.token_counter = token_counter

    def decide(self, question: str) -> GateDecision:
        self._debug(
            f"gate.decide: evaluating question='{question[:60]}...' with model={self._model_name}"
        )
        prompt = [
            {"role": "system", "content": character.decide_rag},
            {"role": "user", "content": question},
        ]

        schema = {
            "type": "object",
            "properties": {
                "is_regulation": {"type": "boolean"},
                "reason": {"type": "string"},
            },
            "required": ["is_regulation", "reason"],
            "additionalProperties": False,
        }

        # 키워드 폴백 준비 (LLM 실패 시 사용)
        keywords = ["학사", "규정", "졸업", "수강", "성적", "장학", "징계", "학점", "전공", "복학", "휴학", "재입학", "전과", "교과", "비교과", "조기졸업", "장학금", "등록", "수료", "학위", "이수", "필수", "선택", "학부", "학과"]
        
        try:
            # LLM Manager 사용 (교체 가능, JSON 스키마 지원 모델 필요)
            provider = get_provider("gate")
            raw = provider.structured_completion(prompt, schema).strip()
            
            # ✅ 토큰 계산 추가
            if self.token_counter:
                prompt_text = "\n".join([msg.get('content', '') for msg in prompt])
                self.token_counter.count_with_provider(
                    provider=provider,
                    input_text=prompt_text,
                    output_text=raw,
                    role="gate",
                    category="rag"
                )
            
            # 빈 응답 체크
            if not raw:
                self._debug("gate.decide: empty response from provider -> fallback")
                raise ValueError("Empty response from LLM provider")
            
            # JSON 파싱 시도
            payload = json.loads(raw)
            
            # 필수 필드 확인
            if "is_regulation" not in payload:
                self._debug("gate.decide: missing 'is_regulation' field -> fallback")
                raise ValueError("Missing required field 'is_regulation'")
            
            is_reg = bool(payload.get("is_regulation"))
            reason = (payload.get("reason") or "").strip() or None
            if reason:
                self._debug(f"gate.decide: reason='{reason}'")
            self._debug(f"gate.decide: decision={is_reg}")
            return GateDecision(is_regulation=is_reg, reason=reason)
            
        except Exception as exc:
            self._debug(f"gate.decide: structured output failure -> {exc}")
            # 키워드 기반 폴백
            fallback = any(keyword in question for keyword in keywords)
            self._debug(f"gate.decide: keyword fallback decision={fallback} (matched: {[k for k in keywords if k in question]})")
            reason_text = f"LLM 판단 실패로 키워드 기반 폴백 사용 ({exc})"
            return GateDecision(is_regulation=fallback, reason=reason_text)
