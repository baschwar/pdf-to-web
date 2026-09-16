from __future__ import annotations

import html
import re
from typing import Any


def is_excluded(block: dict[str, Any]) -> bool:
    return block.get("review", {}).get("status") == "excluded" or bool(block.get("excluded"))


def is_footnote_body(block: dict[str, Any]) -> bool:
    return bool(block.get("export_as_footnote_body"))


def _reference_link(reference: dict[str, Any]) -> str:
    ref_id = html.escape(str(reference.get("id", "")), quote=True)
    footnote_id = html.escape(str(reference.get("footnote_id", "")), quote=True)
    marker = html.escape(str(reference.get("marker", "")))
    return f'<sup><a href="#{footnote_id}" id="{ref_id}">{marker}</a></sup>'


def _render_text_with_footnote_references(text: str, references: list[dict[str, Any]]) -> str:
    if not references:
        return html.escape(text)
    replacements = sorted(
        (
            int(ref["start"]),
            int(ref["end"]),
            _reference_link(ref),
        )
        for ref in references
        if isinstance(ref.get("start"), int)
        and isinstance(ref.get("end"), int)
        and 0 <= int(ref["start"]) < int(ref["end"]) <= len(text)
    )
    if replacements:
        parts: list[str] = []
        cursor = 0
        for start, end, link in replacements:
            if start < cursor:
                continue
            parts.append(html.escape(text[cursor:start]))
            parts.append(link)
            cursor = end
        parts.append(html.escape(text[cursor:]))
        return "".join(parts)

    rendered = html.escape(text)
    for reference in references:
        marker = str(reference.get("marker", ""))
        if not marker:
            continue
        pattern = re.compile(rf"(?<!\w){re.escape(html.escape(marker))}(?!\w)")
        rendered, changed = pattern.subn(_reference_link(reference), rendered, count=1)
        if changed:
            break
    return rendered


def render_inline(block: dict[str, Any]) -> str:
    references = [
        ref for ref in block.get("footnote_references", []) if isinstance(ref, dict)
    ]
    runs = block.get("runs")
    if not isinstance(runs, list):
        return _render_text_with_footnote_references(str(block.get("content", "")), references)
    rendered: list[str] = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        value = html.escape(str(run.get("text", "")))
        run_type = run.get("type", "text")
        if run_type == "strong":
            rendered.append(f"<strong>{value}</strong>")
        elif run_type == "emphasis":
            rendered.append(f"<em>{value}</em>")
        elif run_type == "link":
            href = html.escape(str(run.get("url", "")), quote=True)
            rendered.append(f'<a href="{href}">{value}</a>')
        else:
            rendered.append(value)
    inline = "".join(rendered)
    for reference in references:
        inline += _reference_link(reference)
    return inline


def render_footnote_backlinks(footnote: dict[str, Any]) -> str:
    references = [
        ref for ref in footnote.get("references", []) if isinstance(ref, dict)
    ]
    links: list[str] = []
    for index, reference in enumerate(references, start=1):
        ref_id = html.escape(str(reference.get("id", "")), quote=True)
        marker = str(reference.get("marker") or footnote.get("marker") or index)
        if len(references) == 1:
            label = f"Back to footnote reference {marker}"
            visible = "↩"
        else:
            label = f"Back to reference {index} for footnote {marker}"
            visible = f"↩{index}"
        links.append(f'<a href="#{ref_id}" aria-label="{html.escape(label, quote=True)}">{html.escape(visible)}</a>')
    return " ".join(links)


def render_footnotes_list(document: dict[str, Any]) -> str:
    items: list[str] = []
    for footnote in document.get("footnotes", []):
        if not isinstance(footnote, dict):
            continue
        footnote_id = html.escape(str(footnote.get("id", "")), quote=True)
        text = html.escape(str(footnote.get("text", "")))
        backlinks = render_footnote_backlinks(footnote)
        items.append(f'<li id="{footnote_id}">{text} {backlinks}</li>')
    if not items:
        return ""
    return '<section class="footnotes" aria-labelledby="footnotes-heading"><h2 id="footnotes-heading">Footnotes</h2><ol>' + "".join(items) + "</ol></section>"


def image_src(block: dict[str, Any]) -> str:
    return html.escape(str(block.get("src") or "MEDIA_URL_REQUIRED"), quote=True)


def table_cell(cell: Any) -> tuple[str, int, int]:
    if isinstance(cell, dict):
        return (
            str(cell.get("content", "")),
            int(cell.get("row_span", 1) or 1),
            int(cell.get("column_span", 1) or 1),
        )
    return str(cell), 1, 1
