"""
Scan API Router (Controller) - Endpoints cho chức năng scan OCR.

Tương đương: @RestController trong Spring.

Tầng Controller: nhận HTTP request, validate input, gọi Service, trả response.
KHÔNG chứa business logic.

Cập nhật v2:
- POST /api/scan/batch        : upload 3-5 file, xử lý OCR bất đồng bộ (HTTP 202)
- GET  /api/scan/batch/{id}   : polling tiến độ batch
- GET  /api/scan/{id}         : chi tiết 1 phiếu
- GET  /api/scan/             : danh sách
- PUT  /api/scan/{id}/html    : lưu HTML chỉnh sửa
- PUT  /api/scan/{id}/json    : lưu ocr_json chỉnh sửa
- DELETE /api/scan/{id}       : xóa
"""

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.database.connection import get_db
from app.models.user import User
from app.schemas.auth_schema import MessageResponse
from app.schemas.scan_schema import (
    BatchUploadResponse,
    BatchItemResponse,
    BatchStatusResponse,
    BatchItemStatusResponse,
    ScanResultResponse,
    ScanResultSummary,
    HTMLUpdateRequest,
    OCRJsonUpdateRequest,
    WorkflowApproveRequest,
    WorkflowRejectRequest,
)
from app.services.ocr_service import OCRService
from app.services.workflow_service import WorkflowService
from app.utils.auth_guard import require_permission
from app.utils.i18n import get_message
from app.utils.image_helper import (
    validate_file_extension,
    validate_file_size,
    save_upload_file,
)
from app.utils.response_helper import get_language, LocalizedHTTPException

router = APIRouter(prefix="/api/scan", tags=["Scan OCR"])


@router.post(
    "/upload",
    response_model=ScanResultResponse,
    summary="Upload 1 ảnh phiếu để scan OCR (đồng bộ)",
)
async def upload_single(
    file: UploadFile = File(...),
    lang: str = Depends(get_language),
    current_user: User = Depends(require_permission("scan:upload")),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload 1 file, gọi OCR ngay trong request và trả về kết quả (đơn luồng).
    Dùng cho trường hợp cần kết quả ngay lập tức thay vì xử lý nền.
    """
    if not validate_file_extension(file.filename):
        raise LocalizedHTTPException(
            status.HTTP_400_BAD_REQUEST, "scan.file_invalid_ext", lang
        )
    content = await file.read()
    if not validate_file_size(content):
        raise LocalizedHTTPException(
            status.HTTP_400_BAD_REQUEST, "scan.file_too_large", lang
        )
    image_path = await save_upload_file(content, file.filename)
    
    scan = await OCRService.process_single(db, (file.filename, image_path), uploaded_by=current_user.id)
    return scan


@router.post(
    "/batch",
    response_model=BatchUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload 3-5 ảnh phiếu để scan OCR (bất đồng bộ)",
)
async def upload_batch(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(..., description="Danh sách 3-5 file ảnh phiếu"),
    lang: str = Depends(get_language),
    current_user: User = Depends(require_permission("scan:upload")),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload nhiều file (min 3, max 5) → tạo batch + scan (pending) → xử lý nền.

    Trả về NGAY batch_id + danh sách scan_id (HTTP 202). FE polling tiến độ.
    """
    # Validate số lượng file
    if len(files) < settings.SCAN_BATCH_MIN_FILES:
        raise LocalizedHTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "scan.batch_too_few",
            lang,
        )
    if len(files) > settings.SCAN_BATCH_MAX_FILES:
        raise LocalizedHTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "scan.batch_too_many",
            lang,
        )

    # Validate + lưu từng file
    saved_files: list[tuple[str, str]] = []
    for file in files:
        if not validate_file_extension(file.filename):
            raise LocalizedHTTPException(
                status.HTTP_400_BAD_REQUEST, "scan.file_invalid_ext", lang
            )
        content = await file.read()
        if not validate_file_size(content):
            raise LocalizedHTTPException(
                status.HTTP_400_BAD_REQUEST, "scan.file_too_large", lang
            )
        image_path = await save_upload_file(content, file.filename)
        saved_files.append((file.filename, image_path))

    # Tạo batch + scans (pending) trong session request
    batch = await OCRService.create_batch(db, saved_files, uploaded_by=current_user.id)

    # Kick xử lý OCR nền (session riêng, sau khi response trả về)
    background_tasks.add_task(OCRService.process_batch, batch.id)

    message = get_message("scan.batch_received", lang).format(count=len(saved_files))
    return BatchUploadResponse(
        batch_id=batch.id,
        total_files=batch.total_files,
        status=batch.status,
        items=[
            BatchItemResponse(
                scan_id=s.id,
                original_filename=s.original_filename,
                status=s.status,
            )
            for s in batch.scans
        ],
        message=message,
    )


