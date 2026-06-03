"""
Image Preprocessing - Bước 1 trong pipeline OCR.

Chịu trách nhiệm: đọc ảnh, khử nhiễu, tăng tương phản, nhị phân hóa nhẹ.
KHÔNG xoay/căn chỉnh — việc đó để cho `orientation.py` và `alignment.py`.
"""

from __future__ import annotations

try:
    import cv2
    import numpy as np
    _CV2_OK = True
except ImportError:  # pragma: no cover
    _CV2_OK = False


def load_image(image_path: str):
    """Đọc ảnh từ đĩa, raise nếu không đọc được."""
    if not _CV2_OK:
        raise RuntimeError("OpenCV (cv2) chưa được cài đặt")
    img = cv2.imread(image_path)
    if img is None:
        raise RuntimeError(f"Không đọc được ảnh: {image_path}")
    return img


def to_grayscale(img):
    """Chuyển BGR → grayscale (giữ nét chữ rõ hơn)."""
    if len(img.shape) == 2:
        return img
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def denoise(gray):
    """Khử nhiễu nhẹ (giữ nét chữ)."""
    return cv2.fastNlMeansDenoising(gray, h=10)


def enhance_contrast(gray):
    """Tăng tương phản bằng CLAHE (adaptive histogram)."""
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def preprocess(img, *, denoise_enabled: bool = True, contrast_enabled: bool = True):
    """
    Pipeline tiền xử lý chuẩn (chưa xoay/căn chỉnh).

    Args:
        img: ảnh BGR (numpy array).
        denoise_enabled: bật khử nhiễu.
        contrast_enabled: bật CLAHE.

    Returns:
        Ảnh grayscale đã làm sạch (numpy array).
    """
    gray = to_grayscale(img)
    if denoise_enabled:
        gray = denoise(gray)
    if contrast_enabled:
        gray = enhance_contrast(gray)
    return gray
