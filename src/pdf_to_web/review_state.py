from __future__ import annotations

import copy
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .errors import PdfToWebError
from .project import load_project, save_project, utc_now

REVIEW_SCHEMA = "pdf-to-web-review-v1"
BLOCK_TYPES = {"heading", "paragraph", "list", "quote", "caption", "callout", "unknown"}
BLOCK_REVIEW_STATES = {"unreviewed", "approved", "needs_review", "excluded"}
TEXT_BLOCK_TYPES = {"heading", "paragraph", "quote", "caption", "callout", "unknown"}


def review_path(project_dir: Path) -> Path:
    return project_dir.expanduser().resolve() / "review" / "current.json"


def original_path(project_dir: Path) -> Path:
    return project_dir.expanduser().resolve() / "extraction" / "normalized" / "document.json"


def _read_document(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PdfToWebError(f"Document data was not found: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise PdfToWebError(f"Could not read document data: {exc}") from exc
    if data.get("schema_version") != "pdf-to-web-normalized-v1":
        raise PdfToWebError(f"Unsupported normalized schema: {data.get('schema_version')!r}")
    return data


def _walk(blocks: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for block in blocks:
        yield block
        yield from _walk(block.get("children", []))


def _default_block_status(block: dict[str, Any]) -> str:
    if block.get("review", {}).get("status") == "excluded":
        return "excluded"
    if block.get("review", {}).get("status") == "needs_review":
        return "needs_review"
    if block.get("review_status") == "review_required" or block.get("type") == "unknown":
        return "needs_review"
    return "unreviewed"


def _prepare(document: dict[str, Any]) -> dict[str, Any]:
    prepared = copy.deepcopy(document)
    now = utc_now()
    prepared["review_session"] = {
        "schema_version": REVIEW_SCHEMA,
        "created_at": now,
        "updated_at": now,
        "revision": 0,
    }
    for block in _walk(prepared.get("blocks", [])):
        review = block.setdefault("review", {})
        review.setdefault("status", _default_block_status(block))
        review.setdefault("updated_at", now)
    return prepared


def ensure_review_document(project_dir: Path) -> dict[str, Any]:
    path = review_path(project_dir)
    if path.is_file():
        document = _read_document(path)
        from .normalize import _clean_list_markers, apply_source_supplemental_regions, apply_source_title, reconcile_visual_reading_order

        changed = apply_source_title(document, project_dir)
        changed = apply_source_supplemental_regions(document, project_dir) or changed
        session = document.get("review_session", {})
        if not session.get("manual_order_override") and int(session.get("revision", 0)) == 0:
            changed = reconcile_visual_reading_order(document) or changed
        before = json.dumps(document.get("blocks", []), sort_keys=True)
        _clean_list_markers(document.get("blocks", []))
        for block in _walk(document.get("blocks", [])):
            if (
                block.get("type") == "image"
                and not block.get("decorative")
                and not str(block.get("alt") or "").strip()
                and block.get("review", {}).get("status") == "approved"
            ):
                _set_status(block, "needs_review")
        changed = changed or before != json.dumps(document.get("blocks", []), sort_keys=True)
        if not document.get("footnotes"):
            from .normalize import _extract_footnotes

            _extract_footnotes(document)
            if document.get("footnotes"):
                changed = True
        if changed:
            _atomic_write(path, document)
        return document
    document = _prepare(_read_document(original_path(project_dir)))
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(path, document)
    project = load_project(project_dir)
    project["review_revision_at"] = document["review_session"]["updated_at"]
    save_project(project_dir, project)
    return document


def load_reviewed_document(project_dir: Path, *, initialize: bool = False) -> dict[str, Any]:
    path = review_path(project_dir)
    if path.is_file():
        return ensure_review_document(project_dir)
    return ensure_review_document(project_dir) if initialize else _read_document(original_path(project_dir))


def _atomic_write(path: Path, data: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def _snapshot(project_dir: Path, current: dict[str, Any]) -> Path:
    directory = project_dir / "review" / "revisions"
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    path = directory / f"{stamp}.json"
    _atomic_write(path, current)
    revisions = sorted(directory.glob("*.json"))
    for stale in revisions[:-50]:
        stale.unlink(missing_ok=True)
    return path


def save_review_document(project_dir: Path, document: dict[str, Any], *, snapshot: bool = True) -> dict[str, Any]:
    project_dir = project_dir.expanduser().resolve()
    path = review_path(project_dir)
    if snapshot and path.is_file():
        _snapshot(project_dir, _read_document(path))
    now = utc_now()
    session = document.setdefault("review_session", {})
    session["schema_version"] = REVIEW_SCHEMA
    session.setdefault("created_at", now)
    session["updated_at"] = now
    session["revision"] = int(session.get("revision", 0)) + 1
    _atomic_write(path, document)
    project = load_project(project_dir)
    project["review_revision_at"] = now
    save_project(project_dir, project)
    return document


def _find_location(
    blocks: list[dict[str, Any]], block_id: str
) -> tuple[list[dict[str, Any]], int, dict[str, Any]]:
    for index, block in enumerate(blocks):
        if str(block.get("id")) == block_id:
            return blocks, index, block
        children = block.get("children")
        if isinstance(children, list):
            try:
                return _find_location(children, block_id)
            except KeyError:
                pass
    raise KeyError(f"Block was not found: {block_id}")


def _set_status(block: dict[str, Any], status: str) -> None:
    if status not in BLOCK_REVIEW_STATES:
        raise ValueError(f"Unsupported review status: {status}")
    review = block.setdefault("review", {})
    review["status"] = status
    review["updated_at"] = utc_now()


def update_block(project_dir: Path, block_id: str, changes: dict[str, Any]) -> dict[str, Any]:
    document = ensure_review_document(project_dir)
    _siblings, _index, block = _find_location(document.get("blocks", []), block_id)
    if "type" in changes:
        block_type = str(changes["type"])
        if block_type not in BLOCK_TYPES:
            raise ValueError(f"Unsupported editable block type: {block_type}")
        block["type"] = block_type
        if block_type == "heading":
            block["level"] = max(1, min(6, int(changes.get("level", block.get("level", 2)))))
    if "level" in changes:
        if block.get("type") != "heading":
            raise ValueError("Heading level can only be set on a heading block")
        block["level"] = max(1, min(6, int(changes["level"])))
    if "content" in changes:
        if block.get("type") not in TEXT_BLOCK_TYPES and block.get("type") != "list":
            raise ValueError("Text editing is not supported for this block type")
        content = str(changes["content"])
        block["content"] = content
        block.pop("runs", None)
        if block.get("type") == "list":
            old_children = block.get("children", [])
            provenance = copy.deepcopy(block.get("provenance", {}))
            block["children"] = [
                {
                    "id": str(old_children[index].get("id"))
                    if index < len(old_children)
                    else f"{block_id}-item-{index + 1}",
                    "type": "list_item",
                    "content": line.strip(),
                    "children": [],
                    "provenance": copy.deepcopy(
                        old_children[index].get("provenance", provenance)
                        if index < len(old_children)
                        else provenance
                    ),
                    "review": {"status": "needs_review", "updated_at": utc_now()},
                }
                for index, line in enumerate(content.splitlines())
                if line.strip()
            ]
    if any(field in changes for field in ("alt", "caption", "decorative")):
        if block.get("type") != "image":
            raise ValueError("Image accessibility fields can only be set on an image block")
        if "decorative" in changes:
            value = changes["decorative"]
            block["decorative"] = value if isinstance(value, bool) else str(value).lower() in {"1", "true", "yes", "on"}
        if "alt" in changes:
            block["alt"] = str(changes["alt"]).strip()
        if "caption" in changes:
            block["caption"] = str(changes["caption"]).strip()
        if block.get("decorative"):
            block["alt"] = ""
    if "review_status" in changes:
        status = str(changes["review_status"])
        if (
            status == "approved"
            and block.get("type") == "image"
            and not block.get("decorative")
            and not str(block.get("alt") or "").strip()
        ):
            raise ValueError("Add alt text or mark the image as decorative before approving it")
        _set_status(block, status)
    return save_review_document(project_dir, document)


def move_block(project_dir: Path, block_id: str, direction: str) -> dict[str, Any]:
    document = ensure_review_document(project_dir)
    siblings, index, _block = _find_location(document.get("blocks", []), block_id)
    targets = {"start": 0, "up": index - 1, "down": index + 1, "end": len(siblings) - 1}
    if direction not in targets:
        raise ValueError(f"Unsupported move direction: {direction}")
    target = targets[direction]
    if target < 0 or target >= len(siblings):
        raise ValueError(f"Block cannot move {direction}")
    if target == index:
        return document
    block = siblings.pop(index)
    siblings.insert(target, block)
    document.setdefault("review_session", {})["manual_order_override"] = True
    return save_review_document(project_dir, document)


def merge_with_next(project_dir: Path, block_id: str) -> dict[str, Any]:
    document = ensure_review_document(project_dir)
    siblings, index, block = _find_location(document.get("blocks", []), block_id)
    if index + 1 >= len(siblings):
        raise ValueError("There is no following block to merge")
    following = siblings[index + 1]
    if block.get("type") not in TEXT_BLOCK_TYPES or block.get("type") != following.get("type"):
        raise ValueError("Only adjacent text blocks of the same type can be merged")
    first = str(block.get("content", "")).rstrip()
    second = str(following.get("content", "")).lstrip()
    block["content"] = f"{first}\n\n{second}" if first and second else first or second
    block.pop("runs", None)
    provenance = block.setdefault("provenance", {})
    provenance.setdefault("review_changes", []).append(
        {"action": "merge", "merged_block_id": following.get("id"), "at": utc_now()}
    )
    del siblings[index + 1]
    _set_status(block, "needs_review")
    return save_review_document(project_dir, document)


def split_block(project_dir: Path, block_id: str, offset: int) -> dict[str, Any]:
    document = ensure_review_document(project_dir)
    siblings, index, block = _find_location(document.get("blocks", []), block_id)
    if block.get("type") not in TEXT_BLOCK_TYPES:
        raise ValueError("Only text blocks can be split")
    content = str(block.get("content", ""))
    if offset <= 0 or offset >= len(content):
        raise ValueError("Split position must be inside the block text")
    left, right = content[:offset].rstrip(), content[offset:].lstrip()
    if not left or not right:
        raise ValueError("Both split blocks must contain text")
    block["content"] = left
    block.pop("runs", None)
    new_block = copy.deepcopy(block)
    base = re.sub(r"-split-\d+$", "", str(block.get("id", "block")))
    existing = {str(item.get("id")) for item in _walk(document.get("blocks", []))}
    number = 1
    while f"{base}-split-{number}" in existing:
        number += 1
    new_block["id"] = f"{base}-split-{number}"
    new_block["content"] = right
    new_block["provenance"] = copy.deepcopy(block.get("provenance", {}))
    new_block["provenance"].setdefault("review_changes", []).append(
        {"action": "split", "source_block_id": block_id, "at": utc_now()}
    )
    _set_status(block, "needs_review")
    _set_status(new_block, "needs_review")
    siblings.insert(index + 1, new_block)
    return save_review_document(project_dir, document)


def undo_last(project_dir: Path) -> dict[str, Any]:
    project_dir = project_dir.expanduser().resolve()
    revisions = sorted((project_dir / "review" / "revisions").glob("*.json"))
    if not revisions:
        raise ValueError("There are no review actions to undo")
    latest = revisions[-1]
    restored = _read_document(latest)
    latest.unlink()
    return save_review_document(project_dir, restored, snapshot=False)


def update_complex_visual(
    project_dir: Path, visual_id: str, changes: dict[str, Any]
) -> dict[str, Any]:
    document = ensure_review_document(project_dir)
    visuals = document.get("review", {}).get("complex_visuals", [])
    visual = next((item for item in visuals if str(item.get("id")) == visual_id), None)
    if visual is None:
        raise KeyError(f"Complex visual was not found: {visual_id}")
    if "status" in changes:
        status = str(changes["status"])
        if status not in {"needs_text_equivalent", "excluded", "reclassified"}:
            raise ValueError(f"Unsupported complex visual status: {status}")
        visual["status"] = status
    if "type" in changes:
        visual_type = str(changes["type"]).strip()
        if not visual_type:
            raise ValueError("Complex visual type cannot be empty")
        visual["type"] = visual_type
    if "recovered_text" in changes:
        visual["recovered_text"] = str(changes["recovered_text"])
    visual["reviewed_at"] = utc_now()
    return save_review_document(project_dir, document)


def review_progress(document: dict[str, Any]) -> dict[str, int]:
    counts = {state: 0 for state in BLOCK_REVIEW_STATES}
    blocks = list(document.get("blocks", []))
    for block in blocks:
        status = str(block.get("review", {}).get("status", _default_block_status(block)))
        counts[status if status in counts else "unreviewed"] += 1
    reviewed = counts["approved"] + counts["needs_review"] + counts["excluded"]
    return {"total": len(blocks), "reviewed": reviewed, **counts}


def archive_review_document(project_dir: Path, reason: str) -> Path | None:
    project_dir = project_dir.expanduser().resolve()
    path = review_path(project_dir)
    if not path.is_file():
        return None
    document = _read_document(path)
    document.setdefault("review_session", {})["archived_reason"] = reason
    archived = _snapshot(project_dir, document)
    path.unlink()
    return archived


def table_summary(block: dict[str, Any]) -> dict[str, int]:
    rows = block.get("rows", [])
    return {
        "rows": len(rows),
        "columns": max((sum(int(cell.get("column_span", 1)) if isinstance(cell, dict) else 1 for cell in row) for row in rows), default=0),
        "spans": sum(
            (int(cell.get("row_span", 1)) > 1 or int(cell.get("column_span", 1)) > 1)
            for row in rows
            for cell in row
            if isinstance(cell, dict)
        ),
    }
