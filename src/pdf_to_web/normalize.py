from __future__ import annotations

import json
import re
from collections import Counter
from itertools import count
from pathlib import Path
from typing import Any, Iterable

from .errors import PdfToWebError
from .project import load_project, utc_now

NORMALIZED_SCHEMA = "pdf-to-web-normalized-v1"
READINESS_STATUSES = {"review_ready", "needs_review", "conversion_blocked"}
PAGE_NUMBER_PATTERN = re.compile(
    r"(?:\bpage\s*(?:\||of)?\s*\d+\b|\b\d+\s*(?:of|/)\s*\d+\b)", re.IGNORECASE
)
FOOTNOTE_SOURCE_TYPES = {"footnote", "endnote", "note"}
FOOTNOTE_START_RE = re.compile(r"^\s*(?:\[(?P<bracket>[A-Za-z0-9]+)\]|(?P<plain>[A-Za-z0-9]{1,3}))[.)]?\s+(?P<text>.+)$", re.DOTALL)
LIST_MARKER_RE = re.compile(r"^\s*(?:[•◦▪‣⁃·]|o(?=\s))\s*")
INLINE_SUBITEM_RE = re.compile(r"^(?P<parent>.+?)\s+o\s+(?P<child>[A-Z].+)$")

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
    references = _raw_footnote_references(element)
    if references:
        block["footnote_references"] = references
    return block


def _raw_footnote_references(element: dict[str, Any]) -> list[dict[str, Any]]:
    raw_refs = (
        element.get("footnote references")
        or element.get("footnote_references")
        or element.get("references")
    )
    if not isinstance(raw_refs, list):
        return []
    references: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_refs, start=1):
        if not isinstance(raw, dict):
            continue
        marker = raw.get("marker") or raw.get("label") or raw.get("number")
        if marker is None:
            continue
        footnote_id = raw.get("footnote_id") or raw.get("footnote id")
        references.append(
            {
                "marker": str(marker),
                "footnote_id": str(footnote_id) if footnote_id is not None else "",
                "source_page": raw.get("page number", element.get("page number", element.get("page"))),
                "source_block": _block_id(element, index),
                "occurrence_order": index,
                "start": raw.get("start"),
                "end": raw.get("end"),
            }
        )
    return references


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


def _clean_list_markers(blocks: list[dict[str, Any]]) -> None:
    for block in blocks:
        children = block.get("children", [])
        if block.get("type") == "list":
            for child in children:
                if child.get("type") != "list_item":
                    continue
                content = LIST_MARKER_RE.sub("", str(child.get("content", "")), count=1).strip()
                match = INLINE_SUBITEM_RE.match(content)
                has_nested_list = any(item.get("type") == "list" for item in child.get("children", []))
                if match and not has_nested_list:
                    child["content"] = match.group("parent").strip()
                    child.setdefault("children", []).append(
                        {
                            "id": f"{child.get('id', 'list-item')}-subitem-1",
                            "type": "list",
                            "content": "",
                            "ordered": False,
                            "children": [
                                {
                                    "id": f"{child.get('id', 'list-item')}-subitem-1-item-1",
                                    "type": "list_item",
                                    "content": match.group("child").strip(),
                                    "children": [],
                                    "provenance": dict(child.get("provenance", {})),
                                }
                            ],
                            "provenance": dict(child.get("provenance", {})),
                        }
                    )
                else:
                    child["content"] = content
        _clean_list_markers(children)


def recover_source_title(project_dir: Path) -> str | None:
    project = load_project(project_dir)
    source = project_dir / str(project.get("source", {}).get("path") or "")
    if not source.is_file():
        return None
    try:
        from pypdf import PdfReader

        text = PdfReader(source).pages[0].extract_text() or ""
    except Exception:
        return None
    for line in (part.strip() for part in text.splitlines()):
        if not line or len(line) > 200 or PAGE_NUMBER_PATTERN.search(line):
            continue
        if re.search(r"\bupdated\b", line, re.IGNORECASE):
            continue
        return line
    return None


def apply_source_title(document: dict[str, Any], project_dir: Path) -> bool:
    project = load_project(project_dir)
    metadata = document.setdefault("metadata", {})
    current = str(metadata.get("title") or "")
    fallback_titles = {"", "Untitled document", str(project.get("title") or "")}
    title = recover_source_title(project_dir)
    if not title or current not in fallback_titles:
        return False
    metadata["title"] = title
    blocks = document.setdefault("blocks", [])
    if not any(block.get("type") == "heading" and int(block.get("level", 2)) == 1 for block in blocks):
        blocks.insert(
            0,
            {
                "id": "recovered-document-title",
                "type": "heading",
                "level": 1,
                "content": title,
                "provenance": {"source_type": "recovered first-page header", "source_page": 1},
                "review": {
                    "status": "needs_review",
                    "issues": [{"code": "recovered_document_title", "message": "Document title recovered from the first-page PDF header."}],
                },
            },
        )
    return True


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
    _clean_list_markers(document["blocks"])
    _associate_image_captions(document["blocks"])
    _extract_footnotes(document)
    _mark_automatic_page_artifacts(document["blocks"])
    return document


