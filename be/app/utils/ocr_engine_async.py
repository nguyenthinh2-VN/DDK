"""
OCR Engine Async - Xử lý PaddleOCR-VL thông qua API Async (job-based).
Dùng cho Upload Batch (background). Trả về cấu trúc dựa trên Markdown.
"""

import re
import traceback
from pathlib import Path
from app.config.settings import settings

def _extract_table_html_async(markdown_text: str) -> str:
    match = re.search(r"(<table.*?</table>)", markdown_text, re.DOTALL | re.IGNORECASE)
    if match:
        html = match.group(1).replace("\\\\n", "<br>").replace("\\n", "<br>").replace("\n", "<br>")
        rows = re.findall(r"(<tr[^>]*>.*?</tr>)", html, re.DOTALL | re.IGNORECASE)
        for row in rows:
            if "總經理" in row or "Tổng Giám Đốc" in row or "tổng giám đốc" in row.lower():
                cells = re.findall(r"(<td[^>]*>)(.*?)(</td>)", row, re.DOTALL | re.IGNORECASE)
                new_row = row
                for start_td, content, end_td in cells:
                    labels = ["總經理", "Tổng Giám Đốc", "Tổng giám đốc", "出納", "Thủ quỹ", "Thủ qũy", "會計", "Kế toán"]
                    if not any(k in content for k in labels):
                        old_cell = f"{start_td}{content}{end_td}"
                        new_cell = f"{start_td}&nbsp;{end_td}"
                        new_row = new_row.replace(old_cell, new_cell)
                html = html.replace(row, new_row)
        return html
    return ""

def _parse_async_json(markdown_text: str, layout_boxes: list = None) -> dict:
    result = {
        "document_type": "advance_payment_slip",
        "info": {"don_vi": "", "ho_ten": "", "so_the": "", "chu_quan": ""},
        "line_items": [],
        "footer": {},
        "form_no": "",
        "ngay": ""
    }

    # 1. Header
    m_form = re.search(r"\b(\d{6})\b", markdown_text)
    result["form_no"] = m_form.group(1) if m_form else ""
    
    m_ngay = re.search(r"日期[：:]*\s*(\d{4}年\d{1,2}月\d{1,2}日)", markdown_text)
    result["ngay"] = m_ngay.group(1) if m_ngay else ""

    if layout_boxes:
        for box in layout_boxes:
            label = str(box.get("label", "")).lower()
            if label == "table":
                result["table_bbox"] = box.get("coordinate")
                result["table_score"] = box.get("score")

    # 2. Table parsing
    table_match = re.search(r"(<table.*?</table>)", markdown_text, re.DOTALL | re.IGNORECASE)
    if not table_match:
        return result

    table_content = table_match.group(1)
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table_content, re.DOTALL | re.IGNORECASE)

    if rows:
        cells_raw = re.findall(r"<(?:td|th)[^>]*>(.*?)</(?:td|th)>", rows[0], re.DOTALL | re.IGNORECASE)
        cells = [re.sub(r"<[^>]+>", " ", c).replace("\\n", " ").replace("\n", " ").strip() for c in cells_raw]
        
        info = {"don_vi": "", "ho_ten": "", "so_the": "", "chu_quan": ""}
        for i, cell in enumerate(cells):
            if any(k in cell for k in ["單位", "Đơn vị", "Don vi"]):
                val = re.sub(r"(?:單位|Đơn vị|Don vi)[：:]*\s*", "", cell, flags=re.IGNORECASE).strip()
                val_cells = [val] if val else []
                j = i + 1
                while j < len(cells) and not any(k in cells[j] for k in ["姓名", "Họ tên", "卡號", "Số thẻ", "主管", "Chủ quản"]):
                    if cells[j]: val_cells.append(cells[j])
                    j += 1
                info["don_vi"] = " ".join(val_cells).strip()
            elif any(k in cell for k in ["姓名", "Họ tên", "Ho ten"]):
                val = re.sub(r"(?:姓名|Họ tên|Ho ten)[：:]*\s*", "", cell, flags=re.IGNORECASE).strip()
                val_cells = [val] if val else []
                j = i + 1
                while j < len(cells) and not any(k in cells[j] for k in ["卡號", "Số thẻ", "主管", "Chủ quản"]):
                    if cells[j]: val_cells.append(cells[j])
                    j += 1
                info["ho_ten"] = " ".join(val_cells).strip()
            elif any(k in cell for k in ["卡號", "Số thẻ", "So the"]):
                val = re.sub(r"(?:卡號|Số thẻ|So the)[：:]*\s*", "", cell, flags=re.IGNORECASE).strip()
                if not val and i + 1 < len(cells):
                    next_cell = cells[i + 1]
                    if not any(k in next_cell for k in ["主管", "Chủ quản"]): val = next_cell
                if not info["so_the"]: info["so_the"] = val
            elif any(k in cell for k in ["主管", "Chủ quản", "Chu quan"]):
                val = re.sub(r"(?:主管|Chủ quản|Chu quan)[：:]*\s*", "", cell, flags=re.IGNORECASE).strip()
                if not val and i + 1 < len(cells): val = cells[i + 1]
                info["chu_quan"] = val
        result["info"] = info

    HEADER_KEYWORDS = ["序號", "項目", "用途說明", "數量單價", "單據號碼", "Hạng mục", "Mục đích", "Số lượng", "Số chứng"]
    _STT_LEAK_RE = re.compile(r"^\s*\d+[.。]\s*$")

    def _cell_clean(raw: str) -> str:
        text = re.sub(r"<[^>]+>", " ", raw)
        text = text.replace("\\n", "\n").replace("\\\\n", "\n")
        return text.strip()

    def _cell_parts(raw: str) -> list[str]:
        text = re.sub(r"<br\s*/?>", "\n", raw, flags=re.IGNORECASE)
        text = text.replace("\\n", "\n").replace("\\\\n", "\n")
        return [p.strip() for p in text.split("\n") if p.strip()]

    def _clean_hang_muc(raw: str) -> str:
        parts = _cell_parts(raw)
        filtered = [p for p in parts if not _STT_LEAK_RE.match(p)]
        return "\n".join(filtered).strip()

    line_items = []
    for row in rows[2:]:
        cells_raw = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL | re.IGNORECASE)
        if not cells_raw:
            continue
            
        cell_texts = [_cell_clean(c) for c in cells_raw]
        combined = " ".join(cell_texts)
        
        if "預支金額" in combined or "總經理" in combined or "Tổng Giám Đốc" in combined:
            for ct in cell_texts:
                clean = re.sub(r"[^0-9.,]", "", ct)
                if clean and len(clean) >= 3:
                    result["footer"] = {"so_tien_tam_ung": clean}
                    break
            continue
            
        if any(kw in combined for kw in HEADER_KEYWORDS):
            continue
            
        if len([t for t in cell_texts if t]) < 2:
            continue
            
        if len(cells_raw) >= 2:
            hang_muc = _clean_hang_muc(cells_raw[1]) if len(cells_raw) > 1 else ""
            muc_dich = "\n".join(_cell_parts(cells_raw[2])) if len(cells_raw) > 2 else ""
            so_luong = "\n".join(_cell_parts(cells_raw[3])) if len(cells_raw) > 3 else ""
            so_tien  = "\n".join(_cell_parts(cells_raw[4])) if len(cells_raw) > 4 else ""
            so_ct    = "\n".join(_cell_parts(cells_raw[5])) if len(cells_raw) > 5 else ""
            
            item = {
                "hang_muc": hang_muc,
                "muc_dich": muc_dich,
                "so_luong_don_gia": so_luong,
                "so_tien": so_tien,
                "so_chung_tu": so_ct,
            }
            if any(v for v in item.values()):
                line_items.append(item)

    result["line_items"] = line_items
    if "footer" not in result:
        result["footer"] = {}

    return result


