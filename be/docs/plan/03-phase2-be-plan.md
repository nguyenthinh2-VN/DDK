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

### 2.3 Phân tích Bounding Box (bbox) từ PaddleOCR
Theo file `raw_result.json`, API của PaddleOCR-VL (Document Parsing mode) **không trả về tọa độ (bbox) cho từng ô (cell) trong bảng**, mà nó trả về:
1. Tọa độ của các đoạn text nằm ngoài bảng (như Số Phiếu, Ngày Tháng).
2. Tọa độ của **toàn bộ cái bảng** (Label: `table`).

**Giải pháp**: 
- BE sẽ sửa lại hàm `_extract_fields_from_markdown` trong `ocr_engine.py` để duyệt qua `layout_det_res.boxes` và lấy `coordinate`.
- BE sẽ gán `table_bbox` cho phần bảng, và `form_no_bbox`, `ngay_bbox` cho các field rời rạc.
- FE khi hover vào nguyên cái bảng sẽ sáng lên nguyên bảng trên ảnh gốc. Khi hover vào Ngày/Số Phiếu sẽ sáng đúng vùng đó. 

### 3. Tích hợp
- Cập nhật router trong `main.py` để nạp `stats` router.
