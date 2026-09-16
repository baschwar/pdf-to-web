from __future__ import annotations

import importlib.metadata
import json
import os
from pathlib import Path

from .assets import extract_pdf_assets
from .doctor import find_supported_java, java_environment
from .errors import PdfToWebError
from .project import load_project, save_project, utc_now


def run_extraction(project_dir: Path, use_struct_tree: bool = False) -> list[Path]:
    project_dir = project_dir.expanduser().resolve()
    data = load_project(project_dir)
    source = project_dir / "source" / "original.pdf"
    if not source.is_file():
        raise PdfToWebError("Import a source PDF before running extraction")
    java, _ = find_supported_java()
    if java is None:
        raise PdfToWebError(
            "Java 11 or newer is required by OpenDataLoader. Run pdf-to-web doctor."
        )
    try:
        import opendataloader_pdf
    except ImportError as exc:
        raise PdfToWebError(
            "OpenDataLoader PDF is not installed. Run: python -m pip install -e ."
        ) from exc

    raw_dir = project_dir / "extraction" / "raw"
    image_dir = raw_dir / "images"
    raw_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)
    before = {path.resolve() for path in raw_dir.rglob("*") if path.is_file()}

    old_env = dict(os.environ)
    try:
        os.environ.clear()
        os.environ.update(java_environment())
        opendataloader_pdf.convert(
            input_path=str(source),
            output_dir=str(raw_dir),
            format="json,markdown",
            image_output="external",
            image_format="png",
            image_dir=str(image_dir),
            reading_order="xycut",
            markdown_page_separator="\n\n<!-- source-page:%page-number% -->\n\n",
            use_struct_tree=use_struct_tree,
            hybrid="off",
            threads="1",
            quiet=True,
        )
    except Exception as exc:
        data["extraction"]["status"] = "failed"
        data["extraction"]["last_error"] = str(exc)
        save_project(project_dir, data)
        raise PdfToWebError(f"OpenDataLoader extraction failed: {exc}") from exc
    finally:
        os.environ.clear()
        os.environ.update(old_env)

    after = {path.resolve() for path in raw_dir.rglob("*") if path.is_file()}
    outputs = sorted(after - before)
    asset_manifest = extract_pdf_assets(
        source, project_dir / "extraction" / "assets" / "images"
    )
    version = importlib.metadata.version("opendataloader-pdf")
    data["extraction"].update(
        {
            "status": "complete",
            "engine_version": version,
            "completed_at": utc_now(),
            "use_struct_tree": use_struct_tree,
            "opendataloader_image_output": "external",
            "asset_engine": "pypdf",
            "asset_count": asset_manifest["asset_reference_count"],
            "asset_error_count": len(asset_manifest["errors"]),
            "raw_outputs": [str(path.relative_to(project_dir)) for path in outputs],
        }
    )
    save_project(project_dir, data)
    run_record = {
        "engine": "opendataloader-pdf",
        "engine_version": version,
        "mode": "local_deterministic",
        "hybrid": "off",
        "opendataloader_image_output": "external",
        "asset_engine": "pypdf",
        "asset_count": asset_manifest["asset_reference_count"],
        "asset_error_count": len(asset_manifest["errors"]),
        "java": str(java),
        "use_struct_tree": use_struct_tree,
        "outputs": [str(path.relative_to(project_dir)) for path in outputs],
        "completed_at": data["extraction"]["completed_at"],
    }
    (project_dir / "extraction" / "extraction-run.json").write_text(
        json.dumps(run_record, indent=2) + "\n", encoding="utf-8"
    )
    return outputs