def run_ocr_async(image_path: str, original_filename: str = "") -> dict:
    from app.utils.ocr_engine import _build_mock_result, _preprocess_if_enabled
    if not settings.OCR_ENABLED:
        return _build_mock_result(original_filename)

    processed = _preprocess_if_enabled(image_path)

    from app.ocr.paddleocr_vl_client import submit_job, poll_job, download_jsonl, PaddleOCRVLError
    token = settings.PADDLEOCR_VL_TOKEN
    
    try:
        job_id = submit_job(str(processed), token=token)
        data = poll_job(job_id, token=token)
        jsonl_url = data.get("resultUrl", {}).get("jsonUrl")
        if not jsonl_url:
            raise PaddleOCRVLError("Done but no jsonl resultUrl returned")
        results = download_jsonl(jsonl_url)
    except Exception as e:
        raise RuntimeError(f"Async API Failed: {e}")

    # Tải ảnh bbox nếu có
    bbox_image_url = None
    straightened_image_url = None
    try:
        import requests
        img_name = Path(image_path).name
        first_res = results[0].get("result", {}).get("layoutParsingResults", [])[0]
        output_imgs = first_res.get("outputImages", {})
        for img_key, img_url in output_imgs.items():
            try:
                r = requests.get(img_url, timeout=30)
                if r.status_code == 200:
                    img_path = Path(settings.UPLOAD_DIR) / f"async_{img_name}"
                    img_path.parent.mkdir(parents=True, exist_ok=True)
                    img_path.write_bytes(r.content)
                    bbox_image_url = f"/uploads/async_{img_name}"
                    break
            except Exception:
                pass
    except Exception:
        pass

    try:
        first_res = results[0].get("result", {}).get("layoutParsingResults", [])[0]
        markdown_text = first_res.get("markdown", {}).get("text", "")
        layout_boxes = first_res.get("layout_det_res", [])
    except (IndexError, AttributeError):
        markdown_text = ""
        layout_boxes = []

    ocr_json = _parse_async_json(markdown_text, layout_boxes)
    table_html = _extract_table_html_async(markdown_text)

    # Ghi đè HTML render chuẩn
    from app.utils.html_renderer import render_slip_html
    try:
        clean_html = render_slip_html(ocr_json)
        if "<tr>" in clean_html:
            table_html = clean_html
    except Exception:
        pass

    if bbox_image_url:
        ocr_json["bbox_image_url"] = bbox_image_url

    # Tích hợp S2T
    from app.utils.ocr_engine import _convert_s2t
    ocr_json = _convert_s2t(ocr_json)

    ocr_text = re.sub(r"<[^>]+>", "", markdown_text).strip()

    return {
        "ocr_text": ocr_text,
        "ocr_json": ocr_json,
        "ocr_raw_json": results,
        "html_content": table_html,
        "markdown": markdown_text,
        "confidence_avg": None,
        "processed_image_path": None,
    }
