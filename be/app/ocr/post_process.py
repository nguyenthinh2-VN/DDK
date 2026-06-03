"""
Post-Processing - Bước 6 trong pipeline OCR.

Làm sạch giá trị OCR theo KIỂU dữ liệu (number / date / text / text_cn /
text_mixed). Mỗi field cố định 1 kiểu trong template.
"""

from __future__ import annotations

import re

# Sửa nhầm lẫn ký tự → chữ số (cho ô KIỂU SỐ). PaddleOCR/OCR.space hay đọc số
# viết tay thành chữ cái gần giống.
_NUMBER_MISREAD = str.maketrans({
    "O": "0", "o": "0", "D": "0", "Q": "0",
    "l": "1", "I": "1", "i": "1", "|": "1", "/": "1",
    "Z": "2", "z": "2",
    "S": "5", "s": "5",
    "G": "6",
    "T": "7",
    "B": "8",
    "g": "9", "q": "9",
})


def clean_number(text: str) -> str:
    """Ô số: chỉ giữ chữ số + `.,`; sửa misread chữ↔số."""
    if not text:
        return ""
    t = text.translate(_NUMBER_MISREAD)
    t = re.sub(r"[^0-9.,]", "", t)
    return t.strip(".,")


def number_to_int(cleaned: str) -> int | None:
    """Chuỗi số đã làm sạch → int (bỏ mọi dấu phân cách)."""
    digits = re.sub(r"[^0-9]", "", cleaned or "")
    return int(digits) if digits else None


def clean_date(text: str) -> str:
    """Ô ngày: giữ `0-9 / - . 年 月 日`."""
    if not text:
        return ""
    return re.sub(r"[^0-9/\-.年月日]", "", text).strip()


def clean_text(text: str) -> str:
    """Ô chữ: gọn khoảng trắng đầu/cuối + nội bộ."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def clean_value(text: str, field_type: str | None) -> str:
    """Phân nhánh theo kiểu field."""
    if field_type == "number":
        return clean_number(text)
    if field_type == "date":
        return clean_date(text)
    return clean_text(text)


def extract_leading_date(value: str) -> tuple[str | None, str]:
    """
    Tách ngày tháng ở ĐẦU chuỗi (vd '5/27 ...') ra.

    Returns:
        (date_or_None, remainder). Nếu không có ngày → (None, value).
    """
    if not value:
        return None, value
    m = re.match(r"\s*(\d{1,2}\s*[/\-.]\s*\d{1,2}(?:\s*[/\-.]\s*\d{2,4})?)\s*(.*)", value)
    if not m:
        return None, value
    date = re.sub(r"\s+", "", m.group(1))
    rest = (m.group(2) or "").strip()
    return date, rest
