from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
import redis.asyncio as redis
import logging

from app.schemas.chat_schema import ChatRequest
from app.db.mongodb import get_mongo_db
from app.db.redis import get_redis_client
from app.services.chat_service import stream_chat_response
from app.services.cost_limit import check_cost_limit


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("")
async def chat(request: ChatRequest, 
               mongo_client: AsyncIOMotorDatabase = Depends(get_mongo_db), 
               redis_client: redis.Redis = Depends(get_redis_client)):
    try:
        await check_cost_limit(redis_client)
        return StreamingResponse(stream_chat_response(request, mongo_client, redis_client), media_type="text/event-stream")
    
    except HTTPException as e:
        error_message = "챗봇 운영이 일시 중지되었습니다. (월 사용량 한도 초과)"
        return StreamingResponse([error_message.encode('utf-8')],media_type="text/event-stream")
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
