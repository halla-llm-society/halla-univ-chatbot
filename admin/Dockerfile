#------------------------
# 1. 프론트엔드 빌드    
#------------------------
FROM node:18-alpine AS frontend-builder
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build


#-------------------
# 2. 백엔드 빌드    
#-------------------
FROM python:3.11-slim
WORKDIR /app

# pip 업그레이드 및 pip-tools 설치
RUN pip install --no-cache-dir --upgrade pip pip-tools

# 의존성 정의 복사 및 requirements.txt 생성
# 도커가 pyproject.toml과 uv.lock을 인식하지 못하는 일이 종종 있어서, requirements.txt로 의존성 작성(추후 수정)
COPY backend/pyproject.toml ./
RUN pip-compile pyproject.toml --output-file=requirements.txt

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

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
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]