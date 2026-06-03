# Kế hoạch Phase 2: BE (Dashboard Stats & Static Files & Bbox Mapping)

## 1. Mục tiêu
- Cung cấp API thống kê cho Dashboard.
- Mở quyền truy cập file tĩnh (Static Files) để FE tải ảnh gốc và ảnh kết quả.
- Trích xuất tọa độ Bounding Box (`bbox`) từ JSON của PaddleOCR và map vào dữ liệu trả về cho FE.

## 2. Các công việc cần thực hiện

### 2.1 API Thống kê Dashboard
**Tạo file**: `app/api/stats.py`
**Endpoint**: `GET /api/stats/dashboard`
**Response**:
```json
{
  "total_uploaded_files": 120,
  "total_scanned_slips": 115,
  "total_failed_slips": 5
}
```
**Quyền**: Bất kỳ user đã đăng nhập nào (`scan:read`).

### 2.2 Phục vụ file tĩnh (Static Files)
- Trong `app/main.py`, thêm thư mục `uploads` vào `StaticFiles`:
```python
from fastapi.staticfiles import StaticFiles
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
```
Điều này cho phép FE gọi trực tiếp `http://localhost:8000/uploads/anh_1.jpg`.

### 2.3 Phân tích Bounding Box (bbox) và Ảnh Nhãn từ PaddleOCR
Theo file `raw_result.json`, API của PaddleOCR-VL (Document Parsing mode) **không trả về tọa độ (bbox) cho từng ô (cell) trong bảng**, mà nó trả về:
1. Tọa độ của các đoạn text nằm ngoài bảng (như Số Phiếu, Ngày Tháng).
2. Tọa độ của **toàn bộ cái bảng** (Label: `table`).
3. Điểm tin cậy (`score`) cho từng khối (block).
4. Đường dẫn ảnh đã được Paddle vẽ sẵn Bbox và nhãn (`outputImages.layout_det_res`).

**Giải pháp**: 
- BE sẽ sửa lại hàm `_extract_fields_from_markdown` trong `ocr_engine.py` để duyệt qua `layout_det_res.boxes`.
- Bóc tách tọa độ (`coordinate`) kèm **điểm tin cậy** (`score`). Gán `table_bbox` và `table_score` cho phần bảng, và tương tự với các field rời rạc.
- **Tự động tải ảnh Bbox**: Để tránh link ảnh tạm thời của aistudio hết hạn, Backend (`run_ocr`) sẽ tự động tải file ảnh `outputImages.layout_det_res` về lưu chung trong thư mục `uploads/` và trả về qua trường `bbox_image_url` cho FE sử dụng.

### 3. Tích hợp
- Cập nhật router trong `main.py` để nạp `stats` router.
