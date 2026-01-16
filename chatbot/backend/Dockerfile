# 1. 베이스 이미지 설정
FROM python:3.12.3-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. uv 설치
RUN pip install --no-cache-dir uv

# 4. pyproject.toml 복사
COPY pyproject.toml ./

# 5. uv.lock 파일 toml 기반에서 pip 기반으로 변경
RUN uv pip compile pyproject.toml -o uv.lock

# 6. 의존성 설치 
RUN uv pip sync uv.lock --link-mode=copy --system

# 7. 애플리케이션 코드 복사
COPY . .

# 8. 비루트 사용자 생성 및 권한 설정
RUN useradd -m prod_backend_user && chown -R prod_backend_user:prod_backend_user /app
USER prod_backend_user

# 9. 컨테이너 포트 
EXPOSE 8000

# 10. 컨테이너 실행 명령
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app.main:app"]