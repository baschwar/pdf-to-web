from __future__ import annotations

import copy
import json
import re
from collections import Counter
from itertools import count
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote

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
ORDERED_MARKER_RE = re.compile(
    r"^\s*(?P<marker>(?:\d+|[A-Za-z]|[ivxlcdmIVXLCDM]+))[.)]\s+"
)


def _source_marker_style(value: Any) -> str | None:
    style = str(value or "").lower()
    if style in {"arabic numbers", "arabic", "decimal", "number", "numbers"}:
        return "decimal"
    if style in {"english letters", "letters", "alpha", "alphabetic"}:
        return "lower-alpha"
    if style in {"roman numbers", "roman", "roman numerals"}:
        return "lower-roman"
    return None

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
            "source_order": index,
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
        if block["ordered"]:
            marker_style = _source_marker_style(style)
            if marker_style:
                block["marker_style"] = marker_style
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


def _geometry(block: dict[str, Any]) -> tuple[float, float, float, float] | None:
    bbox = block.get("provenance", {}).get("bounding_box")
    if not isinstance(bbox, list) or len(bbox) != 4:
        return None
    try:
        x0, y0, x1, y1 = (float(value) for value in bbox)
    except (TypeError, ValueError):
        return None
    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1


def _add_reading_order_issue(block: dict[str, Any], message: str) -> None:
    review = block.setdefault("review", {})
    if review.get("status") in {None, "unreviewed", "auto_detected"}:
        review["status"] = "needs_review"
    issues = review.setdefault("issues", [])
    if not any(issue.get("code") == "reading_order_needs_review" for issue in issues):
        issues.append({"code": "reading_order_needs_review", "message": message})


def _heading_table_score(heading: dict[str, Any], table: dict[str, Any]) -> float | None:
    heading_box, table_box = _geometry(heading), _geometry(table)
    if not heading_box or not table_box:
        return None
    if heading.get("provenance", {}).get("source_page") != table.get("provenance", {}).get("source_page"):
        return None
    hx0, hy0, hx1, _hy1 = heading_box
    tx0, _ty0, tx1, ty1 = table_box
    gap = hy0 - ty1
    heading_width = hx1 - hx0
    overlap = max(0.0, min(hx1, tx1) - max(hx0, tx0))
    overlap_ratio = overlap / heading_width
    # PDF coordinates grow upward. Require a nearby label immediately above a
    # substantially wider table; this deliberately rejects column fragments.
    if gap < -1.0 or gap > 24.0 or overlap_ratio < 0.8 or (tx1 - tx0) < heading_width * 2:
        return None
    return round(min(0.99, 0.90 + 0.05 * overlap_ratio + 0.04 * (1 - max(gap, 0) / 24)), 3)


def _mark_visual_order(block: dict[str, Any], visual_order: int, confidence: float) -> None:
    provenance = block.setdefault("provenance", {})
    provenance["visual_order"] = visual_order
    provenance["visual_order_reason"] = "heading_table_association"
    provenance["visual_order_confidence"] = confidence


def _descendant_bbox(block: dict[str, Any]) -> list[float] | None:
    boxes = [_geometry(item) for item in [block, *_flatten(block.get("children", []))]]
    valid = [box for box in boxes if box]
    if not valid:
        return None
    return [min(box[0] for box in valid), min(box[1] for box in valid), max(box[2] for box in valid), max(box[3] for box in valid)]


def _same_image_region(first: dict[str, Any], second: dict[str, Any]) -> bool:
    first_box, second_box = _geometry(first), _geometry(second)
    if not first_box or not second_box:
        return False
    if first.get("provenance", {}).get("source_page") != second.get("provenance", {}).get("source_page"):
        return False
    intersection = max(0.0, min(first_box[2], second_box[2]) - max(first_box[0], second_box[0])) * max(0.0, min(first_box[3], second_box[3]) - max(first_box[1], second_box[1]))
    smaller = min((first_box[2] - first_box[0]) * (first_box[3] - first_box[1]), (second_box[2] - second_box[0]) * (second_box[3] - second_box[1]))
    return bool(smaller and intersection / smaller >= 0.95)


