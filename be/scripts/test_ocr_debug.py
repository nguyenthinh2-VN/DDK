
import sys
import json
import requests
from pathlib import Path

# Thêm thư mục root vào sys.path để import app.*
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from app.config.settings import settings
from app.ocr.preprocess import load_image, preprocess
import cv2

def run_debug(image_path: str):
    debug_dir = Path("debug")
    debug_dir.mkdir(exist_ok=True)
    
    print(f"--- BẮT ĐẦU DEBUG: {image_path} ---")
    
    # 2. Gọi PaddleOCR-VL Sync API
    print("2. Gọi PaddleOCR-VL Sync API...")
    token = settings.PADDLEOCR_VL_TOKEN
    if not token:
        print("   -> Lỗi: Chưa cấu hình PADDLEOCR_VL_TOKEN")
        return
        
    try:
        from app.ocr.paddleocr_vl_client import call_sync
        url = settings.PADDLEOCR_VL_SYNC_URL
        sync_result = call_sync(str(image_path), token=token, url=url)
        with open(debug_dir / "raw_result.json", "w", encoding="utf-8") as f:
            json.dump(sync_result, f, ensure_ascii=False, indent=2)
        print(f"   -> Đã lưu raw JSON tại: {debug_dir / 'raw_result.json'}")
    except Exception as e:
        print(f"   -> Lỗi gọi API: {e}")
        return

    # 3. Trích xuất ảnh output từ API
    print("3. Trích xuất ảnh Output từ API (như layout_det_res)...")
    found_image = False
    
    result = sync_result.get("result", {})
    for idx, res in enumerate(result.get("layoutParsingResults", [])):
        output_images = res.get("outputImages") or {}
        for img_name, img_url in output_images.items():
            print(f"   -> Đang tải ảnh từ API: {img_name}...")
            try:
                r = requests.get(img_url, timeout=30)
                if r.status_code == 200:
                    out_img_path = debug_dir / f"sync_{img_name}_{idx}.jpg"
                    out_img_path.write_bytes(r.content)
                    print(f"   -> Đã lưu ảnh API tại: {out_img_path}")
                    found_image = True
            except Exception as e:
                print(f"   -> Lỗi tải ảnh {img_name}: {e}")

    # Fallback: API Sync đôi khi không chứa outputImages, thử gọi Async
    if not found_image:
        print("\n   -> CẢNH BÁO: API Sync không trả về ảnh bbox (outputImages).")
        print("   -> Đang thử dùng API Async (để chắc chắn lấy được ảnh bbox)...")
        from app.ocr.paddleocr_vl_client import submit_job, poll_job, download_jsonl
        try:
            job_id = submit_job(str(image_path), token=token)
            print(f"   -> Đã submit Async Job: {job_id}")
            data = poll_job(job_id, token=token)
            jsonl_url = (data.get("resultUrl") or {}).get("jsonUrl")
            async_results = download_jsonl(jsonl_url)
            for entry in async_results:
                result = entry.get("result", {})
                for idx, res in enumerate(result.get("layoutParsingResults", [])):
                    output_images = res.get("outputImages") or {}
                    for img_name, img_url in output_images.items():
                        print(f"   -> Đang tải ảnh từ Async API: {img_name}...")
                        r = requests.get(img_url, timeout=30)
                        if r.status_code == 200:
                            out_img_path = debug_dir / f"async_{img_name}_{idx}.jpg"
                            out_img_path.write_bytes(r.content)
                            print(f"   -> Đã lưu ảnh Async API tại: {out_img_path}")
        except Exception as e:
            print(f"   -> Lỗi khi dùng Async API: {e}")
                        
    print("--- HOÀN TẤT DEBUG ---")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Cách dùng: python scripts/test_ocr_debug.py <đường_dẫn_ảnh>")
        sys.exit(1)
    run_debug(sys.argv[1])
