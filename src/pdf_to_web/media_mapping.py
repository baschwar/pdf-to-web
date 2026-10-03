from __future__ import annotations

import csv
import io
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlparse

from .review_state import ensure_review_document, save_review_document
from .exporters.common import is_excluded

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
        if is_excluded(block):
            continue
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
        # A completed mapping CSV may predate authoring edits. It changes
        # attachment identity only; alternatives and captions remain authored.
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


def apply_wordpress_media_export(project_dir: Path, xml_text: str) -> dict[str, Any]:
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
        raise ValueError("Prepare the images ZIP and mapping CSV first on the Export screen")
    with mapping_path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not set(MAPPING_FIELDS).issubset(reader.fieldnames):
            raise ValueError("The generated media-mapping.csv has unexpected columns")
        rows = list(reader)

    matched = 0
    unmatched = 0
    ambiguous = 0
    used: set[tuple[int, str]] = set()
    current_images = {str(b.get('id')): b for b in _walk(ensure_review_document(project_dir).get('blocks', []))
                      if b.get('type') == 'image' and not b.get('decorative')}
    matched_rows = []
    unmatched_images, ambiguous_images = [], []
    positions = {str(b.get('id')): i for i, b in enumerate(ensure_review_document(project_dir).get('blocks', []), 1)}
    def describe(row, reason):
        block = current_images[row['block_id']]
        return {'block_id': row['block_id'], 'position': positions.get(row['block_id']),
                'asset_filename': row.get('asset_filename'), 'alt_text': block.get('alt', ''),
                'source_page': block.get('provenance', {}).get('source_page'), 'reason': reason}
    for row in rows:
        if row.get('block_id') not in current_images:
            continue
        if str(row.get("wordpress_url") or "").strip():
            continue
        candidates = attachments.get(str(row.get("asset_filename") or "").casefold(), [])
        if not candidates:
            unmatched += 1
            unmatched_images.append(describe(row, 'No exact filename match in the selected WordPress Media XML.'))
            continue
        if len(candidates) > 1:
            ambiguous += 1
            ambiguous_images.append(describe(row, 'Multiple WordPress attachments have this filename. Choose the intended URL in the CSV.'))
            continue
        attachment_id, url = candidates[0]
        row["wordpress_attachment_id"] = str(attachment_id)
        row["wordpress_url"] = url
        used.add(candidates[0])
        matched += 1
        matched_rows.append(row)

    # XML matching changes media identity only. A CSV prepared earlier must not
    # replace newer reviewer-authored alternatives or captions.
    media_fields = ('block_id', 'wordpress_attachment_id', 'wordpress_url')
    mapped_csv = io.StringIO()
    writer = csv.DictWriter(mapped_csv, fieldnames=media_fields)
    writer.writeheader()
    writer.writerows({field: row.get(field, '') for field in media_fields} for row in matched_rows)
    applied = apply_media_mapping(project_dir, mapped_csv.getvalue())
    with mapping_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=MAPPING_FIELDS)
        writer.writeheader()
        for row in rows:
            block = current_images.get(row.get('block_id'))
            if block:
                row['alt_text'], row['caption'] = block.get('alt', ''), block.get('caption', '')
        writer.writerows({field: row.get(field, "") for field in MAPPING_FIELDS} for row in rows)
    return {
        **applied,
        "matched": matched,
        "unmatched": unmatched,
        "ambiguous": ambiguous,
        "attachments_found": attachment_count,
        "unused_attachments": attachment_count - len(used),
        'unmatched_images': unmatched_images,
        'ambiguous_images': ambiguous_images,
    }
