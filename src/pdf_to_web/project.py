from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .errors import PdfToWebError

PROJECT_SCHEMA = "pdf-to-web-project-v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "document"


def project_file(project_dir: Path) -> Path:
    return project_dir / "project.json"


def validate_project_destination(project_dir: Path) -> Path:
    """Allow loose input files, but never reuse another project's working data."""
    project_dir = project_dir.expanduser().resolve()
    if project_dir.exists() and not project_dir.is_dir():
        raise PdfToWebError(f"Project destination is not a folder: {project_dir}")
    if (project_dir / 'project.json').exists() or (project_dir / 'project.json').is_symlink():
        raise PdfToWebError(f"A PDF to Web project already exists at {project_dir}. Open it instead, or choose a different folder.")
    for name in ('extraction', 'review', 'output'):
        entry = project_dir / name
        if entry.exists() or entry.is_symlink():
            raise PdfToWebError(f"The destination already contains {name}: {project_dir}. Choose a folder without existing project working directories; no files were changed.")
    source = project_dir / 'source'
    if source.exists() or source.is_symlink():
        if source.is_symlink() or not source.is_dir():
            raise PdfToWebError(f"The source entry is not a safe local folder: {source}")
        if any(p.is_symlink() or not p.is_file() or p.suffix.lower() != '.pdf' for p in source.iterdir()):
            raise PdfToWebError(f"The existing source folder must contain only regular PDF files: {source}")
    return project_dir


def create_project(project_dir: Path, title: str | None = None) -> dict[str, Any]:
    project_dir = validate_project_destination(project_dir)
    now = utc_now()
    data: dict[str, Any] = {
        "schema_version": PROJECT_SCHEMA,
        "title": title or project_dir.name,
        "source": {
            "path": None,
            "original_filename": None,
            "classification": None,
            "page_count": None,
        },
        "extraction": {
            "status": "not_started",
            "engine": "opendataloader-pdf",
            "engine_version": None,
            "mode": "local_deterministic",
        },
        "export": {
            "wordpress_profile": "generic",
            "hero": {"enabled": False, "headingTag": "h1"},
            "section_defaults": {},
            "wordpress": {
                "post_type": "page",
                "status": "draft",
                "author": "pdf-to-web",
            },
        },
        "created_at": now,
        "updated_at": now,
    }
    directories = ('source', 'extraction/raw/images', 'extraction/assets/images',
                   'extraction/normalized', 'review/revisions', 'review/source-pages',
                   'output/markdown', 'output/html', 'output/wordpress/blocks',
                   'output/wordpress/wxr', 'output/reports')
    needed = set()
    for relative in directories:
        folder = project_dir / relative
        while not folder.exists():
            if folder.is_symlink():
                raise PdfToWebError(f"Project folder contains a broken link: {folder}")
            needed.add(folder)
            folder = folder.parent
    created = []
    metadata_created = False
    try:
        for folder in sorted(needed, key=lambda p: len(p.parts)):
            folder.mkdir()
            created.append(folder)
        # Exclusive creation prevents a collision from overwriting project data.
        with project_file(project_dir).open('x', encoding='utf-8') as output:
            metadata_created = True
            output.write(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    except Exception:
        if metadata_created:
            try:
                project_file(project_dir).unlink(missing_ok=True)
            except OSError:
                pass
        for folder in reversed(created):
            try:
                folder.rmdir()  # Remove only newly created, still-empty folders.
            except OSError:
                pass
        raise
    return data


def load_project(project_dir: Path) -> dict[str, Any]:
    path = project_file(project_dir.expanduser().resolve())
    if not path.is_file():
        raise PdfToWebError(f"No PDF to Web project found at {path.parent}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PdfToWebError(f"Could not read project file: {exc}") from exc
    if data.get("schema_version") != PROJECT_SCHEMA:
        raise PdfToWebError(
            f"Unsupported project schema: {data.get('schema_version')!r}"
        )
    return data


def save_project(project_dir: Path, data: dict[str, Any]) -> None:
    data["updated_at"] = utc_now()
    path = project_file(project_dir.expanduser().resolve())
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def import_pdf(project_dir: Path, source_pdf: Path) -> dict[str, Any]:
    from .pdf_analysis import analyze_pdf

    project_dir = project_dir.expanduser().resolve()
    data = load_project(project_dir)
    source_pdf = source_pdf.expanduser().resolve()
    if not source_pdf.is_file() or source_pdf.suffix.lower() != ".pdf":
        raise PdfToWebError(f"Source is not a readable PDF file: {source_pdf}")

    source_dir = project_dir / 'source'
    if source_dir.is_symlink() or source_dir.resolve() != source_dir or not source_dir.is_dir():
        raise PdfToWebError(f"Project source folder is not a confined local directory: {source_dir}")
    destination = source_dir / source_pdf.name
    if destination.is_symlink():
        raise PdfToWebError(f"Project source filename is a link: {destination}")
    if destination.exists() and destination.resolve() != source_pdf:
        counter = 2
        while True:
            candidate = destination.with_name(
                f"{destination.stem}-{counter}{destination.suffix}"
            )
            if not candidate.exists() and not candidate.is_symlink():
                destination = candidate
                break
            counter += 1
    if destination.resolve() != source_pdf:
        shutil.copy2(source_pdf, destination)
    analysis = analyze_pdf(destination)
    data["source"] = {
        "path": str(destination.relative_to(project_dir)),
        "original_filename": source_pdf.name,
        **analysis,
    }
    data["title"] = analysis.get("title") or data["title"]
    data["extraction"]["status"] = "not_started"
    save_project(project_dir, data)
    return analysis
