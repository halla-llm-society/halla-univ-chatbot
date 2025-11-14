from pydantic import BaseModel, Field
from typing import List, Literal


# 기존 메시지
class MessageHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=300)


# /api/chat 엔드포인트의 request body type
class ChatRequest(BaseModel):
    user_input: str = Field(..., max_length=300)
    message_history: List[MessageHistoryItem]
    language: Literal["KOR", "ENG", "VNM", "CHN", "UZB", "MNG", "IDN"]
