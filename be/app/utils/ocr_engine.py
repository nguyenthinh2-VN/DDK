"""
OCR Engine - Điểm vào thống nhất cho OCR.

Pipeline đơn giản:
    Upload ảnh → (tùy chọn) OpenCV preprocess → Gọi PaddleOCR-VL API → Trả kết quả.

Khi OCR_ENABLED=false → trả mock (chạy luồng upload/batch mà không gọi API).
"""

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
    except Exception as e:
        print(f"Lỗi chuyển đổi S2T: {e}")
        
    return ocr_json
