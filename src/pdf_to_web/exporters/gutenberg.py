from __future__ import annotations

import html
import json
import re
from typing import Any

from .common import image_src, render_inline, table_cell


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
    items: list[str] = []
    for child in block.get("children", []):
        nested = "".join(
            _list_markup(item)
            for item in child.get("children", [])
            if item.get("type") == "list"
        )
        items.append(f"<li>{render_inline(child)}{nested}</li>")
    return f'<{tag} class="wp-block-list">{"".join(items)}</{tag}>'


def _render_list(block: dict[str, Any]) -> str:
    attrs = {"ordered": True} if block.get("ordered") else {}
    return _wrap("list", _list_markup(block), attrs)


def _render_table(block: dict[str, Any]) -> str:
    rows = block.get("rows", [])
    body = []
    for row_index, row in enumerate(rows):
        cell_tag = "th" if row_index == 0 else "td"
        cells: list[str] = []
        for cell in row:
            content, row_span, column_span = table_cell(cell)
            spans = ""
            if row_span > 1:
                spans += f' rowspan="{row_span}"'
            if column_span > 1:
                spans += f' colspan="{column_span}"'
            cells.append(f"<{cell_tag}{spans}>{html.escape(content)}</{cell_tag}>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    caption = block.get("caption")
    caption_markup = f"<figcaption>{html.escape(str(caption))}</figcaption>" if caption else ""
    markup = (
        '<figure class="wp-block-table"><table><tbody>'
        + "".join(body)
        + f"</tbody></table>{caption_markup}</figure>"
    )
    return _wrap("table", markup)


def render_block(block: dict[str, Any]) -> str:
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
        return _wrap("paragraph", f"<p>{render_inline(block)}</p>")
    if block_type == "list":
        return _render_list(block)
    if block_type == "image":
        attrs = {"id": block["image_id"]} if block.get("image_id") is not None else {}
        alt = "" if block.get("decorative") else html.escape(str(block.get("alt", "")), quote=True)
        markup = f'<figure class="wp-block-image"><img src="{image_src(block)}" alt="{alt}"'
        if block.get("image_id") is not None:
            markup += f' class="wp-image-{int(block["image_id"])}"'
        markup += ">"
        if block.get("caption"):
            markup += f"<figcaption>{html.escape(str(block['caption']))}</figcaption>"
        markup += "</figure>"
        return _wrap("image", markup, attrs)
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
        rendered.append(f"<!-- wp:wsuwp/section{_attrs(section, escape_hyphens=True)} -->")
        rendered.extend(content for block in blocks if (content := render_block(block)))
        rendered.append("<!-- /wp:wsuwp/section -->")
    elif profile == "generic":
        rendered.extend(content for block in blocks if (content := render_block(block)))
    else:
        raise ValueError(f"Unknown WordPress export profile: {profile}")
    return "\n\n".join(rendered) + "\n"
