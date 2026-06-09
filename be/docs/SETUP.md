# 🚀 Hướng dẫn cài đặt & chạy dự án DDK OCR Backend

---

## ❓ Tại sao `pip` và `py` khác nhau?

Đây là câu hỏi thường gặp với người mới dùng Python trên Windows.

### Vấn đề: Máy có nhiều bản Python

```
C:\Users\...\Python313\   ← Python 3.13  (py trỏ vào đây)
C:\Users\...\Python312\   ← Python 3.12  (pip trỏ vào đây)
```

Khi bạn gõ `pip install`, nó install vào Python 3.12.  
Khi bạn gõ `py -m uvicorn`, nó chạy Python 3.13 → không thấy package!

### ✅ Giải pháp: Dùng Virtual Environment (venv)

Virtual environment tạo ra 1 môi trường Python **độc lập**, chỉ dùng 1 phiên bản Python duy nhất.
Mọi `pip install` và `py` đều dùng chung 1 Python → không bao giờ lẫn lộn nữa.

---

## 📦 Lần đầu cài đặt (chỉ làm 1 lần)

> Mở PowerShell, `cd` vào thư mục `be`:

```powershell
cd e:\DDK\be
```

### Bước 1: Tạo virtual environment
```powershell
py -3.12 -m venv venv
```
> Tạo thư mục `venv/` chứa Python 3.12 riêng biệt cho dự án này.

### Bước 2: Kích hoạt venv
```powershell
.\venv\Scripts\activate
```
> Sau khi kích hoạt, terminal sẽ hiện `(venv)` ở đầu dòng:
> ```
> (venv) PS E:\DDK\be>
> ```

### Bước 3: Install dependencies
```powershell
pip install -r requirements.txt
```
> Lần này `pip` install đúng vào `venv`, không lẫn với Python hệ thống.

### Bước 4: Tải trình duyệt cho Playwright (BẮT BUỘC để xuất PDF)
Sau khi cài đặt thư viện thành công, bạn cần chạy lệnh sau để tải Chromium ẩn:
```powershell
playwright install chromium
```
> **Lưu ý trên VPS (Linux):** Khi đưa lên VPS Ubuntu/Linux, ngoài lệnh trên bạn có thể phải chạy thêm lệnh `playwright install-deps` để cài các thư viện hệ thống (system dependencies) cần thiết cho Chrome chạy được trên Linux.


---

## ▶️ Chạy server (mỗi lần làm việc)

```powershell
cd e:\DDK\be
.\venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> Sau khi activate venv rồi, dùng `uvicorn` bình thường (không cần `py -3.12 -m` nữa).

---

## 🌐 Truy cập sau khi chạy

| URL | Mô tả |
|---|---|
| http://localhost:8000 | Health check (xem server có chạy không) |
| http://localhost:8000/docs | **Swagger UI** — test API trực tiếp trên browser |
| http://localhost:8000/redoc | ReDoc — API documentation đẹp hơn |

---

## 🛑 Dừng server

Nhấn `Ctrl + C` trong terminal đang chạy uvicorn.

---

## ⚠️ Lưu ý quan trọng

- **Luôn activate venv trước khi làm việc**: `.\venv\Scripts\activate`
- **Cài thêm package**: `pip install <tên-package>` (sau khi activate)
- **Thoát venv**: gõ `deactivate`
- **Không commit thư mục `venv/`** vào git (đã có trong `.gitignore`)

---

## 📁 File dependencies

| File | Dùng khi nào |
|---|---|
| `requirements-dev.txt` | **Dùng để dev** — nhẹ, chỉ FastAPI + DB, chưa có OCR |
| `requirements.txt` | **Full production** — có PaddleOCR, WeasyPrint (nặng) |