@router.get(
    "/batch/{batch_id}",
    response_model=BatchStatusResponse,
    summary="Polling tiến độ xử lý batch",
)
async def get_batch_status(
    batch_id: str,
    lang: str = Depends(get_language),
    current_user: User = Depends(require_permission("scan:read")),
    db: AsyncSession = Depends(get_db),
):
    """Lấy tiến độ batch + trạng thái/kết quả từng file."""
    batch = await OCRService.get_batch(db, batch_id)
    if batch is None:
        raise LocalizedHTTPException(
            status.HTTP_404_NOT_FOUND, "scan.batch_not_found", lang
        )

    return BatchStatusResponse(
        batch_id=batch.id,
        status=batch.status,
        total_files=batch.total_files,
        completed_files=batch.completed_files,
        failed_files=batch.failed_files,
        items=[
            BatchItemStatusResponse(
                scan_id=s.id,
                original_filename=s.original_filename,
                status=s.status,
                confidence_avg=s.confidence_avg,
                error_message=s.error_message,
            )
            for s in batch.scans
        ],
    )


@router.get(
    "/",
    response_model=list[ScanResultSummary],
    summary="Danh sách kết quả scan",
)
async def list_scans(
    current_user: User = Depends(require_permission("scan:read")),
    db: AsyncSession = Depends(get_db),
):
    """Lấy danh sách tất cả phiếu scan (tóm tắt)."""
    return await OCRService.get_all_results(db)


@router.get(
    "/{scan_id}",
    response_model=ScanResultResponse,
    summary="Chi tiết 1 phiếu scan",
)
async def get_scan(
    scan_id: str,
    lang: str = Depends(get_language),
    current_user: User = Depends(require_permission("scan:read")),
    db: AsyncSession = Depends(get_db),
):
    """Lấy chi tiết 1 phiếu: ocr_json + html_content + ảnh."""
    scan = await OCRService.get_scan_result(db, scan_id)
    if scan is None:
        raise LocalizedHTTPException(status.HTTP_404_NOT_FOUND, "scan.not_found", lang)
    return scan


@router.get(
    "/{scan_id}/export-pdf",
    summary="Xuất PDF phiếu tạm ứng",
)
async def export_pdf(
    scan_id: str,
    lang: str = Depends(get_language),
    current_user: User = Depends(require_permission("scan:read")),
    db: AsyncSession = Depends(get_db),
):
    """Xuất PDF phiếu tạm ứng với chữ ký (chỉ khi COMPLETED)."""
    from fastapi.responses import FileResponse
    from fastapi import HTTPException
    
    scan = await OCRService.get_scan_result(db, scan_id)
    if not scan:
        raise LocalizedHTTPException(status.HTTP_404_NOT_FOUND, "scan.not_found", lang)
        
    if scan.workflow_status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Chỉ xuất PDF khi Workflow COMPLETED")

    from app.services.pdf_service import generate_advance_payment_pdf
    try:
        pdf_path = generate_advance_payment_pdf(scan)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xuất PDF: {str(e)}")
        
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"PhieuTamUng_{(scan.ocr_json or {}).get('form_no') or scan_id[:6]}.pdf"
    )


@router.put(
    "/{scan_id}/html",
    response_model=ScanResultResponse,
    summary="Lưu HTML đã chỉnh sửa",
)
async def update_html(
    scan_id: str,
    body: HTMLUpdateRequest,
    lang: str = Depends(get_language),
    current_user: User = Depends(require_permission("scan:update")),
    db: AsyncSession = Depends(get_db),
):
    """Cập nhật HTML content sau khi user chỉnh sửa trên editor."""
    scan = await OCRService.update_html_content(db, scan_id, body.html_content)
    if scan is None:
        raise LocalizedHTTPException(status.HTTP_404_NOT_FOUND, "scan.not_found", lang)
    return scan


