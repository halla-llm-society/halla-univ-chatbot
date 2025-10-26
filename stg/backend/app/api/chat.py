import os
import httpx
import json  
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from ..schemas.chat_schemas import ChatRequest
from ..db.database import save_to_mongodb, save_chat_and_return_id

router = APIRouter()
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://chatbot-ai-container:8000")


@router.post("")
async def proxy_chat_to_ai(request: ChatRequest):
    return StreamingResponse(stream_ai_response(request), media_type="text/event-stream")


async def stream_ai_response(request: ChatRequest):
    ai_endpoint = f"{AI_SERVICE_URL}/api/chat"

    ################### For stg-chat ###################
    data = request.model_dump()
    question = data["user_input"]
    answer = ""
    decision = ""
    ################### For stg-chat ###################


    ################### For stg-token ##################
    preset = ""
    totalTokens = ""
    ################### For stg-token ##################


    ################### For stg-metadata ###############
    metadata = {}
    ################### For stg-metadata ###############

    try:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST", ai_endpoint, json=request.dict(), timeout=120.0
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    payload = json.loads(line)
                    type = payload.get("type")

                    if type == "delta":
                        content = payload.get("content", "")
                        answer += content
                        yield content.encode("utf-8")

                    elif type == "metadata":
                        #gate_reason 추출
                        metadata = payload.get("data", {})
                        rag = metadata.get("rag", {})
                        decision = rag.get("gate_reason", "") or ""

                        # 토큰 관련 데이터 추출
                        tokenUsage = metadata.get("token_usage", {})
                        totalTokens = tokenUsage.get("total_tokens", "")
                        preset = tokenUsage.get("preset", "")

                    elif type == "error":
                        error_msg = payload.get("message", "Unknown AI error")
                        error_code = payload.get("code", "UNKNOWN")
                        detailed_error = f"[AI Error ({error_code})]: {error_msg}"
                        yield detailed_error.encode("utf-8")

        chatId = await save_chat_and_return_id(
            {"question": question, "answer": answer, "decision": decision},
            "stg-chat"
        )

        await save_to_mongodb(
            {"chatId": chatId, "preset": preset, "totalTokens": totalTokens },
            "stg-token"
        )

        await save_to_mongodb(
            {"chatId": chatId, "metadata": metadata},
            "stg-metadata"
        )

    except httpx.RequestError as exc:
        error_message = f"Error calling AI service: {exc}"
        yield error_message.encode("utf-8")
