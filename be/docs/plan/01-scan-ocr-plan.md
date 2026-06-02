# 📋 Plan: Chức năng Scan OCR - Cập nhật (v2)

> **Mục tiêu**: User upload **nhiều ảnh** (tối thiểu 3, tối đa 5) phiếu giấy theo **mẫu form cố định** → BE dùng PaddleOCR nhận diện text **kèm tọa độ** → Trích xuất ra **JSON có cấu trúc theo từng ô của form** → Lưu DB → Generate **HTML tái dựng đúng bố cục bảng như ảnh** → (sau cùng) Export PDF. Xử lý **bất đồng bộ** (FE polling). Hỗ trợ đa ngôn ngữ (i18n).

---

## 0. Bối cảnh & Phân tích mẫu form

Ảnh upload là **phiếu tạm ứng (預支單 / PHIẾU TẠM ỨNG)** của DDK — một **biểu mẫu cố định**:

- **Nhãn (label) in sẵn**: song ngữ Tiếng Trung **phồn thể (繁體)** + Tiếng Việt đánh máy → đã biết trước, KHÔNG cần OCR.
- **Giá trị do người dùng điền** (sẽ có ở phiếu thật): chủ yếu là **chữ Trung phồn thể viết tay** + **chữ số** (số tiền, ngày, số thẻ). Có vài ô đánh máy.
- **Bố cục cố định**: vị trí các ô (đơn vị, họ tên, số thẻ, ngày, bảng line-item...) gần như không đổi giữa các phiếu.
- **KHÔNG xử lý 2 dòng cuối** (khu phê duyệt/ký tên: 預支金額·簽收·實支·Bổ sung·Trả lại và 總經理·出納·會計·出納) — đây là ô ký tay/đóng dấu, không cần OCR.

> 📌 **Lưu ý về ảnh mẫu**: Ảnh đang dùng để phân tích là **form TRẮNG (mới in, đánh máy, chưa điền tay)**. Ta dùng nó để **xác định trước tọa độ từng ô (zone)**. Phần OCR điền `value` sẽ áp dụng khi có phiếu đã điền tay thật.

> 💡 **Hệ quả quan trọng**: Vì form cố định, ta dùng chiến lược **OCR theo vùng (template/zone-based extraction)**. PaddleOCR trả về **text + bounding box (tọa độ)** cho từng cụm chữ → ta map mỗi cụm vào đúng "ô" của form dựa trên tọa độ → xuất ra JSON có cấu trúc. **Trả lời câu hỏi: CÓ, OCR in ra được vị trí nhận diện (bounding box) cho từng text.**

---

## 1. Trả lời các câu hỏi xác nhận (đã chốt)

| # | Câu hỏi | Quyết định |
|---|---|---|
| 1 | Ngôn ngữ chữ viết | Mẫu có **Trung phồn thể (viết tay + đánh máy)** và **Việt đánh máy**. Dùng model OCR **`chinese_cht`** (phồn thể) làm chính cho phần viết tay. Nhãn tiếng Việt in sẵn → lấy từ template, không cần OCR. Cho phép **OCR 2 pass** nếu cần (pass 1: `chinese_cht`, pass 2: `vi`) rồi gộp kết quả theo tọa độ. |
| 2 | Đồng bộ / Bất đồng bộ | **Bất đồng bộ**. Upload **1 lần nhiều file (min 3, max 5)** → trả về `batch_id` + danh sách `scan_id` ở trạng thái `pending` → BE xử lý nền (BackgroundTasks) → **FE polling** lấy kết quả. |
| 3 | HTML output | **Tái dựng bố cục giống ảnh**: render lại thành `<table>` mô phỏng đúng layout phiếu (header, các ô thông tin, bảng line-item), điền giá trị OCR vào đúng ô. 2 dòng cuối (ký tên/phê duyệt) chỉ vẽ lại khung trống, không OCR. Không chỉ `<p>` đơn giản. |
| 4 | Multi-page PDF | **Chưa cần**. Hiện tại **1 ảnh = 1 trang = 1 phiếu**. Sẽ cập nhật sau. |

