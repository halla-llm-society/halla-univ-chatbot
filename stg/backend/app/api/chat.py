from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.config import settings
from bson import ObjectId
import logging

from app.schemas.chat_schema import ChatRequest
from app.db.mongodb import get_mongo_db
from app.services.chat_service import stream_chat_response
from app.services.cost_limit import check_cost_limit
from app.db.mongodb_crud import get_chat_history


router = APIRouter()
logger = logging.getLogger(__name__)




@router.post("")
async def chat(request: ChatRequest, http_req: Request, http_res: Response, mongo_client: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    
    
    try:
        # await check_cost_limit()
        cookie_id = http_req.cookies.get("chatId")
        is_new_user = False
        is_tampered = False

        if cookie_id:
            current_chat_id = cookie_id

        elif cookie_id and not ObjectId.is_valid(cookie_id):
            logger.warning(f"잘못된 쿠키 감지됨: {cookie_id}")
            current_chat_id = str(ObjectId()) 
            is_new_user = True
            is_tampered = True

        else:
         
            current_chat_id = str(ObjectId())
            is_new_user = True

        stream_generator = stream_chat_response(request, mongo_client, current_chat_id, is_tampered)
        
        response = StreamingResponse(stream_generator, media_type="text/event-stream")

        if is_new_user:
            response.set_cookie(
                key="chatId",
                value=current_chat_id,
                max_age=86400,   
                httponly=False,  
                secure=True  
                
            )
            
        return response
    

    
    except HTTPException as e:
        if e.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            error_message = "월 사용량 한도 초과로 인해 챗봇 운영이 일시 중지되었습니다."
            return StreamingResponse([error_message.encode("utf-8")], media_type="text/event-stream")
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)

@router.get("/history")
async def get_history(
    request: Request, 
    mongo_client: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    chat_id = request.cookies.get("chatId")

    if not chat_id:
        
        return []

    try:
        
        collection_name = f"chat{settings.MONGODB_SUFFIX}"
        collection = mongo_client[collection_name] 

      
        query_filters = [{"chatId": chat_id}]
        if ObjectId.is_valid(chat_id):
            query_filters.append({"chatId": ObjectId(chat_id)})
            
        cursor = collection.find({"$or": query_filters}).limit(6)
        
        
        raw_history = await cursor.to_list(length=6)
        
        
        formatted_history = []
        for log in raw_history:
            if "question" in log:
                formatted_history.append({"role": "user", "content": log["question"]})
            if "answer" in log:
                formatted_history.append({"role": "assistant", "content": log["answer"]})

        return formatted_history
    
    except Exception as e:
        logger.error(f"History fetch error: {e}")
        return []        
