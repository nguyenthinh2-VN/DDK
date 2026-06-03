"""
PDF Generator - Export HTML content → PDF bằng WeasyPrint.

Tương đương: tầng tiện ích render tài liệu.

Dùng cho endpoint POST /api/scan/{id}/export-pdf. Import WeasyPrint trễ
(import bên trong hàm) vì thư viện nặng và cần native deps (GTK trên Windows).
"""

from pathlib import Path

from app.config.settings import settings

_PDF_SUBDIR = "pdf"


def _pdf_dir() -> Path:
    """Thư mục lưu PDF export (uploads/pdf/)."""
    path = Path(settings.UPLOAD_DIR) / _PDF_SUBDIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def html_to_pdf(html_content: str, filename_stem: str) -> str:
    """
    Render HTML → file PDF, trả về đường dẫn file PDF.

    Args:
        html_content: nội dung HTML (đã có CSS inline).
        filename_stem: tên file (không đuôi) cho PDF output.

    Returns:
        Đường dẫn file PDF đã tạo.

    Raises:
        RuntimeError nếu WeasyPrint không khả dụng / lỗi render.
    """
    try:
        from weasyprint import HTML
    except (ImportError, OSError) as exc:  # OSError: thiếu native deps (GTK)
        raise RuntimeError(f"WeasyPrint không khả dụng: {exc}") from exc

    out_path = _pdf_dir() / f"{filename_stem}.pdf"
    HTML(string=html_content).write_pdf(str(out_path))
    return str(out_path)
