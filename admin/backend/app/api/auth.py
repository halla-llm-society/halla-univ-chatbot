from fastapi import APIRouter, HTTPException, status, Response, Depends, Request
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import jwt

from app.core.config import settings
from app.core.security import create_access_token, get_current_admin

router = APIRouter()

class GoogleToken(BaseModel):
    id_token: str

@router.post("/auth/google/login", tags=["Authentication"])
async def google_login(token_data: GoogleToken, response: Response):
    """
    Google 로그인을 처리하고 HTTP-only Cookie를 발급
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
            
        # 이메일이 확인됨 -> JWT 생성
        app_access_token = create_access_token(email=email)
        
        # 5. 쿠키 설정 (순수 토큰 값만 저장)
        response.set_cookie(
            key="access_token",
            value=app_access_token, # Bearer 없이 저장
            httponly=True,          # JS 접근 불가
            secure=True,            # HTTPS 전용 여부
            samesite="Lax",         # CSRF 방지
            max_age=60 * 60 * 12,   # 12시간
            path="/"                # 모든 경로에서 접근 가능
        )

        return {
            "message": "Login successful",
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
    
@router.post("/auth/logout", tags=["Authentication"])
async def logout(response: Response):
    """
    로그아웃 시 쿠키를 만료시켜 삭제합니다.
    """
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}

@router.get("/auth/me", tags=["Authentication"])
async def check_auth_status(request: Request, email: str = Depends(get_current_admin)):
    """
    로그인 상태 확인 및 만료 시간(exp) 반환
    get_current_admin을 통과했다면 토큰은 유효합니다.
    """
    token = request.cookies.get("access_token")
    exp = None
    
    if token:
        try:
            # 확실한 디코딩을 위해 Secret Key와 Algorithm을 명시합니다.
            # 공백 제거 및 Bearer 처리
            clean_token = token.strip()
            if clean_token.startswith("Bearer "):
                clean_token = clean_token.replace("Bearer ", "")
            
            # security.py와 동일한 파라미터로 디코딩
            payload = jwt.decode(
                clean_token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            exp = payload.get("exp")
            
        except Exception as e:
            # 서버 로그에 에러를 출력하여 원인 파악 (터미널에서 확인 가능)
            print(f"[Auth Error] Failed to decode token for exp: {e}")
            pass

    return {
        "status": "authenticated", 
        "email": email,
        "exp": exp
    }