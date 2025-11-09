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

    ################### For chat ###################
    data = request.model_dump()
    question = data["user_input"]
    answer = ""
    decision = ""
    ################### For chat ###################


    ################### For token ##################
    preset = ""
    totalTokens = ""
    ################### For token ##################


    ################### For metadata ###############
    metadata = {}
    ################### For metadata ###############

    try:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST", ai_endpoint, json=request.dict(), timeout=120.0
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError:
                        print(f"JSON 파싱 오류: {line}")
                        continue

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
                        print(f"[AI Error ({error_code})]: {error_msg}") # 개발자용 로그
                        
                        friendly_error = "죄송합니다. AI 응답 생성 중 오류가 발생했습니다."
                        yield friendly_error.encode("utf-8")
                        break

    except httpx.RequestError as exc:
        print(f"AI 서비스 연결 실패: {exc}") # 개발자용 로그
        friendly_error = "죄송합니다. 챗봇 서버에 연결할 수 없습니다."
        yield friendly_error.encode("utf-8")

    except Exception as e:
        # httpx 오류도, AI가 준 error도 아닌, 코드 로직상의 오류(KeyError 등)
        print(f"스트리밍 중 예상치 못한 오류: {e}") # 개발자용 로그
        friendly_error = "죄송합니다. 알 수 없는 오류가 발생했습니다."
        yield friendly_error.encode("utf-8")            

    try:
        if answer: # 답변이 성공적으로 생성되었을 때만 저장
            chatId = await save_chat_and_return_id(
                {"question": question, "answer": answer, "decision": decision},
                "chat"
            )
            await save_to_mongodb(
                {"chatId": chatId, "preset": preset, "totalTokens": totalTokens },
                "token"
            )
            await save_to_mongodb(
                {"chatId": chatId, "metadata": metadata},
                "metadata"
            )
    except Exception as e:
        # 이 오류는 사용자에게 보낼 수 없음
        print(f"!!! DB 저장 실패: {e} !!!")
        print(f"저장 실패 데이터 (question): {question}")
        print(f"저장 실패 데이터 (answer): {answer}")

