"""
OCR Engine - Điểm vào thống nhất cho OCR.

Pipeline đơn giản:
    Upload ảnh → (tùy chọn) OpenCV preprocess → Gọi PaddleOCR-VL API → Trả kết quả.

PaddleOCR-VL (aistudio) xử lý toàn trang:
    - Orientation detection
    - Layout analysis + table recognition
    - OCR chữ viết tay (Trung phồn thể + Việt + English)
    - Trả Markdown (có bảng HTML) + JSON

Khi OCR_ENABLED=false → trả mock (chạy luồng upload/batch mà không gọi API).
"""

import re
from pathlib import Path

from app.config.settings import settings


def _preprocess_if_enabled(image_path: str) -> str:
    """Chạy OpenCV preprocess nếu bật. Trả đường dẫn ảnh (gốc hoặc đã xử lý)."""
    if not settings.OCR_PREPROCESS_ENABLED:
        return image_path
    try:
        from app.ocr.preprocess import load_image, preprocess
        import cv2

        img = load_image(image_path)
        gray = preprocess(img)
        out_dir = Path(settings.UPLOAD_DIR) / "processed"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{Path(image_path).stem}_processed.png"
        cv2.imwrite(str(out_path), gray)
        return str(out_path)
    except Exception:  # noqa: BLE001 — nếu preprocess lỗi, dùng ảnh gốc
        return image_path


def _extract_table_html(markdown_text: str) -> str:
    """Trích bảng HTML từ markdown output của PaddleOCR-VL."""
    match = re.search(r"(<table.*?</table>)", markdown_text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).replace("\\n", "<br>")
    return ""


def _extract_fields_from_markdown(markdown_text: str) -> dict:
    """
    Trích xuất các field phiếu tạm ứng từ markdown text của PaddleOCR-VL.

    PaddleOCR-VL trả bảng HTML + text trước bảng (header). Ta parse bảng để lấy
    giá trị user điền.
    """
    result: dict = {"document_type": "advance_payment_slip"}

    # Header fields trước bảng
    # form_no: tìm dãy 6 chữ số
    m = re.search(r"\b(\d{6})\b", markdown_text)
    result["form_no"] = m.group(1) if m else ""

    # Ngày
    m = re.search(r"日期[：:\s]*(.+?)(?:\n|$)", markdown_text)
    result["ngay"] = m.group(1).strip() if m else ""

    # Parse bảng HTML
    table_match = re.search(r"<table.*?>(.*?)</table>", markdown_text, re.DOTALL | re.IGNORECASE)
    if not table_match:
        result["info"] = {}
        result["line_items"] = []
        result["footer"] = {}
        return result

    table_content = table_match.group(1)
    # Lấy tất cả hàng
    rows = re.findall(r"<tr>(.*?)</tr>", table_content, re.DOTALL | re.IGNORECASE)

    # Hàng đầu: info (單位, 姓名, 卡號, 主管)
    info = {}
    if rows:
        cells = re.findall(r"<td[^>]*>(.*?)</td>", rows[0], re.DOTALL | re.IGNORECASE)
        for cell in cells:
            cell_text = re.sub(r"<[^>]+>", "\n", cell).strip()
            lines = [l.strip() for l in cell_text.split("\n") if l.strip()]
            if any("單位" in l or "Đơn vị" in l for l in lines):
                val = re.sub(r"(?:單位|Đơn vị|Don vi)[：:]*\s*", "", " ".join(lines), flags=re.IGNORECASE).strip()
                info["don_vi"] = val
            elif any("姓名" in l or "Họ tên" in l for l in lines):
                val = re.sub(r"(?:姓名|Họ tên|Ho ten)[：:]*\s*", "", " ".join(lines), flags=re.IGNORECASE).strip()
                info["ho_ten"] = val
            elif any("卡號" in l or "Số thẻ" in l for l in lines):
                val = re.sub(r"(?:卡號|Số thẻ|So the)[：:]*\s*", "", " ".join(lines), flags=re.IGNORECASE).strip()
                info["so_the"] = val
            elif any("主管" in l or "Chủ quản" in l for l in lines):
                val = re.sub(r"(?:主管|Chủ quản|Chu quan)[：:]*\s*", "", " ".join(lines), flags=re.IGNORECASE).strip()
                info["chu_quan"] = val
    result["info"] = info

    # Line items (bỏ qua hàng header và hàng cuối footer)
    line_items = []
    for row in rows[2:]:  # skip info row + header row
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL | re.IGNORECASE)
        if not cells:
            continue
        cell_texts = [re.sub(r"<[^>]+>", " ", c).strip() for c in cells]
        # Kiểm tra có phải dòng footer (預支金額 / 總經理)
        combined = " ".join(cell_texts)
        if "預支金額" in combined or "總經理" in combined or "Tổng Giám Đốc" in combined:
            # Footer: lấy số tiền tạm ứng
            for ct in cell_texts:
                clean = re.sub(r"[^0-9.,]", "", ct)
                if clean and len(clean) >= 3:
                    result["footer"] = {"so_tien_tam_ung": clean}
                    break
            continue
        # Line item bình thường
        if len(cell_texts) >= 5:
            item = {
                "hang_muc": cell_texts[1] if len(cell_texts) > 1 else "",
                "muc_dich": cell_texts[2] if len(cell_texts) > 2 else "",
                "so_luong_don_gia": cell_texts[3] if len(cell_texts) > 3 else "",
                "so_tien": cell_texts[4] if len(cell_texts) > 4 else "",
                "so_chung_tu": cell_texts[5] if len(cell_texts) > 5 else "",
            }
            # Chỉ thêm nếu có ít nhất 1 giá trị
            if any(v for v in item.values()):
                line_items.append(item)

    result["line_items"] = line_items
    if "footer" not in result:
        result["footer"] = {}

    return result


