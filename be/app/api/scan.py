"""
Scan API Router (Controller) - Định nghĩa các API endpoints cho chức năng scan.

Tương đương: @RestController trong Spring.

Tầng Controller: 
- Nhận HTTP request
- Validate input (thông qua Schema/DTO)
- Gọi Service để xử lý
- Trả HTTP response

KHÔNG chứa business logic - chỉ điều phối request/response.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.schemas.scan_schema import (
    ScanUploadResponse,
    ScanResultResponse,
    HTMLUpdateRequest,
    ExportPDFResponse,
)
from app.services.ocr_service import OCRService
from app.utils.image_helper import validate_file_extension, save_upload_file

# Tương đương @RequestMapping("/api/scan") trong Spring
router = APIRouter(prefix="/api/scan", tags=["Scan OCR"])


@router.post(
    "/upload",
    response_model=ScanUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload ảnh để scan OCR",
)
async def upload_image(
    file: UploadFile = File(..., description="File ảnh chữ viết tay"),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload ảnh chữ viết tay để scan OCR.

    Tương đương: @PostMapping("/upload") trong Spring.
    """
    # Validate file extension
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File không hợp lệ. Chỉ chấp nhận: .jpg, .jpeg, .png, .bmp, .tiff, .pdf",
        )

    # Lưu file
    file_content = await file.read()
    image_path = await save_upload_file(file_content, file.filename)

    # Gọi service xử lý
    service = OCRService(db)
    result = await service.upload_and_scan(file.filename, image_path)

    return ScanUploadResponse(
        id=result.id,
        original_filename=result.original_filename,
        status=result.status,
    )


@router.get(
    "/{scan_id}",
    response_model=ScanResultResponse,
    summary="Lấy kết quả scan theo ID",
)
async def get_scan_result(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Lấy kết quả scan OCR theo ID.

    Tương đương: @GetMapping("/{id}") trong Spring.
    """
    service = OCRService(db)
    result = await service.get_scan_result(scan_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy kết quả scan với ID: {scan_id}",
        )

    return result


@router.get(
    "/",
    response_model=list[ScanResultResponse],
    summary="Lấy tất cả kết quả scan",
)
async def get_all_results(
    db: AsyncSession = Depends(get_db),
):
    """
    Lấy danh sách tất cả kết quả scan.

    Tương đương: @GetMapping("/") trong Spring.
    """
    service = OCRService(db)
    return await service.get_all_results()


@router.put(
    "/{scan_id}/html",
    response_model=ScanResultResponse,
    summary="Cập nhật nội dung HTML",
)
async def update_html(
    scan_id: str,
    body: HTMLUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Cập nhật nội dung HTML sau khi user chỉnh sửa trên editor.

    Tương đương: @PutMapping("/{id}/html") trong Spring.
    """
    service = OCRService(db)
    result = await service.update_html_content(scan_id, body.html_content)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy kết quả scan với ID: {scan_id}",
        )

    return result


@router.delete(
    "/{scan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa kết quả scan",
)
async def delete_scan(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Xóa kết quả scan theo ID.

    Tương đương: @DeleteMapping("/{id}") trong Spring.
    """
    service = OCRService(db)
    deleted = await service.delete_scan(scan_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy kết quả scan với ID: {scan_id}",
        )