def _footnote_marker_and_text(block: dict[str, Any]) -> tuple[str, str] | None:
    raw = block.get("provenance", {}).get("raw", {})
    marker = raw.get("footnote marker") or raw.get("footnote_marker") or raw.get("marker")
    text = raw.get("footnote text") or raw.get("footnote_text")
    if marker is not None and text:
        return str(marker), str(text).strip()
    content = str(block.get("content", "")).strip()
    match = FOOTNOTE_START_RE.match(content)
    if not match:
        return None
    return str(match.group("bracket") or match.group("plain")), match.group("text").strip()


def _explicit_footnote_id(block: dict[str, Any], marker: str) -> str:
    raw = block.get("provenance", {}).get("raw", {})
    source_id = raw.get("footnote id") or raw.get("footnote_id") or raw.get("id")
    base = str(source_id) if source_id is not None else marker
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "-", base).strip("-").lower()
    return f"fn-{cleaned or marker}"


def _marker_occurrences(text: str, marker: str) -> list[tuple[int, int]]:
    if not marker:
        return []
    pattern = re.compile(rf"(?<![A-Za-z0-9]){re.escape(marker)}(?![A-Za-z0-9])")
    return [match.span() for match in pattern.finditer(text)]


def _find_reference_blocks(
    blocks: list[dict[str, Any]], note_index: int, marker: str, page: Any
) -> list[tuple[dict[str, Any], int, int]]:
    references: list[tuple[dict[str, Any], int, int]] = []
    for block in reversed(blocks[:note_index]):
        if block.get("export_as_footnote_body") or block.get("type") not in {"paragraph", "heading", "caption", "list_item"}:
            continue
        if block.get("provenance", {}).get("source_page") != page:
            continue
        text = str(block.get("content", ""))
        for start, end in _marker_occurrences(text, marker):
            references.append((block, start, end))
        if references:
            return list(reversed(references))
    return references


def _append_reference(
    block: dict[str, Any],
    footnote_id: str,
    marker: str,
    order: int,
    start: int | None = None,
    end: int | None = None,
) -> dict[str, Any]:
    suffix = "" if order == 1 else f"-{order}"
    reference = {
        "id": f"fnref-{footnote_id.removeprefix('fn-')}{suffix}",
        "footnote_id": footnote_id,
        "marker": marker,
        "source_page": block.get("provenance", {}).get("source_page"),
        "source_block": block.get("id"),
        "occurrence_order": order,
    }
    if start is not None and end is not None:
        reference.update({"start": start, "end": end})
    block.setdefault("footnote_references", []).append(reference)
    return reference


def _extract_footnotes(document: dict[str, Any]) -> None:
    blocks = list(_flatten(document.get("blocks", [])))
    footnotes: list[dict[str, Any]] = []
    reference_order = 1

    for parent_index, parent in enumerate(blocks):
        children = parent.get("children", [])
        if parent.get("type") != "list" or not parent.get("ordered") or len(children) < 2:
            continue
        parsed_children = [_footnote_marker_and_text(child) for child in children]
        if any(parsed is None for parsed in parsed_children):
            continue
        markers = [parsed[0] for parsed in parsed_children if parsed]
        if markers != [str(number) for number in range(1, len(markers) + 1)]:
            continue
        page = parent.get("provenance", {}).get("source_page")
        matches_by_child = [
            _find_reference_blocks(blocks, blocks.index(child), marker, page)
            for child, marker in zip(children, markers)
        ]
        if any(not matches for matches in matches_by_child):
            continue
        parent["export_as_footnote_body"] = True
        for child, parsed, matches in zip(children, parsed_children, matches_by_child):
            marker, text = parsed
            footnote_id = _explicit_footnote_id(child, marker)
            references = []
            for reference_block, start, end in matches:
                references.append(
                    _append_reference(reference_block, footnote_id, marker, reference_order, start, end)
                )
                reference_order += 1
            child["export_as_footnote_body"] = True
            child["footnote_body_id"] = footnote_id
            footnotes.append(
                {
                    "id": footnote_id,
                    "marker": marker,
                    "text": text,
                    "references": references,
                    "source_page": page,
                    "source_element_provenance": child.get("provenance", {}),
                    "original_source_position": parent_index + 1,
                    "review": {"status": "auto_detected"},
                }
            )

    for index, block in enumerate(blocks):
        if block.get("export_as_footnote_body"):
            continue
        source_type = str(block.get("provenance", {}).get("source_type") or "").lower()
        explicit = source_type in FOOTNOTE_SOURCE_TYPES or bool(
            block.get("provenance", {}).get("raw", {}).get("footnote")
        )
        if not explicit:
            continue
        parsed = _footnote_marker_and_text(block)
        if parsed is None:
            block.setdefault("review", {}).setdefault("issues", []).append(
                {
                    "code": "uncertain_footnote",
                    "message": "A note-like source element could not be confidently matched as a footnote.",
                }
            )
            block.setdefault("review", {})["status"] = "needs_review"
            continue
        marker, text = parsed
        footnote_id = _explicit_footnote_id(block, marker)
        page = block.get("provenance", {}).get("source_page")
        matches = _find_reference_blocks(blocks, index, marker, page)
        if not matches:
            block.setdefault("review", {}).setdefault("issues", []).append(
                {
                    "code": "unmatched_footnote",
                    "message": "Footnote text was preserved inline because no matching body reference was found.",
                }
            )
            block.setdefault("review", {})["status"] = "needs_review"
            continue
        references = []
        for reference_block, start, end in matches:
            references.append(
                _append_reference(
                    reference_block, footnote_id, marker, reference_order, start, end
                )
            )
            reference_order += 1
        block["export_as_footnote_body"] = True
        block["footnote_body_id"] = footnote_id
        footnotes.append(
            {
                "id": footnote_id,
                "marker": marker,
                "text": text,
                "references": references,
                "source_page": page,
                "source_element_provenance": block.get("provenance", {}),
                "original_source_position": index + 1,
                "review": {"status": "auto_detected"},
            }
        )
    if footnotes:
        document["footnotes"] = footnotes


