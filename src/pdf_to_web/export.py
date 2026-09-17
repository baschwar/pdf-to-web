from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .errors import PdfToWebError
from .exporters import gutenberg, html, markdown, wxr
from .normalize import load_normalized
from .project import load_project, slugify


def _publication_item(
    document: dict[str, Any], content: str, config: dict[str, Any]
) -> dict[str, Any]:
    metadata = document.get("metadata", {})
    wordpress = config.get("wordpress", {})
    title = str(metadata.get("title") or "Untitled document")
    return {
        "key": slugify(title),
        "title": title,
        "slug": wordpress.get("slug") or slugify(title),
        "post_type": wordpress.get("post_type", "page"),
        "status": wordpress.get("status", "draft"),
        "author": wordpress.get("author", "pdf-to-web"),
        "excerpt": wordpress.get("excerpt", ""),
        "date": wordpress.get("publication_date"),
        "menu_order": wordpress.get("menu_order", 0),
        "categories": wordpress.get("categories", []),
        "tags": wordpress.get("tags", []),
        "content": content,
    }


def _write_manifest(
    project_dir: Path, item: dict[str, Any], profile: str, output_slug: str
) -> None:
    report_dir = project_dir / "output" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "wordpress_profile": profile,
        "items": [
            {
                "title": item["title"],
                "slug": item["slug"],
                "post_type": item["post_type"],
                "status": item["status"],
                "gutenberg_file": f"output/wordpress/blocks/{output_slug}.html",
                "wxr_file": f"output/wordpress/wxr/{output_slug}.xml",
                "media_status": "mapping_required",
            }
        ],
    }
    (report_dir / "export-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    with (report_dir / "manifest.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(manifest["items"][0]))
        writer.writeheader()
        writer.writerows(manifest["items"])


def export_project(project_dir: Path, target: str, profile: str | None = None) -> list[Path]:
    project_dir = project_dir.expanduser().resolve()
    document = load_normalized(project_dir)
    project = load_project(project_dir)
    config = project.get("export", {})
    selected_profile = profile or config.get("wordpress_profile", "generic")
    if selected_profile not in {"generic", "wsuwp"}:
        raise PdfToWebError(f"Unsupported WordPress profile: {selected_profile}")
    review_status = document.get("review", {}).get("status", "needs_review")
    if review_status == "conversion_blocked" and target in {
        "gutenberg",
        "wordpress-xml",
        "all",
    }:
        raise PdfToWebError(
            "Conversion is blocked by extraction issues; Gutenberg and WXR export were not generated"
        )

    gutenberg_content = gutenberg.render_document(document, selected_profile, config)
    item = _publication_item(document, gutenberg_content, config)
    source_filename = str(project.get("source", {}).get("original_filename") or "")
    output_slug = slugify(Path(source_filename).stem) if source_filename else item["slug"]
    outputs: list[Path] = []

    if target in {"markdown", "all"}:
        path = project_dir / "output" / "markdown" / f"{output_slug}.md"
        path.write_text(markdown.render_document(document), encoding="utf-8")
        outputs.append(path)
    if target in {"html", "all"}:
        path = project_dir / "output" / "html" / f"{output_slug}.html"
        path.write_text(html.render_document(document), encoding="utf-8")
        outputs.append(path)
    if target in {"gutenberg", "all"}:
        path = project_dir / "output" / "wordpress" / "blocks" / f"{output_slug}.html"
        path.write_text(gutenberg_content, encoding="utf-8")
        outputs.append(path)
    if target in {"wordpress-xml", "all"}:
        path = project_dir / "output" / "wordpress" / "wxr" / f"{output_slug}.xml"
        path.write_text(wxr.render_wxr([item]), encoding="utf-8")
        outputs.append(path)
    _write_manifest(project_dir, item, selected_profile, output_slug)
    return outputs
