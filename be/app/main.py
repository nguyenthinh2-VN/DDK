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
# Import models để SQLAlchemy đăng ký bảng với Base.metadata
from app.models import scan_batch, scan_result, user, role, permission, role_permission, signature  # noqa: F401
from app.api import scan, auth, stats, signature as signature_api
from app.api.admin import users as admin_users
from app.api.admin import roles as admin_roles


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

import os
from fastapi.staticfiles import StaticFiles

# Mount uploads directory for static files
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


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
app.include_router(auth.router)
app.include_router(admin_users.router)
app.include_router(admin_roles.router)
app.include_router(stats.router)
app.include_router(signature_api.router)


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
