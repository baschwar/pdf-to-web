from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any

CONTENT_NS = "http://purl.org/rss/1.0/modules/content/"
DC_NS = "http://purl.org/dc/elements/1.1/"
EXCERPT_NS = "http://wordpress.org/export/1.2/excerpt/"
WP_NS = "http://wordpress.org/export/1.2/"

ET.register_namespace("content", CONTENT_NS)
ET.register_namespace("dc", DC_NS)
ET.register_namespace("excerpt", EXCERPT_NS)
ET.register_namespace("wp", WP_NS)


def _sub(parent: ET.Element, tag: str, value: Any = "") -> ET.Element:
    node = ET.SubElement(parent, tag)
    node.text = "" if value is None else str(value)
    return node


def render_wxr(
    items: list[dict[str, Any]],
    site: dict[str, Any] | None = None,
) -> str:
    site = site or {}
    root = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(root, "channel")
    _sub(channel, "title", site.get("title", "PDF to Web export"))
    _sub(channel, "link", site.get("url", "https://example.invalid"))
    _sub(channel, "description", "Generated locally by PDF to Web")
    _sub(channel, "language", site.get("language", "en-US"))
    _sub(channel, f"{{{WP_NS}}}wxr_version", "1.2")
    _sub(channel, f"{{{WP_NS}}}base_site_url", site.get("url", "https://example.invalid"))
    _sub(channel, f"{{{WP_NS}}}base_blog_url", site.get("url", "https://example.invalid"))

    ids: dict[str, int] = {}
    for index, item in enumerate(items, start=1):
        ids[str(item.get("key") or item.get("slug") or index)] = int(item.get("post_id", index))

    for index, item in enumerate(items, start=1):
        post_id = int(item.get("post_id", index))
        key = str(item.get("key") or item.get("slug") or index)
        parent_key = item.get("parent")
        parent_id = ids.get(str(parent_key), 0) if parent_key else 0
        post_type = str(item.get("post_type", "page"))
        status = str(item.get("status", "draft"))
        date = str(item.get("date") or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))

        node = ET.SubElement(channel, "item")
        _sub(node, "title", item.get("title", "Untitled"))
        _sub(node, "link", "")
        _sub(node, "pubDate", "")
        _sub(node, "guid", f"pdf-to-web:{key}").set("isPermaLink", "false")
        _sub(node, "description", "")
        _sub(node, f"{{{CONTENT_NS}}}encoded", item.get("content", ""))
        _sub(node, f"{{{EXCERPT_NS}}}encoded", item.get("excerpt", ""))
        _sub(node, f"{{{WP_NS}}}post_id", post_id)
        _sub(node, f"{{{WP_NS}}}post_date", date)
        _sub(node, f"{{{WP_NS}}}post_date_gmt", date)
        _sub(node, f"{{{WP_NS}}}comment_status", "closed")
        _sub(node, f"{{{WP_NS}}}ping_status", "closed")
        _sub(node, f"{{{WP_NS}}}post_name", item.get("slug", key))
        _sub(node, f"{{{WP_NS}}}status", status)
        _sub(node, f"{{{WP_NS}}}post_parent", parent_id)
        _sub(node, f"{{{WP_NS}}}menu_order", int(item.get("menu_order", 0)))
        _sub(node, f"{{{WP_NS}}}post_type", post_type)
        _sub(node, f"{{{WP_NS}}}post_password", "")
        _sub(node, f"{{{WP_NS}}}is_sticky", 0)
        creator = ET.SubElement(node, f"{{{DC_NS}}}creator")
        creator.text = str(item.get("author", "pdf-to-web"))
        for category in item.get("categories", []):
            term = _sub(node, "category", category)
            term.set("domain", "category")
            term.set("nicename", str(category).lower().replace(" ", "-"))
        for tag in item.get("tags", []):
            term = _sub(node, "category", tag)
            term.set("domain", "post_tag")
            term.set("nicename", str(tag).lower().replace(" ", "-"))

    xml = ET.tostring(root, encoding="unicode", xml_declaration=False)
    return '<?xml version="1.0" encoding="UTF-8" ?>\n' + xml + "\n"
