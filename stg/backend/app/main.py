import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router 
from app.core.config import settings
from app.core.lifespan import lifespan

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Chatbot Backend Service",
    lifespan=lifespan,
    root_path=settings.ROOT_PATH
)

origins = [
    "http://localhost:5173", # local 프론트엔드 url
    "https://halla-chatbot.com", # prod, stg 프론트엔드 url
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

# 접속 테스트
@app.get("/")
async def root():
    return {
        "server": "staging",
        "service": "backend",
        "status": "ok"
    }