@router.put(
    "/{scan_id}/json",
    response_model=ScanResultResponse,
    summary="Lưu ocr_json đã chỉnh sửa",
)
async def update_json(
    scan_id: str,
    body: OCRJsonUpdateRequest,
    lang: str = Depends(get_language),
    current_user: User = Depends(require_permission("scan:update")),
    db: AsyncSession = Depends(get_db),
):
    """Cập nhật lại các field trong ocr_json sau khi user sửa."""
    scan = await OCRService.update_ocr_json(db, scan_id, body.ocr_json)
    if scan is None:
        raise LocalizedHTTPException(status.HTTP_404_NOT_FOUND, "scan.not_found", lang)
    return scan


@router.post(
    "/{scan_id}/export-pdf",
    summary="Export phiếu scan ra PDF",
)
async def export_pdf(
    scan_id: str,
    lang: str = Depends(get_language),
    current_user: User = Depends(require_permission("scan:read")),
    db: AsyncSession = Depends(get_db),
):
    """Render html_content của phiếu thành PDF và trả file về."""
    pdf_path, error_key = await OCRService.export_pdf(db, scan_id)
    if error_key is not None:
        # not_found / no_html → lỗi nghiệp vụ; còn lại là lỗi render WeasyPrint
        if error_key in ("scan.not_found", "scan.no_html"):
            code = (
                status.HTTP_404_NOT_FOUND
                if error_key == "scan.not_found"
                else status.HTTP_400_BAD_REQUEST
            )
            raise LocalizedHTTPException(code, error_key, lang)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_key
        )

    filename = f"{Path(pdf_path).name}"
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=filename,
    )


@router.delete(
    "/{scan_id}",
    response_model=MessageResponse,
    summary="Xóa kết quả scan",
)
async def delete_scan(
    scan_id: str,
    lang: str = Depends(get_language),
    current_user: User = Depends(require_permission("scan:delete")),
    db: AsyncSession = Depends(get_db),
):
    """Xóa 1 phiếu scan theo ID."""
    deleted = await OCRService.delete_scan(db, scan_id)
    if not deleted:
        raise LocalizedHTTPException(status.HTTP_404_NOT_FOUND, "scan.not_found", lang)
    return MessageResponse(message=get_message("scan.deleted", lang))

@router.post(
    "/{scan_id}/signature",
    response_model=ScanResultResponse,
    summary="Ký nháp vào phiếu",
)
async def draft_signature(
    scan_id: str,
    body: WorkflowApproveRequest,
    lang: str = Depends(get_language),
    current_user: User = Depends(require_permission("scan:update")),
    db: AsyncSession = Depends(get_db),
):
    """Ký nháp (chèn chữ ký vào phiếu nhưng chưa đẩy đi)."""
    return await WorkflowService.apply_draft_signature(db, scan_id, current_user, body.signature_id)

@router.delete(
    "/{scan_id}/signature",
    response_model=ScanResultResponse,
    summary="Xóa chữ ký nháp",
)
async def remove_draft_signature(
    scan_id: str,
    lang: str = Depends(get_language),
    current_user: User = Depends(require_permission("scan:update")),
    db: AsyncSession = Depends(get_db),
):
    """Xóa chữ ký nháp khỏi phiếu."""
    return await WorkflowService.remove_draft_signature(db, scan_id, current_user)

@router.post(
    "/{scan_id}/approve",
    response_model=ScanResultResponse,
    summary="Phê duyệt phiếu",
)
async def approve_scan(
    scan_id: str,
    body: WorkflowApproveRequest,
    lang: str = Depends(get_language),
    current_user: User = Depends(require_permission("scan:update")),
    db: AsyncSession = Depends(get_db),
):
    """Phê duyệt phiếu scan (Maker trình, Kế toán/Thủ quỹ/CEO duyệt)."""
    return await WorkflowService.approve_scan(db, scan_id, current_user, body.signature_id)

@router.post(
    "/{scan_id}/reject",
    response_model=ScanResultResponse,
    summary="Từ chối phiếu",
)
async def reject_scan(
    scan_id: str,
    body: WorkflowRejectRequest,
    lang: str = Depends(get_language),
    current_user: User = Depends(require_permission("scan:update")),
    db: AsyncSession = Depends(get_db),
):
    """Từ chối phiếu, trả về cho Maker sửa."""
    return await WorkflowService.reject_scan(db, scan_id, current_user, body.note)
