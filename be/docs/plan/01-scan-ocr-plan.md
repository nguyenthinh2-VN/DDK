# 📋 Plan: Chức năng Scan OCR - v3 (Tối giản)

> **Mục tiêu**: User upload ảnh phiếu tạm ứng DDK → BE gọi **PaddleOCR-VL API** (aistudio) → Trả kết quả (markdown + HTML table + JSON structured chỉ chứa giá trị user điền) → Lưu DB → FE hiển thị.

---

## 1. Quy trình đơn giản

```
Upload ảnh (1–5 file)
        │
        ▼
(Tùy chọn) OpenCV Preprocess ← bật/tắt qua OCR_PREPROCESS_ENABLED
        │
        ▼
PaddleOCR-VL API ← 2 mode:
  │
  ├── 1 file → Sync API (nhanh, 1 request, không polling)
  │     POST https://hanaj6q2m6oc0bpa.aistudio-app.com/layout-parsing
  │     Auth: token <TOKEN>
  │     Body: { file: base64, fileType: 1 (image) }
  │     Response trực tiếp: { result: { layoutParsingResults: [...] } }
  │
  └── Nhiều file (batch) → Gọi Sync API N lần (tối đa 5 file song song)
        Hoặc nếu file lớn/chậm → Async API (submit + poll mỗi file):
          POST https://paddleocr.aistudio-app.com/api/v2/ocr/jobs
          Auth: bearer <TOKEN>
          Rồi polling GET /jobs/{jobId} cho đến done
        │
        ▼
Parse markdown → trích xuất JSON structured (chỉ giá trị user điền)
Parse markdown → trích HTML bảng (cho FE hiển thị)
        │
        ▼
Lưu DB: ocr_text, ocr_json, html_content, ocr_raw_json
        │
        ▼
FE nhận: JSON structured + HTML bảng + ảnh gốc
```

### So sánh 2 mode API

| | Sync (layout-parsing) | Async (jobs) |
|---|---|---|
| Endpoint | `https://hanaj6q2m6oc0bpa.aistudio-app.com/layout-parsing` | `https://paddleocr.aistudio-app.com/api/v2/ocr/jobs` |
| Auth header | `token <TOKEN>` | `bearer <TOKEN>` |
| Input | Base64 encoded file + fileType | Multipart file hoặc fileUrl |
| Xử lý | Đồng bộ — 1 request trả kết quả luôn | Bất đồng bộ — submit → poll → download |
| Phù hợp | 1 file, ảnh nhỏ, cần response nhanh | File lớn, PDF nhiều trang |
| Dùng cho batch | Gọi song song N lần (tối đa 5) | Cũng được nhưng chậm hơn (phải poll) |

**Quyết định**: Dùng **Sync API** cho pipeline chính (nhanh, đơn giản). Nếu 1–5 file → gọi sync song song. Giữ async API trong client để dự phòng (file quá lớn / timeout).

---

## 2. Business Rule

- **Form CỐ ĐỊNH** — nhãn in sẵn biết trước, KHÔNG OCR nhãn, KHÔNG trả nhãn trong JSON.
- **Chỉ trích xuất User Values** (giá trị người dùng điền: viết tay / đánh máy).
- PaddleOCR-VL API tự xử lý orientation, deskew, layout → ta KHÔNG cần làm các bước đó ở BE.
- **Chuyển giản thể → phồn thể**: API đôi khi trả về chữ giản thể (简体) cho chữ viết tay phồn thể. Sau khi parse xong JSON, chạy bước **Simplified → Traditional conversion** cho tất cả text field trước khi lưu DB / trả FE.

---

## 2.1 Pipeline xử lý chi tiết

```
API trả Markdown (có HTML bảng)
        │
        ▼
Parse markdown → trích xuất giá trị user → JSON thô
        │
        ▼
Chuyển giản thể → phồn thể (Simplified → Traditional)
  Thư viện: opencc-python-reimplemented hoặc OpenCC (s2t conversion)
  Chỉ convert các field text_cn/text_mixed (info.ho_ten, hang_muc, muc_dich, chu_quan)
  KHÔNG convert field số (form_no, so_the, so_tien, so_luong_don_gia)
        │
        ▼
JSON sạch (phồn thể) → lưu DB → trả FE
```

---

## 3. Output JSON (chỉ giá trị thật)

```json
{
  "document_type": "advance_payment_slip",
  "form_no": "000046",
  "ngay": "2026年5月27日",
  "info": {
    "don_vi": "KD",
    "ho_ten": "高雄盛",
    "so_the": "1789900",
    "chu_quan": ""
  },
  "line_items": [
    {
      "hang_muc": "水务",
      "muc_dich": "5/27 不正家，所以會使日求合求喝。",
      "so_luong_don_gia": "9,700,900",
      "so_tien": "9,700,900",
      "so_chung_tu": ""
    }
  ],
  "footer": {
    "so_tien_tam_ung": "1,700,000"
  }
}
```

