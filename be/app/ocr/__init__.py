"""
OCR Package - Pipeline OCR cho phiếu DDK.

Quy trình tối giản (xem app/utils/ocr_engine.run_ocr):
    Upload ảnh → (tùy chọn) OpenCV preprocess → PaddleOCR-VL API → kết quả.

Modules:
    preprocess.py            - tiền xử lý ảnh bằng OpenCV (tùy chọn)
    paddleocr_vl_client.py   - client gọi PaddleOCR-VL API (aistudio)
"""
