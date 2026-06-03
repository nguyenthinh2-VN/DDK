"""
OCR Service - Business Logic Layer cho chức năng scan OCR.

Tương đương: @Service class trong Spring.

Tầng Service: chứa business logic, điều phối Repository + utils.
Cập nhật v2: hỗ trợ batch upload nhiều file + xử lý OCR bất đồng bộ
(BackgroundTasks) + structured JSON + confidence.

Lưu ý quan trọng về async/background:
- Endpoint tạo batch + N scan (status=pending) rồi commit, trả response ngay.
- Background worker MỞ SESSION RIÊNG (không dùng lại session của request) để
  xử lý từng file, vì session request đã đóng sau khi trả response.
"""

from app.config.settings import settings
from app.database.connection import async_session_factory
from app.models.scan_batch import ScanBatch
from app.models.scan_result import ScanResult
from app.repositories.scan_batch_repository import ScanBatchRepository
from app.repositories.scan_repository import ScanRepository
from app.utils.ocr_engine import run_ocr


class OCRService:
    """Service xử lý nghiệp vụ OCR scan (batch + bất đồng bộ)."""

    # ── Tạo batch (chạy trong session của request) ───

    @staticmethod
    async def create_batch(
        db,
        files: list[tuple[str, str]],
        uploaded_by: str | None = None,
    ) -> ScanBatch:
        """
        Tạo 1 ScanBatch + N ScanResult (status=pending).

        Args:
            db: AsyncSession của request.
            files: danh sách (original_filename, image_path) đã lưu.
            uploaded_by: user id từ JWT (nullable).

        Returns:
            ScanBatch đã tạo (kèm scans).
        """
        batch_repo = ScanBatchRepository(db)
        scan_repo = ScanRepository(db)

        batch = ScanBatch(
            total_files=len(files),
            status="pending",
            uploaded_by=uploaded_by,
        )
        await batch_repo.create(batch)

        for original_filename, image_path in files:
            scan = ScanResult(
                batch_id=batch.id,
                original_filename=original_filename,
                image_path=image_path,
                document_type=settings.SCAN_DOC_TYPE_DEFAULT,
                status="pending",
            )
            await scan_repo.create(scan)

        # Reload để có quan hệ scans đầy đủ
        return await batch_repo.find_by_id(batch.id)

    # ── Xử lý đơn luồng (Single Upload) ──────────────

    @staticmethod
    async def process_single(
        db,
        file: tuple[str, str],
        uploaded_by: str | None = None,
    ) -> ScanResult:
        """
        Xử lý OCR cho 1 file ngay lập tức (chạy đồng bộ trong luồng request).
        
        Args:
            db: AsyncSession của request.
            file: (original_filename, image_path)
            uploaded_by: user id từ JWT.
            
        Returns:
            ScanResult đã hoàn tất.
        """
        scan_repo = ScanRepository(db)
        original_filename, image_path = file
        
        # 1. Lưu bản ghi pending
        scan = ScanResult(
            original_filename=original_filename,
            image_path=image_path,
            document_type=settings.SCAN_DOC_TYPE_DEFAULT,
            status="processing",
            uploaded_by=uploaded_by,
        )
        await scan_repo.create(scan)
        
        # 2. Gọi OCR (đồng bộ)
        try:
            result = run_ocr(scan.image_path, scan.original_filename)

            scan.ocr_text = result.get("ocr_text")
            scan.ocr_json = result.get("ocr_json")
            scan.ocr_raw_json = result.get("ocr_raw_json")
            scan.confidence_avg = result.get("confidence_avg")
            if result.get("processed_image_path"):
                scan.processed_image_path = result.get("processed_image_path")
            scan.html_content = result.get("html_content") or ""
            scan.status = "completed"
        except Exception as exc:
            scan.status = "failed"
            scan.error_message = str(exc)

        # 3. Cập nhật và trả về
        await scan_repo.update(scan)
        await db.commit()
        return scan

    # ── Background worker (session RIÊNG) ────────────

    @staticmethod
    async def process_batch(batch_id: str) -> None:
        """
        Xử lý OCR cho toàn bộ file trong batch (chạy nền).

        Mở session riêng vì session của request đã đóng. Cập nhật trạng thái
        từng scan và tiến độ của batch.
        """
        async with async_session_factory() as db:
            batch_repo = ScanBatchRepository(db)
            scan_repo = ScanRepository(db)

            batch = await batch_repo.find_by_id(batch_id)
            if batch is None:
                return

            batch.status = "processing"
            await batch_repo.update(batch)
            await db.commit()

            scans = await scan_repo.find_by_batch_id(batch_id)
            completed = 0
            failed = 0

            for scan in scans:
                try:
                    scan.status = "processing"
                    await scan_repo.update(scan)
                    await db.commit()

                    result = run_ocr(scan.image_path, scan.original_filename)

                    scan.ocr_text = result.get("ocr_text")
                    scan.ocr_json = result.get("ocr_json")
                    scan.ocr_raw_json = result.get("ocr_raw_json")
                    scan.confidence_avg = result.get("confidence_avg")
                    if result.get("processed_image_path"):
                        scan.processed_image_path = result.get("processed_image_path")
                    # HTML bảng trả trực tiếp từ PaddleOCR-VL (hoặc rỗng nếu mock)
                    scan.html_content = result.get("html_content") or ""
                    scan.status = "completed"
                    scan.error_message = None
                    completed += 1
                except Exception as exc:  # noqa: BLE001 - ghi lại lỗi vào DB
                    scan.status = "failed"
                    scan.error_message = str(exc)
                    failed += 1

                await scan_repo.update(scan)
                await db.commit()

            # Cập nhật tổng kết batch
            batch.completed_files = completed
            batch.failed_files = failed
            if failed == 0:
                batch.status = "completed"
            elif completed == 0:
                batch.status = "failed"
            else:
                batch.status = "partial_failed"
            await batch_repo.update(batch)
            await db.commit()

    # ── Truy vấn (session của request) ───────────────

    @staticmethod
    async def get_batch(db, batch_id: str) -> ScanBatch | None:
        """Lấy batch theo ID (kèm scans)."""
        return await ScanBatchRepository(db).find_by_id(batch_id)

    @staticmethod
    async def get_scan_result(db, scan_id: str) -> ScanResult | None:
        """Lấy chi tiết 1 phiếu scan."""
        return await ScanRepository(db).find_by_id(scan_id)

    @staticmethod
    async def get_all_results(db) -> list[ScanResult]:
        """Lấy danh sách tất cả phiếu scan."""
        return await ScanRepository(db).find_all()

    @staticmethod
    async def update_html_content(db, scan_id: str, html_content: str) -> ScanResult | None:
        """Cập nhật HTML sau khi user chỉnh sửa."""
        repo = ScanRepository(db)
        scan = await repo.find_by_id(scan_id)
        if scan is None:
            return None
        scan.html_content = html_content
        return await repo.update(scan)

    @staticmethod
    async def update_ocr_json(db, scan_id: str, ocr_json: dict) -> ScanResult | None:
        """Cập nhật ocr_json sau khi user sửa field."""
        repo = ScanRepository(db)
        scan = await repo.find_by_id(scan_id)
        if scan is None:
            return None
        scan.ocr_json = ocr_json
        return await repo.update(scan)

    @staticmethod
    async def delete_scan(db, scan_id: str) -> bool:
        """Xóa 1 phiếu scan."""
        return await ScanRepository(db).delete(scan_id)

    @staticmethod
    async def export_pdf(db, scan_id: str) -> tuple[str | None, str | None]:
        """
        Export phiếu scan ra PDF từ html_content.

        Returns:
            (pdf_path, None) nếu thành công;
            (None, error_key) nếu không tìm thấy / chưa có HTML / lỗi render.
        """
        from pathlib import Path

        from app.utils.pdf_generator import html_to_pdf

        scan = await ScanRepository(db).find_by_id(scan_id)
        if scan is None:
            return None, "scan.not_found"
        if not scan.html_content:
            return None, "scan.no_html"

        stem = Path(scan.original_filename).stem or scan.id
        try:
            pdf_path = html_to_pdf(scan.html_content, f"{stem}_{scan.id[:8]}")
        except RuntimeError as exc:
            return None, str(exc)
        return pdf_path, None