def repair_interleaved_images(document: dict[str, Any]) -> bool:
    """Remove image wrappers and split lists only at clear image boundaries."""
    state = document.get("reading_order", {})
    repair_version = int(state.get("interleaved_image_repair_version", 0))
    if repair_version == 2:
        return False
    blocks = document.get("blocks", [])
    changed = False

    images = [block for block in blocks if block.get("type") == "image"]
    wrappers = [
        block for block in blocks
        if block.get("type") == "paragraph"
        and not str(block.get("content") or "").strip()
        and any(_same_image_region(block, image) for image in images)
    ]
    if wrappers:
        blocks[:] = [block for block in blocks if block not in wrappers]
        changed = True

    while True:
        repaired = False
        for list_block in list(blocks):
            children = list_block.get("children", [])
            if list_block.get("type") != "list" or len(children) < 2:
                continue
            page = list_block.get("provenance", {}).get("source_page")
            for image in [block for block in blocks if block.get("type") == "image" and block.get("provenance", {}).get("source_page") == page]:
                image_box = _geometry(image)
                if not image_box:
                    continue
                split_at = next((
                    index for index in range(1, len(children))
                    if (above := _geometry(children[index - 1]))
                    and (below := _geometry(children[index]))
                    and above[1] >= image_box[3] - 4
                    and below[3] <= image_box[1] + 4
                ), None)
                if split_at is None:
                    continue
                continuation = copy.deepcopy(list_block)
                continuation["id"] = f'{list_block.get("id")}-continuation-{split_at + int(list_block.get("start", 1))}'
                continuation["children"] = children[split_at:]
                if continuation.get("ordered"):
                    continuation["start"] = int(list_block.get("start", 1)) + split_at
                continuation.setdefault("normalization", {})["split_around_image"] = image.get("id")
                list_block["children"] = children[:split_at]
                list_block.setdefault("normalization", {})["split_around_image"] = image.get("id")
                for item in (list_block, continuation):
                    bbox = _descendant_bbox(item)
                    if bbox:
                        item.setdefault("provenance", {})["bounding_box"] = bbox
                blocks.remove(image)
                insertion = blocks.index(list_block)
                blocks[insertion:insertion + 1] = [list_block, image, continuation]
                changed = repaired = True
                break
            if repaired:
                break
        if not repaired:
            break

    for index in range(len(blocks) - 2, -1, -1):
        parent, nested = blocks[index:index + 2]
        if parent.get("type") != "list" or nested.get("type") != "list" or not parent.get("children"):
            continue
        item = parent["children"][-1]
        item_box, nested_box = _geometry(item), _geometry(nested)
        if not item_box or not nested_box:
            continue
        if parent.get("provenance", {}).get("source_page") != nested.get("provenance", {}).get("source_page"):
            continue
        vertical_gap = item_box[1] - nested_box[3]
        if not (nested_box[0] >= item_box[0] + 18 and -2 <= vertical_gap <= 14):
            continue
        item.setdefault("children", []).append(nested)
        item.setdefault("normalization", {})["associated_indented_list"] = nested.get("id")
        blocks.pop(index + 1)
        bbox = _descendant_bbox(parent)
        if bbox:
            parent.setdefault("provenance", {})["bounding_box"] = bbox
        changed = True

    if changed or repair_version == 1:
        document.setdefault("reading_order", {})["interleaved_image_repair_version"] = 2
        return True
    return False


