import uuid
import base64
import asyncio
import sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from app.config.settings import settings
from app.models.scan_result import ScanResult

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=False,
)

# Thư mục tìm font hỗ trợ tiếng Việt
_FONT_SEARCH_PATHS = [
    Path("C:/Windows/Fonts"),
    Path("C:/Users/THINH/AppData/Local/Microsoft/Windows/Fonts"),
    Path(__file__).resolve().parent.parent / "static" / "fonts",
]

_PREFERRED_FONTS_REGULAR = [
    "NotoSans-Regular.ttf",
    "segoeui.ttf",
    "arial.ttf",
    "Arial.ttf",
    "tahoma.ttf",
    "verdana.ttf",
]

_PREFERRED_FONTS_BOLD = [
    "NotoSans-Bold.ttf",
    "segoeuib.ttf",
    "arialbd.ttf",
    "tahomabd.ttf",
    "verdanab.ttf",
]


def _find_font(preferred_list: list[str]) -> Path | None:
    """Tìm file font hỗ trợ tiếng Việt trên hệ thống."""
    for search_dir in _FONT_SEARCH_PATHS:
        if not search_dir.exists():
            continue
        for font_name in preferred_list:
            font_path = search_dir / font_name
            if font_path.exists():
                return font_path
    return None


def _font_to_base64_face(font_path: Path, weight: str = "400") -> str:
    """Chuyển font file thành @font-face base64 CSS."""
    data = font_path.read_bytes()
    b64 = base64.b64encode(data).decode("utf-8")
    suffix = font_path.suffix.lower().lstrip(".")
    mime = "font/ttf" if suffix in ("ttf", "otf") else "font/woff2"
    return (
        "@font-face {\n"
        "  font-family: 'VietFont';\n"
        f"  src: url('data:{mime};base64,{b64}') format('truetype');\n"
        f"  font-weight: {weight};\n"
        "  font-style: normal;\n"
        "}\n"
    )


def _build_embedded_font_css() -> str:
    """Tạo CSS nhúng font tiếng Việt (regular + bold) từ file trên máy."""
    css_parts = []
    regular = _find_font(_PREFERRED_FONTS_REGULAR)
    bold = _find_font(_PREFERRED_FONTS_BOLD)
    if regular:
        css_parts.append(_font_to_base64_face(regular, "400"))
    if bold:
        css_parts.append(_font_to_base64_face(bold, "700"))
    if css_parts:
        css_parts.append(
            "body, td, th, h2 { font-family: 'VietFont', 'Arial Unicode MS', Arial, sans-serif; }\n"
        )
    return "\n".join(css_parts)


def _image_to_base64_src(img_path: Path) -> str | None:
    """Chuyển ảnh chữ ký sang data URI để nhúng trực tiếp vào HTML."""
    if not img_path.exists():
        return None
    data = img_path.read_bytes()
    b64 = base64.b64encode(data).decode("utf-8")
    suffix = img_path.suffix.lower().lstrip(".")
    mime_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
    }
    mime = mime_map.get(suffix, "image/png")
    return f"data:{mime};base64,{b64}"


def _render_html(scan: ScanResult) -> str:
    """Render HTML từ template + dữ liệu scan."""
    template = _env.get_template("advance_payment_slip_pdf.html")

    ocr_json = scan.ocr_json or {}
    info = ocr_json.get("info") or {}
    footer = ocr_json.get("footer") or {}
    line_items = ocr_json.get("line_items") or []

    safe_items = []
    for item in line_items:
        safe_items.append({
            "hang_muc": item.get("hang_muc", ""),
            "muc_dich": item.get("muc_dich", ""),
            "so_luong_don_gia": item.get("so_luong_don_gia", ""),
            "so_tien": item.get("so_tien", ""),
            "so_chung_tu": item.get("so_chung_tu", ""),
        })

    signatures_map = {}
    if scan.approvals:
        for approval in scan.approvals:
            if (
                approval.action == "APPROVED"
                and approval.signature
                and approval.signature.processed_file_path
            ):
                abs_path = (
                    Path(settings.UPLOAD_DIR).parent / approval.signature.processed_file_path
                ).resolve()
                b64_src = _image_to_base64_src(abs_path)
                if b64_src:
                    signatures_map[approval.role] = b64_src

    return template.render(
        form_no=ocr_json.get("form_no", ""),
        ngay=ocr_json.get("ngay", ""),
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
        signatures=signatures_map,
        embedded_font_css=_build_embedded_font_css(),
    )


def _playwright_pdf_sync(html_string: str, out_path: str) -> None:
    """
    Tạo PDF bằng Playwright sync API.
    Hàm này chạy trong một worker thread để tránh block main thread.
    
    CỰC KỲ QUAN TRỌNG TRÊN WINDOWS:
    Mặc định Python dùng WindowsSelectorEventLoopPolicy cho các child thread,
    mà event loop đó KHÔNG hỗ trợ subprocess (cần thiết để chạy trình duyệt).
    Do đó, phải ép kiểu WindowsProactorEventLoopPolicy riêng cho thread này!
    """
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html_string, wait_until="networkidle")
        page.pdf(
            path=out_path,
            format="A4",
            landscape=True,
            margin={"top": "15mm", "bottom": "15mm", "left": "15mm", "right": "15mm"},
            print_background=True,
        )
        browser.close()


async def generate_advance_payment_pdf(scan: ScanResult) -> str:
    """
    Tạo file PDF từ kết quả scan và trả về đường dẫn file PDF.
    
    Sử dụng asyncio.to_thread() để đưa việc tạo PDF nặng (Playwright) 
    sang một background thread để không block event loop của FastAPI.
    """
    out_dir = Path(settings.UPLOAD_DIR) / "pdf"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = str(out_dir / f"phieu_tam_ung_{scan.id}_{uuid.uuid4().hex[:6]}.pdf")

    # Tạo HTML (nhanh)
    html_string = _render_html(scan)

    # Đưa việc render PDF sang background thread
    await asyncio.to_thread(_playwright_pdf_sync, html_string, out_path)

    return out_path
