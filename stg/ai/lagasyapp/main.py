from fastapi import FastAPI
from .api.routes import router

app = FastAPI(title="Chatbot AI Service")

app.include_router(router, prefix="/api")

@app.get("/")
async def root():
    return {
        "server": "staging", 
        "service": "ai", 
        "status": "ok"
    }