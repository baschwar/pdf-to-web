from __future__ import annotations

import json
from collections import Counter
from itertools import count
from pathlib import Path
from typing import Any, Iterable

from .errors import PdfToWebError
from .project import load_project, utc_now

NORMALIZED_SCHEMA = "pdf-to-web-normalized-v1"

TYPE_MAP = {
    "heading": "heading",
    "paragraph": "paragraph",
    "text block": "paragraph",
    "text chunk": "paragraph",
    "list": "list",
    "list item": "list_item",
    "list_item": "list_item",
    "image": "image",
    "caption": "caption",
    "quote": "quote",
    "blockquote": "quote",
    "table": "table",
    "page break": "page_break",
    "page_break": "page_break",
    "formula": "unknown",
    "header": "unknown",
    "footer": "unknown",
}


def _content(element: dict[str, Any]) -> str:
    for key in ("content", "text", "value"):
        value = element.get(key)
        if isinstance(value, str):
            return value
    return ""


def _children(element: dict[str, Any]) -> list[dict[str, Any]]:
    children: list[dict[str, Any]] = []
    for key in ("kids", "list items", "items"):
        value = element.get(key)
        if isinstance(value, list):
            children.extend(item for item in value if isinstance(item, dict))
    return children


def _descendant_text(element: dict[str, Any]) -> str:
    own = _content(element).strip()
    parts = [own] if own else []
    for child in _children(element):
        child_text = _descendant_text(child)
        if child_text:
            parts.append(child_text)
    return " ".join(parts)


def _normalize_table_rows(element: dict[str, Any]) -> list[list[dict[str, Any]]]:
    normalized_rows: list[list[dict[str, Any]]] = []
    for row in element.get("rows", []):
        if not isinstance(row, dict):
            continue
        normalized_cells: list[dict[str, Any]] = []
        for cell in row.get("cells", []):
            if not isinstance(cell, dict):
                continue
            normalized_cells.append(
                {
                    "content": _descendant_text(cell),
                    "row_span": int(cell.get("row span", 1) or 1),
                    "column_span": int(cell.get("column span", 1) or 1),
                    "provenance": {
                        "source_page": cell.get("page number", element.get("page number")),
                        "bounding_box": cell.get("bounding box"),
                        "row_number": cell.get("row number"),
                        "column_number": cell.get("column number"),
                        "raw": cell,
                    },
                }
            )
        normalized_rows.append(normalized_cells)
    return normalized_rows


def _block_id(element: dict[str, Any], index: int) -> str:
    source_id = element.get("id")
    return f"odl-{source_id}" if source_id is not None else f"block-{index:05d}"


def _normalize_element(element: dict[str, Any], index: int) -> dict[str, Any]:
    source_type = str(element.get("type", "unknown")).lower()
    block_type = TYPE_MAP.get(source_type, "unknown")
    block: dict[str, Any] = {
        "id": _block_id(element, index),
        "type": block_type,
        "content": _content(element),
        "provenance": {
            "source_element_id": element.get("id"),
            "source_type": element.get("type"),
            "source_page": element.get("page number", element.get("page")),
            "bounding_box": element.get("bounding box", element.get("bbox")),
            "confidence": element.get("confidence"),
            "raw": element,
        },
    }
    if block_type == "heading":
        level = element.get("heading level", element.get("level", 2))
        if isinstance(level, str):
            level = 1 if level.lower() in {"title", "h1"} else 2
        block["level"] = max(1, min(6, int(level or 2)))
    elif block_type == "list":
        style = str(element.get("numbering style", "")).lower()
        block["ordered"] = style not in {"", "bullet", "unordered", "none"}
    elif block_type == "image":
        block["src"] = element.get("source") or element.get("src")
        block["alt"] = ""
        block["decorative"] = False
    elif block_type == "table":
        block["rows"] = _normalize_table_rows(element)
        block["caption"] = element.get("caption")
    if block_type == "unknown":
        block["review_status"] = "review_required"
    return block


def _walk(
    elements: Iterable[dict[str, Any]], counter: Iterable[int] | None = None
) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    sequence = counter or count(1)
    stack = list(reversed(list(elements)))
    while stack:
        element = stack.pop()
        block = _normalize_element(element, next(sequence))
        children = _children(element)
        if children:
            child_blocks = _walk(children, sequence)
            if block["type"] in {"list", "list_item"}:
                block["children"] = child_blocks
            else:
                blocks.append(block)
                blocks.extend(child_blocks)
                continue
        blocks.append(block)
    return blocks


def normalize_document(raw: dict[str, Any]) -> dict[str, Any]:
    elements = raw.get("kids")
    if not isinstance(elements, list):
        elements = raw.get("elements", raw.get("content", []))
    if not isinstance(elements, list):
        raise PdfToWebError("OpenDataLoader JSON does not contain a recognized element list")
    metadata = {
        "title": raw.get("title") or "Untitled document",
        "author": raw.get("author"),
        "source_filename": raw.get("file name"),
        "page_count": raw.get("number of pages"),
    }
    return {
        "schema_version": NORMALIZED_SCHEMA,
        "created_at": utc_now(),
        "metadata": metadata,
        "blocks": _walk(item for item in elements if isinstance(item, dict)),
    }


