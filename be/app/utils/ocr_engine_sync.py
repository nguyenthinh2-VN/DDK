"""
OCR Engine Sync - Xử lý PaddleOCR-VL thông qua API Sync đơn luồng.
Dùng cho Upload Single. Trả về cấu trúc chi tiết, tận dụng parsing_res_list.
"""

import re
from pathlib import Path
from app.config.settings import settings

def _extract_table_html_sync(table_html_source: str) -> str:
    match = re.search(r"(<table.*?</table>)", table_html_source, re.DOTALL | re.IGNORECASE)
    if match:
        html = match.group(1).replace("\\n", "<br>").replace("\n", "<br>")
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

def _parse_sync_json(sync_result: dict) -> dict:
    result = {
        "document_type": "advance_payment_slip",
        "info": {"don_vi": "", "ho_ten": "", "so_the": "", "chu_quan": ""},
        "line_items": [],
        "footer": {},
        "form_no": "",
        "ngay": ""
    }

    # Trích xuất dữ liệu từ pruning
    layout_results = sync_result.get("result", {}).get("layoutParsingResults", [])
    if not layout_results:
        return result
        
    parsing_res_list = layout_results[0].get("prunedResult", {}).get("parsing_res_list", [])
    
    table_block_content = ""
    for block in parsing_res_list:
        label = block.get("block_label", "").lower()
        content = block.get("block_content", "")
        bbox = block.get("block_bbox")
        
        # Thử tìm form_no
        m_form_no = re.search(r"\b(\d{6})\b", content)
        if m_form_no and not result["form_no"]:
            result["form_no"] = m_form_no.group(1)
            result["form_no_bbox"] = bbox
            
        # Thử tìm ngày
        m_ngay = re.search(r"日期[：:]*\s*(\d{4}年\d{1,2}月\d{1,2}日)", content)
        if m_ngay and not result["ngay"]:
            result["ngay"] = m_ngay.group(1)
            result["ngay_bbox"] = bbox
            
        if label == "table":
            table_block_content = content
            result["table_bbox"] = bbox

    # Xử lý bảng HTML
    if not table_block_content:
        return result
        
    # Chuẩn hóa để split
    table_html = _extract_table_html_sync(table_block_content)
    
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table_block_content, re.DOTALL | re.IGNORECASE)
    if not rows:
        return result

    # 1. Info row
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

    # 2. Line Items
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

    return result, table_html

def run_ocr_sync(image_path: str, original_filename: str = "") -> dict:
    from app.utils.ocr_engine import _build_mock_result, _preprocess_if_enabled
    if not settings.OCR_ENABLED:
        return _build_mock_result(original_filename)

    processed = _preprocess_if_enabled(image_path)

    from app.ocr.paddleocr_vl_client import call_sync
    token = settings.PADDLEOCR_VL_TOKEN
    url = settings.PADDLEOCR_VL_SYNC_URL
    
    try:
        sync_result = call_sync(str(processed), token=token, url=url)
    except Exception as e:
        raise RuntimeError(f"Sync API Failed: {e}")
        
    ocr_json, table_html = _parse_sync_json(sync_result)
    
    # Render table UI chuẩn
    from app.utils.html_renderer import render_slip_html
    try:
        clean_html = render_slip_html(ocr_json)
        if "<tr>" in clean_html:
            table_html = clean_html
    except Exception:
        pass
        
    # Tích hợp S2T
    from app.utils.ocr_engine import _convert_s2t
    ocr_json = _convert_s2t(ocr_json)
    
    # Trích xuất Markdown để UI có text full
    markdown_text = ""
    try:
        markdown_text = sync_result.get("result", {}).get("layoutParsingResults", [])[0].get("markdown", {}).get("text", "")
    except Exception:
        pass
        
    ocr_text = re.sub(r"<[^>]+>", "", markdown_text).strip()
    
    return {
        "ocr_text": ocr_text,
        "ocr_json": ocr_json,
        "ocr_raw_json": [sync_result], # fake list array cho đồng bộ
        "html_content": table_html,
        "markdown": markdown_text,
        "confidence_avg": None,
        "processed_image_path": None,
    }
