from fastapi import APIRouter, Request, HTTPException, status, Body
from pydantic import BaseModel, Field
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class DbSwitchRequest(BaseModel):
    environment: str = Field(..., description="연결할 데이터베이스 환경 ('stg' 또는 'prod')")

@router.post("/switch-database", status_code=status.HTTP_200_OK, summary="데이터베이스 연결 환경 전환")
async def switch_database(request: Request, payload: DbSwitchRequest):
    """
    FastAPI 애플리케이션의 MongoDB 연결을 STG 또는 PROD로 전환합니다.
    서버 상태를 변경하지 않고(중요함), 클라이언트에게 확인 메시지만 반환합니다.
    실제 전환은 클라이언트가 헤더를 변경함으로써 이루어집니다.

    """
    env = payload.environment.lower()
    if env not in ("stg", "prod"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid environment. Must be 'stg' or 'prod'.")

    # DB 인스턴스가 app.state에 초기화되었는지 확인
    if not hasattr(request.app.state, 'stg_db') or not hasattr(request.app.state, 'prod_db'):
        logger.error("Databases are not initialized in app.state")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Invalid environment")
    
    return {"message": f"Successfully switched to {env} database."}

@router.get("/current-database", status_code=status.HTTP_200_OK,summary="현재 연결된 데이터베이스 환경 조회")
async def get_current_database(request: Request):
    """
    현재 FastAPI 애플리케이션이 사용 중인 DB 환경('stg' 또는 'prod')을 반환합니다.
    """
    env = getattr(request.app.state, 'current_db_env', 'unknown')
    return {"environment": env}