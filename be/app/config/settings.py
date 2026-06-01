"""
Application Settings - Đọc cấu hình từ .env file.

Tương đương: application.properties / application.yml trong Spring Boot.
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Cấu hình toàn cục của ứng dụng."""

    # ── App ──────────────────────────────────────────
    APP_NAME: str = "DDK-OCR-Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ── Server ───────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Database ─────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./ddk_ocr.db"

    # ── Upload ───────────────────────────────────────
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: str = ".jpg,.jpeg,.png,.bmp,.tiff,.pdf"

    @property
    def allowed_extensions_list(self) -> list[str]:
        """Trả về danh sách extension được phép upload."""
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        """Trả về max file size tính bằng bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton instance - import settings từ đây để dùng chung
settings = Settings()
