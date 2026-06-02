# 🔐 API Specification - Auth & RBAC

> Tài liệu API cho FE team xây dựng giao diện đăng nhập & phân quyền.
> Base URL: `http://localhost:8000`
> Swagger UI: `http://localhost:8000/docs`

---

## Quy ước chung

### Đa ngôn ngữ (i18n)
Tất cả `message` trong response được dịch theo header `Accept-Language`.

| Header | Ngôn ngữ |
|---|---|
| `Accept-Language: vi` | Tiếng Việt (mặc định) |
| `Accept-Language: tw` | Tiếng Trung phồn thể |

> Nếu không gửi header hoặc ngôn ngữ không hỗ trợ → mặc định `vi`.

### Xác thực (Authentication)
Các endpoint có dấu ✅ yêu cầu gửi kèm JWT access token:

```
Authorization: Bearer <access_token>
```

### Phân quyền (Authorization)
Hệ thống dùng RBAC theo cấp bậc role (số nhỏ = quyền cao):

| Role | Level | Mô tả |
|---|---|---|
| `CEO` | 1 | Giám đốc điều hành (cao nhất) |
| `DIRECTOR` | 2 | Giám đốc |
| `MANAGER` | 3 | Quản lý |
| `EMPLOYEE` | 4 | Nhân viên (thấp nhất) |

> "Min Role" nghĩa là cấp bậc tối thiểu. VD: Min Role = Director → CEO và Director được phép, Manager và Employee bị chặn (403).

### Mã lỗi chung
| Status | Mô tả |
|---|---|
| `401` | Chưa đăng nhập / token sai / token hết hạn |
| `403` | Không đủ quyền / tài khoản bị vô hiệu hóa |
| `404` | Không tìm thấy dữ liệu |
| `422` | Dữ liệu request không hợp lệ (validation) |

---

# Phần A — Authentication

## A.1 Đăng nhập

```
POST /api/auth/login
Content-Type: application/json
```

🔓 **Public** (không cần token)

**Request Body**
```json
{
  "username": "admin",
  "password": "Admin@123"
}
```

| Field | Type | Required | Mô tả |
|---|---|---|---|
| `username` | string | ✅ | Tên đăng nhập |
| `password` | string | ✅ | Mật khẩu |

**Response** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "message": "Đăng nhập thành công"
}
```

**Error Responses**
| Status | Mô tả |
|---|---|
| `401` | Tên đăng nhập hoặc mật khẩu không đúng |
| `403` | Tài khoản đã bị vô hiệu hóa |

---

## A.2 Đăng xuất

```
POST /api/auth/logout
```

✅ **Required**

> JWT là stateless (không Refresh Token). Endpoint này xác nhận token hợp lệ và trả message; FE tự xóa token phía client.

**Response** `200 OK`
```json
{
  "message": "Đăng xuất thành công"
}
```

**Error Responses**
| Status | Mô tả |
|---|---|
| `401` | Chưa đăng nhập / token không hợp lệ |

---

## A.3 Thông tin user hiện tại

```
GET /api/auth/me
```

✅ **Required**

**Response** `200 OK`
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "username": "admin",
  "full_name": "System Administrator",
  "role": "CEO",
  "role_level": 1,
  "permissions": [
    "scan:upload",
    "scan:read",
    "user:create",
    "user:read",
    "user:update",
    "user:delete",
    "role:read",
    "role:assign_permission"
  ]
}
```

**Error Responses**
| Status | Mô tả |
|---|---|
| `401` | Chưa đăng nhập / token không hợp lệ |

---

## A.4 Đổi mật khẩu

```
PUT /api/auth/change-password
Content-Type: application/json
```

✅ **Required**

**Request Body**
```json
{
  "old_password": "Admin@123",
  "new_password": "NewPass@456"
}
```

| Field | Type | Required | Mô tả |
|---|---|---|---|
| `old_password` | string | ✅ | Mật khẩu cũ |
| `new_password` | string | ✅ | Mật khẩu mới (tối thiểu 6 ký tự) |

**Response** `200 OK`
```json
{
  "message": "Đổi mật khẩu thành công"
}
```

**Error Responses**
| Status | Mô tả |
|---|---|
| `400` | Mật khẩu cũ không chính xác |
| `401` | Chưa đăng nhập |
| `422` | Mật khẩu mới không đạt yêu cầu (< 6 ký tự) |

---

# Phần B — Admin: Quản lý User

> Base path: `/api/admin/users`

## B.1 Tạo user mới

```
POST /api/admin/users
Content-Type: application/json
```

✅ **Required** — Min Role: **Director**

**Request Body**
```json
{
  "username": "nhanvien01",
  "password": "Pass@123",
  "full_name": "Nguyễn Văn A",
  "role_id": "f0e1d2c3-b4a5-6789-0123-456789abcdef"
}
```

