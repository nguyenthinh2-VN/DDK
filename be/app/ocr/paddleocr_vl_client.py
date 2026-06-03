"""
PaddleOCR-VL API Client - Gọi dịch vụ aistudio (whole-image, không cắt zone).

Mục đích: tích hợp sẵn để DÙNG SAU. Hiện chưa wire vào pipeline zone-based —
gọi trực tiếp khi cần so sánh chất lượng hoặc khi muốn để API tự phân tích
toàn trang (PaddleOCR-VL hỗ trợ cả layout + table + chữ viết tay).

Endpoint: https://paddleocr.aistudio-app.com/api/v2/ocr/jobs
Mode: async — submit job → poll → tải JSONL kết quả + ảnh markdown.

Cách dùng (script): xem `scripts/paddleocr_vl_scan.py`.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests

import base64

JOB_URL = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"

class PaddleOCRVLError(RuntimeError):
    """Lỗi phát sinh khi gọi PaddleOCR-VL API."""


def submit_job(
    file_path_or_url: str,
    *,
    token: str,
    model: str = "PaddleOCR-VL-1.6",
    optional_payload: dict | None = None,
    timeout: int = 60,
) -> str:
    """Gửi job OCR. Trả về jobId."""
    headers = {"Authorization": f"bearer {token}"}
    optional_payload = optional_payload or {
        "useDocOrientationClassify": False,
        "useDocUnwarping": False,
        "useChartRecognition": False,
    }

    if str(file_path_or_url).startswith("http"):
        headers["Content-Type"] = "application/json"
        payload = {
            "fileUrl": file_path_or_url,
            "model": model,
            "optionalPayload": optional_payload,
        }
        resp = requests.post(JOB_URL, json=payload, headers=headers, timeout=timeout)
    else:
        if not os.path.exists(file_path_or_url):
            raise PaddleOCRVLError(f"File not found: {file_path_or_url}")
        data = {"model": model, "optionalPayload": json.dumps(optional_payload)}
        with open(file_path_or_url, "rb") as f:
            files = {"file": f}
            resp = requests.post(JOB_URL, headers=headers, data=data, files=files, timeout=timeout)

    if resp.status_code != 200:
        raise PaddleOCRVLError(f"Submit failed [{resp.status_code}]: {resp.text}")
    return resp.json()["data"]["jobId"]


def call_sync(
    file_path: str,
    *,
    token: str,
    url: str = "https://hanaj6q2m6oc0bpa.aistudio-app.com/layout-parsing",
    timeout: int = 60,
) -> dict:
    """Gọi Sync API. Trả về dict kết quả trực tiếp."""
    headers = {"Authorization": f"token {token}"}
    
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    b64_file = base64.b64encode(file_bytes).decode("utf-8")
    
    payload = {
        "file": b64_file,
        "fileType": 1
    }
    
    resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
    if resp.status_code != 200:
        raise PaddleOCRVLError(f"Sync API failed [{resp.status_code}]: {resp.text}")
        
    return resp.json()

def poll_job(
    job_id: str,
    *,
    token: str,
    poll_interval: float = 5.0,
    max_wait_seconds: int = 600,
) -> dict:
    """Polling đến khi job xong (hoặc fail). Trả về phần `data` của response."""
    headers = {"Authorization": f"bearer {token}"}
    deadline = time.time() + max_wait_seconds

    while True:
        resp = requests.get(f"{JOB_URL}/{job_id}", headers=headers, timeout=30)
        if resp.status_code != 200:
            raise PaddleOCRVLError(f"Poll failed [{resp.status_code}]: {resp.text}")
        data = resp.json()["data"]
        state = data.get("state")
        if state == "done":
            return data
        if state == "failed":
            raise PaddleOCRVLError(f"Job failed: {data.get('errorMsg')}")

        if time.time() > deadline:
            raise PaddleOCRVLError(f"Job timed out after {max_wait_seconds}s (state={state})")
        time.sleep(poll_interval)


def download_jsonl(jsonl_url: str) -> list[dict]:
    """Tải JSONL kết quả → list dict."""
    resp = requests.get(jsonl_url, timeout=120)
    resp.raise_for_status()
    out: list[dict] = []
    for line in resp.text.strip().split("\n"):
        if line.strip():
            out.append(json.loads(line))
    return out


def save_markdown_outputs(results: list[dict], output_dir: str | Path, original_image_path: str | None = None) -> list[str]:
    """
    Lưu kết quả markdown + ảnh đính kèm + HTML viewer ra `output_dir`.

    Returns: list các path file markdown đã lưu.
    """
    import re

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_md: list[str] = []
    page_num = 0

    for entry in results:
        result = entry.get("result") or {}
        for res in result.get("layoutParsingResults", []):
            md_text = res.get("markdown", {}).get("text", "")
            md_path = output_dir / f"doc_{page_num}.md"
            md_path.write_text(md_text, encoding="utf-8")
            saved_md.append(str(md_path))

            # HTML viewer: trích xuất bảng từ markdown rồi render HTML
            html_path = output_dir / f"doc_{page_num}.html"
            table_html = ""
            table_match = re.search(r"(<table.*?</table>)", md_text, re.DOTALL | re.IGNORECASE)
            if table_match:
                table_html = table_match.group(1).replace("\\n", "<br>")

            img_tag = ""
            if original_image_path:
                rel_img = os.path.relpath(original_image_path, str(output_dir)).replace("\\", "/")
                img_tag = f'<img src="{rel_img}" alt="Original" class="img-preview">'

            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OCR Result Preview</title>
    <style>
        body {{ font-family: Arial, sans-serif; background:#f4f7f6; padding:20px; }}
        .container {{ display:flex; gap:20px; max-width:1400px; margin:auto; }}
        .panel {{ flex:1; background:#fff; padding:20px; border-radius:8px; box-shadow:0 4px 6px rgba(0,0,0,0.1); overflow-x:auto; }}
        h2 {{ color:#333; text-align:center; }}
        table {{ width:100%; border-collapse:collapse; margin-top:20px; table-layout:fixed; }}
        th, td {{ border:1px solid #ddd !important; padding:12px; vertical-align:top; }}
        td:hover {{ background:#e9ecef !important; cursor:pointer; }}
        .img-preview {{ max-width:100%; height:auto; border:1px solid #ccc; }}
    </style>
</head>
<body>
    <h2>Kết quả PaddleOCR-VL</h2>
    <div class="container">
        <div class="panel">
            <h2>Bảng dữ liệu</h2>
            {table_html}
        </div>
        <div class="panel">
            <h2>Ảnh gốc</h2>
            {img_tag}
        </div>
    </div>
</body>
</html>"""
            html_path.write_text(html_content, encoding="utf-8")

            # Ảnh tham chiếu trong markdown
            for img_path_key, img_url in (res.get("markdown", {}).get("images") or {}).items():
                full = output_dir / img_path_key
                full.parent.mkdir(parents=True, exist_ok=True)
                try:
                    full.write_bytes(requests.get(img_url, timeout=120).content)
                except requests.RequestException:
                    continue

            # Output images (visualization)
            for img_name, img_url in (res.get("outputImages") or {}).items():
                try:
                    r = requests.get(img_url, timeout=120)
                    if r.status_code == 200:
                        (output_dir / f"{img_name}_{page_num}.jpg").write_bytes(r.content)
                except requests.RequestException:
                    continue

            page_num += 1

    return saved_md


def run_paddleocr_vl(
    file_path_or_url: str,
    *,
    token: str,
    output_dir: str | Path = "output",
    model: str = "PaddleOCR-VL-1.6",
) -> dict:
    """
    End-to-end: submit → poll → download. Trả về dict tóm tắt.

    Returns: { "job_id", "jsonl_url", "results": [...], "saved_markdown": [...] }
    """
    job_id = submit_job(file_path_or_url, token=token, model=model)
    data = poll_job(job_id, token=token)
    jsonl_url = (data.get("resultUrl") or {}).get("jsonUrl")
    if not jsonl_url:
        raise PaddleOCRVLError("Done but no jsonl resultUrl returned")
    results = download_jsonl(jsonl_url)
    # Truyền original image path để HTML viewer embed ảnh gốc bên cạnh bảng
    original_path = file_path_or_url if not str(file_path_or_url).startswith("http") else None
    saved = save_markdown_outputs(results, output_dir, original_image_path=original_path)
    return {
        "job_id": job_id,
        "jsonl_url": jsonl_url,
        "results": results,
        "saved_markdown": saved,
    }
