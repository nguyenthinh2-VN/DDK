# 📋 Plan: Hệ thống Login nội bộ & Phân quyền động (RBAC) - Cập nhật

> **Mục tiêu**: Hệ thống xác thực và phân quyền cho dự án nội bộ. Tích hợp đa ngôn ngữ (i18n) cho các response messages trả về FE.

---

## 1. Đa ngôn ngữ (i18n) cho API Responses

**Yêu cầu:** Khi FE chuyển ngôn ngữ (VD: Tiếng Việt ↔ Tiếng Trung giản thể), BE phải trả về JSON messages tương ứng.

**Giải pháp:**
- FE truyền ngôn ngữ qua header `Accept-Language: zh-CN` hoặc `Accept-Language: vi`.
- BE tạo một Middleware hoặc FastAPI Dependency để đọc header này.
- Dữ liệu dịch thuật lưu trong các file JSON:
  - `app/locales/vi.json` (Tiếng Việt mặc định)
  - `app/locales/zh.json` (Tiếng Trung giản thể)
- Xây dựng hàm `get_message(key, lang)` để lấy text dịch, ví dụ: `get_message("user_not_found", "zh")` -> `用户不存在`.
- Toàn bộ exception (`HTTPException`) và response message đều dùng cơ chế này.

---

## 2. Tổng quan hệ thống Auth & RBAC

### Luồng Login:
```
FE gửi username/password + Accept-Language
        │
        ▼
[api/auth.py] ← Controller nhận request
        │
        ▼
[services/auth_service.py] ← Verify password → Tạo JWT token (chỉ Access Token)
        │
        ▼
[repositories/user_repository.py] ← Tìm user trong DB
        │
        ▼
Trả về: access_token (kèm message theo ngôn ngữ)
```

### Luồng gọi API có bảo vệ:
```
FE gửi request + Bearer Token + Accept-Language
        │
        ▼
[utils/jwt_helper.py] ← Middleware verify JWT (FastAPI Depends)
        │
        ├── Token hợp lệ → Decode → lấy user_id, role
        │
        ▼
[middleware/auth_guard.py] ← Kiểm tra quyền theo role
        │
        ▼
[api/...] ← Controller xử lý bình thường
```

---

## 3. Thiết kế Database (Cập nhật: 1 User = 1 Role)

### Bảng: `roles`
| Column | Type | Mô tả |
|---|---|---|
| `id` | VARCHAR(36) (PK) | UUID |
| `name` | VARCHAR(50) UNIQUE | `CEO`, `DIRECTOR`, `MANAGER`, `EMPLOYEE` |
| `display_name` | VARCHAR(100) | Tên hiển thị |
| `level` | INT | Cấp bậc (CEO=1 cao nhất, EMPLOYEE=4 thấp nhất) |

### Bảng: `users`
| Column | Type | Mô tả |
|---|---|---|
| `id` | VARCHAR(36) (PK) | UUID |
| `username` | VARCHAR(50) UNIQUE | Tên đăng nhập |
| `hashed_password` | VARCHAR(255) | Mật khẩu đã hash (bcrypt) |
| `full_name` | VARCHAR(255) | Họ tên đầy đủ |
| `role_id` | VARCHAR(36) (FK) | **Foreign Key tới bảng roles (1 user có 1 role)** |
| `is_active` | BOOLEAN DEFAULT true | Tài khoản có hoạt động không |
| `created_at` | DATETIME | |

### Bảng: `permissions`
| Column | Type | Mô tả |
|---|---|---|
| `id` | VARCHAR(36) (PK) | UUID |
| `code` | VARCHAR(100) UNIQUE | VD: `scan:upload`, `user:create` |
| `name` | VARCHAR(255) | Tên hiển thị |

### Bảng: `role_permissions` (Many-to-Many — phân quyền động)
| Column | Type | Mô tả |
|---|---|---|
| `role_id` | VARCHAR(36) (FK) | |
| `permission_id` | VARCHAR(36) (FK) | |

### Quan hệ:
```
User (N) ──── (1) Role (1) ──── (N) role_permissions (N) ──── (1) Permission
```
> Admin có thể thêm/bớt permission vào role bất kỳ lúc nào → **phân quyền động**. Mỗi user sẽ kế thừa quyền từ 1 role duy nhất của họ.

---

## 4. API Endpoints cho FE

### Authentication & User Actions
| Method | Endpoint | Mô tả | Auth |
|---|---|---|---|
| `POST` | `/api/auth/login` | Đăng nhập (Trả về Access Token) | ❌ Public |
| `POST` | `/api/auth/logout` | Đăng xuất | ✅ Required |
| `GET` | `/api/auth/me` | Lấy thông tin user hiện tại | ✅ Required |
| `PUT` | `/api/auth/change-password` | **Đổi mật khẩu** | ✅ Required |

*(Ghi chú: Không cần Refresh Token, không cần Quên mật khẩu như yêu cầu).*

### Admin - Quản lý User
| Method | Endpoint | Mô tả | Min Role |
|---|---|---|---|
| `POST` | `/api/admin/users` | Tạo user mới | Director |
| `GET` | `/api/admin/users` | Danh sách user | Director |
| `GET` | `/api/admin/users/{id}` | Chi tiết user | Manager |
| `PUT` | `/api/admin/users/{id}` | Cập nhật user (đổi role_id ở đây) | Manager |
| `DELETE` | `/api/admin/users/{id}` | Xóa user | CEO |

### Admin - Quản lý Role & Permission
| Method | Endpoint | Mô tả | Min Role |
|---|---|---|---|
| `GET` | `/api/admin/roles` | Danh sách roles | Manager |
| `GET` | `/api/admin/roles/{id}/permissions` | Quyền của role | Manager |
| `POST` | `/api/admin/roles/{id}/permissions` | Gán quyền vào role | CEO |
| `DELETE` | `/api/admin/roles/{id}/permissions/{perm_id}` | Bỏ quyền khỏi role | CEO |

---

## 5. Tạo tài khoản Admin đầu tiên

**Giải pháp:** Dùng script Python độc lập.
- Tạo file `scripts/create_admin.py`.
- Khi cần tạo admin (lúc mới setup hoặc deploy), chạy lệnh: `py scripts/create_admin.py`
- Script sẽ hỏi nhập username, password (hoặc lấy từ `.env`), tự động tạo Role `CEO` (nếu chưa có) và gán cho user này.

---

## 6. Kế hoạch triển khai (thứ tự code)

| Bước | Việc làm | File chính |
|---|---|---|
| 1 | Setup i18n | `app/locales/vi.json`, `app/locales/zh.json`, `app/utils/i18n.py` |
| 2 | Tạo Models (Entity) | `user.py`, `role.py`, `permission.py` |
| 3 | Tạo Schemas (DTO) | `auth_schema.py`, `user_schema.py` |
| 4 | Tạo Utils | `jwt_helper.py`, `password_helper.py`, `auth_guard.py` |
| 5 | Tạo Repositories | `user_repository.py`, `role_repository.py` |
| 6 | Tạo Services | `auth_service.py`, `user_service.py` |
| 7 | Tạo Controllers | `api/auth.py`, `api/admin/users.py`, `api/admin/roles.py` |
| 8 | **Tạo Script Admin** | `scripts/create_admin.py` |
| 9 | Đăng ký router | `app/main.py` |

---

## 7. Dependencies cần thêm vào requirements

```text
python-jose[cryptography]==3.5.0   ← JWT encode/decode
passlib[bcrypt]==1.7.4             ← Bcrypt password hashing
```
