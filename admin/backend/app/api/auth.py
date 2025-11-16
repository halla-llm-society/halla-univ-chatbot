from fastapi import APIRouter, HTTPException, status, Body
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.core.config import settings
from app.core.security import create_access_token

router = APIRouter()

class GoogleToken(BaseModel):
    id_token: str

@router.post("/auth/google/login", tags=["Authentication"])
async def google_login(token_data: GoogleToken):
    """
    프론트엔드에서 받은 Google ID 토큰을 검증하고,
    허용된 이메일이면 우리 앱의 JWT 토큰을 발급합니다.
    """
    try:
        # Google ID 토큰 검증
        idinfo = id_token.verify_oauth2_token(
            token_data.id_token, 
            google_requests.Request(), 
            settings.GOOGLE_CLIENT_ID
        )
        
        email = idinfo.get('email')

        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Email not found in Google token"
            )

        # 허용된 이메일인지 확인
        if email != settings.ALLOWED_ADMIN_EMAIL:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied for email: {email}"
            )
            
        # 이메일이 확인됨 -> 우리 앱 전용 JWT 생성
        app_access_token = create_access_token(email=email)
        
        return {
            "access_token": app_access_token,
            "token_type": "bearer",
            "email": email
        }

    except ValueError as e:
        # ID 토큰이 유효하지 않은 경우
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )