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


def _extract_fields_from_markdown(markdown_text: str, layout_boxes: list = None, parsing_res_list: list = None) -> dict:
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

    # Parse bbox từ layout_det_res (chỉ có label/coord/score)
    if layout_boxes:
        for box in layout_boxes:
            label = str(box.get("label", "")).lower()
            if label == "table":
                result["table_bbox"] = box.get("coordinate")
                result["table_score"] = box.get("score")

    # Parse bbox từ parsing_res_list (có block_content → match chính xác hơn)
    form_no_val = result.get("form_no", "")
    if parsing_res_list:
        for block in parsing_res_list:
            content = str(block.get("block_content", ""))
            label = str(block.get("block_label", "")).lower()
            bbox = block.get("block_bbox")  # [x_min, y_min, x_max, y_max]
            if not bbox:
                continue
            # form_no bbox: block text chứa 6 chữ số đó
            if form_no_val and form_no_val in content and "form_no_bbox" not in result:
                result["form_no_bbox"] = bbox
            # ngay bbox: block text chứa 日期
            if ("日期" in content) and "ngay_bbox" not in result:
                result["ngay_bbox"] = bbox
            # info/table bbox ưu tiên từ table block
            if label == "table" and "table_bbox" not in result:
                result["table_bbox"] = bbox

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
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table_content, re.DOTALL | re.IGNORECASE)

    # Hàng đầu: info (單位, 姓名, 卡號, 主管) - label và value nằm ở 2 ô riêng nhau
    info = {}
    if rows:
        cells_raw = re.findall(r"<td[^>]*>(.*?)</td>", rows[0], re.DOTALL | re.IGNORECASE)
        cells = [re.sub(r"<[^>]+>", "", c).strip() for c in cells_raw]

        # Tìm vị trí của từng label rồi lấy ô tiếp theo làm value
        for i, cell in enumerate(cells):
            if any(k in cell for k in ["單位", "Đơn vị", "Don vi"]):
                # value ở ô kế tiếp
                val_cells = []
                j = i + 1
                while j < len(cells) and not any(k in cells[j] for k in ["姓名", "Họ tên", "卡號", "主管"]):
                    if cells[j]:
                        val_cells.append(cells[j])
                    j += 1
                info["don_vi"] = " ".join(val_cells).strip()
            elif any(k in cell for k in ["姓名", "Họ tên", "Ho ten"]):
                val_cells = []
                j = i + 1
                while j < len(cells) and not any(k in cells[j] for k in ["卡號", "Số thẻ", "主管"]):
                    if cells[j]:
                        val_cells.append(cells[j])
                    j += 1
                info["ho_ten"] = " ".join(val_cells).strip()
            elif any(k in cell for k in ["卡號", "Số thẻ", "So the"]):
                # value ở ô kế tiếp (bỏ qua nếu chứa label)
                j = i + 1
                val = cells[j] if j < len(cells) else ""
                val = re.sub(r"(?:卡號|Số thẻ|So the)[：:]*\s*", "", val, flags=re.IGNORECASE).strip()
                info["so_the"] = val
            elif any(k in cell for k in ["主管", "Chủ quản", "Chu quan"]):
                # value ở ô kế tiếp hoặc trong cùng ô sau label
                val = re.sub(r"(?:主管|Chủ quản|Chu quan)[：:]*\s*", "", cell, flags=re.IGNORECASE).strip()
                if not val and i + 1 < len(cells):
                    val = cells[i + 1]
                info["chu_quan"] = val

    result["info"] = info

    # Từ khóa nhận biết hàng header của bảng (để bỏ qua)
    HEADER_KEYWORDS = ["序號", "項目", "用途說明", "數量單價", "單據號碼", "Hạng mục", "Mục đích", "Số lượng", "Số chứng"]

    # Line items (bỏ qua hàng info [0] + hàng header [1], dùng HEADER_KEYWORDS làm guard thêm)
    line_items = []
    for row in rows[2:]:  # skip info row + header row
        cells_raw = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL | re.IGNORECASE)
        if not cells_raw:
            continue
        cell_texts = [re.sub(r"<[^>]+>", " ", c).strip() for c in cells_raw]
        combined = " ".join(cell_texts)
        # Kiểm tra có phải dòng footer
        if "預支金額" in combined or "總經理" in combined or "Tổng Giám Đốc" in combined:
            for ct in cell_texts:
                clean = re.sub(r"[^0-9.,]", "", ct)
                if clean and len(clean) >= 3:
                    result["footer"] = {"so_tien_tam_ung": clean}
                    break
            continue
        # Bỏ qua hàng header lọt vào
        if any(kw in combined for kw in HEADER_KEYWORDS):
            continue
        non_empty = [t for t in cell_texts if t]
        if len(non_empty) < 2:
            continue
        if len(cell_texts) >= 5:
            item = {
                "hang_muc": cell_texts[1] if len(cell_texts) > 1 else "",
                "muc_dich": cell_texts[2] if len(cell_texts) > 2 else "",
                "so_luong_don_gia": cell_texts[3] if len(cell_texts) > 3 else "",
                "so_tien": cell_texts[4] if len(cell_texts) > 4 else "",
                "so_chung_tu": cell_texts[5] if len(cell_texts) > 5 else "",
            }
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


