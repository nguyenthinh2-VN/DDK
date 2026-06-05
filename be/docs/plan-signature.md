# Plan Phase 1: Upload chu ky, 1 account = 1 chu ky active

## Progress

- [x] Cap nhat role constants sang `CEO`, `THU_QUY`, `KE_TOAN`, `MAKER`
- [x] Cap nhat `seed.sql` them role va permission `signature:*`
- [x] Tao bang `signatures`
- [x] Tao migration script `be/scripts/migrate_signature.sql`
- [x] Tao backend `model / repository / service / schema / router` cho chu ky
- [x] Ho tro 2 mode upload:
  - [x] Backend tu xoa nen
  - [x] Upload anh da xoa nen san
- [x] Xu ly anh chu ky bang OpenCV va xuat PNG
- [x] Tao frontend page quan ly chu ky trong `fe/`
- [x] Them route va sidebar menu cho trang chu ky
- [x] Cho phep xem chu ky hien tai va go chu ky hien tai
- [ ] Workflow ky tuan tu
- [ ] Reject / tra ve maker
- [ ] Sign history
- [ ] Chen chu ky vao ScanViewer / PDF

## Pham vi da lam

Phase nay chi tap trung vao nen mong:

1. Moi tai khoan co toi da 1 chu ky active.
2. User co the upload anh chu ky moi.
3. User co the chon:
   - backend tu xoa nen
   - anh da trong suot san
4. He thong luu file goc va file da xu ly.
5. Frontend co trang rieng de upload, preview, thay the va xoa chu ky.

## Auth / role

Role hien tai trong codebase da duoc doi ve:

- `CEO`
- `THU_QUY`
- `KE_TOAN`
- `MAKER`

Code lien quan:

- `be/app/config/constants.py`
- `be/scripts/seed.sql`

Luu y:

- Cac endpoint admin dang dung check theo level van duoc giu tuong thich qua alias constant.

## Database

Bang moi:

- `signatures`

Muc dich:

- Luu chu ky cua user
- Danh dau `is_active`
- Luu ca file goc va file da xu ly

Script:

- `be/scripts/migrate_signature.sql`

## Backend API da lam

Router:

- `be/app/api/signature.py`

Endpoints:

- `POST /api/signatures/upload`
- `GET /api/signatures/me`
- `DELETE /api/signatures/me`

### Request upload

`multipart/form-data`

Fields:

- `file`
- `signer_name`
- `remove_background`

### Rule upload

- Cho phep `.png`, `.jpg`, `.jpeg`
- Gioi han 3 MB
- Neu user da co chu ky active:
  - chu ky cu se bi set `is_active = false`
  - chu ky moi tro thanh active

## Xu ly anh

Helper:

- `be/app/utils/signature_image_helper.py`

Da ho tro:

1. Luu file goc vao `uploads/signatures/original/`
2. Neu `remove_background = true`:
   - dung OpenCV threshold + morphology
   - tao PNG co alpha nen trong suot
3. Neu `remove_background = false`:
   - chuan hoa anh dau vao thanh PNG
   - giu nguyen nen trong suot neu file da co san
4. Luu file ket qua vao `uploads/signatures/processed/`

## Frontend da lam

Trang moi:

- `fe/src/pages/Signature/SignatureManager.tsx`

Da ho tro:

- upload chu ky
- chon mode xoa nen / da xoa nen san
- preview anh vua chon
- xem chu ky active hien tai
- go chu ky active

Route:

- `/signature`

Menu:

- da them vao sidebar

## File da tao

Backend:

- `be/app/models/signature.py`
- `be/app/repositories/signature_repository.py`
- `be/app/services/signature_service.py`
- `be/app/schemas/signature_schema.py`
- `be/app/api/signature.py`
- `be/app/utils/signature_image_helper.py`
- `be/scripts/migrate_signature.sql`

Frontend:

- `fe/src/pages/Signature/SignatureManager.tsx`

## File da sua

Backend:

- `be/app/config/settings.py`
- `be/app/config/constants.py`
- `be/app/main.py`
- `be/app/models/user.py`
- `be/scripts/seed.sql`

Frontend:

- `fe/src/App.tsx`
- `fe/src/contexts/AuthContext.tsx`
- `fe/src/layouts/DashboardLayout.tsx`
- `fe/src/pages/Dashboard/Dashboard.tsx`
- `fe/tsconfig.app.json`

## Verification

Da verify:

- [x] Backend compile OK bang bundled Python runtime

Chua verify tron ven:

- [ ] FE build clean

Ly do:

- Repo hien dang thieu mot so package Radix trong moi truong build (`@radix-ui/react-dropdown-menu`, `@radix-ui/react-scroll-area`, `@radix-ui/react-tabs`), khong phai loi moi do page chu ky tao ra.

## Buoc tiep theo de code tiep

1. Chay migration tao bang `signatures`
2. Seed lai roles / permissions neu DB hien tai van dang dung role cu
3. Noi ScanViewer voi chu ky active cua user
4. Lam workflow ky tuan tu va sign history