---

## 4. Cấu trúc thư mục (hiện tại)

```
app/
├── ocr/
│   ├── __init__.py               ← package init
│   ├── preprocess.py             ← (tùy chọn) OpenCV grayscale + denoise + CLAHE
│   └── paddleocr_vl_client.py    ← Client 2 mode: sync (layout-parsing) + async (jobs)
├── utils/
│   ├── ocr_engine.py             ← Entry point: run_ocr() → preprocess → sync API → parse → JSON
│   ├── image_helper.py           ← validate extension/size + save upload
│   ├── i18n.py, response_helper.py, password_helper.py, jwt_helper.py, auth_guard.py
│   └── pdf_generator.py          ← WeasyPrint HTML→PDF
├── api/scan.py                   ← Endpoints batch upload + polling + CRUD
├── services/ocr_service.py       ← Batch logic + background worker gọi run_ocr
├── models/, repositories/, schemas/, config/, database/

scripts/
├── paddleocr_vl_scan.py          ← CLI: gọi 1 file (sync) hoặc nhiều file (batch sync song song)
├── create_admin.py, seed.sql, migrate_scan_v2.sql
```

---

## 5. Files CẦN XÓA (không dùng nữa)

| File | Lý do |
|---|---|
| `app/ocr/orientation.py` | API tự xử lý orientation |
| `app/ocr/zone_extractor.py` | Không crop zone nữa |
| `app/ocr/post_process.py` | Cleaning giờ trong ocr_engine |
| `app/ocr/orchestrator.py` | Pipeline cũ đã thay |
| `app/ocr/debug.py` | Debug zone-based cũ |
| `app/ocr/providers.py` | Providers zone-based cũ |
| `app/ocr/alignment.py` | ĐÃ XÓA |
| `app/utils/html_generator.py` | HTML lấy từ API, không generate nữa |
| `app/templates/advance_payment_slip.json` | Template zone-based cũ |
| `app/templates/advance_payment_slip.bak.json` | Backup template cũ |
| `scripts/template_marker.py` | Tool click-to-mark zone cũ |
| `scripts/debug_scan.py` | Debug zone-based cũ |

---

## 6. Files GIỮ LẠI

| File | Vai trò |
|---|---|
| `app/ocr/__init__.py` | Package init |
| `app/ocr/preprocess.py` | OpenCV tiền xử lý (tùy chọn bật/tắt) |
| `app/ocr/paddleocr_vl_client.py` | Client 2 mode: sync + async |
| `app/utils/ocr_engine.py` | Entry point: run_ocr() — gọi sync API → parse → JSON |
| `app/services/ocr_service.py` | Batch + background worker |
| `app/api/scan.py` | REST endpoints |
| `scripts/paddleocr_vl_scan.py` | CLI test: 1 file (sync) hoặc batch (sync song song) |

---

## 7. Settings (.env)

```env
OCR_ENABLED=true                    # false=mock, true=gọi API thật
OCR_PREPROCESS_ENABLED=false        # bật/tắt OpenCV trước khi gửi ảnh
PADDLEOCR_VL_TOKEN=<token>          # Token aistudio (dùng chung cho cả 2 mode)
PADDLEOCR_VL_MODEL=PaddleOCR-VL-1.6

# Sync API (chính — nhanh, 1 request):
PADDLEOCR_VL_SYNC_URL=https://hanaj6q2m6oc0bpa.aistudio-app.com/layout-parsing

# Async API (dự phòng — file lớn / PDF):
PADDLEOCR_VL_ASYNC_URL=https://paddleocr.aistudio-app.com/api/v2/ocr/jobs

# Batch
SCAN_BATCH_MIN_FILES=1
SCAN_BATCH_MAX_FILES=5
```

---

## 8. API Endpoints

| Method | Endpoint | Mô tả |
|---|---|---|
| `POST` | `/api/scan/batch` | Upload 1–5 file → tạo batch → xử lý nền → HTTP 202 |
| `GET` | `/api/scan/batch/{id}` | Polling tiến độ batch |
| `GET` | `/api/scan/{id}` | Chi tiết 1 phiếu (ocr_json + html_content + ảnh gốc) |
| `GET` | `/api/scan/` | Danh sách scan |
| `PUT` | `/api/scan/{id}/html` | Lưu HTML chỉnh sửa |
| `PUT` | `/api/scan/{id}/json` | Lưu ocr_json chỉnh sửa |
| `POST` | `/api/scan/{id}/export-pdf` | Export PDF |
| `DELETE` | `/api/scan/{id}` | Xóa |

