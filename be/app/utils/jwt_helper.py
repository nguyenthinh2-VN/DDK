"""
JWT Helper - Tạo & verify JWT access token.

Tương đương: JwtTokenProvider trong Spring Security.

Chỉ dùng Access Token (không Refresh Token theo yêu cầu).
Token chứa: user_id (sub), username, role, role_level.
"""

from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError

from app.config.settings import settings


def create_access_token(
    user_id: str,
    username: str,
    role: str,
    role_level: int,
) -> str:
    """
    Tạo JWT access token.

    Payload gồm thông tin nhận diện user và role để phân quyền,
    kèm thời gian hết hạn (exp).
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "role_level": role_level,
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """
    Giải mã & verify JWT token.

    Returns:
        Payload (dict) nếu token hợp lệ; None nếu token sai/hết hạn.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None
