"""
PaddleOCR-VL Scan - CLI để gọi API aistudio cho 1 file (local hoặc URL).

Cách dùng:
    py scripts/paddleocr_vl_scan.py <đường_dẫn_hoặc_url> [output_dir]

Token đọc từ env PADDLEOCR_VL_TOKEN, hoặc từ .env nếu có.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# UTF-8 stdout cho Windows console
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

from app.ocr.paddleocr_vl_client import run_paddleocr_vl  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    file_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"

    token = os.getenv("PADDLEOCR_VL_TOKEN")
    if not token:
        # Fallback: đọc từ .env
        env_path = Path(__file__).resolve().parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("PADDLEOCR_VL_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not token:
        print("❌ Thiếu PADDLEOCR_VL_TOKEN trong env hoặc .env")
        return 1

    print(f"🔍 Submit: {file_path}")
    info = run_paddleocr_vl(file_path, token=token, output_dir=output_dir)
    print(f"✅ Job: {info['job_id']}")
    print(f"📄 Markdown saved: {info['saved_markdown']}")
    print(f"📁 Output dir: {output_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
