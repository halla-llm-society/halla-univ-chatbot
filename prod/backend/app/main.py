import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import routers

ROOT_PATH = os.getenv("ROOT_PATH", "") # stg용 root path
app = FastAPI(
    title="Chatbot Prod Backend Service",
    root_path=ROOT_PATH 
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

app.include_router(routers.router)

# 접속 테스트
@app.get("/")
async def root():
    return {
        "server": "prod",
        "service": "backend",
        "status": "ok"
    }