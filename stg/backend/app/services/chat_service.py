import httpx
import json
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.chat_schema import ChatRequest
from app.db.mongodb_crud import save_to_mongodb, save_chat_and_return_id
from app.core.config import settings

import time  

logger = logging.getLogger(__name__)


async def stream_chat_response(request: ChatRequest, mongo_client: AsyncIOMotorDatabase):
    ai_endpoint = f"{settings.AI_SERVICE_URL}/api/chat"

    question = request.user_input
    answer = ""
    decision = ""
    preset = ""
    totalTokens = ""
    metadata = {}
    totalCostUsd = ""

    # 시작 시간 측정(로그)
    start_time = time.perf_counter()
    first_token_received = False

    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", ai_endpoint, json=request.model_dump(), timeout=120.0) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError:
                        logger.warning(f"JSON 파싱 오류: {line}", exc_info=True)
                        continue

                    event_type = payload.get("type")

                    # 채팅 본문
                    if event_type == "delta":
                        content = payload.get("content", "")
                        
                        # 첫 번째 토큰이 도착했을 때 시간(로그)
                        if not first_token_received and content:
                            first_token_time = time.perf_counter() - start_time
                            logger.info(f"[AI 첫 응답 소요 시간]: {first_token_time:.4f}초 | 첫 토큰: {content}")
                            first_token_received = True

                        answer += content
                        yield content.encode("utf-8")

                    # 메타 데이터
                    elif event_type == "metadata":
                        metadata = payload.get("data", {})
                        rag = metadata.get("rag", {})
                        decision = rag.get("gate_reason", "") or ""

                        tokenUsage = metadata.get("token_usage", {})
                        totalTokens = tokenUsage.get("total_tokens", "")
                        preset = tokenUsage.get("preset", "")
                        totalCostUsd = tokenUsage.get("total_cost_usd", "")

                    # 에러
                    elif event_type == "error":
                        error_msg = payload.get("message", "Unknown AI error")
                        error_code = payload.get("code", "UNKNOWN")
                        logger.error(f"[AI Error ({error_code})]: {error_msg}", exc_info=True)
                        
                        friendly_error = "AI 응답 생성 중 오류가 발생했습니다. 다시 시도해주세요."
                        yield friendly_error.encode("utf-8")
                        break

        # 총 소요 시간 측정(로그)
        total_duration = time.perf_counter() - start_time
        logger.info(f"[AI  완료 총 소요 시간]: {total_duration:.4f}초")

    except httpx.RequestError as exc:
        logger.error(f"AI 서비스 연결 실패: {exc}", exc_info=True)
        friendly_error = "챗봇 서버에 연결할 수 없습니다. 다시 시도해주세요."
        yield friendly_error.encode("utf-8")

    except Exception as e:
        logger.error(f"스트리밍 중 예상치 못한 오류: {e}", exc_info=True)
        friendly_error = "알 수 없는 오류가 발생했습니다. 다시 시도해주세요."
        yield friendly_error.encode("utf-8")
    
    try:
        if answer:
            chatId = await save_chat_and_return_id(
                mongo_client,
                {"question": question, "answer": answer, "decision": decision},
                "chat"
            )

            await save_to_mongodb(
                mongo_client,
                {"chatId": chatId, "preset": preset, "totalTokens": totalTokens },
                "token" 
            )

            await save_to_mongodb(
                mongo_client, 
                {"chatId": chatId, "metadata": metadata},
                "metadata"
            )
            
    except Exception as e:
        logger.error(f"DB 저장 실패: {e}", exc_info=True)