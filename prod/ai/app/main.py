import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

# CloudWatch용 로깅 설정 (stdout으로 출력)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
# 외부 라이브러리 로그 레벨 조정 (너무 많은 로그 방지)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("pymongo").setLevel(logging.WARNING)  # MongoDB heartbeat 로그 숨김
logging.getLogger("pymongo.topology").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.info("AI 서버 시작")

origins = [
    "http://localhost",
    "http://localhost:80",
    "https://localhost",
    "https://localhost:443",

    "http://chatbot.o-r.kr",
    "https://chatbot.o-r.kr",
    "http://www.chatbot.o-r.kr",
    "https://www.chatbot.o-r.kr",

    "http://3.34.181.25",
    "http://3.34.181.25:80",
    "https://3.34.181.25",
    "https://3.34.181.25:443",
]

app = FastAPI(title="Chatbot API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "chatbot project access"}