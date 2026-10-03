from __future__ import annotations

import csv
import copy
import json
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .errors import PdfToWebError
from .exporters import gutenberg, html, markdown, wxr
from .normalize import load_normalized
from .project import load_project, slugify
from .media_mapping import MAPPING_FIELDS
from .accessibility import write_reports
from .exporters.common import is_excluded


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
    project_dir = project_dir.resolve()
    relative = Path(source)
    if not source or relative.is_absolute() or ".." in relative.parts:
        return None
    candidates = [project_dir / relative] if source.startswith(("extraction/raw/", "extraction/assets/images/")) else [project_dir / "extraction" / "raw" / relative, project_dir / "extraction" / "assets" / relative]
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_file() and resolved.is_relative_to(project_dir):
            return resolved
    return None


def media_prefix(document: dict[str, Any]) -> str:
    prefix = document.get('media_export', {}).get('image_prefix')
    return prefix if prefix is not None else slugify(str(document.get('metadata', {}).get('title') or 'document'))[:80] + '-'


def validate_media_prefix(prefix: str) -> str:
    prefix = prefix.strip().rstrip('-')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}', prefix):
        raise ValueError('Use an image prefix of 1–80 lowercase letters, digits or hyphens, starting with a letter or digit')
    return prefix.rstrip('-') + '-'


def _media_asset_names(project_dir: Path, document: dict[str, Any]) -> dict[Path, str]:
    # Immutable extraction order keeps filenames stable through reading-order edits,
    # exclusions and output-page arrangements. New assets follow the original set.
    original = project_dir / 'extraction/normalized/document.json'
    source_document = json.loads(original.read_text(encoding='utf-8')) if original.is_file() else document
    names: dict[Path, str] = {}
    prefix = validate_media_prefix(media_prefix(document))
    for block in [*_walk(source_document.get('blocks', [])), *_walk(document.get('blocks', []))]:
        if block.get('type') != 'image':
            continue
        source = _local_image_path(project_dir, str(block.get('src') or ''))
        if source and source not in names:
            names[source] = f'{prefix}image{len(names) + 1}{source.suffix.lower()}'
    return names


def _copy_media_asset(source: Path, destination_dir: Path, name: str) -> Path:
    destination = destination_dir / name
    shutil.copy2(source, destination)
    return destination


def _visible_walk(blocks):
    for block in blocks:
        if is_excluded(block):
            continue
        yield block
        yield from _visible_walk(block.get('children', []))


def _html_with_local_assets(project_dir: Path, document: dict[str, Any], directory: Path, *, name_document=None) -> tuple[dict[str, Any], list[Path]]:
    projected = copy.deepcopy(document)
    names = _media_asset_names(project_dir, name_document or document)
    copied: set[Path] = set()
    for block in _visible_walk(projected.get('blocks', [])):
        if block.get('type') != 'image':
            continue
        url, _ = _wordpress_media_values(block)
        if url:
            block['src'] = url
            continue
        source = _local_image_path(project_dir, str(block.get('src') or ''))
        if source:
            assets = directory / 'assets'
            assets.mkdir(parents=True, exist_ok=True)
            destination = assets / names[source]
            if destination not in copied:
                _copy_media_asset(source, assets, names[source])
                copied.add(destination)
            block['src'] = 'assets/' + names[source]
    return projected, sorted(copied)


def _write_media_manifest(project_dir: Path, document: dict[str, Any]) -> tuple[list[Path], dict[str, Any]]:
    assets_dir = project_dir / "output" / "wordpress" / "assets"
    reports_dir = project_dir / "output" / "wordpress" / "reports"
    assets_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    entries: list[dict[str, Any]] = []
    copied: dict[Path, Path] = {}
    names = _media_asset_names(project_dir, document)
    for block in _visible_walk(document.get("blocks", [])):
        if block.get("type") != "image":
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
                exported_asset = _copy_media_asset(local_source, assets_dir, names[local_source])
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
    mapping_path = reports_dir / "media-mapping.csv"
    with mapping_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=MAPPING_FIELDS)
        writer.writeheader()
        for item in entries:
            if item["decorative"]:
                continue
            writer.writerow({
                "block_id": item["block_id"],
                "asset_filename": item["asset_filename"],
                "wordpress_attachment_id": item["wordpress_attachment_id"] or "",
                "wordpress_url": item["wordpress_url"] or "",
                "alt_text": item["alt_text"],
                "caption": item["caption"],
            })
    outputs.append(mapping_path)
    upload_assets = sorted(
        {
            project_dir / str(item["asset_path"])
            for item in entries
            if item["asset_path"]
        },
        key=lambda path: path.name.lower(),
    )
    zip_path = project_dir / "output" / "wordpress" / "media-upload.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for asset in upload_assets:
            archive.write(asset, arcname=asset.name)
    outputs.append(zip_path)
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
    previous_manifest = report_dir / 'export-manifest.json'
    if previous_manifest.is_file():
        manifest['publication_artifacts'] = json.loads(previous_manifest.read_text()).get('publication_artifacts', {})
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
    if target == 'accessibility':
        return write_reports(project_dir, document)
    if target not in {'html', 'markdown', 'gutenberg', 'wordpress-xml', 'all'}:
        raise PdfToWebError('Unsupported export format')
    from .publication import require_ready, register_artifacts
    require_ready(document)

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
        projected, assets = _html_with_local_assets(project_dir, document, path.parent)
        path.write_text(html.render_document(projected), encoding="utf-8")
        outputs.append(path)
        outputs.extend(assets)
        if document.get('publication', {}).get('title_in_template'):
            body_path = path.with_name(path.stem + '.body.html')
            body_path.write_text(html.render_document(projected, body_only=True, template_title=True), encoding='utf-8')
            outputs.append(body_path)
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
    if target in {"accessibility", "all"}:
        outputs.extend(write_reports(project_dir, document))
    _write_manifest(project_dir, item, selected_profile, output_slug)
    register_artifacts(project_dir, document, project, outputs)
    return outputs
