import os  
import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from .schemas import ChatRequest

router = APIRouter()
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://chatbot-ai-container:8000")

@router.post("/chat")
async def proxy_chat_to_ai(request: ChatRequest):
    return StreamingResponse(stream_ai_response(request), media_type="text/event-stream")


async def stream_ai_response(request: ChatRequest):
    ai_endpoint = f"{AI_SERVICE_URL}/api/chat"
    
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", ai_endpoint, json=request.dict(), timeout=120.0) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    yield chunk
    except httpx.RequestError as exc:
        error_message = f"Error calling AI service: {exc}"
        print(error_message)
        yield error_message.encode('utf-8')