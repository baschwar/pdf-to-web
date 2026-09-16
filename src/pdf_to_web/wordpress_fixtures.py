from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .exporters.gutenberg import render_document
from .exporters.wxr import render_wxr


def _document(title: str) -> dict[str, Any]:
    return {
        "metadata": {"title": title},
        "blocks": [
            {"id": "heading", "type": "heading", "level": 1, "content": title},
            {
                "id": "intro",
                "type": "paragraph",
                "runs": [
                    {"type": "text", "text": "Café access includes "},
                    {"type": "strong", "text": "clear structure"},
                    {"type": "text", "text": ", "},
                    {"type": "emphasis", "text": "useful alternatives"},
                    {"type": "text", "text": ", and "},
                    {"type": "link", "text": "source context", "url": "https://example.edu/?a=1&b=2"},
                    {"type": "text", "text": "."},
                ],
            },
            {
                "id": "list",
                "type": "list",
                "ordered": False,
                "children": [
                    {"id": "one", "type": "list_item", "content": "First finding", "children": []},
                    {"id": "two", "type": "list_item", "content": "Second finding", "children": []},
                ],
            },
            {
                "id": "image",
                "type": "image",
                "src": "https://example.edu/publication-image.jpg",
                "alt": "Students working together in a clinical simulation lab",
                "caption": "Practice builds confidence.",
            },
            {"id": "quote", "type": "quote", "content": "Care begins with listening."},
            {
                "id": "table",
                "type": "table",
                "caption": "Enrollment",
                "rows": [["Program", "Students"], ["BSN", "42"]],
            },
        ],
    }


def _item(key: str, title: str, post_type: str = "page", **values: Any) -> dict[str, Any]:
    item = {
        "key": key,
        "title": title,
        "slug": key,
        "post_type": post_type,
        "status": "draft",
        "author": "pdf-to-web",
        "date": "2026-09-16 12:00:00",
        "content": render_document(_document(title)),
    }
    item.update(values)
    return item


def fixture_sets() -> dict[str, list[dict[str, Any]]]:
    page = _item("roundtrip-page", "Round-trip Page")
    post = _item(
        "roundtrip-post",
        "Round-trip Post",
        "post",
        categories=["Research"],
        tags=["Accessibility"],
    )
    parent = _item("roundtrip-parent", "Round-trip Parent", menu_order=3)
    child = _item("roundtrip-child", "Round-trip Child", parent="roundtrip-parent", menu_order=4)
    wsu_document = _document("WSU Block Contract")
    wsu_content = render_document(
        wsu_document,
        "wsuwp",
        {
            "hero": {
                "enabled": True,
                "caption": "College of Nursing",
                "imageSrc": "https://example.edu/hero.jpg",
                "backgroundType": "image",
                "className": "wsu-hero--style-boxed wsu-hero--size-xsmall",
            },
            "section_defaults": {
                "id": "top",
                "className": "wsu-color-background--white wsu-spacing-after--none",
            },
        },
    )
    wsu = _item("wsu-block-contract", "WSU Block Contract", content=wsu_content)
    return {
        "single-page.xml": [page],
        "single-post.xml": [post],
        "parent-child.xml": [parent, child],
        "multi-item.xml": [page, post, parent, child],
        "wsuwp-page.xml": [wsu],
    }


def write_wordpress_fixtures(output_dir: Path) -> list[Path]:
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    expected: dict[str, list[dict[str, Any]]] = {}
    for filename, items in fixture_sets().items():
        path = output_dir / filename
        path.write_text(
            render_wxr(items, {"title": "PDF to Web round-trip", "url": "http://localhost:8099"}),
            encoding="utf-8",
        )
        created.append(path)
        expected[filename] = [
            {
                "title": item["title"],
                "slug": item["slug"],
                "post_type": item["post_type"],
                "status": item["status"],
                "parent": item.get("parent"),
                "menu_order": item.get("menu_order", 0),
            }
            for item in items
        ]
    expected_path = output_dir / "expected.json"
    expected_path.write_text(json.dumps(expected, indent=2) + "\n", encoding="utf-8")
    created.append(expected_path)
    return created
