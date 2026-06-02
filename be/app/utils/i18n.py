"""
i18n Utility - Đa ngôn ngữ cho API responses.

Đọc các file JSON dịch thuật trong app/locales/ và cung cấp hàm
get_message(key, lang) để lấy text theo ngôn ngữ.

Cách dùng:
    get_message("auth.invalid_credentials", "vi") -> "Tên đăng nhập hoặc mật khẩu không đúng"
    get_message("user.not_found", "tw")           -> ""

Ngôn ngữ được xác định từ header Accept-Language (xem resolve_language).
"""

import json
from pathlib import Path

from app.config.settings import settings

# Thư mục chứa các file dịch thuật
_LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"

# Cache nội dung file dịch (load 1 lần, dùng lại nhiều lần)
_translations: dict[str, dict] = {}


def _load_translations() -> None:
    """Load tất cả file JSON trong thư mục locales vào cache."""
    for lang in settings.supported_languages_list:
        file_path = _LOCALES_DIR / f"{lang}.json"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                _translations[lang] = json.load(f)


def resolve_language(accept_language: str | None) -> str:
    """
    Xác định ngôn ngữ từ header Accept-Language.

    VD: "tw-CN,tw;q=0.9" -> "tw"; "vi-VN" -> "vi".
    Nếu không hỗ trợ -> trả về ngôn ngữ mặc định.
    """
    if not accept_language:
        return settings.DEFAULT_LANGUAGE

    # Lấy phần ngôn ngữ chính (trước dấu '-' hoặc ',')
    primary = accept_language.split(",")[0].strip().split("-")[0].lower()

    if primary in settings.supported_languages_list:
        return primary
    return settings.DEFAULT_LANGUAGE


def get_message(key: str, lang: str | None = None) -> str:
    """
    Lấy text dịch theo key dạng "group.key" và ngôn ngữ.

    Args:
        key:  Khóa dịch dạng phân cấp, VD "auth.login_success".
        lang: Mã ngôn ngữ ("vi", "tw"). Mặc định lấy DEFAULT_LANGUAGE.

    Returns:
        Text đã dịch. Nếu không tìm thấy key -> trả về chính key đó.
    """
    if not _translations:
        _load_translations()

    lang = lang or settings.DEFAULT_LANGUAGE
    if lang not in _translations:
        lang = settings.DEFAULT_LANGUAGE

    # Duyệt theo các cấp của key (VD "auth.login_success")
    node = _translations.get(lang, {})
    for part in key.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return key  # Không tìm thấy -> trả về key gốc để dễ debug

    return node if isinstance(node, str) else key
