from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

from .review_state import ensure_review_document, save_review_document

MAPPING_FIELDS = (
    "block_id",
    "asset_filename",
    "wordpress_attachment_id",
    "wordpress_url",
    "alt_text",
    "caption",
)


def _walk(blocks: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for block in blocks:
        yield block
        yield from _walk(block.get("children", []))


def apply_media_mapping(project_dir: Path, csv_text: str) -> dict[str, int]:
    try:
        reader = csv.DictReader(io.StringIO(csv_text))
    except csv.Error as exc:
        raise ValueError(f"Could not read media mapping CSV: {exc}") from exc
    if not reader.fieldnames or "block_id" not in reader.fieldnames or "wordpress_url" not in reader.fieldnames:
        raise ValueError("Media mapping CSV must include block_id and wordpress_url columns")

    document = ensure_review_document(project_dir)
    images = {
        str(block.get("id")): block
        for block in _walk(document.get("blocks", []))
        if block.get("type") == "image" and not block.get("decorative")
    }
    seen: set[str] = set()
    mapped = 0
    skipped = 0
    for line, row in enumerate(reader, start=2):
        block_id = str(row.get("block_id") or "").strip()
        url = str(row.get("wordpress_url") or "").strip()
        attachment = str(row.get("wordpress_attachment_id") or "").strip()
        if not block_id:
            skipped += 1
            continue
        if block_id in seen:
            raise ValueError(f"Duplicate media block ID on CSV line {line}: {block_id}")
        seen.add(block_id)
        if block_id not in images:
            raise ValueError(f"Unknown image block ID on CSV line {line}: {block_id}")
        if not url and not attachment:
            skipped += 1
            continue
        if urlparse(url).scheme not in {"http", "https"} or not urlparse(url).netloc:
            raise ValueError(f"A complete HTTP(S) WordPress URL is required on CSV line {line}")
        attachment_id: int | None = None
        if attachment:
            try:
                attachment_id = int(attachment)
            except ValueError as exc:
                raise ValueError(f"Attachment ID must be a positive integer on CSV line {line}") from exc
            if attachment_id < 1:
                raise ValueError(f"Attachment ID must be a positive integer on CSV line {line}")
        block = images[block_id]
        block["wordpress_url"] = url
        block["wordpress_attachment_id"] = attachment_id
        block["wordpress_media"] = {"url": url, "attachment_id": attachment_id}
        if "alt_text" in row:
            block["alt"] = str(row.get("alt_text") or "")
        if "caption" in row:
            block["caption"] = str(row.get("caption") or "")
        mapped += 1
    if mapped:
        save_review_document(project_dir, document)
    remaining = sum(
        not str(block.get("wordpress_url") or block.get("src") or "").startswith(
            ("http://", "https://")
        )
        for block in images.values()
    )
    return {"mapped": mapped, "skipped": skipped, "remaining": remaining}
