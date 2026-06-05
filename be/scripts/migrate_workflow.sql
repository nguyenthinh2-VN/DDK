-- Migration script for Workflow ky tuan tu

-- 1. Add workflow_status and current_assignee_role to scan_results
ALTER TABLE scan_results
ADD COLUMN workflow_status VARCHAR(50) DEFAULT 'DRAFT' COMMENT 'DRAFT | PENDING_KE_TOAN | PENDING_THU_QUY | PENDING_CEO | COMPLETED | REJECTED',
ADD COLUMN current_assignee_role VARCHAR(50) NULL COMMENT 'Role đang chờ duyệt';

-- 2. Create scan_approvals table
CREATE TABLE IF NOT EXISTS scan_approvals (
    id VARCHAR(36) PRIMARY KEY,
    scan_result_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    role VARCHAR(50) NOT NULL COMMENT 'Role lúc duyệt (e.g. KE_TOAN, THU_QUY)',
    action VARCHAR(20) NOT NULL COMMENT 'APPROVED | REJECTED',
    note VARCHAR(500) NULL COMMENT 'Lý do reject (nếu có)',
    signature_id VARCHAR(36) NULL COMMENT 'Chữ ký đã dùng để duyệt',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_scan_approval_scan FOREIGN KEY (scan_result_id) REFERENCES scan_results(id) ON DELETE CASCADE,
    CONSTRAINT fk_scan_approval_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_scan_approval_signature FOREIGN KEY (signature_id) REFERENCES signatures(id) ON DELETE SET NULL
);

-- Index for faster query
CREATE INDEX idx_scan_approval_scan_id ON scan_approvals(scan_result_id);
