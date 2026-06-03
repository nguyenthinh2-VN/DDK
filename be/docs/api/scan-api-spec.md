# Scan API Specification

Tài liệu mô tả các API endpoints phục vụ cho quá trình Upload ảnh phiếu (Scan), xử lý đa luồng bất đồng bộ, kiểm tra tiến độ, và lấy kết quả.

## 1. Upload Batch (Đa luồng / Bất đồng bộ)

**Endpoint:** `POST /api/scan/batch`
**Content-Type:** `multipart/form-data`

### Request:
- `files`: Danh sách các file ảnh (Tối thiểu 3, tối đa 5).

### Response (202 Accepted):
Trả về ngay lập tức để FE không bị treo.
```json
{
  "batch_id": "string (UUID)",
  "total_files": 3,
  "status": "pending",
  "items": [
    {
      "scan_id": "string (UUID)",
      "original_filename": "anh1.jpg",
      "status": "pending"
    },
    ...
  ],
  "message": "Đã nhận 3 file, đang xử lý."
}
```

---

## 2. Polling trạng thái Batch (Kiểm tra tiến độ)

**Endpoint:** `GET /api/scan/batch/{batch_id}`

Được FE gọi mỗi 2-3 giây để kiểm tra xem tiến trình xử lý đa luồng đã hoàn tất chưa.

### Response (200 OK):
```json
{
  "batch_id": "string (UUID)",
  "status": "completed", // pending | processing | completed | partial_failed
  "total_files": 3,
  "completed_files": 3,
  "failed_files": 0,
  "items": [
    {
      "scan_id": "string (UUID)",
      "original_filename": "anh1.jpg",
      "status": "completed",
      "confidence_avg": 0.98,
      "error_message": null
    },
    ...
  ]
}
```

---

## 3. Lấy chi tiết từng phiếu Scan (kèm kết quả OCR)

**Endpoint:** `GET /api/scan/{scan_id}`

Sau khi batch chuyển sang trạng thái `completed`, FE gọi API này để lấy thông tin chi tiết của phiếu (Bao gồm JSON và HTML preview) để hiển thị lên bảng.

### Response (200 OK):
```json
{
  "id": "string (UUID)",
  "batch_id": "string (UUID)",
  "original_filename": "anh1.jpg",
  "image_path": "uploads/anh1.jpg",
  "status": "completed",
  "document_type": "advance_payment_slip",
  "ocr_json": {
    "form_no": "000046",
    "ngay": "2025年01月06日",
    "info": {
      "don_vi": "kD",
      "ho_ten": "高翊庭",
      "so_the": "",
      "chu_quan": ""
    },
    "line_items": [
      {
        "hang_muc": "水合",
        "muc_dich": "5/27:\n因木左家\n我先走了",
        "so_luong_don_gia": "1.970.000",
        "so_tien": "2.700.000",
        "so_chung_tu": "5286"
      }
    ],
    "footer": { ... }
  },
  "html_content": "<table ...>...</table>",
  "created_at": "2026-06-03T09:00:00Z"
}
```

---

## 4. Chỉnh sửa OCR JSON

**Endpoint:** `PUT /api/scan/{scan_id}/json`
**Content-Type:** `application/json`

Lưu lại dữ liệu JSON của user sau khi đã chỉnh sửa trực tiếp trên giao diện FE.

### Request Body:
```json
{
  "ocr_json": {
    "form_no": "000046_SửaLại",
    "ngay": "...",
    ...
  }
}
```

### Response (200 OK):
Trả về toàn bộ object ScanResultResponse tương tự như GET `/api/scan/{scan_id}`.
