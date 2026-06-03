# Tổng kết Luồng Xử Lý Từ Upload Lên Đến Hiển Thị FE (End-to-End Flow)

Tài liệu này tóm tắt toàn bộ quy trình chạy từ lúc người dùng (Frontend) tải ảnh lên, Backend xử lý đa luồng với PaddleOCR, cho đến khi dữ liệu hiển thị hoàn chỉnh lên giao diện.

## 1. Giai đoạn Upload (Giao tiếp Đồng bộ)
1. **Frontend**: Người dùng chọn 3 ảnh và nhấn Upload. FE gửi POST request (`multipart/form-data`) tới endpoint `/api/scan/batch` của Backend.
2. **Backend Controller (`upload_batch`)**:
   - Validate định dạng và dung lượng của các file.
   - Lưu các file vật lý vào ổ cứng (thư mục `uploads/`).
   - Mở giao dịch Database (DB):
     - Tạo 1 dòng `ScanBatch` (status = `pending`).
     - Tạo 3 dòng `ScanResult` (status = `pending`) tham chiếu đến `ScanBatch` này.
   - Trả về HTTP 202 (Accepted) kèm `batch_id` ngay lập tức cho Frontend.
3. **Frontend**: Chuyển giao diện sang màn hình "Đang xử lý / Loading" mà không bị treo trình duyệt do phải đợi AI xử lý dài hạn.

## 2. Giai đoạn AI Xử Lý (Giao tiếp Bất đồng bộ / Background Task)
1. **FastAPI Background Task**: Hàm `OCRService.process_batch(batch_id)` bắt đầu chạy ngầm ở phía sau.
2. Cập nhật trạng thái của 3 bản ghi `ScanResult` thành `processing`.
3. **Đa Luồng (Multi-threading)**:
   - Sử dụng `asyncio.gather` và `asyncio.to_thread`, Backend khởi tạo 3 luồng song song chạy hàm `run_ocr` cho 3 file.
   - Các luồng đồng thời gọi API PaddleOCR qua HTTP POST (`submit_job`), sau đó poll liên tục để tải file JSON kết quả về (`poll_job`).
4. **Bóc tách và Xử lý Markdown (Data Parsing)**:
   - Backend lấy HTML ra từ chuỗi Markdown của PaddleOCR.
   - Xóa bỏ hàng chữ ký của "Tổng Giám Đốc" khỏi HTML.
   - Trích xuất thông tin vào đối tượng JSON có cấu trúc (`ocr_json`) qua hàm `_extract_fields_from_markdown`.
5. **Cập nhật Database**:
   - Lưu `ocr_json`, `html_content` vào DB.
   - Chuyển status của `ScanResult` thành `completed` (hoặc `failed`).
   - Cập nhật tiến trình của `ScanBatch` thành `completed`.

## 3. Giai đoạn Trả Kết Quả Về Giao Diện (Polling)
1. **Frontend Polling**: Trong khi Backend đang làm bước 2, FE liên tục gọi API GET `/api/scan/batch/{batch_id}` (mỗi ~2 giây) để hỏi tiến độ xử lý.
2. Khi API Polling trả về `status: "completed"`, FE nhận được ID cụ thể của các bản ghi `ScanResult` vừa được xử lý thành công.
3. FE lấy chi tiết từng kết quả qua API GET `/api/scan/{scan_id}`.
4. **Hiển thị Giao diện (React Render)**:
   - Vẽ bảng "Bảng chi tiết" dựa trên trường `ocr_json`.
   - Các trường như `don_vi`, `ho_ten`, `line_items` được dàn vào giao diện song ngữ Việt - Đài (được code cứng bằng thẻ table HTML React).
   - Vẽ khung (Bbox - bounding box) lên trên ảnh gốc nếu người dùng hover vào các hàng bên bảng dữ liệu.

## 4. Chỉnh sửa Thông tin (Tương lai)
Người dùng có thể ấn nút "Chỉnh sửa" trên UI, thay đổi giá trị trong các Form Input, và FE sẽ gọi API `PUT /api/scan/{scan_id}/json` để ghi đè kết quả OCR vào trong DB.
