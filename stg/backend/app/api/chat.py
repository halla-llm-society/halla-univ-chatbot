import os
import httpx
import json  # 1. ★★★ JSON 파싱을 위해 임포트 ★★★
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from ..schemas.chat_schemas import ChatRequest

router = APIRouter()
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://chatbot-ai-container:8000")


@router.post("")
async def proxy_chat_to_ai(request: ChatRequest):
    return StreamingResponse(stream_ai_response(request), media_type="text/event-stream")


async def stream_ai_response(request: ChatRequest):
    ai_endpoint = f"{AI_SERVICE_URL}/api/chat"
    
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", ai_endpoint, json=request.dict(), timeout=120.0) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    payload = json.loads(line)
                    type = payload.get('type')
                    
                    # "type": "delta"인 경우, 프론트엔드로 응답 메시지 전송
                    if type == 'delta':
                        content = payload.get('content', '')
                        answer += content  
                        yield content.encode('utf-8')
                        
                    # "type": "error"인 경우, 프론트엔드로 에러 메시지 전송
                    elif type == 'error':
                        error_msg = payload.get('message', 'Unknown AI error')
                        error_code = payload.get('code', 'UNKNOWN')

                        detailed_error = f"[AI Error ({error_code})]: {error_msg}"
                        yield detailed_error.encode('utf-8')
    # http 에러
    except httpx.RequestError as exc:
        error_message = f"Error calling AI service: {exc}"
        yield error_message.encode('utf-8')