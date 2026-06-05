"""
Constants dung chung toan ung dung.
"""

ROLE_CEO = "CEO"
ROLE_TREASURY = "TREASURY"
ROLE_SUB_TREASURY = "SUB_TREASURY"
ROLE_ACCOUNTING = "ACCOUNTING"
ROLE_EMPLOYEE = "MAKER"

# Backward-compatible aliases for old min-role checks.
ROLE_DIRECTOR = ROLE_TREASURY
ROLE_MANAGER = ROLE_ACCOUNTING

# Map level sang role để giữ tính tương thích với hệ thống cũ (nếu có check level)
ROLE_LEVEL_MAP = {
    1: ROLE_CEO,
    2: ROLE_TREASURY,
    3: ROLE_ACCOUNTING,
    4: ROLE_EMPLOYEE,
    5: ROLE_SUB_TREASURY
}

DEFAULT_ROLES = [
    ("CEO", "Giam doc dieu hanh", ROLE_CEO),
    ("TREASURY", "Thu quy", ROLE_TREASURY),
    ("SUB_TREASURY", "Thu quy phu", ROLE_SUB_TREASURY),
    ("ACCOUNTING", "Ke toan", ROLE_ACCOUNTING),
    ("EMPLOYEE", "Nhan vien / Maker", ROLE_EMPLOYEE),
]

DEFAULT_PERMISSIONS = [
    ("scan:upload", "Tai anh len de scan"),
    ("scan:read", "Xem ket qua scan"),
    ("scan:update", "Chinh sua ket qua scan"),
    ("scan:delete", "Xoa ket qua scan"),
    ("user:create", "Tao nguoi dung"),
    ("user:read", "Xem nguoi dung"),
    ("user:update", "Cap nhat nguoi dung"),
    ("user:delete", "Xoa nguoi dung"),
    ("role:read", "Xem vai tro"),
    ("role:assign_permission", "Gan quyen cho vai tro"),
    ("signature:read", "Xem chu ky"),
    ("signature:create", "Tai len chu ky"),
    ("signature:update", "Cap nhat chu ky"),
    ("signature:delete", "Xoa chu ky"),
]
