# Chức năng chỉnh sửa thông tin OCR (Edit Mode) trên Giao diện

## Mục tiêu
Thêm tính năng cho phép người dùng sửa đổi trực tiếp các kết quả nhận dạng chữ (OCR) trên Frontend.
Đảm bảo mã nguồn dễ mở rộng cho các tính năng tương lai và thiết kế phương án tối ưu để đồng bộ dữ liệu sửa đổi giữa dạng cấu trúc (JSON) và dạng hiển thị in ấn (HTML) phục vụ xuất PDF.

## 1. Thiết kế dữ liệu dễ mở rộng (Line Items)
**Yêu cầu:** Mặc định người dùng chỉ sửa các dòng AI đã nhận diện, nhưng code cần chuẩn bị sẵn để dễ dàng bổ sung nút Add/Delete row sau này.
**Giải pháp kiến trúc:**
- Trong State của component React (`ScanViewer.tsx`), khai báo dữ liệu `line_items` dưới dạng một mảng linh hoạt (`Array<Record<string, string>>`).
- Bóc tách phần render bảng Hạng mục (Line Items) thành các đoạn map (vòng lặp).
- Các hàm `handleUpdateRow(index, field, value)` được định nghĩa chuẩn xác để xử lý việc sửa một ô. 
- Mặc dù giao diện hiện tại ẩn các nút "Thêm" hoặc "Xóa", nhưng khi có yêu cầu, lập trình viên chỉ cần tạo nút và gọi hàm `handleAddRow()` hoặc `handleDeleteRow(index)` để thay đổi State mảng mà không phá vỡ cấu trúc cũ.

## 2. Phương án tối ưu Đồng bộ JSON và HTML (PDF Export)
**Vấn đề:** Khi user sửa trên UI, ta có `ocr_json` mới. Tuy nhiên, tính năng xuất PDF và chèn chữ ký hiện đang phụ thuộc vào `html_content` gốc của PaddleOCR. Nếu không cập nhật `html_content`, dữ liệu in ra sẽ là dữ liệu cũ (bị sai).
**Giải pháp kiến trúc (Tối ưu):**
- **Đổi cơ chế lưu HTML:** Thay vì để Frontend cố gắng sửa chuỗi HTML phức tạp, Backend sẽ đảm nhận việc này. 
- **Sử dụng Template Engine:** Tại Backend, tạo một mẫu HTML chuẩn (Ví dụ: `slip_template.html` dùng Jinja2) có cấu trúc y hệt phiếu chuẩn. 
- **Cập nhật đồng thời:** Khi API `PUT /api/scan/{scan_id}/json` nhận được JSON mới từ Frontend, Backend sẽ thực hiện 2 việc:
  1. Cập nhật trường `ocr_json` vào database.
  2. Dùng JSON mới này truyền vào Jinja2 template để **vẽ lại toàn bộ** biến `html_content`, đảm bảo HTML luôn sạch sẽ, chuẩn xác và đồng bộ hoàn hảo 100% với JSON. Sau đó cập nhật `html_content` vào database.
- Bằng cách này, luồng chèn chữ ký và xuất PDF phía sau vẫn hoạt động trên một biến `html_content` hợp lệ, không bị dính mã rác hay lỗi hiển thị từ PaddleOCR raw HTML.

---

## 3. Các bước triển khai (Implementation Steps)

### Bước 1: Frontend (React) - Chế độ Edit
1. **Quản lý State**:
   - `isEditing` (boolean), `editedJson` (object sao chép từ `scan.ocr_json`).
2. **Cập nhật UI**:
   - Thêm nút "Sửa". Chuyển đổi thành "Hủy" và "Lưu" khi `isEditing = true`.
   - Các thẻ Text/`<td>` chuyển thành `<Input>` gọn gàng.
3. **Thao tác dữ liệu**:
   - Gọi `PUT /api/scan/{id}/json` với payload mới khi click Lưu.

### Bước 2: Backend (Python/FastAPI) - Đồng bộ HTML
1. **Tạo Template Jinja2**: 
   - Viết một file `app/templates/advance_payment_slip.html` dựa theo khung HTML chuẩn. Các ô có biến như `{{ info.don_vi }}`, `{{ info.ho_ten }}`, và vòng lặp `{% for item in line_items %}`.
2. **Cập nhật API `update_json`**:
   - Khi nhận `ocr_json`, hàm service gọi Jinja2 render ra chuỗi HTML mới.
   - Ghi đè vào cột `html_content` cùng lúc với `ocr_json`.

*(Kế hoạch đã chốt, chờ phản hồi "ok" từ User để bắt đầu code)*