def reconcile_visual_reading_order(document: dict[str, Any]) -> bool:
    """Apply only high-confidence, local heading/table reading-order repairs."""
    state = document.setdefault("reading_order", {})
    if state.get("visual_reconciliation_version") == 1:
        return False
    state["visual_reconciliation_version"] = 1
    blocks = document.get("blocks", [])
    changed = False
    adjustments: list[dict[str, Any]] = []

    for list_block in list(blocks):
        if list_block.get("type") != "list":
            continue
        labels = list_block.get("children", [])
        if len(labels) < 2 or any(item.get("type") != "list_item" for item in labels):
            continue
        label_texts = [str(item.get("content", "")).strip() for item in labels]
        section_labels = all(re.fullmatch(r"[A-Z][A-Z ]{1,30}\s+\d{1,3}", text) for text in label_texts)
        if list_block.get("ordered") and not section_labels:
            continue
        if any(len(str(item.get("content", "")).strip()) > 80 for item in labels):
            continue
        pages = {item.get("provenance", {}).get("source_page") for item in labels}
        if len(pages) != 1 or None in pages:
            continue
        page = next(iter(pages))
        page_tables = [
            block for block in blocks
            if block.get("type") == "table" and block.get("provenance", {}).get("source_page") == page
        ]
        for item in labels:
            page_tables.extend(child for child in item.get("children", []) if child.get("type") == "table")
        unique_tables = {str(table.get("id")): table for table in page_tables}
        pairs: list[tuple[dict[str, Any], dict[str, Any], float]] = []
        ambiguous = False
        for label in labels:
            candidates = sorted(
                ((score, table) for table in unique_tables.values() if (score := _heading_table_score(label, table)) is not None),
                key=lambda item: item[0], reverse=True,
            )
            if len(candidates) > 1 and candidates[0][0] - candidates[1][0] < 0.02:
                ambiguous = True
                _add_reading_order_issue(label, "Multiple nearby tables could belong to this label; reading order was preserved.")
                continue
            if candidates:
                pairs.append((label, candidates[0][1], candidates[0][0]))
        if ambiguous or len(pairs) != len(labels) or len({id(table) for _, table, _ in pairs}) != len(labels):
            if pairs and not ambiguous:
                _add_reading_order_issue(list_block, "The page contains an incomplete heading/table pattern; reading order was preserved.")
            continue
        table_boxes = [_geometry(table) for _, table, _ in pairs]
        left_edges = [box[0] for box in table_boxes if box]
        if max(left_edges) - min(left_edges) > 24:
            _add_reading_order_issue(list_block, "Table regions do not form one stable page column; reading order was preserved.")
            continue

        involved = {id(list_block), *(id(table) for _, table, _ in pairs)}
        insertion = min(index for index, block in enumerate(blocks) if id(block) in involved)
        ordered: list[dict[str, Any]] = []
        for label, table, confidence in sorted(pairs, key=lambda pair: _geometry(pair[0])[1], reverse=True):
            label["type"] = "heading"
            label["level"] = 2
            label["children"] = [child for child in label.get("children", []) if child is not table]
            ordered.extend((label, table))
            adjustments.append({"heading_id": label.get("id"), "table_id": table.get("id"), "confidence": confidence})
        blocks[:] = [block for block in blocks if id(block) not in involved]
        blocks[insertion:insertion] = ordered
        for visual_order, block in enumerate(blocks):
            if any(block is member for member in ordered):
                confidence = next(pair[2] for pair in pairs if block is pair[0] or block is pair[1])
                _mark_visual_order(block, visual_order, confidence)
        changed = True

    state["visual_reconciliation_applied"] = changed
    state["adjustments"] = adjustments
    return changed


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
            ordered = bool(block.get("ordered"))
            style = str(block.get("marker_style") or "")
            if ordered and not style:
                source_style = _source_marker_style(
                    block.get("provenance", {}).get("raw", {}).get("numbering style")
                )
                if source_style:
                    style = source_style
                    block["marker_style"] = source_style
            for child in children:
                if child.get("type") != "list_item":
                    continue
                original = str(child.get("content", ""))
                content = LIST_MARKER_RE.sub("", original, count=1).strip()
                if ordered:
                    match = ORDERED_MARKER_RE.match(original)
                    if match:
                        marker = match.group("marker")
                        inferred = _ordered_marker_style(marker, style)
                        if not style:
                            style = inferred
                            block["marker_style"] = inferred
                        elif style.startswith("lower-") and inferred.startswith("upper-"):
                            style = inferred
                            block["marker_style"] = inferred
                        if _marker_styles_agree(style, inferred):
                            prefix_length = match.end()
                            content = original[prefix_length:].strip()
                            _strip_run_prefix(child, prefix_length)
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


