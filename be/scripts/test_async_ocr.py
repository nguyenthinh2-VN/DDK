import asyncio
import os
import sys
import json
import io
from pathlib import Path

# Fix lỗi in tiếng Việt trên Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from app.config.settings import settings
from app.utils.ocr_engine import run_ocr

async def process_image_async(image_path: str):
    """Xử lý 1 ảnh qua hàm run_ocr gốc đã được sửa thành API bất đồng bộ"""
    print(f"[{os.path.basename(image_path)}] Đang chạy run_ocr...")
    try:
        # Chạy block IO bằng to_thread để không block loop
        original_filename = os.path.basename(image_path)
        result = await asyncio.to_thread(run_ocr, image_path, original_filename)
        
        table_html = result.get("html_content") or ""
        return image_path, {
            "status": "success",
            "ocr_json": result.get("ocr_json"),
            "has_html_table": bool(table_html),
            "html_preview_end": table_html[-300:] if len(table_html) > 300 else table_html # Xem đuôi HTML để check chữ ký đã rỗng chưa
        }
        
    except Exception as exc:
        return image_path, {"error": str(exc)}

async def main():
    if len(sys.argv) < 2:
        print("Sử dụng: python test_async_ocr.py <duong_dan_anh_1> <duong_dan_anh_2> ...")
        sys.exit(1)
        
    image_paths = sys.argv[1:]
    
    # Bỏ qua OpenCV (Preprocess) đúng như yêu cầu
    settings.OCR_PREPROCESS_ENABLED = False
    token = settings.PADDLEOCR_VL_TOKEN
    
    if not token:
        print("Lỗi: Chưa cấu hình PADDLEOCR_VL_TOKEN trong hệ thống/môi trường.")
        sys.exit(1)
        
    print(f"=== Bắt đầu gọi run_ocr song song {len(image_paths)} ảnh ===")
    
    # Tạo danh sách tasks
    tasks = [process_image_async(path) for path in image_paths]
    
    # Thực thi đồng thời (bất đồng bộ)
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    print("\n" + "="*50)
    print("KẾT QUẢ TEST ĐA LUỒNG")
    print("="*50)
    
    for path, res in results:
        print(f"\n--- FILE: {os.path.basename(path)} ---")
        if isinstance(res, Exception):
            print(f"LỖI FATAL: {str(res)}")
        else:
            print(json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
