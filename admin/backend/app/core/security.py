import jwt
from jwt import PyJWTError
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, ValidationError

from app.core.config import settings

# OAuth2 스킴 정의: "/admin/api/..." 경로에서 토큰을 찾습니다.
# 하지만 프론트엔드가 헤더에 직접 넣어줄 것이므로, 이 자체는 크게 중요하지 않습니다.
# 실제 토큰 확인은 get_current_admin에서 직접 헤더를 읽습니다.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/auth/google/login") 

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
    token: str = Depends(oauth2_scheme)
) -> str:
    """
    FastAPI 의존성 함수:
    API 요청 헤더의 토큰을 검증하고, 유효하면 이메일을 반환합니다.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload_data = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        
        # 'exp' 필드 (만료 시간) 검증
        exp = payload_data.get("exp")
        if exp is None or datetime.now(timezone.utc) > datetime.fromtimestamp(exp, tz=timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 'sub' 필드 (이메일) 검증
        email = payload_data.get("sub")
        if email is None:
            raise credentials_exception
            
    except (PyJWTError, ValidationError):
        raise credentials_exception

    # 여기서 반환된 이메일은 API 라우터에서 사용할 수 있습니다.
    # 우리는 이메일이 허용된 이메일과 같은지만 확인하면 됩니다.
    if email != settings.ALLOWED_ADMIN_EMAIL:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted",
        )
        
    return email