---

## 1.5. Về thư viện OCR & câu hỏi "có cần training không?" + repo PaddleOCR

### a) `paddleocr` (pip) vs repo `github.com/PaddlePaddle/PaddleOCR` — khác gì nhau?

| | Thư viện mình đang dùng (`pip install paddleocr`) | Repo trên GitHub (`PaddlePaddle/PaddleOCR`) |
|---|---|---|
| Bản chất | **Package Python** cài qua pip, gọi trong code | **Toàn bộ mã nguồn + tài liệu + công cụ** của dự án PaddleOCR |
| Dùng để | Nhúng vào BE để chạy OCR (detect + recognize) | Nơi chứa code gốc, model zoo, scripts **train/fine-tune**, pipeline nâng cao (PP-Structure), demo, docs |
| Quan hệ | Chính là bản đóng gói của repo đó | "Nhà máy" sinh ra package; cài pip = lấy phần đã build sẵn |

> **Kết luận**: Repo không phải "thư viện khác" — nó là **nguồn của chính `paddleocr`**. Cài qua pip là đủ để chạy. Vào repo chỉ cần khi muốn: (1) **fine-tune model**, (2) dùng **PP-Structure** (phân tích bảng/layout), (3) tải model zoo, (4) xem ví dụ chi tiết.

### b) Repo đó có gì hữu ích cho mình?

- **PP-StructureV3** — pipeline phân tích tài liệu: **table recognition** (nhận diện bảng), layout detection, khôi phục thứ tự đọc, xuất Markdown/HTML. Hữu ích trực tiếp vì phiếu của mình **là một cái bảng** → có thể tự dựng cấu trúc bảng. *(theo tài liệu PaddleOCR — nội dung đã được diễn giải lại để tuân thủ bản quyền).*
- **PP-OCRv5 / model đa ngôn ngữ** — một model nhận cả Trung giản thể, **phồn thể**, tiếng Anh, **chữ viết tay**... → đúng nhu cầu phiếu viết tay phồn thể.
- **Scripts train/fine-tune** — nếu sau này độ chính xác chữ viết tay chưa đạt, đây là nơi để fine-tune.

