# 📋 Plan: Chức năng Scan OCR - Cập nhật

> **Mục tiêu**: User upload ảnh giấy viết tay → BE dùng PaddleOCR nhận diện text → Trả về HTML chỉnh sửa → Export PDF. Có hỗ trợ đa ngôn ngữ (i18n).

---

## 1. Hỗ trợ đa ngôn ngữ (i18n)

- **API Messages:** Các lỗi như "File không hợp lệ", "Không tìm thấy file", thông báo "Thành công" sẽ được dịch ra Tiếng Việt hoặc Tiếng Trung giản thể (zh-CN) dựa trên header `Accept-Language` từ FE.
- **OCR Engine (Nhận diện chữ):** PaddleOCR hỗ trợ nhận diện chữ Tiếng Trung giản thể (`ch`) và Tiếng Việt (`vi`). Cần thống nhất cấu hình OCR model để có thể đọc được loại chữ mà user tải lên.

---

## 2. Tổng quan luồng xử lý

```
┌─────────┐    Upload ảnh     ┌─────────┐    PaddleOCR     ┌─────────┐
│   FE    │ ───────────────►  │   BE    │ ──────────────►  │  OCR    │
│ (User)  │ (Accept-Lang: zh) │  API    │                  │ Engine  │
└─────────┘                   └────┬────┘                  └────┬────┘
                                   │                            │
                                   │  ◄─── OCR text result ─────┘
                                   │
                              ┌────▼────┐
                              │ Generate │
                              │  HTML    │
                              └────┬────┘
                                   │
     ◄──── Trả HTML cho FE ────────┘
     (JSON response in zh-CN)
```

---

## 3. Phân tích chức năng (Features) & API

*(Các tính năng giữ nguyên như cũ, chỉ thêm i18n cho response)*

1. **Upload & Scan OCR:** `POST /api/scan/upload`
2. **Xem kết quả scan:** `GET /api/scan/{id}`
3. **Danh sách scan:** `GET /api/scan/`
4. **Chỉnh sửa HTML:** `PUT /api/scan/{id}/html`
5. **Export PDF:** `POST /api/scan/{id}/export-pdf`
6. **Xóa scan:** `DELETE /api/scan/{id}`

---

## 4. Thiết kế Database

### Bảng: `scan_results`

| Column | Type | Constraint | Mô tả |
|---|---|---|---|
| `id` | VARCHAR(36) | PK, UUID | ID duy nhất |
| `original_filename` | VARCHAR(255) | NOT NULL | Tên file gốc user upload |
| `image_path` | VARCHAR(500) | NOT NULL | Đường dẫn file ảnh đã lưu |
| `ocr_text` | TEXT | NULLABLE | Nội dung text OCR trích xuất |
| `html_content` | TEXT | NULLABLE | HTML đã generate từ OCR |
| `status` | VARCHAR(20) | DEFAULT 'pending' | pending → processing → completed / failed |
| `created_at` | DATETIME | AUTO | Thời gian tạo |
| `updated_at` | DATETIME | AUTO | Thời gian cập nhật |

---

## 5. Kế hoạch triển khai (Thứ tự code)

### Phase 1: Core OCR & i18n (Ưu tiên cao nhất)
- [ ] **Step 1**: Tích hợp cơ chế i18n (`locales/vi.json`, `locales/zh.json`) cho toàn bộ BE.
- [ ] **Step 2**: Tích hợp PaddleOCR vào `services/ocr_service.py`
- [ ] **Step 3**: Tạo HTML generator trong `utils/html_generator.py`
- [ ] **Step 4**: Hoàn thiện `POST /api/scan/upload` endpoint với đa ngôn ngữ.

### Phase 2: CRUD & Quản lý
- [ ] **Step 5**: Hoàn thiện các endpoint GET, PUT, DELETE cho scan_results.

### Phase 3: Export PDF
- [ ] **Step 6**: Tích hợp WeasyPrint vào `services/ocr_service.py`
- [ ] **Step 7**: Thêm API `POST /api/scan/{id}/export-pdf`

---

## 6. Câu hỏi cần xác nhận (Chưa có câu trả lời)

1. **Ngôn ngữ giấy viết tay tải lên:** Bạn muốn PaddleOCR cấu hình để nhận diện Tiếng Việt hay Tiếng Trung (hay model đa ngôn ngữ)?
2. **Xử lý đồng bộ hay bất đồng bộ:** Upload xong chờ kết quả OCR luôn (request chậm 5-10s) hay trả về ID trước rồi FE tự polling lấy kết quả sau?
3. **HTML output format:** Khi OCR xong, HTML generate ra dạng đơn giản (các thẻ `<p>`) hay cố gắng giữ layout gốc?
4. **Multi-page support:** Có cần hỗ trợ upload file PDF nhiều trang không?
