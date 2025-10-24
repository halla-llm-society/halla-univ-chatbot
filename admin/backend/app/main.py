from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from app.api import routers  

app = FastAPI(title="Chatbot Admin Service")

# origins = [
#     ["*"]
# ]

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routers.router)

#------------------------------------------------
# 프론트엔드 파일 서빙(Docker, Local 구분)                  
#------------------------------------------------

# Docker 컨테이너 내부 경로: /app/static
docker_frontend_path = Path(__file__).parent.parent / "static"

# 로컬 개발 환경 경로: ../../frontend/dist
local_frontend_path = Path(__file__).parent.parent.parent / "frontend" / "dist"

FRONTEND_PATH = None

# 유효한 경로 대입
if docker_frontend_path.exists():
    FRONTEND_PATH = docker_frontend_path
elif local_frontend_path.exists():
    FRONTEND_PATH = local_frontend_path

# 에셋 폴더 마운트
app.mount(
    "/admin/assets", 
    StaticFiles(directory=FRONTEND_PATH / "assets"), 
    name="admin/assets"
)

# 접속 테스트
@app.get("/health")
def root():
    return {
        "service": "admin",
        "status": "ok"
    }

# 파일이 있으면 그대로 return, 없으면 react app에 위임
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    file_path = FRONTEND_PATH / full_path

    if file_path.is_file():
        return FileResponse(file_path)
    else:
        return FileResponse(FRONTEND_PATH / "index.html")