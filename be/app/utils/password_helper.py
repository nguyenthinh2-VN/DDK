"""
Password Helper - Hash & verify mật khẩu bằng bcrypt.

Tương đương: PasswordEncoder (BCryptPasswordEncoder) trong Spring Security.

Không bao giờ lưu mật khẩu plaintext. Luôn hash trước khi lưu DB.
"""

from passlib.context import CryptContext

# Context cấu hình thuật toán hash (bcrypt)
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash mật khẩu plaintext -> chuỗi hash bcrypt để lưu DB."""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """So sánh mật khẩu plaintext với hash đã lưu. True nếu khớp."""
    return _pwd_context.verify(plain_password, hashed_password)
