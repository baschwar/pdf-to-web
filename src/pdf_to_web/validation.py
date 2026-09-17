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
        self.ids: list[str] = []
        self.internal_targets: list[str] = []
        self.external_links: list[dict[str, str]] = []
        self._link: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags[tag] += 1
        values = dict(attrs)
        if re.fullmatch(r"h[1-6]", tag):
            self.heading_levels.append(int(tag[1]))
        if values.get("data-pdf-to-web-type") == "unknown":
            self.unknown_blocks += 1
        if tag == "img" and "alt" not in values:
            self.images_without_alt += 1
        element_id = values.get("id")
        if element_id is not None:
            self.ids.append(element_id)
        if tag == "a":
            href = values.get("href") or ""
            self._link = {"href": href, "text": ""}
            if href.startswith("#"):
                self.internal_targets.append(href[1:])

    def handle_data(self, data: str) -> None:
        if self._link is not None:
            self._link["text"] += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._link is not None:
            if not self._link["href"].startswith("#"):
                self.external_links.append(
                    {"text": self._link["text"].strip(), "href": self._link["href"]}
                )
            self._link = None


def validate_internal_links(markup: str) -> dict[str, Any]:
    parser = _SemanticParser()
    errors: list[str] = []
    try:
        parser.feed(markup)
        parser.close()
    except Exception as exc:
        errors.append(str(exc))
    counts = Counter(parser.ids)
    duplicate_ids = sorted(value for value, count in counts.items() if value and count > 1)
    empty_ids = sum(value == "" for value in parser.ids)
    malformed_targets = sorted(
        target for target in parser.internal_targets if not target or any(char.isspace() for char in target)
    )
    missing_targets = sorted(
        target for target in set(parser.internal_targets) if target and target not in counts
    )
    errors.extend(f"Duplicate id: {value}" for value in duplicate_ids)
    errors.extend("Empty id attribute" for _ in range(empty_ids))
    errors.extend(f"Malformed internal target: #{value}" for value in malformed_targets)
    errors.extend(f"Missing internal target: #{value}" for value in missing_targets)
    return {
        "valid": not errors,
        "ids": len(parser.ids),
        "internal_links": len(parser.internal_targets),
        "resolved_internal_links": len(parser.internal_targets) - len(missing_targets) - len(malformed_targets),
        "duplicate_ids": duplicate_ids,
        "empty_ids": empty_ids,
        "missing_targets": missing_targets,
        "malformed_targets": malformed_targets,
        "errors": errors,
    }


def validate_semantic_html(
    document: dict[str, Any], markup: str, *, enforce_document_title: bool = True
) -> dict[str, Any]:
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
    anchors = validate_internal_links(markup)
    if not anchors["valid"]:
        errors.extend(anchors["errors"])
    literal_bullets = len(re.findall(r"<li[^>]*>\s*[•‣◦▪]", markup))
    if literal_bullets:
        errors.append(f"{literal_bullets} list item(s) retain literal bullet characters")
    h1_count = parser.tags["h1"]
    if enforce_document_title and document.get("metadata", {}).get("title") and h1_count != 1:
        errors.append(f"Expected exactly one document H1; found {h1_count}")
    return {
        "generated": True,
        "valid": not errors,
        "headings": sum(parser.tags[f"h{level}"] for level in range(1, 7)),
        "h1_count": h1_count,
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
        "anchors": anchors,
        "external_links": parser.external_links,
        "literal_bullet_items": literal_bullets,
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
    html_validation = validate_semantic_html(document, markup, enforce_document_title=False)
    errors.extend(html_validation["serialization_errors"])
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
        "anchors": html_validation["anchors"],
        "external_links": html_validation["external_links"],
        "literal_bullet_items": html_validation["literal_bullet_items"],
        "serialization_errors": errors,
    }


def validate_wxr(markup: str, documents: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    errors: list[str] = []
    items: list[dict[str, Any]] = []
    try:
        root = ET.fromstring(markup)
        version = root.findtext(f"./channel/{{{WP_NS}}}wxr_version", "")
        if version != "1.2":
            errors.append(f"Unexpected WXR version: {version or 'missing'}")
        for index, node in enumerate(root.findall("./channel/item")):
            content = node.findtext(f"{{{CONTENT_NS}}}encoded", "")
            document = documents[index] if documents and index < len(documents) else {"blocks": []}
            content_validation = validate_gutenberg(document, content)
            if not content_validation["valid"]:
                errors.extend(f"Item {index + 1}: {message}" for message in content_validation["serialization_errors"])
            items.append(
                {
                    "title": node.findtext("title", ""),
                    "slug": node.findtext(f"{{{WP_NS}}}post_name", ""),
                    "post_type": node.findtext(f"{{{WP_NS}}}post_type", ""),
                    "status": node.findtext(f"{{{WP_NS}}}status", ""),
                    "parent": node.findtext(f"{{{WP_NS}}}post_parent", ""),
                    "menu_order": node.findtext(f"{{{WP_NS}}}menu_order", ""),
                    "excerpt": node.findtext(f"{{{EXCERPT_NS}}}encoded", ""),
                    "content_length": len(content),
                    "content": content,
                    "content_validation": content_validation,
                    "categories": len(node.findall("category")),
                    "taxonomies": [
                        {"domain": category.get("domain", ""), "name": category.text or ""}
                        for category in node.findall("category")
                    ],
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
