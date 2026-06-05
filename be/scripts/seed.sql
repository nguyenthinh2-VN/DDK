USE ddk_ocr;

INSERT IGNORE INTO roles (id, name, display_name, level) VALUES
  ('4782f8ca-712c-44d1-a5c9-ed02b0cdba6a', 'CEO', 'Tong giam doc', 1),
  ('31f65a3d-c5d7-47e0-bc65-70c2cb3d888a', 'THU_QUY', 'Thu quy', 2),
  ('49a6fd9a-6e97-417f-ac59-03086f73b48f', 'KE_TOAN', 'Ke toan', 3),
  ('2bbe4eb9-1945-4c59-9e78-e8e3ef601706', 'MAKER', 'Ky nhan / Maker', 4);

INSERT IGNORE INTO permissions (id, code, name) VALUES
  ('8ef55526-311e-4755-a565-e9abee852249', 'scan:upload', 'Tai anh len de scan'),
  ('39f091e6-2951-4671-98aa-beab0ed44806', 'scan:read', 'Xem ket qua scan'),
  ('ff4a42f1-7ba4-4a56-9db9-283c3df9d575', 'scan:update', 'Chinh sua ket qua scan'),
  ('f0e4f002-625b-44b8-9a82-cc0220f2e369', 'scan:delete', 'Xoa ket qua scan'),
  ('c34e3f5b-0048-46c9-bca9-5704a00c471a', 'user:create', 'Tao nguoi dung'),
  ('4e365350-21e6-49fd-80c9-a303bcdea0a9', 'user:read', 'Xem nguoi dung'),
  ('061000d4-a7b6-4a36-b978-51365408c607', 'user:update', 'Cap nhat nguoi dung'),
  ('a6381cbb-5ec2-4d4a-b1e3-6e370fabc792', 'user:delete', 'Xoa nguoi dung'),
  ('146fa191-992e-4d63-ba44-861edcbf3393', 'role:read', 'Xem vai tro'),
  ('0fec988e-4aad-4e77-941d-cad9e29003a0', 'role:assign_permission', 'Gan quyen cho vai tro'),
  ('5d2d35fa-6f49-4de3-b0b2-1e77bdc12b11', 'signature:read', 'Xem chu ky'),
  ('f4a25b7a-7ab7-4eb5-b2f4-aa74c2ee607f', 'signature:create', 'Tai len chu ky'),
  ('7399ea28-518e-4842-aad3-0fc970f87f91', 'signature:update', 'Cap nhat chu ky'),
  ('7d702537-cacb-4477-b69f-7f8c6b37a76f', 'signature:delete', 'Xoa chu ky');

INSERT IGNORE INTO role_permissions (role_id, permission_id)
SELECT '4782f8ca-712c-44d1-a5c9-ed02b0cdba6a', p.id
FROM permissions p;

INSERT IGNORE INTO role_permissions (role_id, permission_id) VALUES
  ('31f65a3d-c5d7-47e0-bc65-70c2cb3d888a', '5d2d35fa-6f49-4de3-b0b2-1e77bdc12b11'),
  ('31f65a3d-c5d7-47e0-bc65-70c2cb3d888a', 'f4a25b7a-7ab7-4eb5-b2f4-aa74c2ee607f'),
  ('31f65a3d-c5d7-47e0-bc65-70c2cb3d888a', '7399ea28-518e-4842-aad3-0fc970f87f91'),
  ('31f65a3d-c5d7-47e0-bc65-70c2cb3d888a', '7d702537-cacb-4477-b69f-7f8c6b37a76f'),
  ('49a6fd9a-6e97-417f-ac59-03086f73b48f', '5d2d35fa-6f49-4de3-b0b2-1e77bdc12b11'),
  ('49a6fd9a-6e97-417f-ac59-03086f73b48f', 'f4a25b7a-7ab7-4eb5-b2f4-aa74c2ee607f'),
  ('49a6fd9a-6e97-417f-ac59-03086f73b48f', '7399ea28-518e-4842-aad3-0fc970f87f91'),
  ('49a6fd9a-6e97-417f-ac59-03086f73b48f', '7d702537-cacb-4477-b69f-7f8c6b37a76f'),
  ('2bbe4eb9-1945-4c59-9e78-e8e3ef601706', '5d2d35fa-6f49-4de3-b0b2-1e77bdc12b11'),
  ('2bbe4eb9-1945-4c59-9e78-e8e3ef601706', 'f4a25b7a-7ab7-4eb5-b2f4-aa74c2ee607f'),
  ('2bbe4eb9-1945-4c59-9e78-e8e3ef601706', '7399ea28-518e-4842-aad3-0fc970f87f91'),
  ('2bbe4eb9-1945-4c59-9e78-e8e3ef601706', '7d702537-cacb-4477-b69f-7f8c6b37a76f');

INSERT IGNORE INTO users (id, username, hashed_password, full_name, role_id, is_active, created_at) VALUES
  (
    'a3f7d165-f825-45b8-8919-22c0f0253393',
    'admin',
    '$2b$12$Fvcm4x9SdUCPzuliV73a9eNaNMEcRjO/Ck7OxIPu9X8JvTQbg/OK2',
    'System Administrator',
    '4782f8ca-712c-44d1-a5c9-ed02b0cdba6a',
    1,
    NOW()
  );
