# Prod Backend gunicorn.conf

# 워커 수
import multiprocessing
workers = multiprocessing.cpu_count() * 2 + 1

# 워커로 uvicorn 사용
worker_class = "uvicorn.workers.UvicornWorker"

# 서버 속도에 따라 조절
timeout = 60

# 바인드 주소 및 포트 
bind = "0.0.0.0:8000"

# Docker 안에서는 포그라운드
daemon = False   

# 로그
accesslog = "-"            
errorlog = "-"             
capture_output = True     
loglevel = "info"         
enable_stdio_inheritance = True 