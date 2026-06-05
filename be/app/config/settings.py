"""
Application Settings - doc cau hinh tu .env file.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Cau hinh toan cuc cua ung dung."""

    APP_NAME: str = "DDK-OCR-Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DATABASE_URL: str = "mysql+aiomysql://root:root@localhost:3306/ddk_ocr"

    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_use_a_long_random_string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    DEFAULT_LANGUAGE: str = "vi"
    SUPPORTED_LANGUAGES: str = "vi,tw"

    FIRST_ADMIN_USERNAME: str = "admin"
    FIRST_ADMIN_PASSWORD: str = "Admin@123"
    FIRST_ADMIN_FULLNAME: str = "System Administrator"

    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: str = ".jpg,.jpeg,.png,.bmp,.tiff,.pdf"
    SIGNATURE_UPLOAD_DIR: str = "uploads/signatures"
    SIGNATURE_MAX_FILE_SIZE_MB: int = 3
    SIGNATURE_ALLOWED_EXTENSIONS: str = ".jpg,.jpeg,.png"

    SCAN_BATCH_MIN_FILES: int = 1
    SCAN_BATCH_MAX_FILES: int = 5
    SCAN_DOC_TYPE_DEFAULT: str = "advance_payment_slip"

    OCR_ENABLED: bool = False
    OCR_PREPROCESS_ENABLED: bool = False
    OCR_S2T_ENABLED: bool = True
    OCR_S2T_CONFIG: str = "s2t"
    PADDLEOCR_VL_TOKEN: str = ""
    PADDLEOCR_VL_MODEL: str = "PaddleOCR-VL-1.6"
    PADDLEOCR_VL_SYNC_URL: str = "https://hanaj6q2m6oc0bpa.aistudio-app.com/layout-parsing"
    PADDLEOCR_VL_ASYNC_URL: str = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"

    @property
    def supported_languages_list(self) -> list[str]:
        return [lang.strip() for lang in self.SUPPORTED_LANGUAGES.split(",")]

    @property
    def allowed_extensions_list(self) -> list[str]:
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def signature_allowed_extensions_list(self) -> list[str]:
        return [ext.strip() for ext in self.SIGNATURE_ALLOWED_EXTENSIONS.split(",")]

    @property
    def signature_max_file_size_bytes(self) -> int:
        return self.SIGNATURE_MAX_FILE_SIZE_MB * 1024 * 1024

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