---

## 9. Trạng thái triển khai

| Hạng mục | Trạng thái |
|---|---|
| Auth + RBAC (plan 02) | ✅ Done |
| DB schema (scan_batches + scan_results v2) | ✅ Done |
| Batch upload + async + polling | ✅ Done |
| PaddleOCR-VL Async API integration | ✅ Done |
| PaddleOCR-VL Sync API integration | ❌ TODO — thêm `call_sync()` vào client |
| Parse markdown → JSON structured | ✅ Done |
| Giản thể → Phồn thể (s2t conversion) | ❌ TODO — thêm bước convert sau parse |
| HTML bảng trả từ API → lưu DB → FE dùng | ✅ Done |
| OpenCV preprocess (tùy chọn) | ✅ Done (tắt mặc định) |
| PDF export (WeasyPrint) | ⚠️ Cần native GTK trên Windows |
| Xóa file cũ (section 5) | ❌ Chưa xóa — chờ xác nhận |
| Script CLI batch (sync song song) | ❌ TODO |
| FE hiển thị (ảnh gốc + bảng kết quả) | ❌ Chưa làm (FE) |

---

## 10. UI FE — Thiết kế chi tiết

### Layout tổng

```
┌─────────────────────────────────────────────────────────────────────┐
│  Toolbar: [Upload] [Save] [Export PDF]        Phiếu 1/5  ◁ ▷       │
├────────────────────────────────┬────────────────────────────────────┤
│  PANEL TRÁI: Ảnh gốc           │  PANEL PHẢI: Form render           │
│  ┌──────────────────────────┐  │  ┌──────────────────────────────┐ │
│  │                          │  │  │  DDK logo    預支單            │ │
│  │   Ảnh scan gốc           │  │  │  鋒明(越南)   PHIẾU TẠM ỨNG   │ │
│  │   (zoom / pan)           │  │  │                                │ │
│  │                          │  │  │  號碼: [__000046__]            │ │
│  │   Khi hover 1 field bên  │  │  │  日期: [__2026年5月27日__]      │ │
│  │   phải → vẽ bbox đỏ lên  │  │  │                                │ │
│  │   ảnh gốc ở đây          │  │  │  ┌────┬──────┬──────┬──────┐ │ │
│  │                          │  │  │  │單位 │姓名   │卡號   │主管  │ │ │
│  │                          │  │  │  │Đơn vị│Họ tên│Số thẻ│Chủ quản│ │
│  │                          │  │  │  │[KD] │[高翊庭]│[1789900]│[不用]│ │
│  │                          │  │  │  ├────┼──┬───┼──────┼──┬───┤ │ │
│  │                          │  │  │  │STT │項目│用途說明│數量單價│金額│號碼│ │
│  │                          │  │  │  │    │Hạng│Mục đích│Số lượng│Số tiền│Số│ │
│  │                          │  │  │  │ 1  │[水务]│[5/27..]│[9700000]│[9700000]│[ ]│ │
│  │                          │  │  │  ├────┴──┴───┴──────┴──┴───┤ │ │
│  │                          │  │  │  │ Footer (ký tên — read-only) │ │
│  │                          │  │  │  │ 預支金額: [1,700,000]        │ │
│  │                          │  │  │  └──────────────────────────┘ │ │
│  └──────────────────────────┘  │  └──────────────────────────────┘ │
│  [🔍 Zoom] [🔄 Rotate]         │  [✏️ Edit mode] [JSON view]        │
└────────────────────────────────┴────────────────────────────────────┘
```

### Nguyên tắc hiển thị

| Phần | Nguồn | Editable? |
|---|---|---|
| Nhãn cố định (單位, 姓名, 卡號...) | Hard-code trong HTML/CSS của FE | ❌ Không |
| Giá trị user điền (KD, 高翊庭, 1789900...) | Lấy từ `ocr_json` (API GET /api/scan/{id}) | ✅ Có — input/textarea |
| Ảnh gốc | `image_path` (API trả URL) | ❌ Không (xem only) |
| Bbox highlight trên ảnh | Lấy từ `ocr_raw_json` (nếu API trả bbox) hoặc dùng tọa độ template cố định | ❌ |

### Tương tác Hover / Highlight

1. FE render form phải dạng **bảng HTML cố định** (không dùng html_content từ API mà tự render layout từ `ocr_json`).
2. Mỗi ô giá trị (`<input>` / `<td>`) gán `data-field="info.ho_ten"` + `data-bbox="[x0,y0,x1,y1]"`.
3. Khi **hover** 1 ô bên phải:
   - Lấy `data-bbox` → vẽ rectangle overlay lên ảnh gốc bên trái (dùng canvas/SVG overlay).
   - Ô bên phải highlight border xanh.
