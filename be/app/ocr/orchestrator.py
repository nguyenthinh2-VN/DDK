"""
OCR Orchestrator - Pipeline tổng hợp cho 1 ảnh phiếu.

Flow:
    Upload (image_path) → Preprocess → Orientation → Deskew → Template Alignment
    → Zone Crop (chỉ value_zone) → OCR (provider) → Post-Process (theo type)
    → JSON kết quả (KHÔNG có label, chỉ có giá trị thật)

Hợp đồng đầu ra:
    {
      "ocr_text":   str,               # text gộp các zone (debug)
      "ocr_json":   dict,              # JSON sạch, KHÔNG label, có per-field confidence
      "ocr_raw_json": list,            # log raw từng zone (debug)
      "confidence_avg": float | None,
      "processed_image_path": str,     # ảnh canvas đã căn (lưu lại để đối chiếu)
    }
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config.settings import settings
from app.ocr import debug as dbg
from app.ocr.alignment import CANON_H, CANON_W, align_to_template
from app.ocr.orientation import auto_rotate, deskew
from app.ocr.post_process import clean_value, extract_leading_date, number_to_int
from app.ocr.preprocess import load_image, preprocess
from app.ocr.providers import get_provider
from app.ocr.zone_extractor import Zone, extract_zones

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
_template_cache: dict[str, dict] = {}


def _load_template(document_type: str) -> dict:
    """Load template theo document_type (có cache)."""
    if document_type in _template_cache:
        return _template_cache[document_type]
    path = _TEMPLATES_DIR / f"{document_type}.json"
    with open(path, "r", encoding="utf-8") as f:
        tpl = json.load(f)
    _template_cache[document_type] = tpl
    return tpl


def _save_processed(canvas, original_filename: str) -> str:
    """Lưu canvas đã căn vào uploads/processed/ để đối chiếu."""
    import cv2

    out_dir = Path(settings.UPLOAD_DIR) / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(original_filename).stem or "scan"
    out_path = out_dir / f"{stem}_canvas.png"
    cv2.imwrite(str(out_path), canvas)
    return str(out_path)


def _make_field_value(zone: Zone, raw_text: str, conf: float | None) -> dict:
    """Build dict giá trị cho 1 ô (không có label)."""
    cleaned = clean_value(raw_text, zone.field_type)
    out: dict[str, Any] = {
        "value": cleaned,
        "confidence": conf if cleaned else None,
    }
    if zone.field_type == "number":
        out["value_int"] = number_to_int(cleaned)
    if zone.extra.get("leading_date") and cleaned:
        date, remainder = extract_leading_date(cleaned)
        if date:
            out["date"] = date
            out["value"] = remainder if remainder else cleaned
    return out


def _set_path(root: dict, path: str, value: dict) -> None:
    """
    Gán `value` vào `root` theo path dạng:
      "form_no", "info.ho_ten", "footer.so_tien_tam_ung",
      "line_items[0].so_tien"
    """
    parts: list = []
    for token in path.split("."):
        if "[" in token and token.endswith("]"):
            name, idx = token.split("[", 1)
            parts.append(name)
            parts.append(int(idx[:-1]))
        else:
            parts.append(token)

    node: Any = root
    for i, key in enumerate(parts):
        last = i == len(parts) - 1
        if isinstance(key, int):
            # Đảm bảo list đủ phần tử
            while len(node) <= key:
                node.append({})
            if last:
                node[key] = value
            else:
                node = node[key]
        else:
            if last:
                node[key] = value
            else:
                if key not in node or not isinstance(node[key], (dict, list)):
                    # Nếu phần tử kế tiếp là chỉ số → list, ngược lại dict
                    next_key = parts[i + 1]
                    node[key] = [] if isinstance(next_key, int) else {}
                node = node[key]


def run_pipeline(image_path: str, original_filename: str) -> dict:
    """
    Chạy pipeline OCR đầy đủ cho 1 ảnh phiếu.

    Returns: dict theo hợp đồng ở đầu file. KHÔNG raise nếu OCR trống — chỉ
    trả về JSON với value rỗng + confidence None.
    """
    document_type = settings.SCAN_DOC_TYPE_DEFAULT
    template = _load_template(document_type)

    # 1. Đọc ảnh
    img = load_image(image_path)

    # 2. Orientation 0/90/180/270 — TẮT mặc định vì heuristic chưa tin cậy.
    #    Khi user luôn upload đúng chiều thì bỏ qua bước này.
    applied_rotation = 0
    if settings.OCR_AUTO_ROTATE:
        img, applied_rotation = auto_rotate(img)

    # 3. Tiền xử lý sang grayscale + làm sạch
    gray = preprocess(
        img,
        denoise_enabled=settings.OCR_PREPROCESS_ENABLED,
        contrast_enabled=settings.OCR_PREPROCESS_ENABLED,
    )

    # 4. Deskew (nghiêng nhẹ)
    if settings.OCR_DESKEW_ENABLED:
        gray = deskew(gray)

    # 5. Căn về template canvas (perspective warp). Có thể tắt nếu cần.
    if settings.OCR_TEMPLATE_ALIGN:
        canvas, aligned = align_to_template(gray)
    else:
        import cv2  # noqa
        canvas = cv2.resize(gray, (CANON_W, CANON_H), interpolation=cv2.INTER_CUBIC)
        aligned = False

    # 6. Crop từng value_zone (đã có padding theo settings.OCR_PAD_X/Y)
    zones = extract_zones(canvas, template)

    # 6.b Debug: lưu canvas + canvas-with-boxes
    run_dir = dbg.get_run_dir(original_filename) if dbg.is_enabled() else None
    if run_dir is not None:
        dbg.save_aligned(canvas, run_dir)
        dbg.save_aligned_with_boxes(canvas, zones, run_dir)
        dbg.log_field(run_dir, [
            f"=== Scan: {original_filename} ===",
            f"Image: {image_path}",
            f"Rotation applied: {applied_rotation}",
            f"Template aligned: {aligned}",
            f"Canvas size: {canvas.shape[1]}x{canvas.shape[0]}",
            f"Provider: {(settings.OCR_PROVIDER or 'paddle').lower() if settings.OCR_ENABLED else 'mock'}",
            f"PAD_X={settings.OCR_PAD_X}, PAD_Y={settings.OCR_PAD_Y}, UPSCALE={settings.OCR_UPSCALE}",
            "",
        ])

    # 7. OCR từng vùng + 8. post-process
    provider = get_provider()
    raw_log: list[dict] = []
    ocr_json: dict[str, Any] = {
        "document_type": document_type,
        "line_items": [],
    }
    threshold = settings.OCR_CONFIDENCE_WARN_THRESHOLD
    low_conf: list[str] = []
    confs: list[float] = []
    text_parts: list[str] = []
    empty_count = 0

    upscale = settings.OCR_UPSCALE
    for zone in zones:
        crop = zone.image
        # Lưu crop debug TRƯỚC khi upscale để dễ kiểm tra tọa độ thật
        if run_dir is not None:
            dbg.save_crop(crop, zone.path, run_dir)

        # Upscale để OCR dễ đọc chữ nhỏ
        if (
            crop is not None and crop.size > 0
            and upscale and upscale != 1.0
        ):
            import cv2
            crop = cv2.resize(crop, None, fx=upscale, fy=upscale, interpolation=cv2.INTER_CUBIC)

        text, conf = provider.recognize(crop, zone.ocr_lang)

        # Log từng field (ngay cả khi tắt OCR_DEBUG cũng có raw_log đi vào DB)
        crop_shape = (crop.shape[0], crop.shape[1]) if crop is not None and crop.size > 0 else None
        if run_dir is not None:
            dbg.log_field(run_dir, dbg.format_field_log(
                zone.path, zone.box_px, crop_shape, text, conf,
            ))

        raw_log.append({
            "field": zone.path,
            "text": text,
            "confidence": conf,
            "lang": zone.ocr_lang,
            "box_px": zone.box_px,
            "crop_size": crop_shape,
        })
        field_value = _make_field_value(zone, text, conf)
        _set_path(ocr_json, zone.path, field_value)

        if field_value["value"]:
            text_parts.append(field_value["value"])
            if conf is not None:
                confs.append(conf)
                if conf < threshold:
                    low_conf.append(zone.path)
        else:
            empty_count += 1

    ocr_json["confidence_avg"] = (
        round(sum(confs) / len(confs), 4) if confs else None
    )
    ocr_json["low_confidence_fields"] = low_conf

    # Validation: nếu phần lớn field rỗng, đánh dấu nghi alignment hỏng
    total_zones = len(zones) or 1
    empty_ratio = empty_count / total_zones
    alignment_suspected_failed = (
        empty_ratio >= settings.OCR_EMPTY_FIELDS_THRESHOLD
    )

    # Metadata
    ocr_json["_meta"] = {
        "rotation_applied": applied_rotation,
        "template_aligned": aligned,
        "provider": (settings.OCR_PROVIDER or "paddle").lower() if settings.OCR_ENABLED else "mock",
        "total_zones": total_zones,
        "empty_zones": empty_count,
        "empty_ratio": round(empty_ratio, 4),
        "alignment_suspected_failed": alignment_suspected_failed,
    }

    if run_dir is not None:
        dbg.log_field(run_dir, [
            f"--- Summary ---",
            f"Total zones: {total_zones}",
            f"Empty zones: {empty_count} ({round(empty_ratio*100, 1)}%)",
            f"Confidence avg: {ocr_json['confidence_avg']}",
            f"Alignment suspected failed: {alignment_suspected_failed}",
        ])

    processed_path = _save_processed(canvas, original_filename)
    return {
        "ocr_text": "\n".join(text_parts),
        "ocr_json": ocr_json,
        "ocr_raw_json": raw_log,
        "confidence_avg": ocr_json["confidence_avg"],
        "processed_image_path": processed_path,
    }
