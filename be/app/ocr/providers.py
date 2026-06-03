"""
OCR Providers - Bước 5 trong pipeline OCR.

Trừu tượng hóa engine OCR zone-based. Giao diện chung:
    provider.recognize(crop, lang) -> (text, confidence)

Providers:
- "paddle" → PaddleOCR local (lazy load model theo lang).
- "mock"   → trả "" (cho test luồng khi chưa bật OCR_ENABLED).

PaddleOCR-VL (aistudio API) là pipeline TOÀN TRANG riêng — không dùng ở đây.
Xem: app/ocr/paddleocr_vl_client.py + scripts/paddleocr_vl_scan.py.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.config.settings import settings


class OCRProvider(ABC):
    """Giao diện chung cho 1 engine OCR zone-based."""

    @abstractmethod
    def recognize(self, crop, lang: str) -> tuple[str, float | None]:
        """Nhận diện văn bản trong 1 ảnh crop. Trả (text, confidence)."""


# ── Paddle ───────────────────────────────────────────


class _PaddleProvider(OCRProvider):
    """PaddleOCR local — lazy-load model theo từng ngôn ngữ."""

    def __init__(self) -> None:
        self._models: dict = {}

    def _model(self, lang: str):
        if lang in self._models:
            return self._models[lang]
        from paddleocr import PaddleOCR

        m = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)
        self._models[lang] = m
        return m

    def recognize(self, crop, lang: str) -> tuple[str, float | None]:
        if crop is None or crop.size == 0:
            return "", None
        model = self._model(lang)
        raw = model.ocr(crop, cls=True)
        if not raw or not raw[0]:
            return "", None
        texts: list[str] = []
        confs: list[float] = []
        for line in raw[0]:
            try:
                txt = line[1][0]
                score = float(line[1][1])
            except (IndexError, TypeError, ValueError):
                continue
            if txt:
                texts.append(txt)
                confs.append(score)
        text = " ".join(texts).strip()
        conf = round(sum(confs) / len(confs), 4) if confs else None
        return text, conf


# ── Mock ─────────────────────────────────────────────


class _MockProvider(OCRProvider):
    """Trả rỗng — pipeline vẫn chạy nhưng không có giá trị."""

    def recognize(self, crop, lang: str) -> tuple[str, float | None]:
        return "", None


# ── Selector ─────────────────────────────────────────


_provider_singleton: OCRProvider | None = None


def get_provider() -> OCRProvider:
    """Lấy singleton provider theo cấu hình."""
    global _provider_singleton
    if _provider_singleton is not None:
        return _provider_singleton

    if not settings.OCR_ENABLED:
        _provider_singleton = _MockProvider()
        return _provider_singleton

    # Mặc định: PaddleOCR local
    _provider_singleton = _PaddleProvider()
    return _provider_singleton


def reset_provider() -> None:
    """Reset singleton (dùng khi đổi cấu hình lúc chạy / test)."""
    global _provider_singleton
    _provider_singleton = None
