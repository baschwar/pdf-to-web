from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic
from typing import Any

from .errors import PdfToWebError
from .export import export_project
from .exporters.wxr import render_wxr
from .extraction import run_extraction
from .normalize import load_normalized, normalize_project
from .project import create_project, import_pdf, slugify
from .validation import validate_gutenberg, validate_semantic_html, validate_wxr


def _flatten(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for block in blocks:
        flattened.append(block)
        flattened.extend(_flatten(block.get("children", [])))
    return flattened


def run_corpus(sample_dir: Path, output_root: Path) -> Path:
    sample_dir = sample_dir.expanduser().resolve()
    pdfs = sorted(sample_dir.glob("*.pdf"))
    if not pdfs:
        raise PdfToWebError(f"No PDF files found in {sample_dir}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = output_root.expanduser().resolve() / timestamp
    run_dir.mkdir(parents=True, exist_ok=False)
    results: list[dict[str, Any]] = []
    multi_items: list[dict[str, Any]] = []

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
                document = load_normalized(project_dir)
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
                html_path = export_project(project_dir, "html")[0]
                html_markup = html_path.read_text(encoding="utf-8")
                result["html"] = validate_semantic_html(document, html_markup)
                status = document.get("review", {}).get("status")
                if status != "conversion_blocked":
                    gutenberg_path = export_project(project_dir, "gutenberg")[0]
                    gutenberg_markup = gutenberg_path.read_text(encoding="utf-8")
                    result["gutenberg"] = validate_gutenberg(document, gutenberg_markup)
                    wxr_path = export_project(project_dir, "wordpress-xml")[0]
                    wxr_markup = wxr_path.read_text(encoding="utf-8")
                    result["wxr"] = validate_wxr(wxr_markup)
                    if mode == "heuristic":
                        title = str(document.get("metadata", {}).get("title") or pdf.stem)
                        multi_items.append(
                            {
                                "key": slugify(pdf.stem),
                                "title": title,
                                "slug": slugify(pdf.stem),
                                "post_type": "page",
                                "status": "draft",
                                "content": gutenberg_markup,
                            }
                        )
                else:
                    reason = "Skipped because normalized readiness is conversion_blocked"
                    result["gutenberg"] = {"generated": False, "reason": reason}
                    result["wxr"] = {"generated": False, "reason": reason}
                normalized_blocks = _flatten(document.get("blocks", []))
                result["normalized_block_counts"] = dict(
                    sorted(
                        {
                            block_type: sum(
                                block.get("type") == block_type for block in normalized_blocks
                            )
                            for block_type in {str(block.get("type")) for block in normalized_blocks}
                        }.items()
                    )
                )
                result["tables"] = sum(block.get("type") == "table" for block in normalized_blocks)
                result["images"] = sum(block.get("type") == "image" for block in normalized_blocks)
                result["complex_visual_flags"] = document.get("review", {}).get(
                    "complex_visuals", []
                )
                result["review_issues"] = document.get("review", {}).get("issues", [])
            except Exception as exc:
                result.update(
                    {
                        "ok": False,
                        "error": str(exc),
                        "status": "conversion_blocked",
                        "review_issues": [
                            {
                                "code": "extraction_failed",
                                "message": str(exc),
                            }
                        ],
                        "html": {"generated": False},
                        "gutenberg": {"generated": False},
                        "wxr": {"generated": False},
                    }
                )
            result["elapsed_seconds"] = round(monotonic() - started, 3)
            results.append(result)

    multi_markup = render_wxr(multi_items) if multi_items else ""
    multi_path = run_dir / "corpus-multi-item.xml"
    if multi_markup:
        multi_path.write_text(multi_markup, encoding="utf-8")
    report = {
        "schema_version": "pdf-to-web-corpus-v2",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sample_directory": str(sample_dir),
        "documents": results,
        "multi_item_wxr": validate_wxr(multi_markup)
        if multi_markup
        else {"generated": False},
    }
    json_path = run_dir / "corpus-results.json"
    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    fieldnames = sorted(
        {
            key
            for result in results
            for key in result
            if not isinstance(result[key], (dict, list))
        }
    )
    with (run_dir / "corpus-results.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
    lines = [
        "# PDF to Web Corpus Summary",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "| PDF | Mode | Readiness | HTML | Gutenberg | WXR | Text recovery | Complex visuals |",
        "| --- | --- | --- | --- | --- | --- | ---: | ---: |",
    ]
    for result in results:
        lines.append(
            "| {filename} | {mode} | {status} | {html} | {gutenberg} | {wxr} | {recovery} | {visuals} |".format(
                filename=result["filename"].replace("|", "\\|"),
                mode=result["mode"],
                status=result.get("status", "failed"),
                html="pass" if result.get("html", {}).get("valid") else "fail",
                gutenberg=(
                    "pass"
                    if result.get("gutenberg", {}).get("valid")
                    else "skipped"
                    if not result.get("gutenberg", {}).get("generated")
                    else "fail"
                ),
                wxr=(
                    "pass"
                    if result.get("wxr", {}).get("valid")
                    else "skipped"
                    if not result.get("wxr", {}).get("generated")
                    else "fail"
                ),
                recovery=(
                    f"{result['text_recovery_ratio']:.1%}"
                    if result.get("text_recovery_ratio") is not None
                    else "n/a"
                ),
                visuals=len(result.get("complex_visual_flags", [])),
            )
        )
    (run_dir / "corpus-summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path
