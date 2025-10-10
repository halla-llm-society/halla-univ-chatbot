# Prod Ai gunicorn.conf

# 워커 수
import multiprocessing
workers = multiprocessing.cpu_count() * 2 + 1

# 워커로 uvicorn 사용
worker_class = "uvicorn.workers.UvicornWorker"

# 챗봇 답변 속도에 따라 조절
timeout = 120

# 바인드 주소 및 포트 
bind = "0.0.0.0:8000"

# Docker 안에서는 포그라운드
daemon = False   