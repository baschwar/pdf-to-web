from __future__ import annotations

import html
import json
import re
from typing import Any
from urllib.parse import urlparse

from .common import is_excluded, is_footnote_body, render_footnote_backlinks, render_inline, table_cell


def _attrs(values: dict[str, Any], escape_hyphens: bool = False) -> str:
    if not values:
        return ""
    encoded = json.dumps(values, ensure_ascii=True, separators=(",", ":"))
    if escape_hyphens:
        encoded = re.sub(
            r'"className":"(?:\\.|[^"\\])*"',
            lambda match: match.group(0).replace("-", "\\u002d"),
            encoded,
        )
    return f" {encoded}"


def _wrap(name: str, markup: str, attrs: dict[str, Any] | None = None) -> str:
    attributes = _attrs(attrs or {})
    return f"<!-- wp:{name}{attributes} -->\n{markup}\n<!-- /wp:{name} -->"


def _list_markup(block: dict[str, Any]) -> str:
    ordered = bool(block.get("ordered"))
    tag = "ol" if ordered else "ul"
    style_types = {"lower-alpha": "a", "upper-alpha": "A", "lower-roman": "i", "upper-roman": "I"}
    type_attr = f' type="{style_types[block["marker_style"]]}"' if ordered and block.get("marker_style") in style_types else ""
    start_attr = f' start="{int(block["start"])}"' if ordered and int(block.get("start", 1)) != 1 else ""
    items: list[str] = []
    for child in block.get("children", []):
        if is_excluded(child) or is_footnote_body(child):
            continue
        nested_parts: list[str] = []
        for item in child.get("children", []):
            if is_excluded(item) or is_footnote_body(item):
                continue
            if item.get("type") == "list":
                nested_parts.append(_list_markup(item))
            elif item.get("type") == "table":
                nested_parts.append(_table_markup(item))
            elif item.get("type") in {"paragraph", "caption", "callout", "quote"}:
                nested_parts.append(f"<p>{render_inline(item)}</p>")
            else:
                nested_parts.append(html.escape(str(item.get("content", ""))))
        nested = "".join(nested_parts)
        items.append(f"<li>{render_inline(child)}{nested}</li>")
    return f'<{tag}{type_attr}{start_attr} class="wp-block-list">{"".join(items)}</{tag}>'


def _render_list(block: dict[str, Any]) -> str:
    attrs = {"ordered": True} if block.get("ordered") else {}
    style_types = {"lower-alpha": "a", "upper-alpha": "A", "lower-roman": "i", "upper-roman": "I"}
    if block.get("ordered") and block.get("marker_style") in style_types:
        attrs["type"] = style_types[block["marker_style"]]
    if block.get("ordered") and int(block.get("start", 1)) != 1:
        attrs["start"] = int(block["start"])
    return _wrap("list", _list_markup(block), attrs)


def _wordpress_image_values(block: dict[str, Any]) -> tuple[str | None, int | None]:
    media = block.get("wordpress_media") if isinstance(block.get("wordpress_media"), dict) else {}
    url = block.get("wordpress_url") or media.get("url")
    if url and not (
        urlparse(str(url)).scheme in {"http", "https"}
        or str(url).startswith("/api/preview/images/")
    ):
        url = None
    if not url:
        candidate = str(block.get("src") or "")
        if urlparse(candidate).scheme in {"http", "https"}:
            url = candidate
    attachment = block.get(
        "wordpress_attachment_id", media.get("attachment_id", block.get("image_id"))
    )
    try:
        attachment_id = int(attachment) if attachment is not None else None
    except (TypeError, ValueError):
        attachment_id = None
    return (str(url) if url else None), attachment_id


def _render_image(block: dict[str, Any]) -> str:
    url, attachment_id = _wordpress_image_values(block)
    alt_text = "" if block.get("decorative") else str(block.get("alt", ""))
    caption = str(block.get("caption") or "")
    if not url:
        if block.get("decorative"):
            block_id = html.escape(str(block.get("id", "")), quote=True)
            return f'<!-- pdf-to-web: decorative unresolved image omitted; block {block_id} -->'
        block_id = html.escape(str(block.get("id", "")), quote=True)
        alt = html.escape(alt_text, quote=True)
        caption_attr = html.escape(caption, quote=True)
        visible = "Image requires upload"
        if caption:
            visible += f": {html.escape(caption)}"
        elif alt_text:
            visible += f": {html.escape(alt_text)}"
        placeholder = (
            f'<figure class="pdf-to-web-unresolved-media" data-pdf-to-web-media="unresolved" '
            f'data-block-id="{block_id}" data-alt="{alt}" data-caption="{caption_attr}">'
            f'<div role="note"><strong>{visible}</strong></div></figure>'
        )
        return _wrap("html", placeholder)
    attrs = {"id": attachment_id} if attachment_id is not None else {}
    escaped_url = html.escape(url, quote=True)
    alt = html.escape(alt_text, quote=True)
    markup = f'<figure class="wp-block-image"><img src="{escaped_url}" alt="{alt}"'
    if attachment_id is not None:
        markup += f' class="wp-image-{attachment_id}"'
    markup += ">"
    if caption:
        markup += f"<figcaption>{html.escape(caption)}</figcaption>"
    markup += "</figure>"
    return _wrap("image", markup, attrs)


