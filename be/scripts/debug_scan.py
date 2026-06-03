"""
Debug Scan - Chạy pipeline OCR cho 1 ảnh + dump tất cả artefact debug.

Cách dùng:
    py scripts/debug_scan.py <đường_dẫn_ảnh> [--no-ocr]

Bật sẵn OCR_DEBUG=true trong process này. Sản phẩm:
    debug/<stem>/aligned.png
    debug/<stem>/aligned_with_boxes.png
    debug/<stem>/crops/<field>.png
    debug/<stem>/log.txt
    + JSON kết quả in ra stdout.

Tham số:
    --no-ocr  -> tắt OCR thật (dùng provider mock) để chỉ kiểm tra
                 alignment/crop mà không tải PaddleOCR.
"""

import json
import os
import sys
from pathlib import Path

# Đảm bảo OCR_DEBUG bật ngay từ trước khi load settings
os.environ.setdefault("OCR_DEBUG", "true")

# UTF-8 stdout (tránh lỗi UnicodeEncodeError trên Windows cp1252)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

if "--no-ocr" in sys.argv:
    os.environ["OCR_ENABLED"] = "false"
    sys.argv.remove("--no-ocr")

# Import sau khi đã set env
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.ocr import run_pipeline  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    image_path = sys.argv[1]
    if not Path(image_path).exists():
        print(f"❌ Không tìm thấy file: {image_path}")
        return 1

    print(f"🔍 Chạy pipeline cho: {image_path}")
    result = run_pipeline(image_path, Path(image_path).name)

    meta = (result.get("ocr_json") or {}).get("_meta", {})
    stem = Path(image_path).stem
    print(f"\n=== _meta ===")
    print(json.dumps(meta, ensure_ascii=False, indent=2))

    print(f"\n=== Field values (ocr_json) ===")
    j = result.get("ocr_json") or {}
    for k in ("form_no", "ngay"):
        if k in j:
            print(f"  {k}: {j[k]}")
    for k, v in (j.get("info") or {}).items():
        print(f"  info.{k}: {v}")
    for i, item in enumerate(j.get("line_items") or []):
        for k, v in item.items():
            print(f"  line_items[{i}].{k}: {v}")
    for k, v in (j.get("footer") or {}).items():
        print(f"  footer.{k}: {v}")

    print(f"\n📁 Debug artefacts: debug/{stem}/")
    print(f"   - aligned.png, aligned_with_boxes.png, crops/, log.txt")
    print(f"📁 Canvas đã căn:   {result.get('processed_image_path')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