def _ordered_marker_style(marker: str, hinted: str = "") -> str:
    if marker.isdigit():
        return "decimal"
    if "roman" in hinted and re.fullmatch(r"[ivxlcdm]+", marker):
        return "lower-roman"
    if "roman" in hinted and re.fullmatch(r"[IVXLCDM]+", marker):
        return "upper-roman"
    if len(marker) > 1 and re.fullmatch(r"[ivxlcdm]+", marker):
        return "lower-roman"
    if len(marker) > 1 and re.fullmatch(r"[IVXLCDM]+", marker):
        return "upper-roman"
    return "upper-alpha" if marker.isupper() else "lower-alpha"


def _marker_styles_agree(configured: str, inferred: str) -> bool:
    if configured == inferred:
        return True
    return (configured, inferred) in {
        ("lower-alpha", "upper-alpha"),
        ("lower-roman", "upper-roman"),
    }


def _strip_run_prefix(block: dict[str, Any], prefix_length: int) -> None:
    runs = block.get("runs")
    if not isinstance(runs, list):
        return
    remaining = prefix_length
    cleaned: list[dict[str, Any]] = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        current = dict(run)
        text = str(current.get("text", ""))
        if remaining:
            removed = min(remaining, len(text))
            text = text[removed:]
            remaining -= removed
            if not remaining:
                stripped = text.lstrip()
                text = stripped
        current["text"] = text
        if text:
            cleaned.append(current)
    block["runs"] = cleaned


