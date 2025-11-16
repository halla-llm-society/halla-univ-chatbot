#------------------------
# 1. 프론트엔드 빌드    
#------------------------
FROM node:18-alpine AS frontend-builder
WORKDIR /app

# 환경 변수 등록
ARG VITE_GOOGLE_CLIENT_ID
ENV VITE_GOOGLE_CLIENT_ID=${VITE_GOOGLE_CLIENT_ID}

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build


#-------------------
# 2. 백엔드 빌드    
#-------------------
FROM python:3.11-slim
WORKDIR /app

# uv 설치
RUN pip install --no-cache-dir uv

# pyproject.toml 복사
COPY backend/pyproject.toml ./

# uv.lock 파일 toml 기반에서 pip 기반으로 변경
RUN uv pip compile pyproject.toml -o uv.lock

# 의존성 설치
RUN uv pip sync uv.lock --link-mode=copy --system

# 백엔드 코드 복사
COPY backend/app ./app

# 프론트엔드 빌드 결과물 복사
COPY --from=frontend-builder /app/dist ./static

# 비루트 사용자 생성 및 권한 설정
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# 컨테이너 포트 
EXPOSE 8000

# 컨테이너 실행 명령
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "3"]