def _convert_s2t(ocr_json: dict) -> dict:
    """Chuyển đổi giản thể sang phồn thể cho các trường văn bản."""
    if not settings.OCR_S2T_ENABLED:
        return ocr_json
    try:
        import opencc
        converter = opencc.OpenCC(settings.OCR_S2T_CONFIG)
        
        info = ocr_json.get("info", {})
        if "ho_ten" in info:
            info["ho_ten"] = converter.convert(info["ho_ten"])
        if "chu_quan" in info:
            info["chu_quan"] = converter.convert(info["chu_quan"])
            
        for item in ocr_json.get("line_items", []):
            if "hang_muc" in item:
                item["hang_muc"] = converter.convert(item["hang_muc"])
            if "muc_dich" in item:
                item["muc_dich"] = converter.convert(item["muc_dich"])
                
    except ImportError:
        pass
    return ocr_json


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
        call_sync,
    )

    # 1. (Tùy chọn) Preprocess
    processed = _preprocess_if_enabled(image_path)

    # 2. Gọi PaddleOCR-VL API
    token = settings.PADDLEOCR_VL_TOKEN
    if not token:
        raise RuntimeError("PADDLEOCR_VL_TOKEN chưa cấu hình trong .env")

    try:
        url = settings.PADDLEOCR_VL_SYNC_URL
        sync_result = call_sync(processed, token=token, url=url)
        results = [sync_result]
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
    bbox_image_url = ""
    straightened_image_url = ""
    layout_boxes = []
    if results:
        page_result = results[0].get("result", {})
        
        # Lấy ảnh nắn thẳng từ AI
        prep_imgs = page_result.get("preprocessedImages", [])
        if prep_imgs:
            straightened_image_url = prep_imgs[0]
            
        for layout in page_result.get("layoutParsingResults", []):
            markdown_text = layout.get("markdown", {}).get("text", "")
            output_images = layout.get("outputImages") or {}
            for img_name, img_url in output_images.items():
                if "layout" in img_name.lower() or "res" in img_name.lower():
                    bbox_image_url = img_url
                    break
            # Extract boxes from layout_det_res
            layout_det = layout.get("layout_det_res")
            if isinstance(layout_det, dict) and "boxes" in layout_det:
                layout_boxes = layout_det["boxes"]
            elif isinstance(layout_det, list):
                layout_boxes = layout_det
            # Extract parsing_res_list for content-based bbox matching
            pruned = layout.get("prunedResult") or {}
            parsing_res_list = pruned.get("parsing_res_list", [])
            break

    import requests
    import uuid
    
    # Download bbox image
    if bbox_image_url and bbox_image_url.startswith("http"):
        try:
            r = requests.get(bbox_image_url, timeout=30)
            if r.status_code == 200:
                img_name = f"bbox_{uuid.uuid4().hex[:8]}.jpg"
                img_path = Path(settings.UPLOAD_DIR) / img_name
                img_path.parent.mkdir(parents=True, exist_ok=True)
                img_path.write_bytes(r.content)
                bbox_image_url = f"/uploads/{img_name}"
        except Exception:
            pass

    table_html = _extract_table_html(markdown_text)
    ocr_json = _extract_fields_from_markdown(markdown_text, layout_boxes, parsing_res_list)
    
    if bbox_image_url:
        ocr_json["bbox_image_url"] = bbox_image_url
    if straightened_image_url:
        ocr_json["straightened_image_url"] = straightened_image_url
    
    # 4. Chuyển giản thể sang phồn thể
    ocr_json = _convert_s2t(ocr_json)
    
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
