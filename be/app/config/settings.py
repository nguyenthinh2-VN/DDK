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

    # ── Database (MySQL) ─────────────────────────────
    # Format: mysql+aiomysql://<user>:<password>@<host>:<port>/<db>
    DATABASE_URL: str = "mysql+aiomysql://root:root@localhost:3306/ddk_ocr"

    # ── Security / JWT ───────────────────────────────
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_use_a_long_random_string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 giờ

    # ── i18n ─────────────────────────────────────────
    DEFAULT_LANGUAGE: str = "vi"
    SUPPORTED_LANGUAGES: str = "vi,tw"

    # ── First Admin (dùng cho script create_admin) ───
    FIRST_ADMIN_USERNAME: str = "admin"
    FIRST_ADMIN_PASSWORD: str = "Admin@123"
    FIRST_ADMIN_FULLNAME: str = "System Administrator"

    @property
    def supported_languages_list(self) -> list[str]:
        """Trả về danh sách ngôn ngữ được hỗ trợ."""
        return [lang.strip() for lang in self.SUPPORTED_LANGUAGES.split(",")]

    # ── Upload ───────────────────────────────────────
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: str = ".jpg,.jpeg,.png,.bmp,.tiff,.pdf"

    # ── Scan / OCR ───────────────────────────────────
    SCAN_BATCH_MIN_FILES: int = 1
    SCAN_BATCH_MAX_FILES: int = 5
    SCAN_DOC_TYPE_DEFAULT: str = "advance_payment_slip"

    # ── OCR (PaddleOCR-VL API) ───────────────────────
    OCR_ENABLED: bool = False                 # False = mock; True = gọi PaddleOCR-VL API
    OCR_PREPROCESS_ENABLED: bool = False      # bật/tắt OpenCV preprocess trước khi gửi API
    OCR_S2T_ENABLED: bool = True              # chuyển giản thể sang phồn thể
    OCR_S2T_CONFIG: str = "s2t"
    PADDLEOCR_VL_TOKEN: str = ""              # Token aistudio (bắt buộc khi OCR_ENABLED=true)
    PADDLEOCR_VL_MODEL: str = "PaddleOCR-VL-1.6"
    PADDLEOCR_VL_SYNC_URL: str = "https://hanaj6q2m6oc0bpa.aistudio-app.com/layout-parsing"
    PADDLEOCR_VL_ASYNC_URL: str = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"

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
