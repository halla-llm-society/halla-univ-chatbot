from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path


from app.api import conversations, surveys, stats,metrics

# ======================
# FastAPI 인스턴스
# ======================
app = FastAPI(title="Admin Dashboard API")

# ======================
# CORS 설정
# ======================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================
# API 라우터 등록
# ======================
app.include_router(conversations.router, prefix="/api")
app.include_router(surveys.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")

# ======================
# React 정적 파일 서빙
# ======================
FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    # /assets 정적 파일 서빙
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/")
    async def serve_spa():
        """루트 경로에서 React 앱의 index.html 반환"""
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{full_path:path}")
    async def serve_spa_paths(full_path: str):
        """
        모든 경로에서 React SPA 서빙
        API 경로가 아닌 경우 index.html 반환 (React Router 지원)
        """
        if full_path.startswith("api/"):
            return {"detail": "Not Found"}

        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(file_path)

        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/")
    def root():
        return {
            "status": "ok",
            "message": "Backend is running. Frontend build not found.",
            "note": "Run 'npm run build' in frontend directory"
        }
