from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import PdfToWebError


def analyze_pdf(path: Path) -> dict[str, Any]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise PdfToWebError("pypdf is required to analyze PDF sources") from exc

    try:
        reader = PdfReader(path)
        if reader.is_encrypted and not reader.decrypt(""):
            raise PdfToWebError("The PDF is encrypted and requires a password")
        text_counts = [len((page.extract_text() or "").strip()) for page in reader.pages]
    except PdfToWebError:
        raise
    except Exception as exc:
        raise PdfToWebError(f"The PDF could not be read: {exc}") from exc

    page_count = len(text_counts)
    pages_with_text = sum(count >= 40 for count in text_counts)
    ratio = pages_with_text / page_count if page_count else 0.0
    if ratio >= 0.8:
        classification = "TEXT PDF"
    elif pages_with_text:
        classification = "MIXED PDF"
    else:
        classification = "LIKELY SCANNED / IMAGE-ONLY PDF"

    metadata = reader.metadata or {}
    return {
        "classification": classification,
        "page_count": page_count,
        "pages_with_usable_text": pages_with_text,
        "embedded_text_ratio": round(ratio, 3),
        "embedded_text_character_count": sum(max(0, count) for count in text_counts),
        "embedded_text_characters_by_page": text_counts,
        "title": metadata.get("/Title") or None,
        "ocr_status": "OCR REQUIRED" if not pages_with_text else "not_required",
    }
