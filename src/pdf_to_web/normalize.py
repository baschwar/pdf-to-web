from __future__ import annotations

import json
from collections import Counter
from itertools import count
from pathlib import Path
from typing import Any, Iterable

from .errors import PdfToWebError
from .project import load_project, utc_now

NORMALIZED_SCHEMA = "pdf-to-web-normalized-v1"
READINESS_STATUSES = {"review_ready", "needs_review", "conversion_blocked"}

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
        source_level = element.get("heading level", element.get("level"))
        level = source_level if source_level is not None else 2
        if isinstance(level, str):
            level = 1 if level.lower() in {"title", "h1"} else 2
        block["level"] = max(1, min(6, int(level or 2)))
        if source_level is None:
            block["review"] = {
                "status": "needs_review",
                "issues": [
                    {
                        "code": "missing_heading_level",
                        "message": "The source identified a heading without a heading level; H2 was used provisionally.",
                    }
                ],
            }
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
        if source_type in {"header", "footer"}:
            block["role"] = f"page_{source_type}"
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
    document = {
        "schema_version": NORMALIZED_SCHEMA,
        "created_at": utc_now(),
        "metadata": metadata,
        "blocks": _walk(item for item in elements if isinstance(item, dict)),
    }
    _associate_image_captions(document["blocks"])
    return document


def _associate_image_captions(blocks: list[dict[str, Any]]) -> None:
    previous_image: dict[str, Any] | None = None
    for block in blocks:
        block_type = block.get("type")
        page = block.get("provenance", {}).get("source_page")
        if block_type == "image":
            previous_image = block
        elif block_type == "caption" and previous_image is not None:
            image_page = previous_image.get("provenance", {}).get("source_page")
            if page == image_page:
                previous_image["caption"] = block.get("content", "")
                previous_image["caption_block_id"] = block["id"]
                block["associated_image_id"] = previous_image["id"]
                block["export_as_part_of_image"] = True
        elif block_type not in {"paragraph"}:
            previous_image = None


