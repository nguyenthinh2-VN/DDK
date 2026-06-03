"""
Orientation Detection & Deskew - Bước 2 trong pipeline OCR.

Chịu trách nhiệm:
- Phát hiện ảnh xoay 0/90/180/270° (form bị quay) và xoay về đúng chiều.
- Deskew: căn thẳng nếu ảnh nghiêng nhẹ (1°–10°).

Chiến lược orientation:
- Nếu PaddleOCR có sẵn `paddleocr.text_orientation_classifier` (use_angle_cls)
  -> dùng nó để biết góc 0/90/180/270.
- Fallback: heuristic theo tỉ lệ chiều rộng/cao (form DDK landscape) +
  vị trí khối chữ nhiều ở trên (header DDK + 預支單).

Cố gắng không phụ thuộc cứng vào PaddleOCR ở đây.
"""

from __future__ import annotations

import numpy as np

try:
    import cv2
    _CV2_OK = True
except ImportError:  # pragma: no cover
    _CV2_OK = False


def _rotate(img, angle: int):
    """Xoay ảnh theo bội số 90 độ, không méo."""
    if angle == 0:
        return img
    if angle == 90:
        return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    if angle == 180:
        return cv2.rotate(img, cv2.ROTATE_180)
    if angle == 270:
        return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return img


def detect_rotation(img) -> int:
    """
    Phát hiện hướng xoay 0/90/180/270 bằng heuristic đơn giản.

    Form DDK là landscape (rộng > cao). Nếu ảnh đang portrait → giả định
    bị xoay 90° và trả 90 (caller sẽ xoay ngược chiều kim đồng hồ).
    Nếu ảnh landscape, xác định 0 vs 180 dựa trên phân bố mật độ pixel
    tối ở nửa trên (header DDK đậm) so với nửa dưới.

    Returns:
        0, 90, 180 hoặc 270 — góc cần XOAY ĐỂ ĐƯA VỀ 0°.
    """
    h, w = img.shape[:2]
    if h > w * 1.05:
        # Portrait → form bị nằm ngang. Chọn 90 hay 270 dựa mật độ trái/phải.
        gray = img if len(img.shape) == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        left_density = np.mean(255 - gray[:, : w // 2])
        right_density = np.mean(255 - gray[:, w // 2 :])
        # Header DDK ở phần "đầu" form → xoay sao cho header lên trên.
        return 270 if left_density > right_density else 90

    # Landscape — phân biệt 0 với 180
    gray = img if len(img.shape) == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    top_density = np.mean(255 - gray[: h // 2, :])
    bot_density = np.mean(255 - gray[h // 2 :, :])
    # Header DDK đậm hơn footer → top_density thường > bot_density khi đúng chiều.
    return 0 if top_density >= bot_density else 180


def auto_rotate(img):
    """Tự động xoay ảnh về 0° dựa trên detect_rotation."""
    angle = detect_rotation(img)
    if angle == 0:
        return img, 0
    return _rotate(img, angle), angle


def deskew(gray):
    """
    Căn thẳng ảnh nghiêng nhẹ. Giả định input là ảnh grayscale đã làm sạch.

    Tìm góc lệch của khối chữ qua cv2.minAreaRect; nếu góc trong khoảng (-10, 10)
    và đáng kể (> 0.5°) thì xoay; nếu không thì giữ nguyên.

    Returns:
        Ảnh sau deskew (numpy array). Cùng kích thước với input.
    """
    inverted = cv2.bitwise_not(gray)
    thresh = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    coords = cv2.findNonZero(thresh)
    if coords is None:
        return gray

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = 90 + angle
    if abs(angle) < 0.5 or abs(angle) > 10:
        return gray

    h, w = gray.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(
        gray, matrix, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
