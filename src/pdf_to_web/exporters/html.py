from __future__ import annotations

import html
from typing import Any

from .common import image_src, is_excluded, is_footnote_body, render_footnotes_list, render_inline, table_cell


def _list(block: dict[str, Any]) -> str:
    tag = "ol" if block.get("ordered") else "ul"
    style_types = {"lower-alpha": "a", "upper-alpha": "A", "lower-roman": "i", "upper-roman": "I"}
    type_attr = f' type="{style_types[block["marker_style"]]}"' if block.get("ordered") and block.get("marker_style") in style_types else ""
    start_attr = f' start="{int(block["start"])}"' if block.get("ordered") and int(block.get("start", 1)) != 1 else ""
    items: list[str] = []
    for child in block.get("children", []):
        if is_excluded(child) or is_footnote_body(child):
            continue
        if child.get("type") == "list_item":
            nested = "".join(
                _block(grandchild) for grandchild in child.get("children", [])
            )
            items.append(f"<li>{render_inline(child)}{nested}</li>")
        else:
            items.append(f"<li>{_block(child)}</li>")
    return f"<{tag}{type_attr}{start_attr}>{''.join(items)}</{tag}>"


def _table(block: dict[str, Any]) -> str:
    caption = block.get("caption")
    table_review = block.get("table_accessibility", {})
    header_row = table_review.get("header_row", True)
    header_column = table_review.get("header_column", False)
    parts = ["<table>"]
    if caption:
        parts.append(f"<caption>{html.escape(str(caption))}</caption>")
    for row_index, row in enumerate(block.get("rows", [])):
        parts.append("<tr>")
        for column_index, cell in enumerate(row):
            cell_tag = "th" if (header_row and row_index == 0) or (header_column and column_index == 0) else "td"
            content, row_span, column_span = table_cell(cell)
            scope = ""
            if cell_tag == "th":
                scope = ' scope="col"' if header_row and row_index == 0 else ' scope="row"'
            spans = ""
            if row_span > 1:
                spans += f' rowspan="{row_span}"'
            if column_span > 1:
                spans += f' colspan="{column_span}"'
            parts.append(f"<{cell_tag}{scope}{spans}>{html.escape(content)}</{cell_tag}>")
        parts.append("</tr>")
    parts.append("</table>")
    return "".join(parts)


def _block(block: dict[str, Any]) -> str:
    if is_excluded(block) or is_footnote_body(block):
        return ""
    block_type = block.get("type")
    if block.get("export_as_part_of_image"):
        return ""
    if block_type == "heading":
        level = max(1, min(6, int(block.get("level", 2))))
        return f"<h{level}>{render_inline(block)}</h{level}>"
    if block_type in {"paragraph", "caption", "callout"}:
        return f"<p>{render_inline(block)}</p>"
    if block_type == "quote":
        return f"<blockquote><p>{render_inline(block)}</p></blockquote>"
    if block_type == "list":
        return _list(block)
    if block_type == "image":
        alt = "" if block.get("decorative") else html.escape(str(block.get("alt", "")), quote=True)
        image = f'<img src="{image_src(block)}" alt="{alt}">'
        caption = block.get("caption")
        if caption:
            return f"<figure>{image}<figcaption>{html.escape(str(caption))}</figcaption></figure>"
        return f"<figure>{image}</figure>"
    if block_type == "table":
        return _table(block)
    if block_type == "page_break":
        return "<hr>"
    role = block.get("role")
    role_attr = f' data-role="{html.escape(str(role), quote=True)}"' if role else ""
    return f'<div data-pdf-to-web-type="unknown"{role_attr}>{render_inline(block)}</div>'


def render_document(document: dict[str, Any]) -> str:
    title = html.escape(str(document.get("metadata", {}).get("title", "Untitled document")))
    body_parts = [_block(block) for block in document.get("blocks", [])]
    footnotes = render_footnotes_list(document)
    if footnotes:
        body_parts.append(footnotes)
    body = "\n".join(body_parts)
    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{title}</title>\n</head>\n<body>\n<main>\n{body}\n</main>\n"
        "</body>\n</html>\n"
    )
