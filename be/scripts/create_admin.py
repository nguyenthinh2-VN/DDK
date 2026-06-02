"""
Create Admin Script - Tạo tài khoản admin (CEO) đầu tiên + seed dữ liệu.

Cách chạy (từ thư mục be/):
    py scripts/create_admin.py

Script sẽ:
1. Seed các Role mặc định (CEO, DIRECTOR, MANAGER, EMPLOYEE) nếu chưa có.
2. Seed các Permission mặc định nếu chưa có.
3. Gán TẤT CẢ permission cho role CEO.
4. Tạo user admin với role CEO (lấy thông tin từ .env hoặc nhập tay).

Lưu ý: script này độc lập, tự tạo bảng nếu chưa tồn tại.
"""

import asyncio
import getpass
import sys
from pathlib import Path

# Đảm bảo stdout dùng UTF-8 (tránh lỗi UnicodeEncodeError trên Windows cp1252)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# Cho phép import package "app" khi chạy script trực tiếp
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config.constants import DEFAULT_ROLES, DEFAULT_PERMISSIONS
from app.config.settings import settings
from app.database.base import Base
from app.database.connection import engine, async_session_factory
# Import models để đăng ký bảng với Base.metadata
from app.models import scan_result, user, role, permission, role_permission  # noqa: F401
from app.models.role import Role
from app.models.permission import Permission
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.utils.password_helper import hash_password


async def seed_roles(role_repo: RoleRepository) -> dict[str, Role]:
    """Tạo các role mặc định nếu chưa có. Trả về dict {name: Role}."""
    roles: dict[str, Role] = {}
    for name, display_name, level in DEFAULT_ROLES:
        existing = await role_repo.find_role_by_name(name)
        if existing is None:
            existing = await role_repo.create_role(
                Role(name=name, display_name=display_name, level=level)
            )
            print(f"  + Tạo role: {name} (level {level})")
        roles[name] = existing
    return roles


async def seed_permissions(role_repo: RoleRepository) -> list[Permission]:
    """Tạo các permission mặc định nếu chưa có. Trả về danh sách Permission."""
    permissions: list[Permission] = []
    for code, name in DEFAULT_PERMISSIONS:
        existing = await role_repo.find_permission_by_code(code)
        if existing is None:
            existing = await role_repo.create_permission(
                Permission(code=code, name=name)
            )
            print(f"  + Tạo permission: {code}")
        permissions.append(existing)
    return permissions


def _prompt_admin_info() -> tuple[str, str, str]:
    """Lấy thông tin admin từ .env, hoặc hỏi nhập tay nếu cần."""
    username = settings.FIRST_ADMIN_USERNAME
    password = settings.FIRST_ADMIN_PASSWORD
    full_name = settings.FIRST_ADMIN_FULLNAME

    # Chế độ non-interactive: chạy với --yes / -y -> dùng thẳng giá trị từ .env
    if "--yes" in sys.argv or "-y" in sys.argv:
        print("\n── Chế độ non-interactive: dùng thông tin admin từ .env ──")
        return username, password, full_name

    print("\n── Thông tin tài khoản admin ──")
    entered = input(f"Username [{username}]: ").strip()
    if entered:
        username = entered

    entered_pwd = getpass.getpass("Password (Enter để dùng giá trị mặc định từ .env): ").strip()
    if entered_pwd:
        password = entered_pwd

    entered_name = input(f"Full name [{full_name}]: ").strip()
    if entered_name:
        full_name = entered_name

    return username, password, full_name


async def main() -> None:
    print(f"🔧 Khởi tạo dữ liệu cho {settings.APP_NAME}...")

    # Tạo bảng nếu chưa có
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        role_repo = RoleRepository(session)
        user_repo = UserRepository(session)

        print("\n📋 Seed roles...")
        roles = await seed_roles(role_repo)

        print("\n🔑 Seed permissions...")
        permissions = await seed_permissions(role_repo)

        # Gán toàn bộ permission cho CEO
        ceo_role = roles["CEO"]
        for perm in permissions:
            await role_repo.assign_permission(ceo_role, perm)
        print(f"\n✅ Đã gán {len(permissions)} permission cho role CEO")

        # Lấy thông tin admin
        username, password, full_name = _prompt_admin_info()

        existing_user = await user_repo.find_by_username(username)
        if existing_user is not None:
            print(f"\n⚠️  User '{username}' đã tồn tại. Bỏ qua tạo mới.")
        else:
            admin = User(
                username=username,
                hashed_password=hash_password(password),
                full_name=full_name,
                role_id=ceo_role.id,
                is_active=True,
            )
            await user_repo.create(admin)
            print(f"\n✅ Đã tạo admin '{username}' với role CEO")

        await session.commit()

    await engine.dispose()
    print("\n🎉 Hoàn tất!")


if __name__ == "__main__":
    asyncio.run(main())
