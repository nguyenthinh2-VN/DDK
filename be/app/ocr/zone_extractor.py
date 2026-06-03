"""
Zone Extractor - Bước 4 trong pipeline OCR.

Chịu trách nhiệm: từ ảnh đã căn (canvas chuẩn) + template, **CHỈ crop value_zone**
của từng field (KHÔNG crop label_zone). Trả danh sách "zone" để OCR.

BUSINESS RULE: label in sẵn KHÔNG bao giờ được OCR/đưa vào output. Vì vậy ở đây
ta chỉ sinh crop cho value_zone.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Any

from app.config.settings import settings

try:
    import cv2
    _CV2_OK = True
except ImportError:  # pragma: no cover
    _CV2_OK = False


@dataclass
class Zone:
    """1 vùng giá trị cần OCR."""

    path: str                 # đường dẫn field, vd "info.ho_ten" / "line_items[0].so_tien"
    field_type: str           # number | date | text | text_cn | text_mixed
    ocr_lang: str             # 'en' | 'chinese_cht'
    image: Any                # ảnh crop (numpy array)
    box_px: tuple             # (x0, y0, x1, y1) trên canvas SAU khi đã pad
    extra: dict = dc_field(default_factory=dict)  # vd {"leading_date": True}


def _rel_to_px(box: list, w: int, h: int, pad_x: int, pad_y: int) -> tuple[int, int, int, int]:
    """Đổi box tương đối [x0,y0,x1,y1] (0..1) → pixel với padding cấu hình."""
    x0 = max(int(box[0] * w) - pad_x, 0)
    y0 = max(int(box[1] * h) - pad_y, 0)
    x1 = min(int(box[2] * w) + pad_x, w)
    y1 = min(int(box[3] * h) + pad_y, h)
    return x0, y0, x1, y1


def _crop(canvas, box_px):
    x0, y0, x1, y1 = box_px
    return canvas[y0:y1, x0:x1]


def extract_zones(canvas, template: dict) -> list[Zone]:
    """
    Sinh danh sách Zone (chỉ value_zone) từ canvas + template.

    Hỗ trợ: header, info, footer (mỗi field có value_zone) và line_items
    (mỗi cột có x_range; y lấy theo region + row_count).

    Padding crop được lấy từ settings.OCR_PAD_X / OCR_PAD_Y.
    """
    h, w = canvas.shape[:2]
    pad_x = settings.OCR_PAD_X
    pad_y = settings.OCR_PAD_Y
    zones: list[Zone] = []

    def _add(path, spec, box):
        box_px = _rel_to_px(box, w, h, pad_x, pad_y)
        zones.append(Zone(
            path=path,
            field_type=spec.get("type", "text"),
            ocr_lang=spec.get("ocr_lang", "chinese_cht"),
            image=_crop(canvas, box_px),
            box_px=box_px,
            extra={k: spec[k] for k in ("leading_date",) if k in spec},
        ))

    # Header
    for key, spec in template.get("header", {}).items():
        if "value_zone" in spec:
            _add(key, spec, spec["value_zone"])

    # Info
    for key, spec in template.get("info", {}).items():
        if "value_zone" in spec:
            _add(f"info.{key}", spec, spec["value_zone"])

    # Footer
    for key, spec in template.get("footer", {}).items():
        if "value_zone" in spec:
            _add(f"footer.{key}", spec, spec["value_zone"])

    # Line items: value_zone = ô dữ liệu (toàn bộ chiều cao region, không có label trong ô)
    li = template.get("line_items", {})
    if li:
        region = li["region"]
        y_top, y_bot = region[1], region[3]
        row_count = max(int(li.get("row_count", 1)), 1)
        row_h = (y_bot - y_top) / row_count
        for row_idx in range(row_count):
            ry0 = y_top + row_idx * row_h
            ry1 = ry0 + row_h
            for col_key, col_spec in li.get("columns", {}).items():
                x0, x1 = col_spec["x_range"]
                _add(f"line_items[{row_idx}].{col_key}", col_spec, [x0, ry0, x1, ry1])

    return zones
