# 📡 API Specification - Scan OCR

> Tài liệu API cho FE team xây dựng giao diện.  
> Base URL: `http://localhost:8000`  
> Swagger UI: `http://localhost:8000/docs`

---

## 1. Health Check

```
GET /
```

**Response** `200 OK`
```json
{
  "app": "DDK-OCR-Service",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs"
}
```

---

## 2. Upload & Scan OCR

```
POST /api/scan/upload
Content-Type: multipart/form-data
```

**Request Body**
| Field | Type | Required | Mô tả |
|---|---|---|---|
| `file` | File | ✅ | File ảnh (.jpg, .png, .bmp, .tiff) hoặc .pdf |

**Response** `201 Created`
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "original_filename": "bai_viet_tay.jpg",
  "status": "completed",
  "message": "Upload thành công, đã xử lý OCR"
}
```

**Error Responses**
| Status | Mô tả |
|---|---|
| `400` | File không hợp lệ (sai extension, quá lớn) |
| `500` | Lỗi xử lý OCR |

---

## 3. Lấy kết quả scan theo ID

```
GET /api/scan/{scan_id}
```

**Path Parameters**
| Param | Type | Mô tả |
|---|---|---|
| `scan_id` | string (UUID) | ID của scan result |

**Response** `200 OK`
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "original_filename": "bai_viet_tay.jpg",
  "ocr_text": "Đây là nội dung text được nhận diện từ ảnh...",
  "html_content": "<div class=\"ocr-page\"><p>Đây là nội dung text được nhận diện từ ảnh...</p></div>",
  "status": "completed",
  "created_at": "2026-06-01T20:30:00",
  "updated_at": "2026-06-01T20:30:05"
}
```

**Error Responses**
| Status | Mô tả |
|---|---|
| `404` | Không tìm thấy scan với ID này |

---

## 4. Lấy danh sách tất cả scan

```
GET /api/scan/
```

**Query Parameters** (dự kiến Phase 2)
| Param | Type | Default | Mô tả |
|---|---|---|---|
| `page` | int | 1 | Trang hiện tại |
| `limit` | int | 20 | Số item mỗi trang |
| `status` | string | - | Filter theo status |

**Response** `200 OK`
```json
[
  {
    "id": "a1b2c3d4-...",
    "original_filename": "bai_viet_tay.jpg",
    "ocr_text": "Đây là nội dung...",
    "html_content": "<div>...</div>",
    "status": "completed",
    "created_at": "2026-06-01T20:30:00",
    "updated_at": "2026-06-01T20:30:05"
  }
]
```

---

## 5. Cập nhật HTML content (sau khi user chỉnh sửa)

```
PUT /api/scan/{scan_id}/html
Content-Type: application/json
```

**Path Parameters**
| Param | Type | Mô tả |
|---|---|---|
| `scan_id` | string (UUID) | ID của scan result |

**Request Body**
```json
{
  "html_content": "<div class=\"ocr-page\"><p>Nội dung đã chỉnh sửa...</p></div>"
}
```

**Response** `200 OK`
```json
{
  "id": "a1b2c3d4-...",
  "original_filename": "bai_viet_tay.jpg",
  "ocr_text": "Text gốc OCR...",
  "html_content": "<div class=\"ocr-page\"><p>Nội dung đã chỉnh sửa...</p></div>",
  "status": "completed",
  "created_at": "2026-06-01T20:30:00",
  "updated_at": "2026-06-01T20:35:00"
}
```

**Error Responses**
| Status | Mô tả |
|---|---|
| `404` | Không tìm thấy scan |
| `422` | html_content không hợp lệ |

---

## 6. Export PDF

```
POST /api/scan/{scan_id}/export-pdf
```

**Path Parameters**
| Param | Type | Mô tả |
|---|---|---|
| `scan_id` | string (UUID) | ID của scan result |

**Response** `200 OK`
- Content-Type: `application/pdf`
- Content-Disposition: `attachment; filename="bai_viet_tay.pdf"`
- Body: Binary PDF file

**Error Responses**
| Status | Mô tả |
|---|---|
| `404` | Không tìm thấy scan hoặc chưa có HTML content |
| `500` | Lỗi khi generate PDF |

---

## 7. Xóa scan result

```
DELETE /api/scan/{scan_id}
```

**Path Parameters**
| Param | Type | Mô tả |
|---|---|---|
| `scan_id` | string (UUID) | ID của scan result |

**Response** `204 No Content`

**Error Responses**
| Status | Mô tả |
|---|---|
| `404` | Không tìm thấy scan |

---

## Status Values

| Status | Mô tả | Khi nào |
|---|---|---|
| `pending` | Đang chờ xử lý | Vừa upload xong |
| `processing` | Đang chạy OCR | OCR engine đang nhận diện |
| `completed` | Hoàn thành | OCR + HTML generate xong |
| `failed` | Thất bại | OCR lỗi |

---

## FE Integration Notes

### Upload flow gợi ý cho FE:
1. `POST /api/scan/upload` → nhận `id` + `status`
2. Nếu status = `completed` → `GET /api/scan/{id}` lấy HTML
3. Hiển thị HTML trong editor cho user chỉnh sửa
4. User chỉnh xong → `PUT /api/scan/{id}/html` lưu lại
5. User bấm Export → `POST /api/scan/{id}/export-pdf` download PDF

### CORS
- Đã enable CORS cho tất cả origins (development)
- Production sẽ giới hạn origins
