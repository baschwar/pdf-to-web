from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .errors import PdfToWebError
from .project import load_project


def render_source_page(project_dir: Path, page: int) -> Path:
    project_dir = project_dir.expanduser().resolve()
    project = load_project(project_dir)
    page_count = int(project.get("source", {}).get("page_count") or 0)
    if page < 1 or (page_count and page > page_count):
        raise ValueError(f"Source page must be between 1 and {page_count or 1}")
    source = project_dir / str(project.get("source", {}).get("path") or "")
    if not source.is_file() or source.suffix.lower() != ".pdf":
        raise PdfToWebError("Source PDF is unavailable")
    cache = project_dir / "review" / "source-pages"
    cache.mkdir(parents=True, exist_ok=True)
    output = cache / f"page-{page:04d}.png"
    if output.is_file():
        return output
    executable = shutil.which("pdftoppm")
    if not executable:
        raise PdfToWebError("Poppler pdftoppm is required to render source-page context")
    prefix = cache / f"page-{page:04d}"
    try:
        completed = subprocess.run(
            [
                executable,
                "-f",
                str(page),
                "-l",
                str(page),
                "-singlefile",
                "-r",
                "120",
                "-png",
                str(source),
                str(prefix),
            ],
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise PdfToWebError(f"Source page {page} rendering timed out") from exc
    if completed.returncode != 0 or not output.is_file():
        detail = completed.stderr.strip() or "pdftoppm did not create a page image"
        raise PdfToWebError(f"Could not render source page {page}: {detail}")
    return output
