"""
Main Application Entry Point - Khởi tạo FastAPI app.

Tương đương: @SpringBootApplication class trong Spring Boot.

File này là điểm khởi đầu của toàn bộ ứng dụng:
- Tạo FastAPI instance
- Đăng ký các Router (tương đương Spring component scan)
- Cấu hình CORS, middleware
- Khởi tạo database khi startup
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.database.base import Base
from app.database.connection import engine
from app.api import scan


# ── Startup / Shutdown Events ────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle hook - chạy khi app khởi động và tắt.
    Tương đương @PostConstruct / @PreDestroy trong Spring.
    """
    # Startup: Tạo tables nếu chưa có
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f"✅ {settings.APP_NAME} v{settings.APP_VERSION} started!")
    
    yield  # App đang chạy
    
    # Shutdown: cleanup
    await engine.dispose()
    print(f"🛑 {settings.APP_NAME} shutting down...")


# ── Create FastAPI App ───────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API scan giấy viết tay → HTML chỉnh sửa → Export PDF",
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc
    lifespan=lifespan,
)


# ── CORS Middleware ──────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # TODO: Giới hạn origins cho production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Register Routers (tương đương @ComponentScan) ───

app.include_router(scan.router)


# ── Root Endpoint ────────────────────────────────────

@app.get("/", tags=["Health Check"])
async def root():
    """Health check endpoint."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }
