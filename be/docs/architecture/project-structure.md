# DDK OCR Backend - Cấu trúc dự án

## Tổng quan

Dự án AI scan giấy viết tay, chuyển đổi thành HTML chỉnh sửa, rồi xuất PDF.

**Tech stack**: Python, FastAPI, PaddleOCR, Pydantic, SQLAlchemy, WeasyPrint

---

## Kiến trúc phân tầng (Layered Architecture)

```
┌──────────────────────────────────────────────┐
│  Client (FE)                                 │
└──────────────┬───────────────────────────────┘
               │ HTTP Request
┌──────────────▼───────────────────────────────┐
│  api/              🎯 Controller Layer       │
│  - Nhận request, validate input              │
│  - Trả response                              │
│  - KHÔNG chứa business logic                 │
└──────────────┬───────────────────────────────┘
               │ gọi
┌──────────────▼───────────────────────────────┐
│  schemas/          📋 DTO Layer              │
│  - Request/Response models (Pydantic)        │
│  - Validation rules                          │
│  - Tách biệt API contract vs DB entity       │
└──────────────────────────────────────────────┘

┌──────────────▼───────────────────────────────┐
│  services/         ⚙️ Service Layer          │
│  - Business logic, điều phối                 │
│  - Gọi Repository để đọc/ghi DB             │
│  - Gọi Utils để xử lý (OCR, PDF...)         │
└──────────────┬───────────────────────────────┘
               │ gọi
┌──────────────▼───────────────────────────────┐
│  repositories/     💾 Repository Layer       │
│  - CRUD operations                           │
│  - Query database                            │
│  - KHÔNG chứa business logic                 │
└──────────────┬───────────────────────────────┘
               │ gọi
┌──────────────▼───────────────────────────────┐
│  models/           🗃️ Entity Layer           │
│  - ORM models (SQLAlchemy)                   │
│  - Mapping 1:1 với bảng database             │
└──────────────┬───────────────────────────────┘
               │
┌──────────────▼───────────────────────────────┐
│  Database (SQLite)                           │
└──────────────────────────────────────────────┘
```

---

## Cây thư mục

```
be/
├── .env                          ← Cấu hình môi trường
├── .gitignore
├── requirements.txt              ← Dependencies
├── uploads/                      ← Lưu ảnh upload
│
├── docs/                         ← 📚 Tài liệu dự án
│   ├── plan/                     ← Kế hoạch triển khai
│   ├── api/                      ← API specification cho FE
│   └── architecture/             ← Tài liệu cấu trúc
│
└── app/
    ├── main.py                   ← Entry point
    ├── api/                      ← Controller (routes)
    ├── schemas/                  ← DTO (request/response)
    ├── services/                 ← Business logic
    ├── models/                   ← Entity (ORM)
    ├── repositories/             ← Data access
    ├── database/                 ← DB connection & config
    ├── config/                   ← App settings
    └── utils/                    ← Helper functions
```

---

## Quy ước code

### Đặt tên file
- Tên file: `snake_case.py`
- Tên class: `PascalCase`
- Tên function/variable: `snake_case`

### Luồng gọi
```
Controller → Service → Repository → Model → Database
```
> Controller KHÔNG được gọi thẳng Repository. Luôn đi qua Service.

### Dependency Injection
- Sử dụng `Depends()` của FastAPI
- Database session inject qua `get_db()`
