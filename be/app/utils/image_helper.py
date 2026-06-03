"""
Image Helper - Utility functions cho xử lý ảnh.

Tương đương: Utility/Helper class trong Spring.

Tầng Utils: chứa các hàm tiện ích dùng chung, không phụ thuộc business logic.
"""

import os
import uuid
from pathlib import Path

from app.config.settings import settings


def generate_unique_filename(original_filename: str) -> str:
    """Tạo tên file duy nhất để tránh trùng lặp khi upload."""
    ext = Path(original_filename).suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return unique_name


def validate_file_extension(filename: str) -> bool:
    """Kiểm tra extension file có được phép upload không."""
    ext = Path(filename).suffix.lower()
    return ext in settings.allowed_extensions_list


def validate_file_size(file_content: bytes) -> bool:
    """Kiểm tra dung lượng file không vượt quá giới hạn cấu hình."""
    return len(file_content) <= settings.max_file_size_bytes


def get_upload_path(filename: str) -> str:
    """Trả về đường dẫn đầy đủ để lưu file upload."""
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return str(upload_dir / filename)


async def save_upload_file(file_content: bytes, filename: str) -> str:
    """
    Lưu file upload vào thư mục uploads.

    Returns:
        Đường dẫn file đã lưu.
    """
    unique_filename = generate_unique_filename(filename)
    file_path = get_upload_path(unique_filename)

    with open(file_path, "wb") as f:
        f.write(file_content)

    return file_path
