# 📄 API Specification - Scan & OCR

> Tài liệu API cho FE team tích hợp tính năng Upload ảnh, xử lý OCR và quản lý kết quả.
> Base URL: `http://localhost:8000`
> Tất cả API trong module này đều yêu cầu **Authentication (JWT Token)**.
> FE cần gửi header `Accept-Language: vi` hoặc `tw` để nhận thông báo đúng ngôn ngữ.

---

## 1. Upload & Xử lý OCR

### 1.1 Upload 1 Ảnh (Đơn luồng / Đồng bộ)
```
POST /api/scan/upload
Content-Type: multipart/form-data
```
**Quyền yêu cầu**: `scan:upload`

> Nhận vào 1 file ảnh, đẩy sang cho PaddleOCR xử lý và **chờ đến khi có kết quả mới trả về**.
> Sử dụng khi cần test nhanh hoặc luồng xử lý yêu cầu phản hồi ngay lập tức.

**Request Form-Data**
- `file`: 1 file ảnh (`.jpg`, `.jpeg`, `.png`, v.v.)

**Response** `200 OK`
Trả về ngay Object `ScanResultResponse` (tương tự như API 2.2).

---

### 1.2 Upload Batch (Đa luồng / Bất đồng bộ)
```
POST /api/scan/batch
Content-Type: multipart/form-data
```
**Quyền yêu cầu**: `scan:upload`

> Nhận vào từ 3 đến 5 ảnh. Hệ thống sẽ lưu file, tạo dữ liệu `batch`, và **trả về ngay lập tức** (HTTP 202). 
> Quá trình gọi AI (PaddleOCR-VL) diễn ra dưới nền. FE cần dùng `batch_id` để polling tiến độ ở API `1.3`.

**Request Form-Data**
- `files`: Mảng các file ảnh (Tối thiểu 3, tối đa 5). Hỗ trợ `.jpg`, `.jpeg`, `.png`, v.v.

**Response** `202 Accepted`
```json
{
  "batch_id": "b1234567-89ab-cdef-0123-456789abcdef",
  "total_files": 3,
  "status": "processing",
  "message": "Đã nhận 3 file, đang tiến hành OCR...",
  "items": [
    {
      "scan_id": "s1234567-...",
      "original_filename": "anh_1.jpg",
      "status": "pending"
    }
  ]
}
```

---

### 1.3 Polling tiến độ Batch
```
GET /api/scan/batch/{batch_id}
```
**Quyền yêu cầu**: `scan:read`

> FE gọi API này mỗi 3-5 giây để cập nhật trạng thái của Batch cho đến khi `status` là `completed` hoặc `failed`.

**Response** `200 OK`
```json
{
  "batch_id": "b1234567-...",
  "status": "completed",
  "total_files": 3,
  "completed_files": 3,
  "failed_files": 0,
  "items": [
    {
      "scan_id": "s1234567-...",
      "original_filename": "anh_1.jpg",
      "status": "completed",
      "confidence_avg": 0.95,
      "error_message": null
    }
  ]
}
```

---

## 2. Quản lý Danh sách & Chi tiết

### 2.1 Lấy danh sách kết quả (Summary)
```
GET /api/scan/
```
**Quyền yêu cầu**: `scan:read`

**Response** `200 OK`
```json
[
  {
    "id": "s1234567-...",
    "batch_id": "b1234567-...",
    "original_filename": "anh_1.jpg",
    "document_type": "advance_payment_slip",
    "status": "completed",
    "created_at": "2026-06-03T02:00:00"
  }
]
```

---

### 2.2 Lấy chi tiết một Phiếu (Kèm OCR Data)
```
GET /api/scan/{scan_id}
```
**Quyền yêu cầu**: `scan:read`

> Dùng để render màn hình So sánh Ảnh & Form dữ liệu.
> - `image_path`: Đường dẫn ảnh gốc.
> - `straightened_image_url`: (Trong `ocr_json`) Đường dẫn ảnh đã được AI nắn thẳng, có tọa độ bounding box khớp 100%.

**Response** `200 OK`
```json
{
  "id": "s1234567-...",
  "batch_id": "b1234567-...",
  "original_filename": "anh_1.jpg",
  "image_path": "uploads/abc.jpg",
  "status": "completed",
  "ocr_json": {
    "straightened_image_url": "uploads/straightened_abc.jpg",
    "info": { ... },
    "line_items": [ ... ]
  },
  "html_content": "<table>...</table>",
  "created_at": "2026-06-03T02:00:00"
}
```

---

## 3. Chỉnh sửa Dữ liệu (Update)

### 3.1 Cập nhật OCR JSON
```
PUT /api/scan/{scan_id}/json
Content-Type: application/json
```
**Quyền yêu cầu**: `scan:update`

> Khi user chỉnh sửa form dữ liệu trên UI, FE sẽ gom lại và gửi toàn bộ JSON mới lên đây để ghi đè.

**Request Body**
```json
{
  "ocr_json": {
    "info": { ... },
    "line_items": [ ... ]
  }
}
```
**Response** `200 OK` (Trả về toàn bộ object scan chi tiết sau khi cập nhật).

---

### 3.2 Cập nhật HTML Content
```
PUT /api/scan/{scan_id}/html
Content-Type: application/json
```
**Quyền yêu cầu**: `scan:update`

> Khi user sử dụng WYSIWYG Editor để tinh chỉnh bảng HTML.

**Request Body**
```json
{
  "html_content": "<table class='custom'>...</table>"
}
```
**Response** `200 OK` (Trả về object scan mới).

---

## 4. Export & Delete

### 4.1 Export ra PDF
```
POST /api/scan/{scan_id}/export-pdf
```
**Quyền yêu cầu**: `scan:read`

> Render `html_content` thành file PDF (Dùng thư viện WeasyPrint trên Backend).

**Response**
- Trả về trực tiếp File Binary (`application/pdf`). FE có thể dùng trình duyệt để tải xuống hoặc mở Tab mới (`window.open`).

---

### 4.2 Xóa một bản Scan
```
DELETE /api/scan/{scan_id}
```
**Quyền yêu cầu**: `scan:delete`

**Response** `200 OK`
```json
{
  "message": "Xóa kết quả scan thành công"
}
```

---

## 5. Phụ lục: JSON Demo từ AI (PaddleOCR)

Để AI Frontend hiểu rõ cấu trúc JSON trả về thực tế từ thư viện AI (giúp xây dựng UI Mapping chính xác), vui lòng xem file RAW JSON thực tế đang được lưu tại: 
👉 [be/debug/raw_result.json](file:///d:/DDK/be/debug/raw_result.json)

**Cấu trúc tóm tắt của raw_result.json**:
- `result.layoutParsingResults[0].markdown`: Chứa chuỗi Markdown kết quả (bao gồm thẻ `<table>` chứa HTML table).
- `result.layoutParsingResults[0].outputImages`: Chứa link ảnh đã bóc tách layout và bounding box (VD: `layout_det_res`).
- `result.preprocessedImages`: Chứa mảng link ảnh gốc đã được nắn thẳng góc xoay (`straightened_image_url`).

Hệ thống Backend đã parse tự động các thông tin này và đóng gói vào trường `ocr_json` trong API `2.2` (Chi tiết phiếu scan).
