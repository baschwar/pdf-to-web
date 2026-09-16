from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic
from typing import Any

from .errors import PdfToWebError
from .extraction import run_extraction
from .normalize import normalize_project
from .project import create_project, import_pdf, slugify


def run_corpus(sample_dir: Path, output_root: Path) -> Path:
    sample_dir = sample_dir.expanduser().resolve()
    pdfs = sorted(sample_dir.glob("*.pdf"))
    if not pdfs:
        raise PdfToWebError(f"No PDF files found in {sample_dir}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = output_root.expanduser().resolve() / timestamp
    run_dir.mkdir(parents=True, exist_ok=False)
    results: list[dict[str, Any]] = []

    for pdf in pdfs:
        for mode, use_struct_tree in (("heuristic", False), ("structure-tree", True)):
            project_dir = run_dir / f"{slugify(pdf.stem)}--{mode}"
            started = monotonic()
            result: dict[str, Any] = {
                "filename": pdf.name,
                "mode": mode,
                "project": str(project_dir.relative_to(run_dir)),
            }
            try:
                create_project(project_dir, pdf.stem)
                source = import_pdf(project_dir, pdf)
                run_extraction(project_dir, use_struct_tree=use_struct_tree)
                normalize_project(project_dir)
                summary = json.loads(
                    (project_dir / "output" / "reports" / "extraction-summary.json").read_text(
                        encoding="utf-8"
                    )
                )
                assets = json.loads(
                    (project_dir / "extraction" / "assets" / "manifest.json").read_text(
                        encoding="utf-8"
                    )
                )
                result.update(
                    {
                        "ok": True,
                        "source_classification": source["classification"],
                        "asset_reference_count": assets["asset_reference_count"],
                        "unique_asset_count": assets["unique_file_count"],
                        "asset_error_count": len(assets["errors"]),
                        **summary,
                    }
                )
            except Exception as exc:
                result.update({"ok": False, "error": str(exc)})
            result["elapsed_seconds"] = round(monotonic() - started, 3)
            results.append(result)

    json_path = run_dir / "corpus-results.json"
    json_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    fieldnames = sorted({key for result in results for key in result if not isinstance(result[key], dict)})
    with (run_dir / "corpus-results.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
    return json_path