def _mark_automatic_page_artifacts(blocks: list[dict[str, Any]]) -> None:
    for block in _flatten(blocks):
        if block.get("export_as_footnote_body"):
            continue
        provenance = block.get("provenance", {})
        source_type = str(provenance.get("source_type") or "").lower()
        content = str(block.get("content", "")).strip()
        bbox = provenance.get("bounding_box")
        bottom_margin_page_number = False
        if isinstance(bbox, list) and len(bbox) == 4 and PAGE_NUMBER_PATTERN.search(content):
            try:
                bottom_margin_page_number = min(float(bbox[1]), float(bbox[3])) <= 72
            except (TypeError, ValueError):
                pass
        if source_type not in {"header", "footer"} and not bottom_margin_page_number:
            continue
        block["review"] = {
            "status": "excluded",
            "issues": [
                {
                    "code": "auto_excluded_page_artifact",
                    "message": "Automatically excluded as repeated header, footer, or page numbering.",
                }
            ],
        }
        block["normalization"] = {
            "auto_excluded": True,
            "reason": "page_furniture" if source_type in {"header", "footer"} else "page_number",
        }


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
        block
        for block in blocks
        if any(
            issue.get("code") == "missing_heading_level"
            for issue in block.get("review", {}).get("issues", [])
        )
    ]
    if missing_levels:
        issues.append(
            {
                "code": "missing_heading_levels",
                "message": f"{len(missing_levels)} heading(s) use a provisional level.",
                "block_ids": [block["id"] for block in missing_levels],
            }
        )
    review_required_blocks = [
        block
        for block in blocks
        if any(
            issue.get("code") != "missing_heading_level"
            for issue in block.get("review", {}).get("issues", [])
        )
    ]
    if review_required_blocks:
        issues.append(
            {
                "code": "block_review_required",
                "message": f"{len(review_required_blocks)} block(s) require review before export.",
                "block_ids": [block["id"] for block in review_required_blocks],
            }
        )
    furniture = [
        block
        for block in blocks
        if block.get("provenance", {}).get("source_type") in {"header", "footer"}
    ]
    auto_excluded = [
        block for block in blocks if block.get("normalization", {}).get("auto_excluded")
    ]
    pending_furniture = [
        block for block in furniture if block.get("review", {}).get("status") != "excluded"
    ]
    if pending_furniture:
        issues.append(
            {
                "code": "repeated_page_furniture",
                "message": f"{len(pending_furniture)} header/footer block(s) require exclusion review.",
                "severity": "advisory",
                "block_ids": [block["id"] for block in pending_furniture],
            }
        )
    if auto_excluded:
        issues.append(
            {
                "code": "auto_excluded_page_artifacts",
                "message": f"{len(auto_excluded)} repeated header, footer, or page-number block(s) were automatically excluded.",
                "severity": "advisory",
                "block_ids": [block["id"] for block in auto_excluded],
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
    apply_source_title(document, project_dir)
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
    from .review_state import archive_review_document

    archive_review_document(project_dir, "Normalized document was regenerated")
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
    from .review_state import load_reviewed_document

    try:
        return load_reviewed_document(project_dir)
    except PdfToWebError as exc:
        if "was not found" in str(exc):
            raise PdfToWebError("Normalize the extracted document before exporting") from exc
        raise
