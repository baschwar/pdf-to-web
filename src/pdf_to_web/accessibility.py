from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

from .project import utc_now

ACCESSIBILITY_SCHEMA = "pdf-to-web-accessibility-v1"
DECISIONS = {"unresolved", "approved", "not_applicable"}

def _page(block: dict[str, Any]) -> int | None:
    value = block.get("provenance", {}).get("source_page")
    return int(value) if isinstance(value, (int, float)) else None


def _item(
    item_id: str,
    category: str,
    title: str,
    message: str,
    *,
    block: dict[str, Any] | None = None,
    severity: str = "review",
    decision_allowed: bool = False,
) -> dict[str, Any]:
    return {
        "id": item_id,
        "category": category,
        "severity": severity,
        "title": title,
        "message": message,
        "block_id": str(block.get("id")) if block else None,
        "source_page": _page(block) if block else None,
        "decision_allowed": decision_allowed,
    }


def _link_items(block: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for index, run in enumerate(block.get("runs", []), 1):
        if not isinstance(run, dict) or not run.get("href"):
            continue
        text = str(run.get("text") or "").strip()
        normalized = re.sub(r"\s+", " ", text).lower()
        if not text or normalized in {"click here", "here", "more", "read more", "link"}:
            items.append(
                _item(
                    f"link:{block.get('id')}:{index}",
                    "links",
                    "Link purpose needs review",
                    f'The link text "{text or "(empty)"}" may not identify its destination.',
                    block=block,
                    decision_allowed=True,
                )
            )
    return items


def assess_document(document: dict[str, Any]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    decisions = document.get("accessibility_review", {}).get("decisions", {})
    headings: list[dict[str, Any]] = []

    # Structure reviews top-level reading-order blocks. Nested list items remain
    # part of their parent list and must not become unactionable duplicate rows.
    for block in document.get("blocks", []):
        if block.get("review", {}).get("status") == "excluded" or block.get("excluded"):
            continue
        block_id = str(block.get("id") or "unknown")
        block_type = block.get("type")
        review_status = block.get("review", {}).get("status", "unreviewed")
        if review_status in {"unreviewed", "needs_review"}:
            items.append(
                _item(
                    f"structure:{block_id}",
                    "structure",
                    "Structural review incomplete",
                    f"This {block_type or 'unknown'} block is {str(review_status).replace('_', ' ')}.",
                    block=block,
                )
            )
        if block_type == "unknown":
            items.append(
                _item(
                    f"unknown:{block_id}",
                    "unresolved_content",
                    "Unknown content type",
                    "Convert this block to a semantic type or explicitly exclude it.",
                    block=block,
                )
            )
        elif block_type == "heading":
            headings.append(block)
        elif block_type == "image":
            if not block.get("decorative") and not str(block.get("alt") or "").strip():
                items.append(
                    _item(
                        f"image-alt:{block_id}",
                        "images",
                        "Image needs an accessibility decision",
                        "Add purpose-appropriate alt text or mark the image as decorative.",
                        block=block,
                    )
                )
        elif block_type == "table":
            table_review = block.get("table_accessibility", {})
            if not table_review.get("reviewed"):
                items.append(
                    _item(
                        f"table:{block_id}",
                        "tables",
                        "Table structure needs confirmation",
                        "Confirm its header row, header column, and caption before accessibility approval.",
                        block=block,
                    )
                )
        items.extend(_link_items(block))

    previous_level = 0
    h1_count = 0
    for heading in headings:
        level = int(heading.get("level", 2))
        h1_count += level == 1
        if previous_level and level > previous_level + 1:
            items.append(
                _item(
                    f"heading-jump:{heading.get('id')}",
                    "headings",
                    "Heading level is skipped",
                    f"Heading level jumps from H{previous_level} to H{level}.",
                    block=heading,
                )
            )
        previous_level = level
    if h1_count != 1:
        items.append(
            _item(
                "document:h1-count",
                "headings",
                "Document needs one H1",
                f"The reviewed document contains {h1_count} H1 headings.",
            )
        )

    for visual in document.get("review", {}).get("complex_visuals", []):
        if visual.get("status") == "excluded":
            continue
        visual_id = str(visual.get("id") or "unknown")
        equivalent = visual.get("accessibility", {})
        if not str(equivalent.get("short_alt") or "").strip() or not (
            str(equivalent.get("long_description") or "").strip()
            or str(equivalent.get("adjacent_text") or "").strip()
        ):
            items.append(
                {
                    **_item(
                        f"complex:{visual_id}",
                        "complex_visuals",
                        "Complex visual needs a text equivalent",
                        "Provide short alt text and either a long description or adjacent text equivalent.",
                    ),
                    "source_page": visual.get("source_page"),
                    "visual_id": visual_id,
                }
            )

    for issue in document.get("review", {}).get("issues", []):
        code = str(issue.get("code") or "diagnostic")
        key = f"diagnostic:{code}:{issue.get('page', 'document')}"
        items.append(
            {
                **_item(
                    key,
                    "diagnostics",
                    "Extraction diagnostic",
                    str(issue.get("message") or code.replace("_", " ")),
                    decision_allowed=True,
                ),
                "source_page": issue.get("page"),
            }
        )

    for item in items:
        saved = decisions.get(item["id"], {}) if isinstance(decisions, dict) else {}
        decision = saved.get("status", "unresolved") if item["decision_allowed"] else "unresolved"
        item["status"] = decision if decision in DECISIONS else "unresolved"
        item["note"] = str(saved.get("note") or "")
        item["updated_at"] = saved.get("updated_at")

    counts = {"total": len(items), "unresolved": 0, "approved": 0, "not_applicable": 0}
    categories: dict[str, int] = {}
    for item in items:
        counts[item["status"]] += 1
        categories[item["category"]] = categories.get(item["category"], 0) + 1
    return {
        "schema_version": ACCESSIBILITY_SCHEMA,
        "generated_at": utc_now(),
        "status": "review_complete" if counts["unresolved"] == 0 else "needs_review",
        "summary": {**counts, "categories": categories},
        "items": items,
    }


def save_decision(document: dict[str, Any], item_id: str, status: str, note: str) -> None:
    if status not in DECISIONS:
        raise ValueError(f"Unsupported accessibility decision: {status}")
    assessment = assess_document(document)
    item = next((item for item in assessment["items"] if item["id"] == item_id), None)
    if item is None:
        raise KeyError(f"Accessibility item was not found: {item_id}")
    if not item["decision_allowed"]:
        raise ValueError("Resolve this finding in Structure instead of approving it as an exception")
    review = document.setdefault("accessibility_review", {})
    review["schema_version"] = ACCESSIBILITY_SCHEMA
    review.setdefault("decisions", {})[item_id] = {
        "status": status,
        "note": note.strip(),
        "updated_at": utc_now(),
    }


def write_reports(project_dir: Path, document: dict[str, Any]) -> list[Path]:
    report = assess_document(document)
    output_dir = project_dir / "output" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "accessibility-review.json"
    html_path = output_dir / "accessibility-review.html"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    rows = []
    for item in report["items"]:
        page = item.get("source_page") or "Document"
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(page))}</td>"
            f"<td>{html.escape(item['category'].replace('_', ' ').title())}</td>"
            f"<td>{html.escape(item['title'])}<br><small>{html.escape(item['message'])}</small></td>"
            f"<td>{html.escape(item['status'].replace('_', ' ').title())}</td>"
            f"<td>{html.escape(item['note'])}</td>"
            "</tr>"
        )
    summary = report["summary"]
    title = html.escape(str(document.get("metadata", {}).get("title") or "Untitled document"))
    markup = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} accessibility review</title><style>body{{font:1rem/1.5 system-ui,sans-serif;max-width:72rem;margin:auto;padding:2rem}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #999;padding:.6rem;text-align:left;vertical-align:top}}th{{background:#eee}}small{{color:#444}}</style></head><body><main><h1>{title} accessibility review</h1><p><strong>Status:</strong> {html.escape(report['status'].replace('_', ' ').title())}</p><p>{summary['unresolved']} unresolved, {summary['approved']} approved, {summary['not_applicable']} not applicable.</p><table><thead><tr><th>Page</th><th>Category</th><th>Finding</th><th>Decision</th><th>Reviewer note</th></tr></thead><tbody>{''.join(rows) or '<tr><td colspan="5">No review findings.</td></tr>'}</tbody></table><p>This report records review decisions; it is not an automated WCAG certification.</p></main></body></html>'''
    html_path.write_text(markup, encoding="utf-8")
    return [json_path, html_path]
