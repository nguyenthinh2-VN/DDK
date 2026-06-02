"""
Response Helper - Tiện ích cho i18n response & exception.

Cung cấp:
- get_language: FastAPI dependency đọc header Accept-Language -> mã ngôn ngữ.
- LocalizedHTTPException: HTTPException tự động dịch message theo ngôn ngữ.
"""

from fastapi import Header, HTTPException, status

from app.utils.i18n import resolve_language, get_message


def get_language(accept_language: str | None = Header(default=None)) -> str:
    """
    FastAPI dependency: trả về mã ngôn ngữ ("vi" / "zh") từ header Accept-Language.

    Dùng: lang: str = Depends(get_language)
    """
    return resolve_language(accept_language)


class LocalizedHTTPException(HTTPException):
    """
    HTTPException dịch message theo ngôn ngữ.

    Thay vì truyền detail là text cứng, ta truyền message_key + lang,
    và message sẽ được dịch tự động.

    VD: raise LocalizedHTTPException(404, "user.not_found", lang)
    """

    def __init__(
        self,
        status_code: int,
        message_key: str,
        lang: str | None = None,
        headers: dict | None = None,
    ):
        detail = get_message(message_key, lang)
        super().__init__(status_code=status_code, detail=detail, headers=headers)
