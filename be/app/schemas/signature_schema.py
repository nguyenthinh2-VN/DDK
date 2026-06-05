"""
Schemas cho API chu ky.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class SignatureResponse(BaseModel):
    id: str
    user_id: str
    signer_name: str
    original_filename: str
    image_url: str
    bg_removed: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SignatureUploadResponse(SignatureResponse):
    remove_background_applied: bool = Field(
        ..., description="Backend co thuc hien xu ly xoa nen hay khong"
    )
