import uuid
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from app.config.settings import settings
from app.models.scan_result import ScanResult

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=False,
)

def generate_advance_payment_pdf(scan: ScanResult) -> str:
    """
    Tạo file PDF từ kết quả scan và trả về đường dẫn file PDF tạm.
    Sử dụng xhtml2pdf để tránh lỗi phụ thuộc GTK trên Windows.
    """
    from xhtml2pdf import pisa

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

    # Lấy danh sách chữ ký
    signatures_map = {}
    if scan.approvals:
        for approval in scan.approvals:
            if approval.action == "APPROVED" and approval.signature and approval.signature.processed_file_path:
                abs_path = (Path(settings.UPLOAD_DIR).parent / approval.signature.processed_file_path).resolve()
                if abs_path.exists():
                    signatures_map[approval.role] = abs_path.as_posix() # xhtml2pdf dùng path bình thường

    html_string = template.render(
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
        signatures=signatures_map
    )

    out_dir = Path(settings.UPLOAD_DIR) / "pdf"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"phieu_tam_ung_{scan.id}_{uuid.uuid4().hex[:6]}.pdf"

    with open(out_path, "w+b") as result_file:
        pisa_status = pisa.CreatePDF(html_string, dest=result_file)

    if pisa_status.err:
        raise Exception("Không thể tạo file PDF với xhtml2pdf")

    return str(out_path)
