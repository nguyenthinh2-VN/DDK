"""
Constants - Hằng số dùng chung toàn ứng dụng.

Định nghĩa cấp bậc role (level) và danh sách role/permission mặc định
để seed dữ liệu ban đầu.
"""

# ── Role Levels (số nhỏ = quyền cao) ─────────────────
ROLE_CEO = 1
ROLE_DIRECTOR = 2
ROLE_MANAGER = 3
ROLE_EMPLOYEE = 4


# ── Định nghĩa role mặc định (seed) ──────────────────
# (name, display_name, level)
DEFAULT_ROLES = [
    ("CEO", "Giám đốc điều hành", ROLE_CEO),
    ("DIRECTOR", "Giám đốc", ROLE_DIRECTOR),
    ("MANAGER", "Quản lý", ROLE_MANAGER),
    ("EMPLOYEE", "Nhân viên", ROLE_EMPLOYEE),
]


# ── Định nghĩa permission mặc định (seed) ────────────
# (code, name)
DEFAULT_PERMISSIONS = [
    ("scan:upload", "Tải ảnh lên để scan"),
    ("scan:read", "Xem kết quả scan"),
    ("scan:update", "Chỉnh sửa kết quả scan"),
    ("scan:delete", "Xóa kết quả scan"),
    ("user:create", "Tạo người dùng"),
    ("user:read", "Xem người dùng"),
    ("user:update", "Cập nhật người dùng"),
    ("user:delete", "Xóa người dùng"),
    ("role:read", "Xem vai trò"),
    ("role:assign_permission", "Gán quyền cho vai trò"),
]