4. Khi **click** ô → vào edit mode (biến thành input). User sửa xong → gọi `PUT /api/scan/{id}/json` để lưu.

### Bbox từ đâu?

**Cách 1 (đơn giản — dùng trước):** Dùng tọa độ CỐ ĐỊNH (% tương đối) cho từng field — giống template.json nhưng ở FE. Vì form cố định nên bbox của mỗi field không đổi giữa các phiếu (chỉ cần ước lượng 1 lần cho form DDK).

**Cách 2 (chính xác hơn — làm sau):** Từ PaddleOCR-VL API output JSONL, trích `layoutParsingResults` → mỗi block có bounding box. Map block vào field → truyền bbox thật qua `ocr_raw_json`. FE đọc từ đó để vẽ box chính xác.

### Chỉnh sửa giá trị

- FE render mỗi giá trị trong `<input>` (text ngắn) hoặc `<textarea>` (mục đích dài).
- User sửa trực tiếp trên form.
- Bấm "Save" → gọi `PUT /api/scan/{id}/json` với toàn bộ `ocr_json` đã sửa.
- Giá trị confidence thấp (từ `low_confidence_fields`) → viền ô đỏ + tooltip "Cần kiểm tra".

### Component FE gợi ý (React/Vue)

```
ScanViewer/
├── ScanToolbar.vue           ← Upload, Save, Export, Navigation
├── ImagePanel.vue            ← Ảnh gốc + bbox overlay (canvas/SVG)
├── FormPanel.vue             ← Form render cố định + input giá trị
│   ├── FormHeader.vue        ← Logo, tiêu đề, 號碼, 日期
│   ├── FormInfoRow.vue       ← 單位, 姓名, 卡號, 主管
│   ├── FormLineItems.vue     ← Bảng line items (có thể nhiều dòng)
│   └── FormFooter.vue        ← 預支金額 + ký tên (read-only)
└── JsonView.vue              ← Tab xem/sửa raw JSON (developer mode)
```

---

## 11. Cải thiện độ chính xác (nếu cần sau)

1. Bật `OCR_PREPROCESS_ENABLED=true` nếu ảnh nhiễu / mờ.
2. Dùng `useDocOrientationClassify: true` trong API payload nếu ảnh bị xoay.
3. Cập nhật model mới khi PaddleOCR-VL ra version mới (đổi `PADDLEOCR_VL_MODEL`).
4. Fine-tune PaddleOCR local nếu API không đủ chính xác cho chữ viết tay cụ thể của công ty.

---

## 12. Chuyển giản thể → phồn thể (chi tiết)

### Vấn đề
PaddleOCR-VL dùng model `chinese` (có thể trả giản thể cho chữ viết tay phồn thể):
- Input: `高雄盛` (phồn thể) → OCR trả: `高雄盛` ✅ (đúng)
- Input: `處理` (phồn thể) → OCR trả: `处理` ❌ (giản thể)
- Input: `會使用` (phồn thể) → OCR trả: `会使用` ❌ (giản thể)

### Giải pháp
Sau khi parse JSON, chạy conversion `s2t` (Simplified to Traditional) cho các field chữ.

### Thư viện
```
opencc-python-reimplemented==0.1.7
```
Hoặc `opencc` (C binding, nhanh hơn nhưng cần compile). Dùng bản reimplemented (pure Python) cho đơn giản.

### Config
```env
# Bật/tắt chuyển giản thể → phồn thể
OCR_S2T_ENABLED=true
# Conversion config: s2t (Simplified to Traditional — Taiwan standard)
OCR_S2T_CONFIG=s2t
```

### Fields cần convert (chữ Hán):
- `info.ho_ten`
- `info.chu_quan`
- `line_items[].hang_muc`
- `line_items[].muc_dich`

### Fields KHÔNG convert (số / Latin / ngày):
- `form_no`, `ngay`, `info.don_vi`, `info.so_the`
- `line_items[].so_luong_don_gia`, `line_items[].so_tien`, `line_items[].so_chung_tu`
- `footer.so_tien_tam_ung`

---

## 12. Ghi chú

- PaddleOCR-VL API **free tier có giới hạn** (số page/ngày). Nếu dùng production volume lớn → cần plan trả phí hoặc tự host PaddleOCR-VL.
- Hiện `html_content` lưu HTML bảng từ API (có cả nhãn + giá trị). `ocr_json` chỉ chứa giá trị user điền. FE chọn dùng cái nào tùy mục đích hiển thị.
- WeasyPrint cần native GTK trên Windows; nếu không cài được → PDF export sẽ trả lỗi graceful. Trên Linux chạy bình thường.
