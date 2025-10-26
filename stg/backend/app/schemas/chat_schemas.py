from pydantic import BaseModel
from typing import List

class MessageHistory(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    user_input: str
    message_history: List[MessageHistory]
    language: str