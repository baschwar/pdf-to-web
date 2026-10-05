from __future__ import annotations

import html
import copy
import re
from typing import Any


def is_excluded(block: dict[str, Any]) -> bool:
    return block.get("review", {}).get("status") == "excluded" or bool(block.get("excluded"))


def is_footnote_body(block: dict[str, Any]) -> bool:
    return bool(block.get("export_as_footnote_body"))


def retained_list_text(block: dict[str, Any]) -> str:
    content = str(block.get('content') or '')
    return content if content.strip() else ''.join(str(run.get('text') or '') for run in block.get('runs', []) if isinstance(run, dict))


def has_unstructured_list_text(block: dict[str, Any]) -> bool:
    return (block.get('type') == 'list' and not block.get('children')
            and bool(retained_list_text(block).strip()))


def list_render_items(block: dict[str, Any]) -> list[dict[str, Any]]:
    """Keep recoverable legacy list text visible without changing stored state."""
    if has_unstructured_list_text(block):
        return [{**block, 'type': 'list_item', 'content': retained_list_text(block), 'children': []}]
    return block.get('children', [])


def publication_document(document: dict[str, Any], *, template_title: bool = False) -> dict[str, Any]:
    """Heading projection only; reviewed IDs, content, provenance and state stay intact."""
    result = copy.deepcopy(document)
    def headings(blocks):
        for b in blocks:
            if is_excluded(b) or is_footnote_body(b) or b.get('export_as_part_of_image'):
                continue
            if b.get('type') == 'heading':
                yield b
            yield from headings(b.get('children', []))
    group = list(headings(result.get('blocks', [])))
    title = next((b for b in group if int(b.get('level', 2)) == 1), None)
    metadata_title = str(result.get('metadata', {}).get('title') or '').strip()
    if title is None:
        title = next((b for b in group if str(b.get('content') or '').strip() == metadata_title), None) if metadata_title else None
    if title is None and metadata_title:
        ids = set()
        def collect(blocks):
            for b in blocks:
                ids.add(str(b.get('id')))
                collect(b.get('children', []))
        collect(result.get('blocks', []))
        identity, n = 'publication-title', 1
        while identity in ids:
            identity, n = f'publication-title-{n}', n + 1
        title = {'id': identity, 'type': 'heading', 'level': 1, 'content': metadata_title, 'provenance': {'publication_generated': True}}
        result.setdefault('blocks', []).insert(0, title)
        group.insert(0, title)
    settings = result.get('publication', {})
    style = settings.get('heading_style', 'nested')
    previous = 1
    changes = []
    for b in group:
        original = int(b.get('level', 2))
        b.pop('publication_title_only', None)
        level = 1 if b is title else 2 if style == 'sections' else min(max(2, original), previous + 1, 6)
        b['level'] = level
        if b is title and template_title:
            b['publication_title_only'] = True
        if level != original:
            changes.append({'block_id': b.get('id'), 'from': original, 'to': level})
        previous = level
    result['publication_heading_changes'] = changes
    result['publication_title'] = str(title.get('content') or metadata_title) if title else metadata_title
    return result


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


def block_anchors(block, anchors):
    if is_excluded(block):
        return ''
    markup = '<span id="' + html.escape(str(block.get('id')), quote=True) + '"></span>' if str(block.get('id')) in anchors else ''
    return markup + ''.join(block_anchors(child, anchors) for child in block.get('children', []))


def standalone_description_blocks(document, *, prefix=''):
    """Project authored standalone equivalents without changing review records."""
    from ..image_review import descriptions_for

    def walk(blocks):
        for block in blocks:
            yield block
            yield from walk(block.get('children', []))

    blocks = list(walk(document.get('blocks', [])))
    represented = {str(b['publication_description_id']) for b in blocks
                   if b.get('publication_description_id')}
    linked = {str(v.get('id')) for b in blocks if b.get('type') == 'image'
              for v in descriptions_for(document, b)}
    identities = {str(b.get('id')) for b in blocks}
    result = []
    for visual in document.get('review', {}).get('complex_visuals', []):
        identity = str(visual.get('id') or '')
        if (visual.get('status') == 'excluded' or visual.get('source_block_id')
                or identity in linked or identity in represented):
            continue
        fields = visual.get('accessibility', {})
        text = fields.get('long_description') or fields.get('adjacent_text')
        if not text:
            continue
        base = prefix + (identity or 'visual-description')
        block_id, suffix = base, 2
        while block_id in identities:
            block_id, suffix = base + f'-description-{suffix}', suffix + 1
        identities.add(block_id)
        represented.add(identity)
        result.append({'id': block_id, 'type': 'paragraph', 'content': text,
                       'publication_description_id': identity})
    return result


def blocks_with_image_descriptions(document):
    """Render every explicit image equivalent beside its image, preserving IDs."""
    from ..image_review import descriptions_for
    def expand(blocks):
        result = []
        for original in blocks:
            block = copy.deepcopy(original)
            if 'children' in block:
                block['children'] = expand(block['children'])
            result.append(block)
            if block.get('type') != 'image' or is_excluded(block) or block.get('decorative'):
                continue
            for index, visual in enumerate(descriptions_for(document, block)):
                if visual.get('status') == 'excluded':
                    continue
                accessibility = visual.get('accessibility', {})
                text = accessibility.get('long_description') or accessibility.get('adjacent_text')
                if text:
                    identity = str(block['id']) + '-description' + (f'-{index + 1}' if index else '')
                    result.append({'id': identity, 'type': 'paragraph', 'content': text})
        return result
    return expand(document.get('blocks', [])) + standalone_description_blocks(document)