def _flatten(blocks: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for block in blocks:
        yield block
        yield from _flatten(block.get("children", []))


def _block_text(block: dict[str, Any]) -> str:
    parts = [str(block.get("content", ""))]
    if block.get("type") == "table":
        for row in block.get("rows", []):
            for cell in row:
                parts.append(str(cell.get("content", "")) if isinstance(cell, dict) else str(cell))
    for child in block.get("children", []):
        parts.append(_block_text(child))
    return " ".join(part for part in parts if part)


def _page_text(blocks: Iterable[dict[str, Any]], page: int) -> str:
    return " ".join(
        _block_text(block)
        for block in blocks
        if block.get("provenance", {}).get("source_page") == page
    )


def _complex_visuals(
    document: dict[str, Any], asset_manifest: dict[str, Any]
) -> list[dict[str, Any]]:
    blocks = list(_flatten(document.get("blocks", [])))
    assets_by_page: Counter[int] = Counter()
    refs_by_page: dict[int, list[str]] = {}
    for asset in asset_manifest.get("assets", []):
        page = int(asset.get("source_page") or 0)
        if not page:
            continue
        assets_by_page[page] += 1
        refs_by_page.setdefault(page, []).append(str(asset.get("filename", "")))
    image_blocks_by_page = Counter(
        int(block.get("provenance", {}).get("source_page") or 0)
        for block in blocks
        if block.get("type") == "image"
    )
    source_page_counts = document.get("metadata", {}).get(
        "source_embedded_text_characters_by_page", []
    )
    results: list[dict[str, Any]] = []
    for page in sorted(set(assets_by_page) | set(image_blocks_by_page)):
        visual_count = max(assets_by_page[page], image_blocks_by_page[page])
        if visual_count < 5:
            continue
        recovered_text = _page_text(blocks, page)
        source_count = (
            int(source_page_counts[page - 1]) if page <= len(source_page_counts) else 0
        )
        coverage = len(recovered_text) / source_count if source_count else None
        results.append(
            {
                "id": f"complex-visual-page-{page}",
                "type": "infographic",
                "status": "needs_text_equivalent",
                "source_page": page,
                "asset_references": refs_by_page.get(page, []),
                "recovered_text": recovered_text,
                "source_embedded_text_character_count": source_count,
                "text_recovery_ratio": round(coverage, 4) if coverage is not None else None,
                "human_review_required": True,
            }
        )
    return results


def apply_readiness(
    document: dict[str, Any], asset_manifest: dict[str, Any] | None = None
) -> dict[str, Any]:
    summary = extraction_summary(document)
    asset_manifest = asset_manifest or {"assets": []}
    complex_visuals = _complex_visuals(document, asset_manifest)
    issues: list[dict[str, Any]] = []

    recovery = summary.get("text_recovery_ratio")
    if recovery is not None and recovery < 0.85:
        issues.append(
            {
                "code": "incomplete_text_recovery",
                "message": f"Only {recovery:.1%} of embedded source text was recovered.",
                "metric": recovery,
            }
        )
    if summary["page_coverage_ratio"] < 1:
        issues.append(
            {
                "code": "incomplete_page_coverage",
                "message": f"Extracted elements cover {summary['page_coverage_ratio']:.1%} of source pages.",
                "metric": summary["page_coverage_ratio"],
            }
        )
    if summary["replacement_character_ratio"] > 0.02:
        issues.append(
            {
                "code": "invalid_text_characters",
                "message": "Extracted text contains a significant number of replacement characters.",
                "metric": summary["replacement_character_ratio"],
            }
        )
    blocks = list(_flatten(document.get("blocks", [])))
    missing_levels = [
        block for block in blocks if block.get("review", {}).get("issues")
    ]
    if missing_levels:
        issues.append(
            {
                "code": "missing_heading_levels",
                "message": f"{len(missing_levels)} heading(s) use a provisional level.",
                "block_ids": [block["id"] for block in missing_levels],
            }
        )
    furniture = [
        block
        for block in blocks
        if block.get("provenance", {}).get("source_type") in {"header", "footer"}
    ]
    if furniture:
        issues.append(
            {
                "code": "repeated_page_furniture",
                "message": f"{len(furniture)} header/footer block(s) require exclusion review.",
                "severity": "advisory",
                "block_ids": [block["id"] for block in furniture],
            }
        )
    for visual in complex_visuals:
        visual_issue = {
            "code": "complex_visual_detected",
            "page": visual["source_page"],
            "message": "A likely infographic or other complex visual requires a text equivalent.",
            "complex_visual_id": visual["id"],
        }
        issues.append(visual_issue)
        if visual.get("text_recovery_ratio") is not None and visual["text_recovery_ratio"] < 0.85:
            issues.append(
                {
                    "code": "complex_visual_text_loss",
                    "page": visual["source_page"],
                    "message": f"Only {visual['text_recovery_ratio']:.1%} of embedded text was recovered for the complex visual.",
                    "metric": visual["text_recovery_ratio"],
                    "complex_visual_id": visual["id"],
                }
            )

    blocked = (
        not blocks
        or (recovery is not None and recovery < 0.25)
        or summary["replacement_character_ratio"] > 0.25
    )
    review_codes = {issue["code"] for issue in issues if issue.get("severity") != "advisory"}
    status = "conversion_blocked" if blocked else "needs_review" if review_codes else "review_ready"
    review = {"status": status, "issues": issues, "complex_visuals": complex_visuals}
    document["review"] = review
    return review


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
    return {
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
    document["metadata"]["source_embedded_text_characters_by_page"] = project.get(
        "source", {}
    ).get("embedded_text_characters_by_page", [])
    if document["metadata"].get("title") in {None, "Untitled document"}:
        document["metadata"]["title"] = project.get("title") or "Untitled document"
    asset_manifest_path = project_dir / "extraction" / "assets" / "manifest.json"
    asset_manifest = (
        json.loads(asset_manifest_path.read_text(encoding="utf-8"))
        if asset_manifest_path.is_file()
        else {"assets": []}
    )
    review = apply_readiness(document, asset_manifest)
    output = project_dir / "extraction" / "normalized" / "document.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    report = project_dir / "output" / "reports" / "extraction-summary.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    summary = extraction_summary(document)
    summary.update({"status": review["status"], "issues": review["issues"], "complex_visuals": review["complex_visuals"]})
    report.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
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
