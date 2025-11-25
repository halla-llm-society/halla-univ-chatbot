from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from app.schemas.chat_schema import ChatRequest
from app.db.mongodb import get_mongo_db
from app.services.chat_service import stream_chat_response
from app.services.cost_limit import check_cost_limit


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("")
async def chat(request: ChatRequest, mongo_client: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    try:
        # await check_cost_limit()
        return StreamingResponse(stream_chat_response(request, mongo_client), media_type="text/event-stream")
    
    except HTTPException as e:
        if e.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            error_message = "월 사용량 한도 초과로 인해 챗봇 운영이 일시 중지되었습니다."
            return StreamingResponse([error_message.encode("utf-8")], media_type="text/event-stream")
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
