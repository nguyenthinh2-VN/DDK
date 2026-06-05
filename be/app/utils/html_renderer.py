"""
HTML Renderer - Render ocr_json thành HTML bằng Jinja2 template.

Sử dụng khi user chỉnh sửa JSON trên FE → cần đồng bộ html_content
để phục vụ chèn chữ ký và xuất PDF.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# Thư mục chứa templates
_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=False,  # HTML template, không cần escape
)


def render_slip_html(ocr_json: dict) -> str:
    """
    Render ocr_json thành chuỗi HTML dựa trên template phiếu tạm ứng.

    Args:
        ocr_json: dict chứa các trường info, line_items, footer, ...

    Returns:
        Chuỗi HTML đã render.
    """
    template = _env.get_template("advance_payment_slip.html")

    # Chuẩn bị dữ liệu với default rỗng để Jinja không bị lỗi KeyError
    info = ocr_json.get("info") or {}
    footer = ocr_json.get("footer") or {}
    line_items = ocr_json.get("line_items") or []

    # Đảm bảo mỗi item có đủ key
    safe_items = []
    for item in line_items:
        safe_items.append({
            "hang_muc": item.get("hang_muc", ""),
            "muc_dich": item.get("muc_dich", ""),
            "so_luong_don_gia": item.get("so_luong_don_gia", ""),
            "so_tien": item.get("so_tien", ""),
            "so_chung_tu": item.get("so_chung_tu", ""),
        })

    return template.render(
        info={
            "don_vi": info.get("don_vi", ""),
            "ho_ten": info.get("ho_ten", ""),
            "so_the": info.get("so_the", ""),
            "chu_quan": info.get("chu_quan", ""),
        },
        line_items=safe_items,
        footer={
            "so_tien_tam_ung": footer.get("so_tien_tam_ung", ""),
            "ky_nhan": footer.get("ky_nhan", ""),
            "thuc_chi": footer.get("thuc_chi", ""),
            "tong_giam_doc": footer.get("tong_giam_doc", ""),
            "thu_quy_1": footer.get("thu_quy_1", ""),
            "ke_toan": footer.get("ke_toan", ""),
            "thu_quy_2": footer.get("thu_quy_2", ""),
        },
    )
