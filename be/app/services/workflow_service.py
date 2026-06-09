import logging
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.scan_result import ScanResult
from app.models.scan_approval import ScanApproval
from app.models.user import User

logger = logging.getLogger(__name__)

WORKFLOW_STEPS = {
    "DRAFT": {"next": "PENDING_ACCOUNTING", "assignee": "ACCOUNTING"},
    "PENDING_ACCOUNTING": {"next": "PENDING_TREASURY", "assignee": "TREASURY"},
    "PENDING_TREASURY": {"next": "PENDING_CEO", "assignee": "CEO"},
    "PENDING_CEO": {"next": "PENDING_SUB_TREASURY", "assignee": "SUB_TREASURY"},
    "PENDING_SUB_TREASURY": {"next": "COMPLETED", "assignee": None},
}

class WorkflowService:
    @staticmethod
    async def apply_draft_signature(db: AsyncSession, scan_id: str, user: User, signature_id: str) -> ScanResult:
        scan = await db.get(ScanResult, scan_id)
        if not scan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="scan.not_found")
        
        user_role = user.role.name if user.role else "UNKNOWN"
        wf_status = scan.workflow_status or "DRAFT"
        
        if wf_status == "DRAFT" and user_role != "EMPLOYEE":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only EMPLOYEE can submit draft")
        if wf_status.startswith("PENDING_"):
            expected_role = wf_status.replace("PENDING_", "")
            if user_role != expected_role:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Pending {expected_role}")

        # Xóa draft cũ nếu có
        from sqlalchemy import delete
        await db.execute(
            delete(ScanApproval).where(
                ScanApproval.scan_result_id == scan.id,
                ScanApproval.role == user_role,
                ScanApproval.action == "DRAFT"
            )
        )
        
        approval = ScanApproval(
            scan_result_id=scan.id,
            user_id=user.id,
            role=user_role,
            action="DRAFT",
            signature_id=signature_id
        )
        db.add(approval)
        await db.commit()
        from app.repositories.scan_repository import ScanRepository
        return await ScanRepository(db).find_by_id(scan.id)

    @staticmethod
    async def remove_draft_signature(db: AsyncSession, scan_id: str, user: User) -> ScanResult:
        scan = await db.get(ScanResult, scan_id)
        if not scan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="scan.not_found")
            
        user_role = user.role.name if user.role else "UNKNOWN"
        
        from sqlalchemy import delete
        await db.execute(
            delete(ScanApproval).where(
                ScanApproval.scan_result_id == scan.id,
                ScanApproval.role == user_role,
                ScanApproval.action == "DRAFT"
            )
        )
        await db.commit()
        from app.repositories.scan_repository import ScanRepository
        return await ScanRepository(db).find_by_id(scan.id)

    @staticmethod
    async def approve_scan(db: AsyncSession, scan_id: str, user: User, signature_id: str | None = None) -> ScanResult:
        scan = await db.get(ScanResult, scan_id)
        if not scan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="scan.not_found")
        
        user_role = user.role.name if user.role else "UNKNOWN"
        wf_status = scan.workflow_status or "DRAFT"
        
        if wf_status == "DRAFT" and user_role != "EMPLOYEE":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only EMPLOYEE can submit draft")
            
        if wf_status.startswith("PENDING_"):
            expected_role = wf_status.replace("PENDING_", "")
            if user_role != expected_role:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Pending {expected_role}")
                
        if wf_status == "COMPLETED":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already completed")
            
        step_info = WORKFLOW_STEPS.get(wf_status)
        if not step_info:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state")
            
        new_status = step_info["next"]
        new_assignee = step_info["assignee"]
        
        scan.workflow_status = new_status
        scan.current_assignee_role = new_assignee
        
        # Đổi status DRAFT thành APPROVED, nếu có DRAFT. Nếu ko có, báo lỗi phải ký trước!
        from sqlalchemy import select
        stmt = select(ScanApproval).where(
            ScanApproval.scan_result_id == scan.id,
            ScanApproval.role == user_role,
            ScanApproval.action == "DRAFT"
        )
        result = await db.execute(stmt)
        draft_approval = result.scalars().first()
        
        if not draft_approval:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phải ký nháp trước khi xác nhận")
            
        draft_approval.action = "APPROVED"
        await db.commit()
        from app.repositories.scan_repository import ScanRepository
        return await ScanRepository(db).find_by_id(scan.id)

    @staticmethod
    async def reject_scan(db: AsyncSession, scan_id: str, user: User, note: str | None = None) -> ScanResult:
        scan = await db.get(ScanResult, scan_id)
        if not scan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="scan.not_found")
            
        user_role = user.role.name if user.role else "UNKNOWN"
        wf_status = scan.workflow_status or "DRAFT"
        
        if wf_status in ["DRAFT", "COMPLETED", "REJECTED"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot reject in this state")
            
        expected_role = wf_status.replace("PENDING_", "")
        if user_role != expected_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Pending {expected_role}")
            
        scan.workflow_status = "DRAFT"
        scan.current_assignee_role = "EMPLOYEE"
        
        approval = ScanApproval(
            scan_result_id=scan.id,
            user_id=user.id,
            role=user_role,
            action="REJECTED",
            note=note
        )
        db.add(approval)
        await db.commit()
        from app.repositories.scan_repository import ScanRepository
        return await ScanRepository(db).find_by_id(scan.id)
