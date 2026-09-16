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


def create_project(project_dir: Path, title: str | None = None) -> dict[str, Any]:
    project_dir = project_dir.expanduser().resolve()
    if project_file(project_dir).exists():
        raise PdfToWebError(f"A PDF to Web project already exists at {project_dir}")

    for relative in (
        "source",
        "extraction/raw/images",
        "extraction/assets/images",
        "extraction/normalized",
        "output/markdown",
        "output/html",
        "output/wordpress/blocks",
        "output/wordpress/wxr",
        "output/reports",
    ):
        (project_dir / relative).mkdir(parents=True, exist_ok=True)

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
    save_project(project_dir, data)
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

    destination = project_dir / "source" / source_pdf.name
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
