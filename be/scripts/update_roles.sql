USE ddk_ocr;

-- Tắt chế độ Safe Update tạm thời
SET SQL_SAFE_UPDATES = 0;

-- Cập nhật tên và hiển thị cho các Role (dựa vào level làm chuẩn)
UPDATE roles SET name='CEO', display_name='Giám đốc điều hành' WHERE level=1;
UPDATE roles SET name='TREASURY', display_name='Thủ quỹ' WHERE level=2;
UPDATE roles SET name='ACCOUNTING', display_name='Kế toán' WHERE level=3;
UPDATE roles SET name='EMPLOYEE', display_name='Nhân viên / Maker' WHERE level=4;
UPDATE roles SET name='SUB_TREASURY', display_name='Thủ quỹ phụ' WHERE level=5;

-- Đảm bảo admin mang role CEO (level=1)
UPDATE users SET role_id=(SELECT id FROM roles WHERE level=1) WHERE username='admin';

-- Bật lại chế độ Safe Update
SET SQL_SAFE_UPDATES = 1;
