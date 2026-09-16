from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


def _safe_extension(name: str) -> str:
    extension = Path(name).suffix.lower()
    if extension in {".png", ".jpg", ".jpeg", ".jp2", ".tif", ".tiff"}:
        return extension
    return ".bin"


def extract_pdf_assets(source_pdf: Path, output_dir: Path) -> dict[str, Any]:
    """Extract embedded image streams without changing the source PDF."""
    from pypdf import PdfReader

    output_dir.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(source_pdf)
    assets: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    written_by_digest: dict[str, str] = {}

    for page_number, page in enumerate(reader.pages, start=1):
        try:
            page_images = list(page.images)
        except Exception as exc:
            errors.append({"page": page_number, "error": str(exc)})
            continue
        for image_number, image in enumerate(page_images, start=1):
            try:
                data = image.data
                digest = hashlib.sha256(data).hexdigest()
                original_name = str(getattr(image, "name", "image"))
                extension = _safe_extension(original_name)
                if digest in written_by_digest:
                    relative_path = written_by_digest[digest]
                    duplicate = True
                else:
                    filename = f"page-{page_number:03d}-image-{image_number:03d}{extension}"
                    filename = re.sub(r"[^A-Za-z0-9._-]", "-", filename)
                    path = output_dir / filename
                    path.write_bytes(data)
                    relative_path = filename
                    written_by_digest[digest] = relative_path
                    duplicate = False
                width = height = None
                pil_image = getattr(image, "image", None)
                if pil_image is not None:
                    width, height = pil_image.size
                assets.append(
                    {
                        "source_page": page_number,
                        "source_index": image_number,
                        "source_name": original_name,
                        "filename": relative_path,
                        "sha256": digest,
                        "byte_count": len(data),
                        "width": width,
                        "height": height,
                        "duplicate_of_existing_file": duplicate,
                        "extraction_engine": "pypdf",
                        "association_status": "page_only",
                    }
                )
            except Exception as exc:
                errors.append(
                    {"page": page_number, "image_index": image_number, "error": str(exc)}
                )

    manifest = {
        "schema_version": "pdf-to-web-assets-v1",
        "source": str(source_pdf),
        "extraction_engine": "pypdf",
        "association_scope": "source_page_only",
        "unique_file_count": len(written_by_digest),
        "asset_reference_count": len(assets),
        "assets": assets,
        "errors": errors,
    }
    manifest_path = output_dir.parent / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest
