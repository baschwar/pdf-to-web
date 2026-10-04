from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

from .project import utc_now

ACCESSIBILITY_SCHEMA = "pdf-to-web-accessibility-v1"
DECISIONS = {"unresolved", "approved", "not_applicable"}


def visual_readiness(document: dict[str, Any], visual: dict[str, Any]) -> dict[str, Any]:
    block, source_excluded = next(((b, excluded) for b, excluded in _walk_visibility(document.get('blocks', [])) if str(b.get('id')) == str(visual.get('source_block_id'))), (None, False))
    if not block and not visual.get('source_block_id'):
        matches = [(b, excluded) for b, excluded in _walk_visibility(document.get('blocks', [])) if str(b.get('complex_visual_id') or '') == str(visual.get('id'))]
        if len(matches) == 1:
            block, source_excluded = matches[0]
    from .image_review import association_issue
    problem = association_issue(document, block) if block else 'The source image is missing. Verify the description association.' if visual.get('source_block_id') else ''
    if problem and not source_excluded and visual.get('status') != 'excluded':
        return {'complete': False, 'text_complete': False, 'review_complete': False, 'label': 'Image association needs review', 'block_id': visual.get('source_block_id'), 'reason_code': 'association_conflict', 'reason': problem, 'action': 'Open the image editor and verify the exact description association before approval.'}
    status = visual.get('status')
    if status in {'excluded', 'not_applicable'} or source_excluded:
        return {'complete': True, 'text_complete': True, 'review_complete': True, 'label': 'Not applicable' if status == 'not_applicable' else 'Excluded', 'block_id': visual.get('source_block_id'), 'reason': '', 'action': '', 'reason_code': ''}
    if block and block.get('decorative'):
        return {'complete': True, 'text_complete': True, 'review_complete': True, 'label': 'Decorative image', 'block_id': block['id'], 'reason': '', 'action': '', 'reason_code': ''}
    a = visual.get('accessibility', {})
    short = block.get('alt', '') if block else a.get('short_alt', '')
    text_complete = bool(str(short or '').strip() and (str(a.get('long_description') or '').strip() or str(a.get('adjacent_text') or '').strip()))
    reviewed = status == 'reviewed'
    complete = text_complete and reviewed
    label = 'Reviewed' if complete else 'Text provided; awaiting manual review' if text_complete else 'Text equivalent needed'
    reason_code = '' if complete else 'changed_after_approval' if visual.get('review_reason') == 'changed_after_approval' else 'text_equivalent_incomplete' if not text_complete else 'reclassified_pending' if status == 'reclassified' else 'manual_review_pending'
    reason = ''
    if reason_code == 'changed_after_approval':
        labels = {'short_alt': 'short alt text', 'long_description': 'long description', 'adjacent_text': 'adjacent text equivalent', 'type': 'classification', 'recovered_text': 'recovered source text', 'image': 'image content'}
        fields = [labels[field] for field in visual.get('review_change_fields', []) if field in labels]
        reason = 'Changed since Reviewed: ' + ', '.join(fields) + '.' if fields else 'This description changed after it was marked Reviewed.'
    elif reason_code == 'reclassified_pending':
        reason = 'Reclassified is not a completed review decision.'
    elif reason_code == 'text_equivalent_incomplete':
        reason = 'The required text equivalent is incomplete.'
    elif reason_code:
        reason = 'Text is provided, but no current Reviewed decision is recorded.'
    if block and block.get('type') == 'image':
        action = '' if complete else 'Review alt, caption and the displayed descriptions together in Reading order, then use Save and approve once. Choose No separate description needed if short alt is sufficient.'
        return {'complete': complete, 'text_complete': text_complete, 'review_complete': reviewed, 'label': label, 'block_id': block['id'], 'reason_code': reason_code, 'reason': reason, 'action': action}
    action = '' if complete else ('Review the displayed image and description, then use Save and approve in its image editor, or review the saved text' if text_complete and block else 'Review the saved text' if text_complete else 'Add short alt text and either a long description or adjacent text equivalent') + ', then choose Reviewed and save. Choose Not applicable if short alt text is sufficient.'
    return {'complete': complete, 'text_complete': text_complete, 'review_complete': reviewed, 'label': label, 'block_id': visual.get('source_block_id'), 'reason_code': reason_code, 'reason': reason, 'action': action}


def _walk_visibility(blocks, ancestor_excluded=False):
    from .exporters.common import is_excluded
    for block in blocks:
        excluded = ancestor_excluded or is_excluded(block)
        yield block, excluded
        yield from _walk_visibility(block.get('children', []), excluded)


def _walk(blocks):
    for b in blocks:
        yield b
        yield from _walk(b.get('children', []))

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
        if not isinstance(run, dict) or not (run.get("href") or run.get("url")):
            continue
        text = str(run.get("text") or "").strip()
        normalized = re.sub(r"\s+", " ", text).lower()
        raw_url = bool(re.match(r"^(?:https?://|www\.)", text, re.I))
        if raw_url or not text or normalized in {"click here", "here", "more", "read more", "link"}:
            items.append(
                _item(
                    f"link:{block.get('id')}:{index}",
                    "links",
                    "URL used as link text" if raw_url else "Link purpose needs review",
                    (f'The link text "{text}" is a URL. Use a descriptive label in Structure, or record why the visible URL is needed.' if raw_url else f'The link text "{text or "(empty)"}" may not identify its destination.'),
                    block=block,
                    decision_allowed=True,
                )
            )
    for child in block.get('children', []):
        for item in _link_items(child):
            item['block_id'] = str(block.get('id'))
            items.append(item)
    return items


def assess_document(document: dict[str, Any]) -> dict[str, Any]:
    from .publication import effective_block_status
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
        review_status = effective_block_status(block, document)
        from .publication import block_review_issue
        from .image_review import association_issue
        only_linked_description = block_type == 'image' and block_review_issue(block) is None and not association_issue(document, block)
        if review_status in {"unreviewed", "needs_review"} and not only_linked_description:
            from .review_state import block_review_reason
            items.append(
                _item(
                    f"structure:{block_id}",
                    "structure",
                    "Structural review incomplete",
                    block_review_reason(block, document) or f"This {block_type or 'unknown'} block is {str(review_status).replace('_', ' ')}.",
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
        readiness = visual_readiness(document, visual)
        if readiness['complete']:
            continue
        visual_id = str(visual.get("id") or "unknown")
        items.append({
            **_item(f"complex:{visual_id}", "complex_visuals", "Description needs manual review" if readiness['text_complete'] else "Complex visual needs a text equivalent",
                    readiness['reason'] + ' ' + readiness['action']),
            "source_page": visual.get("source_page"), "visual_id": visual_id,
            "block_id": visual.get("source_block_id"),
        })

    for issue in document.get("review", {}).get("issues", []):
        code = str(issue.get("code") or "diagnostic")
        key = f"diagnostic:{code}:{issue.get('page', 'document')}"
        referenced = {str(value) for value in issue.get('block_ids', [])}
        if issue.get('block_id') is not None:
            referenced.add(str(issue['block_id']))
        existing = {str(block.get('id')) for block in _walk(document.get('blocks', []))}
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
                "missing_block_ids": sorted(referenced - existing),
                "related_blocks": [
                    {"id": str(block["id"]), "position": index,
                     "source_page": _page(block), "type": block.get("type", "unknown"),
                     "status": effective_block_status(block),
                     "preview": str(block.get("content") or block.get("alt") or block.get("caption") or "")[:160]}
                    for index, block in enumerate(document.get("blocks", []), 1)
                    if any(str(node.get('id')) in referenced for node in _walk([block]))
                ],
            }
        )

    for item in items:
        saved = decisions.get(item["id"], {}) if isinstance(decisions, dict) else {}
        decision = saved.get("status", "unresolved") if item["decision_allowed"] else "unresolved"
        item["status"] = decision if decision in DECISIONS else "unresolved"
        item["note"] = str(saved.get("note") or "")
        item["updated_at"] = saved.get("updated_at")
        if item['category'] == 'diagnostics' and item['id'].startswith('diagnostic:block_review_required:'):
            related = item.get('related_blocks', [])
            if related and not item.get('missing_block_ids') and all(b['status'] in {'approved', 'excluded'} for b in related):
                item['original_message'] = item['message']
                item['message'] = 'The blocks flagged during extraction are now approved or excluded. No block review remains for this note.'
                item['resolved_by_review'] = True
                if item['status'] == 'unresolved':
                    item['status'] = 'resolved'

    counts = {"total": len(items), "unresolved": 0, "approved": 0, "not_applicable": 0, 'resolved': 0}
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
