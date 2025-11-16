from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

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