def _table_markup(block: dict[str, Any]) -> str:
    rows = block.get("rows", [])
    table_review = block.get("table_accessibility", {})
    header_row = table_review.get("header_row", True)
    header_column = table_review.get("header_column", False)
    body = []
    for row_index, row in enumerate(rows):
        cells: list[str] = []
        for column_index, cell in enumerate(row):
            cell_tag = "th" if (header_row and row_index == 0) or (header_column and column_index == 0) else "td"
            content, row_span, column_span = table_cell(cell)
            spans = ""
            if cell_tag == "th":
                spans += ' scope="col"' if header_row and row_index == 0 else ' scope="row"'
            if row_span > 1:
                spans += f' rowspan="{row_span}"'
            if column_span > 1:
                spans += f' colspan="{column_span}"'
            cells.append(f"<{cell_tag}{spans}>{html.escape(content)}</{cell_tag}>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    caption = block.get("caption")
    caption_markup = f"<figcaption>{html.escape(str(caption))}</figcaption>" if caption else ""
    return (
        '<figure class="wp-block-table"><table><tbody>'
        + "".join(body)
        + f"</tbody></table>{caption_markup}</figure>"
    )


def _render_table(block: dict[str, Any]) -> str:
    return _wrap("table", _table_markup(block))


def render_block(block: dict[str, Any]) -> str:
    if is_excluded(block) or is_footnote_body(block):
        return ""
    if block.get("export_as_part_of_image"):
        return ""
    block_type = block.get("type")
    if block_type == "heading":
        level = max(1, min(6, int(block.get("level", 2))))
        attrs = {} if level == 2 else {"level": level}
        return _wrap(
            "heading", f'<h{level} class="wp-block-heading">{render_inline(block)}</h{level}>', attrs
        )
    if block_type in {"paragraph", "caption", "callout"}:
        if not str(block.get("content", "")).strip() and not block.get("runs") and not block.get("footnote_references"):
            return ""
        return _wrap("paragraph", f"<p>{render_inline(block)}</p>")
    if block_type == "list":
        return _render_list(block)
    if block_type == "image":
        return _render_image(block)
    if block_type == "quote":
        return _wrap(
            "quote", f'<blockquote class="wp-block-quote"><p>{render_inline(block)}</p></blockquote>'
        )
    if block_type == "table":
        return _render_table(block)
    if block_type == "page_break":
        return _wrap("separator", '<hr class="wp-block-separator has-alpha-channel-opacity">')
    content = html.escape(str(block.get("content", "")))
    source_type = html.escape(str(block.get("provenance", {}).get("source_type", "unknown")), quote=True)
    return _wrap(
        "html", f'<div data-pdf-to-web-unknown="{source_type}">{content}</div>'
    )


def _render_footnotes(document: dict[str, Any]) -> list[str]:
    footnotes = [note for note in document.get("footnotes", []) if isinstance(note, dict)]
    if not footnotes:
        return []
    items: list[str] = []
    for footnote in footnotes:
        footnote_id = html.escape(str(footnote.get("id", "")), quote=True)
        text = html.escape(str(footnote.get("text", "")))
        backlinks = render_footnote_backlinks(footnote)
        items.append(f'<li id="{footnote_id}">{text} {backlinks}</li>')
    markup = (
        '<section class="footnotes" aria-labelledby="footnotes-heading">'
        '<h2 id="footnotes-heading">Footnotes</h2>'
        f'<ol>{"".join(items)}</ol></section>'
    )
    return [_wrap("html", markup)]


def _wsu_hero(document: dict[str, Any], config: dict[str, Any]) -> str:
    hero = dict(config.get("hero") or {})
    title = document.get("metadata", {}).get("title", "Untitled document")
    attrs: dict[str, Any] = {
        "title": hero.get("title", title),
        "headingTag": hero.get("headingTag", "h1"),
    }
    for key in ("caption", "imageId", "imageSrc", "backgroundType", "className"):
        if hero.get(key) is not None:
            attrs[key] = hero[key]
    return f"<!-- wp:wsuwp/hero{_attrs(attrs, escape_hyphens=True)} /-->"


def render_document(
    document: dict[str, Any], profile: str = "generic", config: dict[str, Any] | None = None
) -> str:
    config = config or {}
    blocks = list(document.get("blocks", []))
    rendered: list[str] = []
    if profile == "wsuwp":
        if (config.get("hero") or {}).get("enabled"):
            rendered.append(_wsu_hero(document, config))
            title = str(document.get("metadata", {}).get("title", ""))
            if blocks and blocks[0].get("type") == "heading" and blocks[0].get("content") == title:
                blocks = blocks[1:]
        section = dict(config.get("section_defaults") or {})
        wrap_in_section = bool(config.get("wrap_in_section")) or bool(section)
        if wrap_in_section:
            rendered.append(f"<!-- wp:wsuwp/section{_attrs(section, escape_hyphens=True)} -->")
        rendered.extend(content for block in blocks if (content := render_block(block)))
        if wrap_in_section:
            rendered.append("<!-- /wp:wsuwp/section -->")
    elif profile == "generic":
        rendered.extend(content for block in blocks if (content := render_block(block)))
    else:
        raise ValueError(f"Unknown WordPress export profile: {profile}")
    rendered.extend(_render_footnotes(document))
    return "\n\n".join(rendered) + "\n"
