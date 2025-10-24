"""
Message format converter between OpenAI and Gemini APIs.

OpenAI Responses API 형식을 Gemini API 형식으로 변환하고,
그 반대 변환도 지원합니다.
"""

from typing import List, Dict, Any


class ContextConverter:
    """OpenAI ↔ Gemini 메시지 포맷 변환기"""
    
    @staticmethod
    def openai_to_gemini(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        OpenAI Responses API 형식 → Gemini API 형식 변환
        
        변환 규칙:
        1. role 변환: "assistant" → "model", "system" → user에 통합
        2. content 구조 변환: [{"type": "input_text", "text": "..."}] → [{"text": "..."}]
        3. system 메시지는 첫 user 메시지에 프롬프트로 추가
        
        Args:
            messages: OpenAI 형식 메시지 리스트
        
        Returns:
            List[Dict]: Gemini 형식 메시지 리스트
        
        Example:
            >>> openai_msgs = [
            ...     {"role": "system", "content": "당신은 도우미입니다"},
            ...     {"role": "user", "content": [{"type": "input_text", "text": "안녕"}]}
            ... ]
            >>> gemini_msgs = ContextConverter.openai_to_gemini(openai_msgs)
            >>> print(gemini_msgs)
            [{"role": "user", "parts": [{"text": "시스템 지침: 당신은 도우미입니다\\n\\n안녕"}]}]
        """
        gemini_messages = []
        system_prompts = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # System 메시지는 별도로 수집
            if role == "system":
                if isinstance(content, str):
                    system_prompts.append(content)
                elif isinstance(content, list):
                    # content가 리스트인 경우 (Responses API 형식)
                    for item in content:
                        if isinstance(item, dict) and "text" in item:
                            system_prompts.append(item["text"])
                        elif isinstance(item, str):
                            system_prompts.append(item)
                continue
            
            # Role 변환
            gemini_role = "model" if role == "assistant" else "user"
            
            # Content 변환
            parts = ContextConverter._convert_content_to_parts(content)
            
            # 첫 user 메시지에 system 프롬프트 추가
            if gemini_role == "user" and system_prompts and not gemini_messages:
                system_text = "\n\n".join(system_prompts)
                # parts의 첫 텍스트에 시스템 프롬프트 추가
                if parts and "text" in parts[0]:
                    parts[0]["text"] = f"{system_text}\n\n{parts[0]['text']}"
                else:
                    parts.insert(0, {"text": system_text})
                system_prompts.clear()
            
            gemini_messages.append({
                "role": gemini_role,
                "parts": parts
            })
        
        # system 메시지만 있고 user 메시지가 없는 경우
        if system_prompts and not gemini_messages:
            gemini_messages.append({
                "role": "user",
                "parts": [{"text": "\n\n".join(system_prompts)}]
            })
        
        return gemini_messages
    
    @staticmethod
    def _convert_content_to_parts(content: Any) -> List[Dict[str, str]]:
        """
        OpenAI content → Gemini parts 변환
        
        Args:
            content: OpenAI content (str 또는 list)
        
        Returns:
            List[Dict]: Gemini parts 리스트
        """
        if isinstance(content, str):
            return [{"text": content}]
        
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    # Responses API 형식: {"type": "input_text", "text": "..."}
                    if "text" in item:
                        parts.append({"text": item["text"]})
                    # 이미지 등 다른 타입도 처리 가능하도록 확장 가능
                elif isinstance(item, str):
                    parts.append({"text": item})
            return parts if parts else [{"text": ""}]
        
        # 기타 타입은 문자열로 변환
        return [{"text": str(content)}]
    
    @staticmethod
    def gemini_to_openai(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Gemini API 형식 → OpenAI Responses API 형식 변환
        
        변환 규칙:
        1. role 변환: "model" → "assistant"
        2. parts 구조 변환: [{"text": "..."}] → [{"type": "output_text", "text": "..."}]
        
        Args:
            messages: Gemini 형식 메시지 리스트
        
        Returns:
            List[Dict]: OpenAI 형식 메시지 리스트
        """
        openai_messages = []
        
        for msg in messages:
            role = msg.get("role", "user")
            parts = msg.get("parts", [])
            
            # Role 변환
            openai_role = "assistant" if role == "model" else "user"
            
            # Parts → Content 변환
            content = []
            for part in parts:
                if isinstance(part, dict) and "text" in part:
                    content.append({
                        "type": "output_text" if openai_role == "assistant" else "input_text",
                        "text": part["text"]
                    })
            
            # content가 비어있으면 빈 텍스트 추가
            if not content:
                content.append({
                    "type": "output_text" if openai_role == "assistant" else "input_text",
                    "text": ""
                })
            
            openai_messages.append({
                "role": openai_role,
                "content": content
            })
        
        return openai_messages
    
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

