# Chức năng chèn Chữ ký vào Phiếu Scan — Phương án A (Thư viện Chữ ký)

## Tổng quan Flow

```
┌────────────────────────────────────────────────────────────────────┐
│  QUẢN LÝ CHỮ KÝ (trang Settings hoặc Sidebar → "Quản lý chữ ký")│
│                                                                    │
│  1. User (có quyền) vào trang "Quản lý Chữ ký"                   │
│  2. Bấm "Upload chữ ký mới"                                       │
│  3. Popup/Form hiện ra:                                            │
│     - Chọn ảnh (PNG transparent hoặc JPG nền trắng)                │
│     - Nhập tên người ký (VD: 高翊庭 Cao Dực Đình)                  │
│     - Chọn vị trí/chức vụ (Tổng Giám Đốc / Thủ quỹ / Kế toán)   │
│  4. Backend nhận file → convert sang base64 → lưu vào DB           │
│  5. Hiển thị danh sách chữ ký dạng grid card (ảnh + tên + chức vụ)│
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│  CHÈN CHỮ KÝ VÀO PHIẾU (ScanViewer)                              │
│                                                                    │
│  1. User mở chi tiết phiếu scan                                   │
│  2. Bấm "Chèn chữ ký" ở ô cần ký (VD: ô Tổng Giám Đốc)         │
│  3. Modal/Dialog popup lên → hiện danh sách chữ ký phù hợp       │
│     (lọc theo vị trí: chỉ hiện chữ ký của Tổng Giám Đốc)        │
│  4. User bấm chọn 1 chữ ký → ảnh preview ngay trong ô            │
│  5. Bấm "Lưu" → API PUT cập nhật signature_id vào ocr_json       │
│  6. Backend render lại html_content (Jinja2 nhúng <img base64>)   │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│  XUẤT PDF                                                          │
│                                                                    │
│  1. User bấm "Xuất PDF"                                           │
│  2. Backend lấy html_content (đã có ảnh chữ ký base64 nhúng sẵn) │
│  3. WeasyPrint render HTML → PDF                                   │
│  4. Trả file PDF có chữ ký đẹp về cho user                       │
└────────────────────────────────────────────────────────────────────┘
```

---

## 1. Ma trận Role — Quyền Ký (Signature Permission Matrix)

Hệ thống phân quyền hiện có: Role (`CEO`, `DIRECTOR`, `MANAGER`, `EMPLOYEE`) ↔ Permission (N-N qua bảng `role_permissions`).

### Permission codes mới cần thêm vào bảng `permissions`:

| Permission Code | Mô tả | Ghi chú |
|---|---|---|
| `signature:upload` | Upload/Xóa chữ ký vào thư viện | Admin hoặc chính người ký |
| `signature:read` | Xem danh sách chữ ký | Tất cả user |
| `sign:tong_giam_doc` | Quyền ký vào ô Tổng Giám Đốc | Chỉ CEO |
| `sign:thu_quy` | Quyền ký vào ô Thủ quỹ | Chỉ role Thủ quỹ |
| `sign:ke_toan` | Quyền ký vào ô Kế toán | Chỉ role Kế toán |
| `sign:ky_nhan` | Quyền ký vào ô Ký nhận | Người nhận tiền (linh hoạt) |

### Ma trận gán quyền (gợi ý — bạn tùy chỉnh theo công ty):

| Role | `signature:upload` | `signature:read` | `sign:tong_giam_doc` | `sign:thu_quy` | `sign:ke_toan` | `sign:ky_nhan` |
|---|---|---|---|---|---|---|
| **CEO** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **DIRECTOR** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **MANAGER** | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| **EMPLOYEE** | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| *Thủ quỹ** | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| *Kế toán** | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |

> [!IMPORTANT]
> **Thủ quỹ / Kế toán** hiện chưa có trong bảng `roles`. Bạn có thể thêm 2 role mới, hoặc gán permission trực tiếp cho user cụ thể. Kế hoạch này thiết kế permission code sẵn để sau này bạn chỉ cần `INSERT` vào bảng `permissions` + `role_permissions` mà không cần sửa code.

---

## 2. Thiết kế Database

### Bảng mới: `signatures`

