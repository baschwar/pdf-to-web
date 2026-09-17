from __future__ import annotations

import csv
import filecmp
import json
import re
import shutil
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .errors import PdfToWebError
from .exporters import gutenberg, html, markdown, wxr
from .normalize import load_normalized
from .project import load_project, slugify


def _walk(blocks: list[dict[str, Any]]):
    for block in blocks:
        yield block
        yield from _walk(block.get("children", []))


def _wordpress_media_values(block: dict[str, Any]) -> tuple[str | None, int | None]:
    media = block.get("wordpress_media") if isinstance(block.get("wordpress_media"), dict) else {}
    url = block.get("wordpress_url") or media.get("url")
    if url and urlparse(str(url)).scheme not in {"http", "https"}:
        url = None
    if not url:
        source = str(block.get("src") or "")
        if urlparse(source).scheme in {"http", "https"}:
            url = source
    attachment = block.get(
        "wordpress_attachment_id", media.get("attachment_id", block.get("image_id"))
    )
    try:
        attachment_id = int(attachment) if attachment is not None else None
    except (TypeError, ValueError):
        attachment_id = None
    return (str(url) if url else None), attachment_id


def _local_image_path(project_dir: Path, source: str) -> Path | None:
    relative = Path(source)
    if not source or relative.is_absolute() or ".." in relative.parts:
        return None
    candidates = [project_dir / "extraction" / "raw" / relative, project_dir / "extraction" / "assets" / relative]
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_file() and resolved.is_relative_to(project_dir):
            return resolved
    return None


def _copy_media_asset(source: Path, destination_dir: Path) -> Path:
    clean_name = re.sub(r"[^A-Za-z0-9._-]", "-", source.name) or "image"
    destination = destination_dir / clean_name
    index = 2
    while destination.exists() and not filecmp.cmp(source, destination, shallow=False):
        destination = destination_dir / f"{Path(clean_name).stem}-{index}{Path(clean_name).suffix}"
        index += 1
    if not destination.exists():
        shutil.copy2(source, destination)
    return destination


def _write_media_manifest(project_dir: Path, document: dict[str, Any]) -> tuple[list[Path], dict[str, Any]]:
    assets_dir = project_dir / "output" / "wordpress" / "assets"
    reports_dir = project_dir / "output" / "wordpress" / "reports"
    assets_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    entries: list[dict[str, Any]] = []
    copied: dict[Path, Path] = {}
    for block in _walk(document.get("blocks", [])):
        if block.get("type") != "image" or block.get("review", {}).get("status") == "excluded" or block.get("excluded"):
            continue
        url, attachment_id = _wordpress_media_values(block)
        decorative = bool(block.get("decorative"))
        status = "decorative" if decorative else "resolved" if url else "unresolved"
        source_value = str(block.get("src") or "")
        local_source = _local_image_path(project_dir, source_value)
        exported_asset: Path | None = None
        if local_source:
            exported_asset = copied.get(local_source)
            if exported_asset is None:
                exported_asset = _copy_media_asset(local_source, assets_dir)
                copied[local_source] = exported_asset
                outputs.append(exported_asset)
        entries.append(
            {
                "asset_filename": exported_asset.name if exported_asset else Path(source_value).name or None,
                "asset_path": str(exported_asset.relative_to(project_dir)) if exported_asset else None,
                "source_path": source_value or None,
                "source_page": block.get("provenance", {}).get("source_page"),
                "block_id": block.get("id"),
                "caption": str(block.get("caption") or ""),
                "alt_text": str(block.get("alt") or ""),
                "decorative": decorative,
                "wordpress_status": status,
                "wordpress_url": url,
                "wordpress_attachment_id": attachment_id,
            }
        )
    manifest = {
        "schema_version": "pdf-to-web-wordpress-media-v1",
        "summary": {
            "total": len(entries),
            "resolved": sum(item["wordpress_status"] == "resolved" for item in entries),
            "unresolved": sum(item["wordpress_status"] == "unresolved" for item in entries),
            "decorative": sum(item["wordpress_status"] == "decorative" for item in entries),
            "copied_assets": len(copied),
        },
        "items": entries,
    }
    json_path = reports_dir / "media-manifest.json"
    md_path = reports_dir / "media-manifest.md"
    json_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["# WordPress Media Manifest", "", f"Images requiring upload: **{manifest['summary']['unresolved']}**", "", "| Asset | Page | Block | Status | Alt text | Caption | WordPress URL | Attachment ID |", "| --- | ---: | --- | --- | --- | --- | --- | ---: |"]
    for item in entries:
        values = {key: str(value or "").replace("|", "\\|") for key, value in item.items()}
        lines.append(f"| {values['asset_filename']} | {values['source_page']} | {values['block_id']} | {values['wordpress_status']} | {values['alt_text']} | {values['caption']} | {values['wordpress_url']} | {values['wordpress_attachment_id']} |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    outputs.extend([json_path, md_path])
    return outputs, manifest


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
    if target in {"gutenberg", "wordpress-xml", "all"}:
        media_outputs, _ = _write_media_manifest(project_dir, document)
        outputs.extend(media_outputs)
    _write_manifest(project_dir, item, selected_profile, output_slug)
    return outputs
