# Prod AI Dockerfile

# 베이스 이미지
FROM python:3.12.3-slim

# 작업 디렉토리 설정
WORKDIR /app

# uv 설치
RUN pip install --no-cache-dir uv

# pyproject.toml 복사
COPY pyproject.toml ./

# uv.lock 파일 toml 기반에서 pip 기반으로 변경
RUN uv pip compile pyproject.toml -o uv.lock

# 의존성 설치
RUN uv pip sync uv.lock --link-mode=copy --system

# 애플리케이션 코드 복사
COPY . .

# 비루트 사용자 생성 및 권한 설정
RUN useradd -m prod_ai_user && chown -R prod_ai_user:prod_ai_user /app
USER prod_ai_user

# 컨테이너 포트 
EXPOSE 8000

# 컨테이너 실행 명령
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app.main:app"]