```sql
CREATE TABLE signatures (
    id          VARCHAR(36) PRIMARY KEY,
    name        VARCHAR(255) NOT NULL COMMENT 'Tên người ký (VD: 高翊庭)',
    position    VARCHAR(50)  NOT NULL COMMENT 'Vị trí ký: tong_giam_doc | thu_quy | ke_toan | ky_nhan',
    image_path  VARCHAR(500) NOT NULL COMMENT 'Đường dẫn file ảnh gốc',
    image_base64 LONGTEXT    NOT NULL COMMENT 'Ảnh dạng base64 data URI để nhúng HTML/PDF',
    uploaded_by VARCHAR(36)  NULL     COMMENT 'FK → users.id (ai upload)',
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### Cập nhật `ocr_json` (trong bảng `scan_results`):

Khi user chèn chữ ký, thêm các trường `*_signature_id` vào footer:
```json
{
  "footer": {
    "so_tien_tam_ung": "294000",
    "tong_giam_doc_signature_id": "uuid-of-signature",
    "thu_quy_1_signature_id": "uuid-of-signature",
    "ke_toan_signature_id": "uuid-of-signature",
    "ky_nhan_signature_id": "uuid-of-signature",
    "thu_quy_2_signature_id": null
  }
}
```

---

## 3. Backend API

### [NEW] `app/api/signature.py`

| Method | URL | Permission | Mô tả |
|---|---|---|---|
| `POST` | `/api/signatures/upload` | `signature:upload` | Upload ảnh chữ ký (form: name, position, file) |
| `GET` | `/api/signatures` | `signature:read` | Lấy danh sách (có thể lọc theo `?position=thu_quy`) |
| `GET` | `/api/signatures/{id}` | `signature:read` | Chi tiết 1 chữ ký |
| `DELETE` | `/api/signatures/{id}` | `signature:upload` | Xóa chữ ký |

### [MODIFY] `app/services/ocr_service.py` — `update_ocr_json`

Khi render HTML (Jinja2):
1. Đọc các trường `*_signature_id` trong `ocr_json.footer`
2. Query DB lấy `image_base64` tương ứng
3. Truyền vào template → render `<img src="data:image/png;base64,..." />` vào ô chữ ký

### [MODIFY] `app/templates/advance_payment_slip.html`

Thêm render ảnh chữ ký vào các ô:
```html
<td>
  總經理<br>Tổng Giám Đốc
  {% if signatures.tong_giam_doc %}
    <br><img src="{{ signatures.tong_giam_doc }}" style="max-height: 60px;" />
  {% endif %}
</td>
```

---

## 4. Frontend

### [NEW] Trang "Quản lý Chữ ký" (`/signatures`)

- Hiển thị danh sách chữ ký dạng grid card
- Mỗi card: ảnh preview + tên + chức vụ + nút Xóa
- Nút "Upload chữ ký mới" → Form/Dialog:
  - Input: Tên người ký
  - Select: Chức vụ (Tổng Giám Đốc / Thủ quỹ / Kế toán / Ký nhận)
  - File input: Chọn ảnh (PNG/JPG, max 2MB)
  - Preview ảnh trước khi upload
  - Nút Submit → gọi API POST

### [MODIFY] ScanViewer — Kích hoạt button "Chèn chữ ký"

- Bấm button → mở Dialog/Modal
- Dialog hiển thị danh sách chữ ký (lọc theo position tương ứng)
- Bấm chọn → ảnh hiển thị preview trong ô
- Lưu `signature_id` vào `editedJson.footer.*_signature_id`
- Khi bấm "Lưu" → gọi API PUT cập nhật toàn bộ

---

## 5. Verification Plan

### Manual Verification
1. Vào trang "Quản lý Chữ ký" → Upload 1 ảnh chữ ký cho Tổng Giám Đốc
2. Mở 1 phiếu scan → Bấm "Chèn chữ ký" ở ô Tổng Giám Đốc → Chọn chữ ký vừa upload
3. Ảnh chữ ký hiển thị trong ô
4. Bấm "Xuất PDF" → Kiểm tra PDF có ảnh chữ ký đúng vị trí

## Open Questions

> [!IMPORTANT]
> 1. **Menu sidebar:** Bạn muốn đặt trang "Quản lý Chữ ký" ở đâu trong sidebar? (VD: mục mới "Cài đặt" hoặc nằm riêng?)
> 2. **Ảnh chữ ký:** Bạn có sẵn ảnh chữ ký scan chưa? Hay cần tôi hỗ trợ tạo công cụ xóa nền (background removal)?
