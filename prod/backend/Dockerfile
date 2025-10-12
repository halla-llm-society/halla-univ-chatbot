# Prod Backend Dockerfile

# 베이스 이미지
FROM python:3.12.3-slim

# 작업 디렉토리 설정
WORKDIR /app

# pip 업그레이드 및 pip-tools 설치
RUN pip install --no-cache-dir --upgrade pip pip-tools

# 의존성 정의 복사 및 requirements.txt 생성
# 도커가 pyproject.toml과 uv.lock을 인식하지 못하는 일이 종종 있어서, requirements.txt로 의존성 작성(추후 수정)
COPY pyproject.toml ./
RUN pip-compile pyproject.toml --output-file=requirements.txt

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 비루트 사용자 생성 및 권한 설정
RUN useradd -m prod_ai_user && chown -R prod_ai_user:prod_ai_user /app
USER prod_ai_user

# 컨테이너 포트 
EXPOSE 8000

# 컨테이너 실행 명령
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app.main:app"]