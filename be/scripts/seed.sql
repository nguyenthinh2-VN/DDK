-- ============================================================
-- DDK OCR - SQL Seed Script (Auth & RBAC)
-- ------------------------------------------------------------
-- Cách chạy:
--   1) Đảm bảo app đã chạy 1 lần để tạo bảng (hoặc MySQL Workbench đã thấy các bảng).
--   2) Mở MySQL Workbench / CLI, chọn database ddk_ocr, chạy file này.
--      CLI: mysql -u root -p ddk_ocr < scripts/seed.sql
--
-- Dữ liệu seed:
--   - 4 roles: CEO, DIRECTOR, MANAGER, EMPLOYEE
--   - 10 permissions (scan:*, user:*, role:*)
--   - Gán TẤT CẢ permission cho role CEO
--   - 1 admin user: username=admin / password=Admin@123 (role CEO)
--
-- Script idempotent: chạy lại nhiều lần không tạo trùng (dùng INSERT IGNORE).
-- ============================================================

USE ddk_ocr;

-- ── Roles ───────────────────────────────────────────────────
INSERT IGNORE INTO roles (id, name, display_name, level) VALUES
  ('4782f8ca-712c-44d1-a5c9-ed02b0cdba6a', 'CEO',      'Giám đốc điều hành', 1),
  ('31f65a3d-c5d7-47e0-bc65-70c2cb3d888a', 'DIRECTOR', 'Giám đốc',           2),
  ('49a6fd9a-6e97-417f-ac59-03086f73b48f', 'MANAGER',  'Quản lý',            3),
  ('2bbe4eb9-1945-4c59-9e78-e8e3ef601706', 'EMPLOYEE', 'Nhân viên',          4);

-- ── Permissions ─────────────────────────────────────────────
INSERT IGNORE INTO permissions (id, code, name) VALUES
  ('8ef55526-311e-4755-a565-e9abee852249', 'scan:upload',            'Tải ảnh lên để scan'),
  ('39f091e6-2951-4671-98aa-beab0ed44806', 'scan:read',              'Xem kết quả scan'),
  ('ff4a42f1-7ba4-4a56-9db9-283c3df9d575', 'scan:update',            'Chỉnh sửa kết quả scan'),
  ('f0e4f002-625b-44b8-9a82-cc0220f2e369', 'scan:delete',            'Xóa kết quả scan'),
  ('c34e3f5b-0048-46c9-bca9-5704a00c471a', 'user:create',            'Tạo người dùng'),
  ('4e365350-21e6-49fd-80c9-a303bcdea0a9', 'user:read',              'Xem người dùng'),
  ('061000d4-a7b6-4a36-b978-51365408c607', 'user:update',            'Cập nhật người dùng'),
  ('a6381cbb-5ec2-4d4a-b1e3-6e370fabc792', 'user:delete',            'Xóa người dùng'),
  ('146fa191-992e-4d63-ba44-861edcbf3393', 'role:read',              'Xem vai trò'),
  ('0fec988e-4aad-4e77-941d-cad9e29003a0', 'role:assign_permission', 'Gán quyền cho vai trò');

-- ── Gán TẤT CẢ permission cho role CEO ──────────────────────
INSERT IGNORE INTO role_permissions (role_id, permission_id)
SELECT '4782f8ca-712c-44d1-a5c9-ed02b0cdba6a', p.id
FROM permissions p;

-- ── Admin user (username=admin / password=Admin@123) ────────
-- Hash bcrypt của 'Admin@123'. Đổi mật khẩu ngay sau lần đăng nhập đầu tiên.
INSERT IGNORE INTO users (id, username, hashed_password, full_name, role_id, is_active, created_at) VALUES
  (
    'a3f7d165-f825-45b8-8919-22c0f0253393',
    'admin',
    '$2b$12$Fvcm4x9SdUCPzuliV73a9eNaNMEcRjO/Ck7OxIPu9X8JvTQbg/OK2',
    'System Administrator',
    '4782f8ca-712c-44d1-a5c9-ed02b0cdba6a',
    1,
    NOW()
  );

-- ── Kiểm tra kết quả ────────────────────────────────────────
SELECT 'roles' AS tbl, COUNT(*) AS total FROM roles
UNION ALL SELECT 'permissions', COUNT(*) FROM permissions
UNION ALL SELECT 'role_permissions', COUNT(*) FROM role_permissions
UNION ALL SELECT 'users', COUNT(*) FROM users;
