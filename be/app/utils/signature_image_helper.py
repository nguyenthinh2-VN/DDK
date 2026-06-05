"""
Helper xu ly anh chu ky.
"""

import uuid
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from app.config.settings import settings


def validate_signature_extension(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in settings.signature_allowed_extensions_list


def validate_signature_file_size(file_content: bytes) -> bool:
    return len(file_content) <= settings.signature_max_file_size_bytes


def get_signature_directories() -> tuple[Path, Path]:
    base_dir = Path(settings.SIGNATURE_UPLOAD_DIR)
    original_dir = base_dir / "original"
    processed_dir = base_dir / "processed"
    original_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    return original_dir, processed_dir


def save_signature_original(file_content: bytes, original_filename: str) -> tuple[str, str]:
    original_dir, _ = get_signature_directories()
    ext = Path(original_filename).suffix.lower() or ".png"
    stored_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = original_dir / stored_filename
    file_path.write_bytes(file_content)
    return stored_filename, str(file_path)


def save_signature_without_background_processing(
    input_path: str, output_name: str | None = None
) -> str:
    _, processed_dir = get_signature_directories()
    output_filename = output_name or f"{uuid.uuid4().hex}.png"
    output_path = processed_dir / output_filename

    with Image.open(input_path) as image:
        rgba = image.convert("RGBA")
        rgba.save(output_path, format="PNG")

    return str(output_path)


def remove_background_signature(input_path: str, output_name: str | None = None) -> str:
    _, processed_dir = get_signature_directories()
    output_filename = output_name or f"{uuid.uuid4().hex}.png"
    output_path = processed_dir / output_filename

    image = cv2.imread(input_path, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Cannot read signature image")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary_inv = cv2.threshold(
        blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(binary_inv, cv2.MORPH_OPEN, kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)

    b, g, r = cv2.split(image)
    rgba = cv2.merge((b, g, r, cleaned))
    cv2.imwrite(str(output_path), rgba)
    return str(output_path)


def delete_file_if_exists(file_path: str | None) -> None:
    if not file_path:
        return
    path = Path(file_path)
    if path.exists() and path.is_file():
        path.unlink()


def path_to_public_url(file_path: str) -> str:
    normalized = file_path.replace("\\", "/")
    if normalized.startswith("uploads/"):
        return f"/{normalized}"
    uploads_index = normalized.find("uploads/")
    if uploads_index >= 0:
        return f"/{normalized[uploads_index:]}"
    return normalized
