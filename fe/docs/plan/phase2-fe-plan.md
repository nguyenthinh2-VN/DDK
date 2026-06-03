# Kế hoạch Phase 2: FE (Layout chia đôi màn hình & Bounding Box Viewer)

## 1. Mục tiêu
- Tạo màn hình chi tiết phiếu Scan phân làm 2 nửa (Split Screen): Trái là ảnh, Phải là Dữ liệu.
- Giữ nguyên bố cục dữ liệu (Render lại bảng HTML) để User dễ nhìn.
- Tính năng Bounding Box Hover: Đưa chuột vào phần tử bên phải sẽ bôi sáng vùng tương ứng trên ảnh bên trái.

## 2. Các công việc cần thực hiện

### 2.1 Cập nhật Dashboard UI
- Gọi API `GET /api/stats/dashboard`.
- Dùng `Card` của Shadcn để hiển thị 3 chỉ số: Tổng số file upload, Tổng số phiếu đã scan thành công, Tổng số phiếu lỗi.
- Hiện danh sách các bản scan dưới dạng Bảng (Table), bấm vào một dòng sẽ chuyển sang trang `ScanViewer`.

### 2.2 Trang ScanViewer (Mới)
**Path**: `/scan/:id`

**Bố cục (Layout)**:
Dùng `grid` hoặc `flex` chia đôi màn hình:
- **Left Panel (Image Viewer)**:
  - Cung cấp **Nút chuyển đổi (Toggle/Tabs)** để chọn 1 trong 2 chế độ xem ảnh:
    1. **Chế độ mặc định**: Hiển thị ảnh tĩnh gốc (`image_path`). Gắn Overlay Bounding Box ẩn, chỉ hiện khi Hover chuột bên nửa dữ liệu.
    2. **Chế độ xem Bbox của Paddle**: Hiển thị ảnh đã được thuật toán khoanh sẵn Bbox và đánh nhãn (`bbox_image_url` vd: `layout_det_res_0.jpg`). 
  
- **Right Panel (Data Viewer)**:
  - Hiển thị `html_content` trực tiếp thông qua `dangerouslySetInnerHTML` để giữ nguyên bố cục dạng bảng như phiếu gốc.
  - Thêm các khối hiển thị các Field rời rạc (Số Phiếu, Ngày Tháng).
  - **Cảnh báo độ tin cậy**: Dựa vào trường `score` trả về từ Backend, nếu có bất kỳ trường nào có `score < 0.8` (độ tự tin < 80%), hiển thị một Icon cảnh báo (⚠️) màu đỏ/vàng ngay bên cạnh dữ liệu đó để người dùng chú ý kiểm tra.
  - Gắn sự kiện `onMouseEnter` và `onMouseLeave` vào các khối này để cập nhật state `hoveredBbox`.

### 2.3 Xử lý Bounding Box (Phân tích kĩ thuật)
Dựa trên JSON thực tế từ PaddleOCR, Backend sẽ trả về `table_bbox`, `form_no_bbox`, `ngay_bbox`... dưới dạng mảng 4 số `[x_min, y_min, x_max, y_max]` tương ứng với tọa độ pixel trên ảnh gốc.
- FE cần lấy **kích thước thật** của ảnh (Natural Width/Height) và **kích thước hiển thị** trên trình duyệt để tính tỷ lệ (Scale).
- Công thức: `box_left = x_min * scale_x`, `box_width = (x_max - x_min) * scale_x`.
### 2.4 Hỗ trợ Đa ngôn ngữ (i18n)
- Giữ nguyên cơ chế chuyển đổi ngôn ngữ (Tiếng Việt / Tiếng Trung) như màn hình Login.
- Thêm Language Switcher trên thanh Header của Dashboard.
- Cập nhật state `lang` lưu vào `localStorage("app_language")`.
- Tất cả API Axios call trong Dashboard và ScanViewer phải tiếp tục tự động đính kèm Header `Accept-Language: vi` (hoặc `tw`) thông qua Axios Interceptor để Backend trả thông báo chuẩn.
- Các Text tĩnh (Label, Header, Title) trên UI sẽ được chuyển đổi tự động dựa vào bộ từ điển JSON hoặc state ngữ cảnh.