| Field | Type | Required | Mô tả |
|---|---|---|---|
| `username` | string | ✅ | Tên đăng nhập (3–50 ký tự) |
| `password` | string | ✅ | Mật khẩu (tối thiểu 6 ký tự) |
| `full_name` | string | ✅ | Họ tên đầy đủ |
| `role_id` | string (UUID) | ✅ | ID của role gán cho user |

**Response** `201 Created`
```json
{
  "id": "a1b2c3d4-...",
  "username": "nhanvien01",
  "full_name": "Nguyễn Văn A",
  "is_active": true,
  "created_at": "2026-06-02T09:00:00",
  "role": {
    "id": "f0e1d2c3-...",
    "name": "EMPLOYEE",
    "display_name": "Nhân viên",
    "level": 4
  }
}
```

**Error Responses**
| Status | Mô tả |
|---|---|
| `400` | Tên đăng nhập đã tồn tại / role không tồn tại |
| `403` | Không đủ quyền (dưới Director) |

---

## B.2 Danh sách user

```
GET /api/admin/users
```

✅ **Required** — Min Role: **Director**

**Response** `200 OK`
```json
[
  {
    "id": "a1b2c3d4-...",
    "username": "admin",
    "full_name": "System Administrator",
    "is_active": true,
    "created_at": "2026-06-01T08:00:00",
    "role": {
      "id": "f0e1d2c3-...",
      "name": "CEO",
      "display_name": "Giám đốc điều hành",
      "level": 1
    }
  }
]
```

**Error Responses**
| Status | Mô tả |
|---|---|
| `403` | Không đủ quyền (dưới Director) |

---

## B.3 Chi tiết user

```
GET /api/admin/users/{user_id}
```

✅ **Required** — Min Role: **Manager**

**Path Parameters**
| Param | Type | Mô tả |
|---|---|---|
| `user_id` | string (UUID) | ID của user |

**Response** `200 OK`
```json
{
  "id": "a1b2c3d4-...",
  "username": "nhanvien01",
  "full_name": "Nguyễn Văn A",
  "is_active": true,
  "created_at": "2026-06-02T09:00:00",
  "role": {
    "id": "f0e1d2c3-...",
    "name": "EMPLOYEE",
    "display_name": "Nhân viên",
    "level": 4
  }
}
```

**Error Responses**
| Status | Mô tả |
|---|---|
| `403` | Không đủ quyền (dưới Manager) |
| `404` | Không tìm thấy user |

---

## B.4 Cập nhật user

```
PUT /api/admin/users/{user_id}
Content-Type: application/json
```

✅ **Required** — Min Role: **Manager**

> Dùng endpoint này để **đổi role của user** (qua `role_id`), đổi tên, hoặc kích hoạt/vô hiệu hóa. Các field đều optional — chỉ gửi field cần đổi.

**Path Parameters**
| Param | Type | Mô tả |
|---|---|---|
| `user_id` | string (UUID) | ID của user |

**Request Body**
```json
{
  "full_name": "Nguyễn Văn A (Updated)",
  "role_id": "11112222-3333-4444-5555-666677778888",
  "is_active": false
}
```

| Field | Type | Required | Mô tả |
|---|---|---|---|
| `full_name` | string | ❌ | Họ tên đầy đủ |
| `role_id` | string (UUID) | ❌ | Đổi role của user |
| `is_active` | boolean | ❌ | Kích hoạt / vô hiệu hóa tài khoản |

**Response** `200 OK`
```json
{
  "id": "a1b2c3d4-...",
  "username": "nhanvien01",
  "full_name": "Nguyễn Văn A (Updated)",
  "is_active": false,
  "created_at": "2026-06-02T09:00:00",
  "role": {
    "id": "11112222-...",
    "name": "MANAGER",
    "display_name": "Quản lý",
    "level": 3
  }
}
```

**Error Responses**
| Status | Mô tả |
|---|---|
| `400` | Role mới không tồn tại |
| `403` | Không đủ quyền (dưới Manager) |
| `404` | Không tìm thấy user |

---

## B.5 Xóa user

```
DELETE /api/admin/users/{user_id}
```

✅ **Required** — Min Role: **CEO**

**Path Parameters**
| Param | Type | Mô tả |
|---|---|---|
| `user_id` | string (UUID) | ID của user |

**Response** `200 OK`
```json
{
  "message": "Xóa người dùng thành công"
}
```

**Error Responses**
| Status | Mô tả |
|---|---|
| `403` | Không đủ quyền (không phải CEO) |
| `404` | Không tìm thấy user |

---

# Phần C — Admin: Quản lý Role & Permission

> Base path: `/api/admin/roles`
> Phân quyền động: CEO có thể thêm/bớt permission cho role bất kỳ lúc nào.

## C.1 Danh sách roles

```
GET /api/admin/roles
```

✅ **Required** — Min Role: **Manager**

