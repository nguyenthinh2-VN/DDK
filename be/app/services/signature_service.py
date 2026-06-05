"""
Service cho nghiep vu chu ky.
"""

from app.models.signature import Signature
from app.models.user import User
from app.repositories.signature_repository import SignatureRepository
from app.schemas.signature_schema import SignatureUploadResponse
from app.utils.signature_image_helper import (
    delete_file_if_exists,
    path_to_public_url,
    remove_background_signature,
    save_signature_original,
    save_signature_without_background_processing,
    validate_signature_extension,
    validate_signature_file_size,
)


class SignatureService:
    def __init__(self, db):
        self.db = db
        self.repo = SignatureRepository(db)

    @staticmethod
    def _to_response(signature: Signature, remove_background_applied: bool | None = None):
        payload = {
            "id": signature.id,
            "user_id": signature.user_id,
            "signer_name": signature.signer_name,
            "original_filename": signature.original_filename,
            "image_url": path_to_public_url(signature.processed_file_path),
            "bg_removed": signature.bg_removed,
            "is_active": signature.is_active,
            "created_at": signature.created_at,
            "updated_at": signature.updated_at,
        }
        if remove_background_applied is None:
            return payload
        return SignatureUploadResponse(
            **payload,
            remove_background_applied=remove_background_applied,
        )

    async def get_my_signatures(self, current_user: User):
        signatures = await self.repo.find_all_active_by_user_id(current_user.id)
        return [self._to_response(sig) for sig in signatures]

    async def delete_signature(self, signature_id: str, current_user: User) -> bool:
        signature = await self.repo.find_by_id(signature_id)
        if signature is None or signature.user_id != current_user.id:
            return False
        signature.is_active = False
        await self.repo.update(signature)
        return True

    async def upload_signature(
        self,
        current_user: User,
        file_content: bytes,
        original_filename: str,
        signer_name: str | None,
        remove_background: bool,
    ) -> SignatureUploadResponse:
        if not validate_signature_extension(original_filename):
            raise ValueError("signature.file_invalid_ext")
        if not validate_signature_file_size(file_content):
            raise ValueError("signature.file_too_large")

        stored_filename, original_path = save_signature_original(file_content, original_filename)
        processed_output_name = f"{stored_filename.rsplit('.', 1)[0]}.png"

        try:
            if remove_background:
                processed_path = remove_background_signature(original_path, processed_output_name)
            else:
                processed_path = save_signature_without_background_processing(
                    original_path, processed_output_name
                )
        except Exception:
            delete_file_if_exists(original_path)
            raise

        active_signatures = await self.repo.find_all_active_by_user_id(current_user.id)
        if len(active_signatures) >= 3:
            raise ValueError("signature.max_limit_reached")

        signature = Signature(
            user_id=current_user.id,
            signer_name=(signer_name or current_user.full_name).strip() or current_user.full_name,
            original_filename=original_filename,
            stored_filename=processed_output_name,
            original_file_path=original_path,
            processed_file_path=processed_path,
            mime_type="image/png",
            file_size=len(file_content),
            bg_removed=remove_background,
            is_active=True,
        )
        await self.repo.create(signature)
        return self._to_response(signature, remove_background_applied=remove_background)
