from pydantic import BaseModel

# /api/chat 엔드포인트의 request body type
class ChatRequest(BaseModel):
    message: str
    language: str