def _select_source_title(
    text: str, regions: list[tuple[str, list[float], float]]
) -> tuple[str, list[float] | None] | None:
    candidates: list[tuple[float, int, str, list[float] | None]] = []
    for order, line in enumerate(part.strip() for part in text.splitlines()):
        if not line or line.isdigit() or len(line) > 200 or PAGE_NUMBER_PATTERN.search(line):
            continue
        if re.search(r"\bupdated\b", line, re.IGNORECASE):
            continue
        minimum_match = max(8, len(line) // 4)
        matching = [
            (bbox, size)
            for value, bbox, size in regions
            if len(value) >= minimum_match and value in line
        ]
        size = max((item[1] for item in matching), default=0.0)
        boxes = [bbox for bbox, font_size in matching if abs(font_size - size) < 0.1]
        bbox = (
            [min(box[0] for box in boxes), min(box[1] for box in boxes), max(box[2] for box in boxes), max(box[3] for box in boxes)]
            if boxes else None
        )
        repeated = re.fullmatch(r"(.+?)\1+", line)
        candidates.append((size, order, repeated.group(1) if repeated else line, bbox))
    if not candidates:
        return None
    title_size = max(item[0] for item in candidates)
    start = next(index for index, item in enumerate(candidates) if abs(item[0] - title_size) < 0.1)
    selected = [candidates[start]]
    for candidate in candidates[start + 1 : start + 4]:
        if (
            len(selected[0][2]) > 60
            or len(candidate[2]) > 60
            or candidate[1] != selected[-1][1] + 1
            or abs(candidate[0] - title_size) >= 0.1
        ):
            break
        selected.append(candidate)
    title = " ".join(item[2] for item in selected)
    boxes = [item[3] for item in selected if item[3]]
    bbox = (
        [min(box[0] for box in boxes), min(box[1] for box in boxes), max(box[2] for box in boxes), max(box[3] for box in boxes)]
        if boxes else None
    )
    return title, bbox


def recover_source_title_region(project_dir: Path) -> tuple[str, list[float] | None] | None:
    project = load_project(project_dir)
    source = project_dir / str(project.get("source", {}).get("path") or "")
    if not source.is_file():
        return None
    try:
        from pypdf import PdfReader

        page = PdfReader(source).pages[0]
        regions: list[tuple[str, list[float], float]] = []

        def collect_region(text: str, _cm: list[float], tm: list[float], font: Any, size: float) -> None:
            value = " ".join(text.split())
            if not value or font is None:
                return
            first_char = int(font.get("/FirstChar", 0))
            widths = font.get("/Widths") or []
            if hasattr(widths, "get_object"):
                widths = widths.get_object()
            width = 0.0
            for char in value:
                index = ord(char) - first_char
                width += float(widths[index]) if 0 <= index < len(widths) else 500.0
            x, baseline = float(tm[4]), float(tm[5])
            font_size = float(size) * (float(tm[0]) ** 2 + float(tm[1]) ** 2) ** 0.5
            regions.append(
                (value, [x, baseline - font_size * 0.25, x + width * font_size / 1000, baseline + font_size], font_size)
            )

        text = page.extract_text(visitor_text=collect_region) or ""
    except Exception:
        return None
    return _select_source_title(text, regions)


def recover_source_supplemental_regions(project_dir: Path) -> dict[str, tuple[str, list[float]]]:
    project = load_project(project_dir)
    source = project_dir / str(project.get("source", {}).get("path") or "")
    if not source.is_file():
        return {}
    try:
        from pypdf import PdfReader

        page = PdfReader(source).pages[0]
        page_width = float(page.mediabox.width)
        lines: list[tuple[str, float, float, float]] = []

        def collect(text: str, _cm: list[float], tm: list[float], _font: Any, size: float) -> None:
            value = " ".join(text.split())
            if value:
                effective_size = float(size) * (float(tm[0]) ** 2 + float(tm[1]) ** 2) ** 0.5
                lines.append((value, float(tm[4]), float(tm[5]), effective_size))

        text = page.extract_text(visitor_text=collect) or ""
    except Exception:
        return {}

    recovered: dict[str, tuple[str, list[float]]] = {}
    title = recover_source_title_region(project_dir)
    if title and title[1]:
        title_box = title[1]
        subtitle_lines = [
            item for item in lines
            if item[2] < title_box[1] and item[2] >= title_box[1] - 55
            and 0 < item[3] < max(line[3] for line in lines if line[2] >= title_box[1])
        ]
        if subtitle_lines:
            subtitle_size = max(item[3] for item in subtitle_lines)
            selected = [item for item in subtitle_lines if abs(item[3] - subtitle_size) < 0.2]
            selected.sort(key=lambda item: (-item[2], item[1]))
            subtitle = " ".join(item[0] for item in selected)
            subtitle = re.sub(r"\b(\d{3})\s+(\d)\b", r"\1\2", subtitle)
            if subtitle and len(subtitle) <= 160:
                recovered["subtitle"] = (
                    subtitle,
                    [min(item[1] for item in selected), min(item[2] - item[3] * 0.25 for item in selected), page_width - 36, max(item[2] + item[3] for item in selected)],
                )

    footer_match = re.search(
        r"(?P<note>\*?Please note\b.+?)(?P<revision>Revised\s+[^\n]+)$", text, re.IGNORECASE | re.MULTILINE
    )
    if footer_match:
        note = " ".join(footer_match.group("note").split())
        revision = " ".join(footer_match.group("revision").split())
        footer_line = next((item for item in lines if "Please note" in item[0] and "Revised" in item[0]), None)
        baseline = footer_line[2] if footer_line else 47.0
        font_size = footer_line[3] if footer_line else 9.0
        recovered["footer_note"] = (note, [36.0, baseline - font_size * 0.25, page_width * 0.72, baseline + font_size])
        recovered["revision"] = (revision, [page_width * 0.80, baseline - font_size * 0.25, page_width - 36.0, baseline + font_size])
    return recovered


def recover_source_title(project_dir: Path) -> str | None:
    recovered = recover_source_title_region(project_dir)
    return recovered[0] if recovered else None


def apply_source_title(document: dict[str, Any], project_dir: Path) -> bool:
    project = load_project(project_dir)
    metadata = document.setdefault("metadata", {})
    current = str(metadata.get("title") or "")
    fallback_titles = {"", "Untitled document", str(project.get("title") or "")}
    recovered = recover_source_title_region(project_dir)
    if not recovered:
        return False
    title, bounding_box = recovered
    blocks = document.setdefault("blocks", [])
    existing = next((block for block in blocks if block.get("id") == "recovered-document-title"), None)
    if existing:
        provenance = existing.setdefault("provenance", {})
        changed = False
        if provenance.get("source_type") == "recovered first-page header" and str(existing.get("content", "")) != title:
            existing["content"] = title
            metadata["title"] = title
            changed = True
        if bounding_box and provenance.get("bounding_box") != bounding_box:
            provenance["bounding_box"] = bounding_box
            changed = True
        return changed
    if current not in fallback_titles and current != title:
        return False
    changed = current != title
    metadata["title"] = title
    def matches_title(block: dict[str, Any]) -> bool:
        if block.get("type") != "heading" or int(block.get("level", 2)) != 1:
            return False
        content = str(block.get("content", "")).strip()
        return content == title or (
            min(len(content), len(title)) >= 20
            and (content.startswith(title) or title.startswith(content))
        )

    if not any(matches_title(block) for block in blocks):
        blocks.insert(
            0,
            {
                "id": "recovered-document-title",
                "type": "heading",
                "level": 1,
                "content": title,
                "provenance": {
                    "source_type": "recovered first-page header",
                    "source_page": 1,
                    "bounding_box": bounding_box,
                },
                "review": {
                    "status": "needs_review",
                    "issues": [{"code": "recovered_document_title", "message": "Document title recovered from the first-page PDF header."}],
                },
            },
        )
        changed = True
    return changed


def apply_source_supplemental_regions(document: dict[str, Any], project_dir: Path) -> bool:
    recovered = recover_source_supplemental_regions(project_dir)
    if not recovered:
        return False
    blocks = document.setdefault("blocks", [])
    changed = False
    subtitle = recovered.get("subtitle")
    if subtitle and not any(block.get("id") == "recovered-document-subtitle" for block in blocks):
        title_index = next((index for index, block in enumerate(blocks) if block.get("id") == "recovered-document-title"), -1)
        blocks.insert(title_index + 1, {
            "id": "recovered-document-subtitle", "type": "heading", "level": 2,
            "content": subtitle[0],
            "provenance": {"source_type": "recovered first-page subtitle", "source_page": 1, "bounding_box": subtitle[1]},
            "review": {"status": "needs_review", "issues": [{"code": "recovered_document_subtitle", "message": "Document subtitle recovered from the first-page PDF header."}]},
        })
        changed = True
    for key, block_id, label in (
        ("footer_note", "recovered-document-note", "Document note"),
        ("revision", "recovered-document-revision", "Revision date"),
    ):
        value = recovered.get(key)
        if value and not any(block.get("id") == block_id for block in blocks):
            recovered_block = {
                "id": block_id, "type": "paragraph", "content": value[0],
                "provenance": {"source_type": "recovered meaningful footer", "source_page": 1, "bounding_box": value[1]},
                "review": {"status": "needs_review", "issues": [{"code": "recovered_meaningful_footer", "message": f"{label} recovered from the PDF footer."}]},
            }
            if key == "footer_note":
                recovered_block["runs"] = [{"type": "emphasis", "text": value[0]}]
            blocks.append(recovered_block)
            changed = True
    return changed


def _normalize_heading_hierarchy(document: dict[str, Any]) -> None:
    previous_level: int | None = None
    seen_h1 = False
    for block in _flatten(document.get("blocks", [])):
        if block.get("type") != "heading":
            continue
        level = max(1, min(6, int(block.get("level", 2))))
        issue: dict[str, str] | None = None
        if level == 1 and seen_h1:
            level = 2
            issue = {
                "code": "additional_h1_demoted",
                "message": "An additional H1 was changed to H2; verify the source heading hierarchy.",
            }
        elif previous_level is not None and level > previous_level + 1:
            level = previous_level + 1
            issue = {
                "code": "heading_level_jump_corrected",
                "message": "A skipped heading level was corrected; verify the source heading hierarchy.",
            }
        block["level"] = level
        seen_h1 = seen_h1 or level == 1
        previous_level = level
        if issue:
            review = block.setdefault("review", {})
            if review.get("status") in {None, "unreviewed", "auto_detected"}:
                review["status"] = "needs_review"
            issues = review.setdefault("issues", [])
            if not any(existing.get("code") == issue["code"] for existing in issues):
                issues.append(issue)


def _bbox_overlap(first: Any, second: Any) -> float:
    if not isinstance(first, list) or not isinstance(second, list) or len(first) != 4 or len(second) != 4:
        return 0.0
    ax0, ay0, ax1, ay1 = map(float, first)
    bx0, by0, bx1, by1 = map(float, second)
    width = max(0.0, min(max(ax0, ax1), max(bx0, bx1)) - max(min(ax0, ax1), min(bx0, bx1)))
    height = max(0.0, min(max(ay0, ay1), max(by0, by1)) - max(min(ay0, ay1), min(by0, by1)))
    return width * height


def _apply_link_annotations(document: dict[str, Any], annotations: list[dict[str, Any]]) -> None:
    blocks = list(_flatten(document.get("blocks", [])))
    retained: list[dict[str, Any]] = []
    ranges: dict[str, list[tuple[int, int, str]]] = {}
    for annotation in annotations:
        page = annotation.get("source_page")
        bbox = annotation.get("bounding_box")
        url = str(annotation.get("url") or "")
        if not url:
            continue
        candidates = [
            block for block in blocks
            if block.get("provenance", {}).get("source_page") == page
            and _bbox_overlap(block.get("provenance", {}).get("bounding_box"), bbox) > 0
        ]
        visible_variants = tuple(dict.fromkeys((url, unquote(url))))
        content_matches = [
            block for block in candidates
            if any(visible in str(block.get("content", "")) for visible in visible_variants)
        ]
        block = max(
            content_matches or candidates,
            key=lambda item: _bbox_overlap(item.get("provenance", {}).get("bounding_box"), bbox),
            default=None,
        )
        record = dict(annotation)
        record["source_block"] = block.get("id") if block else None
        record["inline_preserved"] = False
        if block:
            content = str(block.get("content", ""))
            for visible in visible_variants:
                start = content.find(visible)
                if start >= 0:
                    ranges.setdefault(str(block.get("id")), []).append((start, start + len(visible), url))
                    record["visible_text"] = visible
                    record["inline_preserved"] = True
                    break
            block.setdefault("source_links", []).append(record)
        retained.append(record)
    for block in blocks:
        matches = sorted(set(ranges.get(str(block.get("id")), [])))
        if not matches:
            continue
        content = str(block.get("content", ""))
        runs: list[dict[str, str]] = []
        cursor = 0
        for start, end, url in matches:
            if start < cursor:
                continue
            if start > cursor:
                runs.append({"type": "text", "text": content[cursor:start]})
            runs.append({"type": "link", "text": content[start:end], "url": url})
            cursor = end
        if cursor < len(content):
            runs.append({"type": "text", "text": content[cursor:]})
        block["runs"] = runs
    if retained:
        document["source_links"] = retained


def apply_source_links(document: dict[str, Any], project_dir: Path) -> None:
    project = load_project(project_dir)
    source = project_dir / str(project.get("source", {}).get("path") or "")
    if not source.is_file():
        return
    annotations: list[dict[str, Any]] = []
    try:
        from pypdf import PdfReader

        for page_number, page in enumerate(PdfReader(source).pages, start=1):
            for reference in page.get("/Annots") or []:
                annotation = reference.get_object()
                if str(annotation.get("/Subtype")) != "/Link":
                    continue
                action = annotation.get("/A") or {}
                url = action.get("/URI")
                rect = annotation.get("/Rect")
                if url and rect and len(rect) == 4:
                    annotations.append(
                        {
                            "url": str(url),
                            "source_page": page_number,
                            "bounding_box": [float(value) for value in rect],
                        }
                    )
    except Exception:
        return
    _apply_link_annotations(document, annotations)


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
    repair_interleaved_images(document)
    reconcile_visual_reading_order(document)
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
    apply_source_supplemental_regions(document, project_dir)
    _normalize_heading_hierarchy(document)
    apply_source_links(document, project_dir)
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
