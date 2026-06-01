"""
OCR Service - Business Logic Layer cho chức năng scan OCR.

Tương đương: @Service class trong Spring.

Tầng Service: chứa business logic, điều phối giữa Repository và các utils.
- Xử lý logic nghiệp vụ
- Gọi Repository để đọc/ghi database
- Gọi Utils để xử lý ảnh, OCR, export...
- KHÔNG xử lý HTTP request/response (đó là việc của API layer)
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan_result import ScanResult
from app.repositories.scan_repository import ScanRepository


class OCRService:
    """
    Service xử lý nghiệp vụ OCR scan.

    Tương đương: @Service public class OCRService trong Spring.
    """

    def __init__(self, db: AsyncSession):
        self.repository = ScanRepository(db)

    async def upload_and_scan(self, filename: str, image_path: str) -> ScanResult:
        """
        Upload ảnh và bắt đầu quá trình OCR.

        TODO: Tích hợp PaddleOCR để nhận diện chữ viết tay.
        """
        scan_result = ScanResult(
            original_filename=filename,
            image_path=image_path,
            status="pending",
        )
        return await self.repository.create(scan_result)

    async def get_scan_result(self, scan_id: str) -> ScanResult | None:
        """Lấy kết quả scan theo ID."""
        return await self.repository.find_by_id(scan_id)

    async def get_all_results(self) -> list[ScanResult]:
        """Lấy tất cả kết quả scan."""
        return await self.repository.find_all()

    async def update_html_content(self, scan_id: str, html_content: str) -> ScanResult | None:
        """
        Cập nhật nội dung HTML sau khi user chỉnh sửa.

        TODO: Validate HTML content trước khi lưu.
        """
        scan_result = await self.repository.find_by_id(scan_id)
        if scan_result is None:
            return None

        scan_result.html_content = html_content
        return await self.repository.update(scan_result)

    async def export_pdf(self, scan_id: str) -> str | None:
        """
        Export HTML content sang PDF.

        TODO: Tích hợp WeasyPrint để convert HTML → PDF.

        Returns:
            Đường dẫn file PDF đã tạo, hoặc None nếu không tìm thấy scan result.
        """
        scan_result = await self.repository.find_by_id(scan_id)
        if scan_result is None or scan_result.html_content is None:
            return None

        # TODO: Implement PDF export logic
        return None

    async def delete_scan(self, scan_id: str) -> bool:
        """Xóa kết quả scan."""
        return await self.repository.delete(scan_id)
