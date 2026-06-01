"""
Scan Schemas (DTO) - Request/Response models cho API.

Tương đương: DTO (Data Transfer Object) trong Spring.

Tầng DTO: định nghĩa dữ liệu truyền qua API, KHÔNG phải entity database.
- Schema dùng cho validation input (request body)
- Schema dùng cho format output (response body)
"""

from datetime import datetime

from pydantic import BaseModel, Field


# ── Request DTOs ─────────────────────────────────────


class ScanUploadResponse(BaseModel):
    """Response sau khi upload ảnh để scan."""

    id: str = Field(..., description="ID của scan result")
    original_filename: str = Field(..., description="Tên file gốc")
    status: str = Field(..., description="Trạng thái xử lý")
    message: str = Field(default="Upload thành công, đang xử lý OCR")


# ── Response DTOs ────────────────────────────────────


class ScanResultResponse(BaseModel):
    """Response trả về kết quả scan OCR."""

    id: str
    original_filename: str
    ocr_text: str | None = None
    html_content: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HTMLUpdateRequest(BaseModel):
    """Request body khi user chỉnh sửa HTML content."""

    html_content: str = Field(..., description="Nội dung HTML đã chỉnh sửa")


class ExportPDFResponse(BaseModel):
    """Response sau khi export PDF."""

    id: str
    pdf_filename: str
    message: str = Field(default="Export PDF thành công")
