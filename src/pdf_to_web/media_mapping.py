from __future__ import annotations

import csv
import io
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlparse

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


def _child_text(node: ET.Element, local_name: str) -> str:
    for child in node:
        if child.tag.rsplit("}", 1)[-1] == local_name:
            return str(child.text or "").strip()
    return ""


def _attachment_filename(item: ET.Element, url: str) -> str:
    for meta in item:
        if meta.tag.rsplit("}", 1)[-1] != "postmeta":
            continue
        if _child_text(meta, "meta_key") == "_wp_attached_file":
            value = _child_text(meta, "meta_value")
            if value:
                return Path(unquote(value)).name
    return Path(unquote(urlparse(url).path)).name


def apply_wordpress_media_export(project_dir: Path, xml_text: str) -> dict[str, int]:
    if "<!DOCTYPE" in xml_text.upper() or "<!ENTITY" in xml_text.upper():
        raise ValueError("WordPress media XML cannot contain document type or entity declarations")
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ValueError(f"Could not read WordPress media XML: {exc}") from exc

    attachments: dict[str, list[tuple[int, str]]] = {}
    attachment_count = 0
    for item in root.iter("item"):
        if _child_text(item, "post_type") != "attachment":
            continue
        url = _child_text(item, "attachment_url")
        post_id = _child_text(item, "post_id")
        filename = _attachment_filename(item, url)
        try:
            attachment_id = int(post_id)
        except ValueError:
            continue
        if attachment_id < 1 or not filename or urlparse(url).scheme not in {"http", "https"}:
            continue
        attachment_count += 1
        attachments.setdefault(filename.casefold(), []).append((attachment_id, url))

    mapping_path = project_dir / "output" / "wordpress" / "reports" / "media-mapping.csv"
    if not mapping_path.is_file():
        raise ValueError("Export Gutenberg or WXR first to create media-mapping.csv")
    with mapping_path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not set(MAPPING_FIELDS).issubset(reader.fieldnames):
            raise ValueError("The generated media-mapping.csv has unexpected columns")
        rows = list(reader)

    matched = 0
    unmatched = 0
    ambiguous = 0
    used: set[tuple[int, str]] = set()
    for row in rows:
        if str(row.get("wordpress_url") or "").strip():
            continue
        candidates = attachments.get(str(row.get("asset_filename") or "").casefold(), [])
        if not candidates:
            unmatched += 1
            continue
        if len(candidates) > 1:
            ambiguous += 1
            continue
        attachment_id, url = candidates[0]
        row["wordpress_attachment_id"] = str(attachment_id)
        row["wordpress_url"] = url
        used.add(candidates[0])
        matched += 1

    with mapping_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=MAPPING_FIELDS)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in MAPPING_FIELDS} for row in rows)
    applied = apply_media_mapping(project_dir, mapping_path.read_text(encoding="utf-8"))
    return {
        **applied,
        "matched": matched,
        "unmatched": unmatched,
        "ambiguous": ambiguous,
        "attachments_found": attachment_count,
        "unused_attachments": attachment_count - len(used),
    }
