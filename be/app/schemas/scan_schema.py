"""
Scan Schemas (DTO) - Request/Response models cho API scan OCR.

Tương đương: DTO (Data Transfer Object) trong Spring.

Tầng DTO: định nghĩa dữ liệu truyền qua API, KHÔNG phải entity database.
Cập nhật v2: thêm batch DTO, structured JSON DTO, per-field confidence.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Batch Upload Response ────────────────────────────


class BatchItemResponse(BaseModel):
    """1 file trong batch (response khi upload)."""

    scan_id: str
    original_filename: str
    status: str


class BatchUploadResponse(BaseModel):
    """Response sau khi upload batch nhiều file (HTTP 202)."""

    batch_id: str
    total_files: int
    status: str
    items: list[BatchItemResponse]
    message: str = Field(default="Đã nhận file, đang xử lý OCR")


# ── Batch Polling Response ───────────────────────────


class BatchItemStatusResponse(BaseModel):
    """Trạng thái 1 file khi polling tiến độ batch."""

    scan_id: str
    original_filename: str
    status: str
    confidence_avg: float | None = None
    error_message: str | None = None

    model_config = {"from_attributes": True}


class BatchStatusResponse(BaseModel):
    """Response polling tiến độ xử lý batch."""

    batch_id: str
    status: str
    total_files: int
    completed_files: int
    failed_files: int
    items: list[BatchItemStatusResponse]

    model_config = {"from_attributes": True}


# ── Scan Result Response ─────────────────────────────


class SignatureBasicResponse(BaseModel):
    id: str
    processed_file_path: str
    signer_name: str
    model_config = {"from_attributes": True}

class ScanApprovalResponse(BaseModel):
    id: str
    user_id: str
    role: str
    action: str
    note: str | None = None
    signature_id: str | None = None
    signature: SignatureBasicResponse | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScanResultResponse(BaseModel):
    """Response chi tiết 1 phiếu scan."""

    id: str
    batch_id: str | None = None
    original_filename: str
    image_path: str
    processed_image_path: str | None = None
    document_type: str | None = None
    ocr_text: str | None = None
    ocr_json: dict[str, Any] | None = None
    html_content: str | None = None
    confidence_avg: float | None = None
    status: str
    error_message: str | None = None
    workflow_status: str | None = "DRAFT"
    current_assignee_role: str | None = None
    approvals: list[ScanApprovalResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScanResultSummary(BaseModel):
    """Bản tóm tắt phiếu scan (cho danh sách)."""

    id: str
    batch_id: str | None = None
    original_filename: str
    document_type: str | None = None
    confidence_avg: float | None = None
    status: str
    workflow_status: str | None = "DRAFT"
    current_assignee_role: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Update Requests ──────────────────────────────────


class HTMLUpdateRequest(BaseModel):
    """Request body khi user chỉnh sửa HTML content."""

    html_content: str = Field(..., description="Nội dung HTML đã chỉnh sửa")


class OCRJsonUpdateRequest(BaseModel):
    """Request body khi user chỉnh sửa lại các field trong ocr_json."""

    ocr_json: dict[str, Any] = Field(..., description="JSON structured đã chỉnh sửa")


# ── Workflow Requests ────────────────────────────────

class WorkflowApproveRequest(BaseModel):
    """Request body khi user duyệt phiếu."""
    signature_id: str | None = Field(default=None, description="ID của chữ ký sẽ chèn (nếu có)")

class WorkflowRejectRequest(BaseModel):
    """Request body khi user từ chối phiếu."""
    note: str | None = Field(default=None, description="Lý do từ chối")


# ── Export PDF ───────────────────────────────────────


class ExportPDFResponse(BaseModel):
    """Response sau khi export PDF."""

    id: str
    pdf_filename: str
    message: str = Field(default="Export PDF thành công")
