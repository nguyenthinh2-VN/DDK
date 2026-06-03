"""
OCR Debug Tools - Lưu crop + ảnh đã căn vẽ box + log chi tiết.

Bật/tắt qua `settings.OCR_DEBUG`. Khi tắt, các hàm trở thành no-op.

Output:
    debug/<scan_stem>/aligned.png
    debug/<scan_stem>/aligned_with_boxes.png
    debug/<scan_stem>/crops/<field>.png
    debug/<scan_stem>/log.txt
"""

from __future__ import annotations

import logging
from pathlib import Path

from app.config.settings import settings

_logger = logging.getLogger("ocr.debug")

# Màu (BGR) cho từng nhóm field khi vẽ box debug
_COLORS = {
    "form_no": (0, 0, 255),       # đỏ
    "ngay": (0, 200, 0),          # xanh lá
    "info.don_vi": (0, 220, 220), # vàng
    "info.ho_ten": (200, 0, 200), # tím
    "info.so_the": (255, 100, 0), # cam
    "info.chu_quan": (255, 0, 0), # xanh dương
    "footer.so_tien_tam_ung": (0, 100, 255),
}
_COLOR_LINE_ITEM = (120, 120, 120)  # xám cho các cột line item
_COLOR_DEFAULT = (0, 0, 0)


def is_enabled() -> bool:
    """Có bật debug không?"""
    return bool(settings.OCR_DEBUG)


def get_run_dir(original_filename: str) -> Path:
    """Thư mục debug cho 1 lần scan: debug/<stem>/."""
    stem = Path(original_filename).stem or "scan"
    base = Path(settings.OCR_DEBUG_DIR) / stem
    (base / "crops").mkdir(parents=True, exist_ok=True)
    return base


def color_for(path: str) -> tuple[int, int, int]:
    """Chọn màu vẽ box cho 1 field path."""
    if path in _COLORS:
        return _COLORS[path]
    if path.startswith("line_items"):
        return _COLOR_LINE_ITEM
    return _COLOR_DEFAULT


def save_aligned(canvas, run_dir: Path) -> None:
    """Lưu ảnh canvas đã căn (chưa vẽ box)."""
    if not is_enabled():
        return
    import cv2

    cv2.imwrite(str(run_dir / "aligned.png"), canvas)


def save_aligned_with_boxes(canvas, zones, run_dir: Path) -> None:
    """Vẽ tất cả value_zone lên canvas và lưu để kiểm tra tọa độ."""
    if not is_enabled():
        return
    import cv2

    # Convert grayscale → BGR để vẽ màu
    if len(canvas.shape) == 2:
        viz = cv2.cvtColor(canvas, cv2.COLOR_GRAY2BGR)
    else:
        viz = canvas.copy()

    for z in zones:
        x0, y0, x1, y1 = z.box_px
        color = color_for(z.path)
        cv2.rectangle(viz, (x0, y0), (x1, y1), color, 2)
        # Nhãn nhỏ ở góc trên-trái box
        cv2.putText(
            viz, z.path, (x0 + 2, max(y0 - 4, 12)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA,
        )

    cv2.imwrite(str(run_dir / "aligned_with_boxes.png"), viz)


def save_crop(crop, path: str, run_dir: Path) -> None:
    """Lưu 1 crop ra debug/<stem>/crops/<safe_name>.png."""
    if not is_enabled():
        return
    if crop is None or crop.size == 0:
        return
    import cv2

    safe = path.replace("/", "_").replace("[", "_").replace("]", "_").replace(".", "_")
    cv2.imwrite(str(run_dir / "crops" / f"{safe}.png"), crop)


def log_field(run_dir: Path, lines: list[str]) -> None:
    """Append nhiều dòng log vào log.txt của lần scan này."""
    if not is_enabled():
        return
    with open(run_dir / "log.txt", "a", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


def format_field_log(
    path: str, box_px: tuple, crop_shape: tuple | None,
    text: str | None, confidence: float | None,
) -> list[str]:
    """Sinh các dòng log mô tả 1 field theo định dạng yêu cầu."""
    lines = [f"Field: {path}", f"Box: {list(box_px)}"]
    if crop_shape is None:
        lines.append("Crop Empty")
        return lines + [""]
    h, w = crop_shape[:2]
    lines.append(f"Crop Size: {w}x{h}")
    if not text:
        lines.append("No OCR Result")
    else:
        lines.append(f"OCR Text: {text}")
    lines.append(f"Confidence: {confidence}")
    return lines + [""]
