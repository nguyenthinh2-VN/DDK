-- ============================================================
-- DDK OCR - Migration v2 (Scan OCR batch + structured JSON)
-- ------------------------------------------------------------
-- Cách chạy:
--   mysql -u root -p ddk_ocr < scripts/migrate_scan_v2.sql
--
-- Nội dung:
--   1) Tạo bảng scan_batches (gom 1 lần upload nhiều file).
--   2) Thêm cột mới cho scan_results + đổi text -> LONGTEXT + thêm JSON.
--
-- Lưu ý: nếu app đã tự create_all thì các bảng/cột có thể đã tồn tại.
--        Script dùng IF NOT EXISTS ở mức có thể; với ADD COLUMN, nếu cột
--        đã tồn tại MySQL sẽ báo lỗi -> có thể bỏ qua dòng đó.
-- ============================================================

USE ddk_ocr;

-- ── 1) Bảng scan_batches ────────────────────────────────────
CREATE TABLE IF NOT EXISTS scan_batches (
    id              VARCHAR(36)  NOT NULL,
    total_files     INT          NOT NULL,
    completed_files INT          NOT NULL DEFAULT 0,
    failed_files    INT          NOT NULL DEFAULT 0,
    status          VARCHAR(20)           DEFAULT 'pending',
    uploaded_by     VARCHAR(36)  NULL,
    created_at      DATETIME     NULL,
    updated_at      DATETIME     NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_scan_batches_user
        FOREIGN KEY (uploaded_by) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── 2) Cập nhật bảng scan_results ───────────────────────────
-- Thêm cột batch_id
ALTER TABLE scan_results
    ADD COLUMN batch_id VARCHAR(36) NULL AFTER id,
    ADD CONSTRAINT fk_scan_results_batch
        FOREIGN KEY (batch_id) REFERENCES scan_batches (id) ON DELETE CASCADE;

-- Ảnh đã tiền xử lý
ALTER TABLE scan_results
    ADD COLUMN processed_image_path VARCHAR(500) NULL AFTER image_path;

-- Loại phiếu
ALTER TABLE scan_results
    ADD COLUMN document_type VARCHAR(50) DEFAULT 'advance_payment_slip' AFTER processed_image_path;

-- JSON structured + raw
ALTER TABLE scan_results
    ADD COLUMN ocr_json JSON NULL AFTER ocr_text,
    ADD COLUMN ocr_raw_json JSON NULL AFTER ocr_json;

-- Độ tin cậy trung bình
ALTER TABLE scan_results
    ADD COLUMN confidence_avg FLOAT NULL AFTER html_content;

-- Lý do lỗi
ALTER TABLE scan_results
    ADD COLUMN error_message LONGTEXT NULL AFTER status;

-- Đổi kiểu text -> LONGTEXT cho nội dung dài
ALTER TABLE scan_results
    MODIFY COLUMN ocr_text LONGTEXT NULL,
    MODIFY COLUMN html_content LONGTEXT NULL;

-- ── Kiểm tra ────────────────────────────────────────────────
SELECT 'scan_batches' AS tbl, COUNT(*) AS total FROM scan_batches
UNION ALL SELECT 'scan_results', COUNT(*) FROM scan_results;
