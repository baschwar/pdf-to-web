from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from html.parser import HTMLParser
from typing import Any, Iterable

from .exporters.wxr import CONTENT_NS, EXCERPT_NS, WP_NS


def _flatten(blocks: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for block in blocks:
        yield block
        yield from _flatten(block.get("children", []))


class _SemanticParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: Counter[str] = Counter()
        self.heading_levels: list[int] = []
        self.unknown_blocks = 0
        self.images_without_alt = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags[tag] += 1
        values = dict(attrs)
        if re.fullmatch(r"h[1-6]", tag):
            self.heading_levels.append(int(tag[1]))
        if values.get("data-pdf-to-web-type") == "unknown":
            self.unknown_blocks += 1
        if tag == "img" and "alt" not in values:
            self.images_without_alt += 1


def validate_semantic_html(document: dict[str, Any], markup: str) -> dict[str, Any]:
    parser = _SemanticParser()
    errors: list[str] = []
    try:
        parser.feed(markup)
        parser.close()
    except Exception as exc:
        errors.append(str(exc))
    heading_jumps = [
        [previous, current]
        for previous, current in zip(parser.heading_levels, parser.heading_levels[1:])
        if current > previous + 1
    ]
    return {
        "generated": True,
        "valid": not errors,
        "headings": sum(parser.tags[f"h{level}"] for level in range(1, 7)),
        "paragraphs": parser.tags["p"],
        "lists": parser.tags["ul"] + parser.tags["ol"],
        "list_items": parser.tags["li"],
        "tables": parser.tags["table"],
        "images": parser.tags["img"],
        "figures": parser.tags["figure"],
        "captions": parser.tags["figcaption"] + parser.tags["caption"],
        "quotes": parser.tags["blockquote"],
        "links": parser.tags["a"],
        "strong": parser.tags["strong"],
        "emphasis": parser.tags["em"],
        "unknown_blocks": parser.unknown_blocks,
        "images_without_alt_attribute": parser.images_without_alt,
        "heading_jumps": heading_jumps,
        "serialization_errors": errors,
    }


BLOCK_COMMENT = re.compile(
    r"<!--\s+(?P<closing>/)?wp:(?P<name>[a-z0-9_-]+(?:/[a-z0-9_-]+)?)"
    r"(?:\s+\{.*?\})?\s*(?P<self>/)?-->",
    re.DOTALL,
)


def validate_gutenberg(document: dict[str, Any], markup: str) -> dict[str, Any]:
    stack: list[str] = []
    errors: list[str] = []
    block_names: Counter[str] = Counter()
    for match in BLOCK_COMMENT.finditer(markup):
        name = match.group("name")
        if match.group("closing"):
            if not stack or stack[-1] != name:
                errors.append(f"Unexpected closing block: {name}")
            else:
                stack.pop()
        else:
            block_names[name] += 1
            if not match.group("self"):
                stack.append(name)
    if stack:
        errors.append(f"Unclosed blocks: {', '.join(stack)}")
    top_level = list(document.get("blocks", []))
    skipped = sum(bool(block.get("export_as_part_of_image")) for block in top_level)
    fallback = sum(block.get("type") == "unknown" for block in top_level)
    return {
        "generated": True,
        "valid": not errors,
        "normalized_block_count": len(list(_flatten(top_level))),
        "normalized_top_level_block_count": len(top_level),
        "exported_top_level_block_count": len(top_level) - skipped,
        "skipped_block_count": skipped,
        "fallback_unknown_count": fallback,
        "block_comment_count": sum(block_names.values()),
        "block_names": dict(sorted(block_names.items())),
        "serialization_errors": errors,
    }


def validate_wxr(markup: str) -> dict[str, Any]:
    errors: list[str] = []
    items: list[dict[str, Any]] = []
    try:
        root = ET.fromstring(markup)
        for node in root.findall("./channel/item"):
            items.append(
                {
                    "title": node.findtext("title", ""),
                    "slug": node.findtext(f"{{{WP_NS}}}post_name", ""),
                    "post_type": node.findtext(f"{{{WP_NS}}}post_type", ""),
                    "status": node.findtext(f"{{{WP_NS}}}status", ""),
                    "parent": node.findtext(f"{{{WP_NS}}}post_parent", ""),
                    "menu_order": node.findtext(f"{{{WP_NS}}}menu_order", ""),
                    "excerpt": node.findtext(f"{{{EXCERPT_NS}}}encoded", ""),
                    "content_length": len(node.findtext(f"{{{CONTENT_NS}}}encoded", "")),
                    "categories": len(node.findall("category")),
                }
            )
    except ET.ParseError as exc:
        errors.append(str(exc))
    return {
        "generated": True,
        "valid": not errors,
        "item_count": len(items),
        "items": items,
        "serialization_errors": errors,
    }