def _flatten(blocks: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for block in blocks:
        yield block
        yield from _flatten(block.get("children", []))


def extraction_summary(document: dict[str, Any]) -> dict[str, Any]:
    blocks = list(_flatten(document.get("blocks", [])))
    text_parts = [str(block.get("content", "")) for block in blocks]
    for block in blocks:
        if block.get("type") == "table":
            for row in block.get("rows", []):
                for cell in row:
                    text_parts.append(
                        str(cell.get("content", "")) if isinstance(cell, dict) else str(cell)
                    )
    text = "".join(text_parts)
    replacement_count = text.count("\ufffd")
    declared_pages = int(document.get("metadata", {}).get("page_count") or 0)
    represented_pages = sorted(
        {
            int(block["provenance"]["source_page"])
            for block in blocks
            if block.get("provenance", {}).get("source_page") is not None
        }
    )
    page_coverage = len(represented_pages) / declared_pages if declared_pages else 0.0
    source_character_count = int(
        document.get("metadata", {}).get("source_embedded_text_character_count") or 0
    )
    text_recovery_ratio = len(text) / source_character_count if source_character_count else None
    source_types = Counter(
        str(block.get("provenance", {}).get("source_type") or "missing") for block in blocks
    )
    normalized_types = Counter(str(block.get("type", "unknown")) for block in blocks)
    ratio = replacement_count / max(1, len(text))
    review_required = (
        ratio > 0.02
        or (declared_pages and page_coverage < 1.0)
        or (text_recovery_ratio is not None and text_recovery_ratio < 0.7)
    )
    return {
        "status": "TEXT EXTRACTION REVIEW REQUIRED" if review_required else "review_ready",
        "block_count": len(blocks),
        "extracted_character_count": len(text),
        "declared_page_count": declared_pages,
        "represented_pages": represented_pages,
        "page_coverage_ratio": round(page_coverage, 4),
        "source_embedded_text_character_count": source_character_count,
        "text_recovery_ratio": round(text_recovery_ratio, 4)
        if text_recovery_ratio is not None
        else None,
        "source_type_counts": dict(sorted(source_types.items())),
        "normalized_type_counts": dict(sorted(normalized_types.items())),
        "unknown_block_count": normalized_types.get("unknown", 0),
        "blocks_missing_source_page": sum(
            block.get("provenance", {}).get("source_page") is None for block in blocks
        ),
        "blocks_missing_bounding_box": sum(
            block.get("provenance", {}).get("bounding_box") is None for block in blocks
        ),
        "blocks_missing_source_id": sum(
            block.get("provenance", {}).get("source_element_id") is None for block in blocks
        ),
        "replacement_character_count": replacement_count,
        "replacement_character_ratio": round(ratio, 4),
    }


def find_raw_json(project_dir: Path) -> Path:
    raw_dir = project_dir / "extraction" / "raw"
    candidates = sorted(path for path in raw_dir.glob("*.json") if path.is_file())
    if not candidates:
        raise PdfToWebError(f"No OpenDataLoader JSON found in {raw_dir}")
    if len(candidates) > 1:
        source_stem = Path(
            load_project(project_dir)["source"].get("original_filename") or "original.pdf"
        ).stem
        matches = [path for path in candidates if path.stem in {"original", source_stem}]
        if len(matches) == 1:
            return matches[0]
        raise PdfToWebError(
            "Multiple raw JSON files were found; keep one source extraction per project"
        )
    return candidates[0]


def normalize_project(project_dir: Path) -> Path:
    project_dir = project_dir.expanduser().resolve()
    raw_path = find_raw_json(project_dir)
    try:
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PdfToWebError(f"Could not load OpenDataLoader JSON: {exc}") from exc
    document = normalize_document(raw)
    project = load_project(project_dir)
    document["metadata"]["source_embedded_text_character_count"] = project.get(
        "source", {}
    ).get("embedded_text_character_count", 0)
    if document["metadata"].get("title") in {None, "Untitled document"}:
        document["metadata"]["title"] = project.get("title") or "Untitled document"
    output = project_dir / "extraction" / "normalized" / "document.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    report = project_dir / "output" / "reports" / "extraction-summary.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(extraction_summary(document), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output


def load_normalized(project_dir: Path) -> dict[str, Any]:
    path = project_dir.expanduser().resolve() / "extraction" / "normalized" / "document.json"
    if not path.is_file():
        raise PdfToWebError("Normalize the extracted document before exporting")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != NORMALIZED_SCHEMA:
        raise PdfToWebError(f"Unsupported normalized schema: {data.get('schema_version')!r}")
    return data
