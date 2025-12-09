from pydantic import BaseModel, Field
from typing import List, Literal, Optional


# 기존 메시지
class MessageHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str


# /api/chat 엔드포인트의 request body type
class ChatRequest(BaseModel):
    user_input: str = Field(..., max_length=300)
    
    language: Literal["KOR", "ENG", "VNM", "CHN", "UZB", "MNG", "IDN"]

    chatId: Optional[str] = None
