"""
Message format converter between OpenAI and Claude APIs.

OpenAI Responses API 형식을 Claude Messages API 형식으로 변환합니다.
"""

from typing import List, Dict, Any


class ContextConverter:
    """OpenAI → Claude 메시지 포맷 변환기"""

    @staticmethod
    def openai_to_claude_request(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        OpenAI Responses API 형식 → Claude Messages API 요청 형식 변환

        변환 규칙:
        1. system 메시지는 전부 모아서 최상위 "system" 문자열로 분리
           (Claude Messages API는 system을 messages 배열이 아닌 별도 필드로 받음)
        2. user/assistant 메시지는 content를 순수 텍스트로 평탄화

        Args:
            messages: OpenAI 형식 메시지 리스트

        Returns:
            Dict: {"messages": [...]} 또는 {"system": str, "messages": [...]}
                  client.messages.create(**request)에 그대로 병합해서 사용
        """
        system_prompts = []
        claude_messages = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                text = ContextConverter.extract_text_from_openai_content(content)
                if text:
                    system_prompts.append(text)
                continue

            claude_role = "assistant" if role == "assistant" else "user"
            text = ContextConverter.extract_text_from_openai_content(content)
            claude_messages.append({"role": claude_role, "content": text})

        request: Dict[str, Any] = {"messages": claude_messages}
        if system_prompts:
            request["system"] = "\n\n".join(system_prompts)
        return request

    @staticmethod
    def extract_text_from_openai_content(content: Any) -> str:
        """
        OpenAI content에서 순수 텍스트 추출

        Args:
            content: OpenAI content (str, list, dict 등)

        Returns:
            str: 추출된 텍스트
        """
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            texts = []
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    texts.append(item["text"])
                elif isinstance(item, str):
                    texts.append(item)
            return " ".join(texts)

        if isinstance(content, dict) and "text" in content:
            return content["text"]

        return str(content)
