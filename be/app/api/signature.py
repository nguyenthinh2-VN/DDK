"""
API router cho chu ky.
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.user import User
from app.schemas.auth_schema import MessageResponse
from app.schemas.signature_schema import SignatureResponse, SignatureUploadResponse
from app.services.signature_service import SignatureService
from app.utils.auth_guard import get_current_user
from app.utils.response_helper import get_language

router = APIRouter(prefix="/api/signatures", tags=["Signatures"])


@router.post(
    "/upload",
    response_model=SignatureUploadResponse,
    summary="Upload chu ky cua tai khoan hien tai",
)
async def upload_signature(
    file: UploadFile = File(...),
    signer_name: str | None = Form(default=None),
    remove_background: bool = Form(default=True),
    _: str = Depends(get_language),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vui lòng chọn file chữ ký")

    content = await file.read()
    service = SignatureService(db)

    try:
        return await service.upload_signature(
            current_user=current_user,
            file_content=content,
            original_filename=file.filename,
            signer_name=signer_name,
            remove_background=remove_background,
        )
    except ValueError as exc:
        error_map = {
            "signature.file_invalid_ext": "File chữ ký không hợp lệ. Chỉ chấp nhận .jpg, .jpeg, .png",
            "signature.file_too_large": "File chữ ký vượt quá dung lượng cho phép",
            "signature.max_limit_reached": "Đã đạt giới hạn tối đa 3 chữ ký",
        }
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_map.get(str(exc), "Dữ liệu chữ ký không hợp lệ"),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể xử lý ảnh chữ ký",
        ) from exc


@router.get(
    "/me",
    response_model=list[SignatureResponse],
    summary="Lay cac chu ky active cua tai khoan hien tai",
)
async def get_my_signatures(
    _: str = Depends(get_language),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SignatureService(db)
    signatures = await service.get_my_signatures(current_user)
    return signatures


@router.delete(
    "/{signature_id}",
    response_model=MessageResponse,
    summary="Disable 1 chu ky cua tai khoan hien tai",
)
async def delete_signature(
    signature_id: str,
    _: str = Depends(get_language),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SignatureService(db)
    deleted = await service.delete_signature(signature_id, current_user)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy chữ ký hoặc bạn không có quyền xóa")
    return MessageResponse(message="Đã gỡ chữ ký")