def _build_mock_result(filename: str) -> dict:
    """Mock kết quả (khi OCR_ENABLED=false)."""
    return {
        "ocr_text": "[MOCK] OCR chưa bật (OCR_ENABLED=false).",
        "ocr_json": {
            "document_type": "advance_payment_slip",
            "form_no": "",
            "ngay": "",
            "info": {"don_vi": "", "ho_ten": "", "so_the": "", "chu_quan": ""},
            "line_items": [],
            "footer": {},
            "_mock": True,
        },
        "ocr_raw_json": [],
        "html_content": "",
        "markdown": "",
        "confidence_avg": None,
        "processed_image_path": None,
    }


def run_ocr(image_path: str, original_filename: str) -> dict:
    """
    Pipeline OCR cho 1 ảnh phiếu.

    Flow: (tùy chọn) preprocess → PaddleOCR-VL API → parse markdown → JSON.

    Returns:
        {
            "ocr_text": str,            # text thô (plain)
            "ocr_json": dict,           # structured fields (chỉ giá trị user điền)
            "ocr_raw_json": list,       # raw JSONL từ API
            "html_content": str,        # HTML bảng từ API markdown
            "markdown": str,            # markdown gốc từ API
            "confidence_avg": None,     # API không trả confidence per-field
            "processed_image_path": str | None,
        }
    """
    if not settings.OCR_ENABLED:
        return _build_mock_result(original_filename)

    from app.ocr.paddleocr_vl_client import (
        PaddleOCRVLError,
        download_jsonl,
        poll_job,
        submit_job,
    )

    # 1. (Tùy chọn) Preprocess
    processed = _preprocess_if_enabled(image_path)

    # 2. Gọi PaddleOCR-VL API
    token = settings.PADDLEOCR_VL_TOKEN
    if not token:
        raise RuntimeError("PADDLEOCR_VL_TOKEN chưa cấu hình trong .env")

    try:
        job_id = submit_job(processed, token=token)
        data = poll_job(job_id, token=token)
        jsonl_url = (data.get("resultUrl") or {}).get("jsonUrl")
        if not jsonl_url:
            raise PaddleOCRVLError("API trả done nhưng thiếu jsonUrl")
        results = download_jsonl(jsonl_url)
    except (PaddleOCRVLError, Exception) as exc:
        # Nếu API lỗi, trả kết quả rỗng + error
        return {
            "ocr_text": "",
            "ocr_json": {
                "document_type": "advance_payment_slip",
                "form_no": "", "ngay": "",
                "info": {}, "line_items": [], "footer": {},
                "_error": str(exc),
            },
            "ocr_raw_json": [],
            "html_content": "",
            "markdown": "",
            "confidence_avg": None,
            "processed_image_path": processed if processed != image_path else None,
        }

    # 3. Parse kết quả
    markdown_text = ""
    if results:
        page_result = results[0].get("result", {})
        for layout in page_result.get("layoutParsingResults", []):
            markdown_text = layout.get("markdown", {}).get("text", "")
            break

    table_html = _extract_table_html(markdown_text)
    ocr_json = _extract_fields_from_markdown(markdown_text)
    ocr_text = re.sub(r"<[^>]+>", "", markdown_text).strip()

    return {
        "ocr_text": ocr_text,
        "ocr_json": ocr_json,
        "ocr_raw_json": results,
        "html_content": table_html,
        "markdown": markdown_text,
        "confidence_avg": None,
        "processed_image_path": processed if processed != image_path else None,
    }
