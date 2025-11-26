import jwt
from jwt import PyJWTError
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyCookie
from pydantic import BaseModel, ValidationError

from app.core.config import settings

# 쿠키 설정
cookie_scheme = APIKeyCookie(name="access_token", auto_error=False)

class TokenPayload(BaseModel):
    sub: str | None = None
    exp: int | None = None

def create_access_token(email: str) -> str:
    """
    우리 앱 전용 JWT 액세스 토큰 생성
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": email,
        "exp": expire.timestamp()
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

async def get_current_admin(
    token_cookie: str | None = Depends(cookie_scheme)
) -> str:
    """
    FastAPI 의존성 함수:
    API 요청 헤더의 토큰을 검증하고, 유효하면 이메일을 반환합니다.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    # 쿠키가 없으면 바로 에러 발생
    if not token_cookie:
        raise credentials_exception
    
    try:
        # 토큰 디코딩
        payload_data = jwt.decode(
            token_cookie, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # 'exp' 필드 (만료 시간) 검증
        exp = payload_data.get("exp")
        if exp is None or datetime.now(timezone.utc) > datetime.fromtimestamp(exp, tz=timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )

        # 이메일 확인
        email = payload_data.get("sub")
        if email is None:
            raise credentials_exception
            
    except (PyJWTError, ValidationError):
        raise credentials_exception

    # 관리자 이메일 일치 확인
    if email != settings.ALLOWED_ADMIN_EMAIL:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted",
        )
        
    return email