**Response** `200 OK`
```json
[
  { "id": "f0e1d2c3-...", "name": "CEO", "display_name": "Giám đốc điều hành", "level": 1 },
  { "id": "a1a2a3a4-...", "name": "DIRECTOR", "display_name": "Giám đốc", "level": 2 },
  { "id": "b1b2b3b4-...", "name": "MANAGER", "display_name": "Quản lý", "level": 3 },
  { "id": "c1c2c3c4-...", "name": "EMPLOYEE", "display_name": "Nhân viên", "level": 4 }
]
```

**Error Responses**
| Status | Mô tả |
|---|---|
| `403` | Không đủ quyền (dưới Manager) |

---

## C.2 Quyền của một role

```
GET /api/admin/roles/{role_id}/permissions
```

✅ **Required** — Min Role: **Manager**

**Path Parameters**
| Param | Type | Mô tả |
|---|---|---|
| `role_id` | string (UUID) | ID của role |

**Response** `200 OK`
```json
[
  { "id": "p1p2p3p4-...", "code": "scan:upload", "name": "Tải ảnh lên để scan" },
  { "id": "p5p6p7p8-...", "code": "user:read", "name": "Xem người dùng" }
]
```

**Error Responses**
| Status | Mô tả |
|---|---|
| `403` | Không đủ quyền (dưới Manager) |
| `404` | Không tìm thấy role |

---

## C.3 Gán quyền vào role

```
POST /api/admin/roles/{role_id}/permissions
Content-Type: application/json
```

✅ **Required** — Min Role: **CEO**

**Path Parameters**
| Param | Type | Mô tả |
|---|---|---|
| `role_id` | string (UUID) | ID của role |

**Request Body**
```json
{
  "permission_id": "p1p2p3p4-5555-6666-7777-888899990000"
}
```

| Field | Type | Required | Mô tả |
|---|---|---|---|
| `permission_id` | string (UUID) | ✅ | ID của permission cần gán |

**Response** `200 OK`
```json
{
  "message": "Gán quyền thành công"
}
```

**Error Responses**
| Status | Mô tả |
|---|---|
| `403` | Không đủ quyền (không phải CEO) |
| `404` | Không tìm thấy role hoặc permission |

---

## C.4 Bỏ quyền khỏi role

```
DELETE /api/admin/roles/{role_id}/permissions/{permission_id}
```

✅ **Required** — Min Role: **CEO**

**Path Parameters**
| Param | Type | Mô tả |
|---|---|---|
| `role_id` | string (UUID) | ID của role |
| `permission_id` | string (UUID) | ID của permission cần bỏ |

**Response** `200 OK`
```json
{
  "message": "Bỏ quyền thành công"
}
```

**Error Responses**
| Status | Mô tả |
|---|---|
| `403` | Không đủ quyền (không phải CEO) |
| `404` | Không tìm thấy role hoặc permission |

---

## Bảng tổng hợp Endpoints

| Method | Endpoint | Auth | Min Role |
|---|---|---|---|
| `POST` | `/api/auth/login` | 🔓 Public | — |
| `POST` | `/api/auth/logout` | ✅ | — |
| `GET` | `/api/auth/me` | ✅ | — |
| `PUT` | `/api/auth/change-password` | ✅ | — |
| `POST` | `/api/admin/users` | ✅ | Director |
| `GET` | `/api/admin/users` | ✅ | Director |
| `GET` | `/api/admin/users/{id}` | ✅ | Manager |
| `PUT` | `/api/admin/users/{id}` | ✅ | Manager |
| `DELETE` | `/api/admin/users/{id}` | ✅ | CEO |
| `GET` | `/api/admin/roles` | ✅ | Manager |
| `GET` | `/api/admin/roles/{id}/permissions` | ✅ | Manager |
| `POST` | `/api/admin/roles/{id}/permissions` | ✅ | CEO |
| `DELETE` | `/api/admin/roles/{id}/permissions/{perm_id}` | ✅ | CEO |

---

## FE Integration Notes

### Login flow gợi ý cho FE:
1. `POST /api/auth/login` (kèm `Accept-Language`) → nhận `access_token`.
2. Lưu token (localStorage / memory) và đính kèm header `Authorization: Bearer <token>` cho mọi request sau.
3. `GET /api/auth/me` → lấy `role`, `role_level`, `permissions` để dựng menu/ẩn-hiện chức năng.
4. Render UI theo `permissions`: chỉ hiển thị nút khi user có permission tương ứng (VD ẩn nút "Tạo user" nếu thiếu `user:create`).
5. Khi nhận `401` từ bất kỳ API nào → token hết hạn → điều hướng về trang login.
6. Logout: gọi `POST /api/auth/logout` rồi xóa token phía client.

### Đa ngôn ngữ
- Luôn gửi header `Accept-Language` (`vi` hoặc `tw`) để nhận message đúng ngôn ngữ.
- Khi user đổi ngôn ngữ trên FE, chỉ cần đổi giá trị header cho các request kế tiếp.

### CORS
- Đã enable CORS cho tất cả origins (development).
- Production sẽ giới hạn origins.