> ⚠️ *Nguồn: tài liệu chính thức PaddleOCR ([paddlepaddle.github.io/PaddleOCR](https://paddlepaddle.github.io/PaddleOCR/)). Nội dung đã được diễn giải lại cho phù hợp giấy phép.*

### c) Có CẦN training không?

**Giai đoạn đầu: KHÔNG cần.** Lý do:

1. PaddleOCR có **model pretrained sẵn** cho phồn thể + chữ viết tay → cài pip là chạy được ngay, không train.
2. Form **cố định** → phần khó (hiểu cấu trúc) mình **giải quyết bằng template/zone-mapping** (toạ độ ô đã biết), không phụ thuộc độ "thông minh" của model.
3. Nhãn in sẵn lấy từ template, model **chỉ cần đọc giá trị** trong từng ô → bài toán nhẹ hơn nhiều.

**Khi nào CẦN cân nhắc fine-tune?**

- Chữ viết tay phồn thể của nhân viên bị nhận sai nhiều dù ảnh rõ.
- Có **chữ ký/ký tự hiếm** hoặc kiểu viết đặc thù model chưa quen.

→ Lúc đó mới thu thập vài trăm mẫu phiếu đã điền + nhãn đúng để **fine-tune model recognition**. Hiện tại **chưa làm**; ưu tiên chạy pretrained + cho user sửa lại field (đã có endpoint sửa JSON/HTML).

### d) Chiến lược chốt cho dự án

- **Bước 1 (giờ)**: dùng `paddleocr` pretrained (`chinese_cht`) + **zone mapping theo template** → đủ chạy, không train.
- **Bước 2 (nếu cần)**: thử **PP-Structure** table recognition để tự dựng bảng, so sánh với cách zone-mapping thủ công.
- **Bước 3 (chỉ khi độ chính xác kém)**: fine-tune model recognition bằng scripts trong repo.

---

## 1.6. Tiền xử lý ảnh bằng OpenCV (nâng chất lượng trước khi OCR)

**Câu trả lời: CÓ — nên dùng.** Ảnh phiếu là **scan giấy viết tay**, thường bị nghiêng, nhiễu, sáng/tối không đều, viền bảng mờ. OpenCV làm sạch ảnh **trước khi** đưa vào PaddleOCR → tăng đáng kể độ chính xác (đặc biệt với chữ viết tay phồn thể) và giúp **map field theo tọa độ** chuẩn hơn (vì bảng được căn thẳng).

### Pipeline tiền xử lý đề xuất (file `utils/image_preprocess.py`)

| Bước | Kỹ thuật OpenCV | Mục đích |
|---|---|---|
| 1. Grayscale | `cv2.cvtColor` | Bỏ màu, giảm dữ liệu thừa (phiếu mực đỏ/xanh) |
| 2. Khử nhiễu | `cv2.fastNlMeansDenoising` / `medianBlur` | Xóa đốm nhiễu khi scan |
| 3. Tăng tương phản | `CLAHE` (adaptive histogram) | Làm nét chữ mờ, cân bằng sáng |
| 4. Nhị phân hóa | `adaptiveThreshold` / Otsu | Tách chữ khỏi nền giấy |
| 5. **Deskew (căn thẳng)** | phát hiện góc nghiêng + `warpAffine` xoay | Bảng thẳng → bbox khớp template |
| 6. (tùy chọn) Bỏ đường kẻ bảng | morphology (erode/dilate) | Tránh đường kẻ bị nhận nhầm thành nét chữ |

> Quan trọng nhất với form viết tay: **deskew** + **adaptiveThreshold**. Các bước khác bật/tắt tùy chất lượng ảnh thực tế.

### Lưu ý
- Lưu **ảnh đã xử lý** vào `uploads/processed/` (giữ ảnh gốc để đối chiếu & cho user xem). OCR chạy trên ảnh đã xử lý; tọa độ bbox map về **ảnh đã xử lý (đã deskew)**.
- Nếu mực phiếu là **đỏ/xanh nhạt** → có thể tách kênh màu (chỉ giữ nét chữ) trước khi grayscale để chữ rõ hơn.
- Tiền xử lý là **tùy chọn bật/tắt** qua config `OCR_PREPROCESS_ENABLED` để dễ so sánh kết quả có/không xử lý.

> ⚠️ `paddlepaddle`/`paddleocr` thường đã kéo theo `opencv-python` (`cv2`). Nếu chưa có sẽ thêm `opencv-python-headless` vào requirements (bản headless nhẹ, hợp server không GUI).

---


## 2. Hỗ trợ đa ngôn ngữ (i18n)

- **API Messages**: lỗi ("File không hợp lệ", "Không tìm thấy"...) và message thành công được dịch theo header `Accept-Language` (`vi` mặc định / `tw` = Trung phồn thể). Dùng chung cơ chế i18n đã có ở module Auth (`app/utils/i18n.py`, `app/locales/vi.json`, `app/locales/tw.json`).
- **OCR Engine**: cấu hình model PaddleOCR `chinese_cht` để đọc chữ phồn thể; tùy chọn pass 2 `vi` cho phần tiếng Việt viết/đánh máy.

---

## 3. Luồng xử lý (bất đồng bộ + batch)

```
┌─────────┐  Upload 3-5 ảnh (multipart)   ┌──────────────┐
│   FE    │ ────────────────────────────► │  POST /api/  │
│ (User)  │  Accept-Language: tw          │  scan/batch  │
└─────────┘                               └──────┬───────┘
     ▲                                           │  (1) Tạo ScanBatch + N ScanResult (status=pending)
     │  batch_id + danh sách scan_id             │  (2) Kick BackgroundTasks xử lý nền
     │◄──────────────────────────────────────────┘  (3) Trả response NGAY (HTTP 202)
     │
     │           ┌──────────── Background Worker ─────────────┐
     │           │  Với mỗi file:                              │
     │           │   status=processing                         │
     │           │   ⓪ OpenCV tiền xử lý ảnh (deskew, khử nhiễu,│
     │           │      tăng tương phản, nhị phân hóa)          │
     │           │   ① PaddleOCR (chinese_cht) → text + bbox    │
     │           │   ② (tùy chọn) pass 2 lang=vi → gộp theo bbox│
     │           │   ③ Map bbox → field theo template          │
     │           │   ④ Build ocr_json (structured)             │
     │           │   ⑤ Build html_content (tái dựng bảng)       │
     │           │   status=completed (hoặc failed + error)    │
     │           └─────────────────────────────────────────────┘
     │
     │  Polling: GET /api/scan/batch/{batch_id}
     └──────────────────────────────────────────► trả tiến độ + kết quả từng file
```

---

## 4. Cấu trúc JSON kết quả OCR (structured) + độ tin cậy từng ô

Mỗi phiếu sau khi OCR → 1 JSON mô tả đầy đủ các ô của form. **Mỗi ô có giá trị `value` kèm `confidence`** (độ tin cậy 0.0–1.0) để FE cảnh báo ô nào quét chưa chắc chắn. Đề xuất schema cho **Phiếu tạm ứng**:

```json
{
  "document_type": "advance_payment_slip",
  "form_no": { "value": "000566", "confidence": 0.99 },
  "card_no_top": { "value": "0530011", "confidence": 0.95 },
  "header": {
    "company": "DDK PRO ACTIVE GLOBAL VIETNAM CO.,LTD",
    "company_cn": "鋒明(越南)國際有限公司",
    "title_cn": "預支單",
    "title_vi": "PHIẾU TẠM ỨNG"
  },
  "info": {
    "don_vi":   { "label_cn": "單位", "label_vi": "Đơn vị",   "value": "KD",      "confidence": 0.88 },
    "ho_ten":   { "label_cn": "姓名", "label_vi": "Họ tên",   "value": "...",     "confidence": 0.62 },
    "so_the":   { "label_cn": "卡號", "label_vi": "Số thẻ",   "value": "2909051", "confidence": 0.93 },
    "chu_quan": { "label_cn": "主管", "label_vi": "Chủ quản", "value": "",        "confidence": null },
    "ngay":     { "label_cn": "日期", "label_vi": "Ngày",     "value": "2026-05-27", "raw": "2026年5月27日", "confidence": 0.71 }
  },
  "line_items": [
    {
      "stt": 1,
      "hang_muc":         { "label_cn": "項目",     "value": "...",      "confidence": 0.55 },
      "muc_dich":         { "label_cn": "用途說明", "value": "多中午用餐 主TUV處理及討論 Reach-RoHs...", "confidence": 0.48 },
      "so_luong_don_gia": { "label_cn": "數量單價", "value": "294,000",  "confidence": 0.90 },
      "so_tien":          { "label_cn": "金額",     "value": "294000",   "confidence": 0.92 },
      "so_chung_tu":      { "label_cn": "單據號碼", "value": "",         "confidence": null }
    }
  ],
  "low_confidence_fields": ["info.ho_ten", "line_items[0].hang_muc", "line_items[0].muc_dich", "info.ngay"],
  "confidence_avg": 0.78
}
```

> 🚫 **KHÔNG quét 2 dòng cuối của phiếu** (khu phê duyệt/ký tên: 預支金額·簽收·實支·補 Bổ sung·退 Trả lại và 總經理·出納·會計·出納 / Tổng Giám Đốc·Thủ quỹ·Kế toán·Thủ quỹ). Đây là các ô **ký tên / đóng dấu tay** → không có giá trị text cần OCR. Bỏ hẳn `footer` khỏi JSON kết quả.

### Quy ước độ tin cậy (confidence)
- Mỗi ô có giá trị OCR → thêm khóa `confidence` (float `0.0`–`1.0`), lấy từ điểm tin cậy mà PaddleOCR trả về cho cụm chữ. Nếu 1 ô gộp nhiều cụm chữ → lấy **trung bình** (hoặc min, sẽ chốt khi code).
- Ô **rỗng / không quét được** → `confidence: null` (không phải 0, để phân biệt "trống" với "quét ra nhưng sai").
- `confidence_avg`: trung bình confidence của các ô **có giá trị** trong phiếu (đã có cột DB `confidence_avg`).
- `low_confidence_fields`: danh sách đường dẫn field có `confidence` **dưới ngưỡng** `OCR_CONFIDENCE_WARN_THRESHOLD` (mặc định `0.75`, cấu hình ở settings). FE dùng list này để **bôi đỏ / cảnh báo** nhanh, khỏi phải tự duyệt toàn bộ JSON.

- Chỉ quét & trích xuất các vùng: `header` (lấy từ template), `info`, `line_items`. **Không** quét khu ký tên/phê duyệt ở 2 dòng cuối.
- **Output thô của PaddleOCR** (text + bbox + confidence từng cụm) KHÔNG đưa vào JSON kết quả; chỉ lưu riêng ở cột DB `ocr_raw_json` để debug / re-map về sau.

> ⚠️ Ảnh mẫu hiện tại là **form trắng (đánh máy, chưa điền tay)** → ở trên ta chỉ đang **định nghĩa trước vị trí (zone) của từng ô**. Khi có phiếu điền tay thật, các `value` + `confidence` mới được OCR điền vào.
>
> Template vùng (toạ độ tương đối từng ô) lưu trong `app/templates/advance_payment_slip.json` để dễ tinh chỉnh mà không sửa code.

---

## 5. Thiết kế Database (cập nhật)

### Bảng MỚI: `scan_batches` (gom 1 lần upload nhiều file)

| Column | Type | Constraint | Mô tả |
|---|---|---|---|
| `id` | VARCHAR(36) | PK, UUID | ID batch |
| `total_files` | INT | NOT NULL | Tổng số file trong batch |
| `completed_files` | INT | DEFAULT 0 | Số file đã xử lý xong |
| `failed_files` | INT | DEFAULT 0 | Số file lỗi |
| `status` | VARCHAR(20) | DEFAULT 'pending' | pending → processing → completed (/ partial_failed) |
| `uploaded_by` | VARCHAR(36) | FK users.id, NULLABLE | User upload (từ JWT) |
| `created_at` | DATETIME | AUTO | |
| `updated_at` | DATETIME | AUTO | |

### Bảng `scan_results` (cập nhật — thêm cột)

| Column | Type | Constraint | Mô tả |
|---|---|---|---|
| `id` | VARCHAR(36) | PK, UUID | |
| `batch_id` | VARCHAR(36) | FK scan_batches.id, NULLABLE | Thuộc batch nào |
| `original_filename` | VARCHAR(255) | NOT NULL | |
| `image_path` | VARCHAR(500) | NOT NULL | |
| `document_type` | VARCHAR(50) | DEFAULT 'advance_payment_slip' | Loại phiếu (mở rộng sau) |
| `ocr_text` | LONGTEXT | NULLABLE | Text OCR gộp (plain) |
| `ocr_json` | JSON | NULLABLE | **Kết quả structured (mục 4)** |
| `ocr_raw_json` | JSON | NULLABLE | Output thô PaddleOCR (text+bbox+confidence) |
| `html_content` | LONGTEXT | NULLABLE | HTML tái dựng bố cục |
| `confidence_avg` | FLOAT | NULLABLE | Độ tin cậy trung bình |
| `status` | VARCHAR(20) | DEFAULT 'pending' | pending → processing → completed / failed |
| `error_message` | TEXT | NULLABLE | Lý do nếu failed |
| `created_at` | DATETIME | AUTO | |
| `updated_at` | DATETIME | AUTO | |

> Đổi `ocr_text`/`html_content` sang **LONGTEXT** (MySQL) cho nội dung dài. Thêm `ocr_json`, `ocr_raw_json` kiểu **JSON** của MySQL.
> Script cập nhật bảng: `scripts/migrate_scan_v2.sql` (ALTER TABLE thêm cột + tạo bảng `scan_batches`).

---

## 6. API Endpoints (cập nhật)

| Method | Endpoint | Mô tả | Auth |
|---|---|---|---|
| `POST` | `/api/scan/batch` | Upload **3–5 file** 1 lần → tạo batch, xử lý nền, trả `batch_id` + scan ids (HTTP 202) | ✅ (`scan:upload`) |
| `GET` | `/api/scan/batch/{batch_id}` | **Polling**: tiến độ batch + trạng thái/kết quả từng file | ✅ (`scan:read`) |
| `GET` | `/api/scan/{scan_id}` | Chi tiết 1 phiếu: `ocr_json` + `html_content` + ảnh | ✅ (`scan:read`) |
| `GET` | `/api/scan/` | Danh sách scan (phân trang sau) | ✅ (`scan:read`) |
| `PUT` | `/api/scan/{scan_id}/html` | Lưu HTML sau khi user chỉnh sửa | ✅ (`scan:update`) |
| `PUT` | `/api/scan/{scan_id}/json` | Lưu lại `ocr_json` sau khi user sửa field | ✅ (`scan:update`) |
| `POST` | `/api/scan/{scan_id}/export-pdf` | Export PDF từ HTML (Phase 3) | ✅ (`scan:read`) |
| `DELETE` | `/api/scan/{scan_id}` | Xóa 1 phiếu | ✅ (`scan:delete`) |

### Ràng buộc upload batch
- Số file: **min 3, max 5** (cấu hình `SCAN_BATCH_MIN_FILES=3`, `SCAN_BATCH_MAX_FILES=5` trong settings) → vi phạm trả `422`.
- Mỗi file validate extension + dung lượng như cũ.

### Response mẫu `POST /api/scan/batch` (202 Accepted)
```json
{
  "batch_id": "b1b2...",
  "total_files": 3,
  "status": "pending",
  "items": [
    { "scan_id": "s1...", "original_filename": "phieu1.jpg", "status": "pending" },
    { "scan_id": "s2...", "original_filename": "phieu2.jpg", "status": "pending" },
    { "scan_id": "s3...", "original_filename": "phieu3.jpg", "status": "pending" }
  ],
  "message": "Đã nhận 3 file, đang xử lý OCR"
}
```

### Response mẫu `GET /api/scan/batch/{batch_id}`
```json
{
  "batch_id": "b1b2...",
  "status": "processing",
  "total_files": 3,
  "completed_files": 1,
  "failed_files": 0,
  "items": [
    { "scan_id": "s1...", "status": "completed", "confidence_avg": 0.91 },
    { "scan_id": "s2...", "status": "processing" },
    { "scan_id": "s3...", "status": "pending" }
  ]
}
```

---

## 7. Cấu trúc thư mục bổ sung

```
app/
├── models/
│   ├── scan_result.py        (cập nhật: thêm cột)
│   └── scan_batch.py         (MỚI)
├── schemas/
│   └── scan_schema.py        (cập nhật: batch DTO, structured JSON DTO)
├── services/
│   └── ocr_service.py        (cập nhật: batch + background + structured extract)
├── repositories/
│   ├── scan_repository.py    (cập nhật)
│   └── scan_batch_repository.py (MỚI)
├── utils/
│   ├── image_preprocess.py   (MỚI: OpenCV deskew + làm sạch ảnh trước OCR)
│   ├── paddle_ocr.py         (MỚI: wrapper PaddleOCR, lazy-load model)
│   ├── field_mapper.py       (MỚI: map bbox → field theo template)
│   └── html_generator.py     (MỚI: dựng HTML bảng từ ocr_json)
├── templates/
│   └── advance_payment_slip.json (MỚI: định nghĩa vùng/ô của form)
└── api/
    └── scan.py               (cập nhật: endpoint batch + polling + json)

scripts/
└── migrate_scan_v2.sql       (MỚI: ALTER bảng + tạo scan_batches)
```

---

## 8. Kế hoạch triển khai (thứ tự code)

### Phase 1 — DB & khung batch bất đồng bộ
- [ ] Step 1: Cập nhật model `scan_result.py` + tạo `scan_batch.py`; viết `scripts/migrate_scan_v2.sql`.
- [ ] Step 2: Repositories (`scan_batch_repository.py`, cập nhật `scan_repository.py`).
- [ ] Step 3: DTO batch + structured JSON trong `scan_schema.py`.
- [ ] Step 4: `POST /api/scan/batch` (validate 3–5 file) + BackgroundTasks + `GET /api/scan/batch/{id}` polling. (Giai đoạn này OCR có thể trả mock để chạy luồng trước.)

### Phase 2 — OCR thực + structured extraction
- [ ] Step 5: `utils/image_preprocess.py` — OpenCV: grayscale, khử nhiễu, CLAHE, adaptiveThreshold, **deskew**; lưu ảnh đã xử lý vào `uploads/processed/`.
- [ ] Step 6: `utils/paddle_ocr.py` — wrapper PaddleOCR `chinese_cht` (lazy load 1 lần), chạy trên ảnh đã tiền xử lý, trả text+bbox+confidence.
- [ ] Step 7: `templates/advance_payment_slip.json` + `utils/field_mapper.py` — map bbox → field → build `ocr_json`.
- [ ] Step 8: (tùy chọn) OCR pass 2 `lang=vi`, gộp kết quả theo bbox.
- [ ] Step 9: Tích hợp vào background worker; lưu `ocr_json` (kèm `confidence` từng ô + `low_confidence_fields`), `ocr_raw_json`, `confidence_avg`.

### Phase 3 — HTML tái dựng & chỉnh sửa
- [ ] Step 10: `utils/html_generator.py` — render `<table>` đúng bố cục phiếu từ `ocr_json`.
- [ ] Step 11: `PUT /api/scan/{id}/html` và `PUT /api/scan/{id}/json` để lưu chỉnh sửa của user.

### Phase 4 — Export PDF
- [ ] Step 12: WeasyPrint render HTML → PDF; `POST /api/scan/{id}/export-pdf`.

---

## 9. Phụ thuộc & cấu hình

```text
# requirements (đã có)
paddleocr==2.10.0
paddlepaddle==3.1.0
weasyprint==65.0
pillow==11.2.1
```

```text
# settings.py (thêm)
OCR_LANG_PRIMARY=chinese_cht     # model phồn thể
OCR_LANG_SECONDARY=vi            # pass 2 (tùy chọn)
OCR_USE_TWO_PASS=false           # bật/tắt OCR 2 lần
OCR_CONFIDENCE_WARN_THRESHOLD=0.75   # field dưới ngưỡng này → đưa vào low_confidence_fields để cảnh báo
SCAN_BATCH_MIN_FILES=3
SCAN_BATCH_MAX_FILES=5
SCAN_DOC_TYPE_DEFAULT=advance_payment_slip
```

> ⚠️ Lần đầu chạy PaddleOCR sẽ tải model `chinese_cht` (vài trăm MB). Cần kết nối mạng lần đầu; model được cache lại cho các lần sau.

---

## 10. Rủi ro & ghi chú

- **Chữ viết tay phồn thể** độ chính xác OCR thường thấp hơn chữ in → cho phép user **chỉnh sửa JSON/HTML** (đã có endpoint). Mỗi ô lưu kèm `confidence`, cộng `confidence_avg` toàn phiếu và `low_confidence_fields` để FE **bôi đỏ / cảnh báo** đúng ô quét chưa chắc chắn.
- **Map field theo tọa độ** phụ thuộc form được scan thẳng, ít lệch. Nếu ảnh nghiêng → cân nhắc bước **deskew/căn chỉnh** ảnh trước OCR (có thể thêm ở `utils/paddle_ocr.py` bằng OpenCV — bổ sung sau nếu cần).
- **BackgroundTasks** của FastAPI chạy in-process, đủ cho quy mô nội bộ. Nếu sau này tải nặng → chuyển sang hàng đợi (Celery/RQ) — chưa làm ở giai đoạn này.
- **1 ảnh = 1 phiếu**: nếu sau cần PDF nhiều trang / nhiều phiếu/ảnh → mở rộng `scan_batch` + tách trang.
