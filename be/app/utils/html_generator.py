"""
HTML Generator - Dựng lại bố cục phiếu thành HTML <table> từ ocr_json.

Tương đương: tầng render/view tạo HTML cho FE chỉnh sửa.

Mục tiêu: tái dựng bố cục giống ảnh phiếu tạm ứng. Nhãn IN SẴN của form
được hard-code trong HTML/CSS (lấy từ template), KHÔNG đọc từ ocr_json.
ocr_json chỉ chứa GIÁ TRỊ user điền (đúng theo business rule).

Mỗi field giá trị có shape:
    { "value": str, "confidence": float|None, "value_int": int? , "date": str? }
Ô có confidence < ngưỡng được bọc <span class="low-confidence"> để FE bôi đỏ.
"""

from typing import Any

from app.config.settings import settings


def _esc(value: Any) -> str:
    """Escape HTML cơ bản."""
    if value is None:
        return ""
    text = str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _cell(field: dict | None) -> str:
    """Render value 1 ô; bọc span cảnh báo nếu confidence dưới ngưỡng."""
    if not field:
        return ""
    value = _esc(field.get("value", ""))
    if not value:
        return ""
    conf = field.get("confidence")
    threshold = settings.OCR_CONFIDENCE_WARN_THRESHOLD
    if conf is not None and conf < threshold:
        return f'<span class="low-confidence" data-confidence="{conf}">{value}</span>'
    return value


def generate_html(ocr_json: dict) -> str:
    """Build HTML phiếu tạm ứng từ ocr_json."""
    if not ocr_json:
        return "<div class='ocr-page'><p>(Chưa có dữ liệu OCR)</p></div>"

    info = ocr_json.get("info", {}) or {}
    line_items = ocr_json.get("line_items", []) or []
    footer_data = ocr_json.get("footer", {}) or {}

    form_no = _cell(ocr_json.get("form_no"))
    ngay = _cell(ocr_json.get("ngay"))

    # Header
    head = f"""
    <div class="slip-header">
      <div class="company">
        <strong>鋒明(越南)國際有限公司</strong><br/>
        DDK PRO ACTIVE GLOBAL VIETNAM CO.,LTD
      </div>
      <div class="title">
        <strong>預支單</strong><br/>
        PHIẾU TẠM ỨNG
      </div>
      <div class="meta">
        <div>號碼 / Số: {form_no}</div>
        <div>日期 / Ngày: {ngay}</div>
      </div>
    </div>
    """

    info_row = f"""
    <table class="slip-info">
      <tr>
        <th>單位<br/>Đơn vị</th><td>{_cell(info.get('don_vi'))}</td>
        <th>姓名<br/>Họ tên</th><td>{_cell(info.get('ho_ten'))}</td>
        <th>卡號<br/>Số thẻ</th><td>{_cell(info.get('so_the'))}</td>
        <th>主管<br/>Chủ quản</th><td>{_cell(info.get('chu_quan'))}</td>
      </tr>
    </table>
    """

    rows_html = ""
    for idx, item in enumerate(line_items, start=1):
        muc_dich = item.get("muc_dich") or {}
        date_prefix = ""
        if muc_dich.get("date"):
            date_prefix = f'<span class="li-date">{_esc(muc_dich["date"])}</span> '
        rows_html += f"""
      <tr>
        <td class="c-stt">{idx}</td>
        <td>{_cell(item.get('hang_muc'))}</td>
        <td>{date_prefix}{_cell(muc_dich)}</td>
        <td>{_cell(item.get('so_luong_don_gia'))}</td>
        <td>{_cell(item.get('so_tien'))}</td>
        <td>{_cell(item.get('so_chung_tu'))}</td>
      </tr>"""
    if not rows_html:
        rows_html = '<tr><td class="c-stt">1</td><td></td><td></td><td></td><td></td><td></td></tr>'

    items_table = f"""
    <table class="slip-items">
      <thead>
        <tr>
          <th>序號<br/>STT</th>
          <th>項目<br/>Hạng mục</th>
          <th>用途說明<br/>Mục đích sử dụng</th>
          <th>數量單價<br/>Số lượng x Đơn giá</th>
          <th>金額<br/>Số tiền</th>
          <th>單據號碼<br/>Số chứng từ</th>
        </tr>
      </thead>
      <tbody>{rows_html}
      </tbody>
    </table>
    """

    so_tien_tam_ung = _cell(footer_data.get("so_tien_tam_ung"))
    footer = f"""
    <table class="slip-footer">
      <tr>
        <th>預支金額<br/>Số tiền tạm ứng</th><td>{so_tien_tam_ung}</td>
        <th>簽收<br/>Ký nhận</th><td></td>
        <th>實支<br/>Thực chi</th><td></td>
        <td class="checkbox">[ ] 補 Bổ sung<br/>[ ] 退 Trả lại</td>
      </tr>
      <tr>
        <th>總經理<br/>Tổng Giám Đốc</th><td></td>
        <th>出納<br/>Thủ quỹ</th><td></td>
        <th>會計<br/>Kế toán</th><td></td>
        <th>出納<br/>Thủ quỹ</th>
      </tr>
    </table>
    """

    css = """
    <style>
      .ocr-page { font-family: Arial, "Microsoft JhengHei", sans-serif; color:#b30000; width:100%; }
      .slip-header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px; }
      .slip-header .title { text-align:center; font-size:20px; }
      .slip-header .meta { text-align:right; font-size:12px; }
      .ocr-page table { width:100%; border-collapse:collapse; margin-bottom:6px; }
      .ocr-page th, .ocr-page td { border:1px solid #b30000; padding:4px 6px; font-size:13px; vertical-align:top; }
      .ocr-page th { font-weight:normal; white-space:nowrap; width:1%; }
      .slip-items tbody td { height:40px; }
      .slip-items .c-stt { text-align:center; width:6%; }
      .low-confidence { background:#ffe0e0; color:#c00; border-bottom:2px dotted #c00; }
      .li-date { font-weight:bold; color:#0050b3; margin-right:4px; }
      .checkbox { font-size:12px; white-space:nowrap; }
    </style>
    """

    return f'<div class="ocr-page">{css}{head}{info_row}{items_table}{footer}</div>'
