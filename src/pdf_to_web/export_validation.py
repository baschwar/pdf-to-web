from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable

from .errors import PdfToWebError
from .export import export_project
from .exporters import gutenberg, html, wxr
from .exporters.common import is_excluded, is_footnote_body, table_cell
from .exporters.wxr import CONTENT_NS
from .normalize import load_normalized
from .project import load_project, slugify
from .validation import validate_gutenberg, validate_semantic_html, validate_wxr
from .wordpress_preview import preview_available, render_gutenberg_preview


def _text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _walk(blocks: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for block in blocks:
        yield block
        yield from _walk(block.get("children", []))


def model_semantics(document: dict[str, Any]) -> dict[str, Any]:
    headings: list[list[Any]] = []
    paragraphs: list[str] = []
    lists: list[list[str]] = []
    links: list[list[str]] = []
    tables: list[list[str]] = []
    images: list[list[str]] = []
    def process(block: dict[str, Any]) -> None:
        if is_excluded(block) or is_footnote_body(block) or block.get("export_as_part_of_image"):
            return
        block_type = block.get("type")
        content = _text(block.get("content"))
        if block_type == "heading":
            headings.append([int(block.get("level", 2)), content])
        elif block_type in {"paragraph", "caption", "callout", "quote", "unknown"} and content:
            paragraphs.append(content)
        elif block_type == "list":
            def collect_list_items(current: dict[str, Any], depth: int) -> None:
                for item in current.get("children", []):
                    if item.get("type") != "list_item" or is_excluded(item):
                        continue
                    lists.append([depth, _text(item.get("content"))])
                    for child in item.get("children", []):
                        if child.get("type") == "list":
                            collect_list_items(child, depth + 1)
                        else:
                            process(child)
            collect_list_items(block, 1)
        elif block_type == "table":
            tables.append([_text(table_cell(cell)[0]) for row in block.get("rows", []) for cell in row])
        elif block_type == "image":
            images.append([_text(block.get("alt")), _text(block.get("caption"))])
        for nested in _walk([block]):
            for run in nested.get("runs", []):
                if isinstance(run, dict) and run.get("type") == "link":
                    links.append([_text(run.get("text")), str(run.get("url", ""))])
    for block in document.get("blocks", []):
        process(block)
    footnotes = [_text(note.get("text")) for note in document.get("footnotes", []) if isinstance(note, dict)]
    return {"title": _text(document.get("metadata", {}).get("title")), "headings": headings, "paragraphs": paragraphs, "lists": lists, "links": links, "tables": tables, "footnotes": footnotes, "images": images}


class _SnapshotParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.snapshot: dict[str, Any] = {"title": "", "headings": [], "paragraphs": [], "lists": [], "links": [], "tables": [], "footnotes": [], "images": []}
        self._capture: list[tuple[str, list[str], dict[str, str]]] = []
        self._list_depth = 0
        self._table: list[str] | None = None
        self._footnotes = False
        self._figures: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "section" and "footnotes" in values.get("class", "").split():
            self._footnotes = True
        if tag in {"title", "p", "li", "th", "td", "figcaption"} or re.fullmatch(r"h[1-6]", tag) or tag == "a":
            self._capture.append((tag, [], values))
        if tag in {"ul", "ol"}:
            self._list_depth += 1
        if tag == "table":
            self._table = []
        if tag == "figure":
            classes = values.get("class", "").split()
            self._figures.append("image" if "wp-block-image" in classes or self._table is None and "wp-block-table" not in classes else "table")
        if tag == "img":
            self.snapshot["images"].append([_text(values.get("alt")), ""])

    def handle_data(self, data: str) -> None:
        for index, (tag, parts, _) in enumerate(self._capture):
            if tag == "li" and any(other_tag in {"li", "th", "td", "p", "figcaption"} or re.fullmatch(r"h[1-6]", other_tag) for other_tag, _, _ in self._capture[index + 1:]):
                continue
            parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._capture and self._capture[-1][0] == tag:
            _, parts, values = self._capture.pop()
            value = _text("".join(parts))
            if tag == "title": self.snapshot["title"] = value
            elif re.fullmatch(r"h[1-6]", tag) and value != "Footnotes": self.snapshot["headings"].append([int(tag[1]), value])
            elif tag == "p" and value: self.snapshot["paragraphs"].append(value)
            elif tag == "li" and self._list_depth:
                self.snapshot["lists"].append([self._list_depth, value])
                if self._footnotes and values.get("id"): self.snapshot["footnotes"].append(value.rstrip(" ↩0123456789"))
            elif tag in {"th", "td"} and self._table is not None: self._table.append(value)
            elif tag == "a" and values.get("href", "").startswith(("http://", "https://", "mailto:")): self.snapshot["links"].append([value, values["href"]])
            elif tag == "figcaption" and self._figures and self._figures[-1] == "image" and self.snapshot["images"]: self.snapshot["images"][-1][1] = value
        if tag in {"ul", "ol"}:
            self._list_depth -= 1
        if tag == "table" and self._table is not None:
            self.snapshot["tables"].append(self._table); self._table = None
        if tag == "section" and self._footnotes: self._footnotes = False
        if tag == "figure" and self._figures: self._figures.pop()


def html_semantics(markup: str) -> dict[str, Any]:
    parser = _SnapshotParser(); parser.feed(markup); parser.close(); return parser.snapshot


def compare_semantics(expected: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for field in ("headings", "paragraphs", "lists", "links", "tables", "footnotes", "images"):
        expected_values = Counter(json.dumps(value, ensure_ascii=False, sort_keys=True) for value in expected[field])
        actual_values = Counter(json.dumps(value, ensure_ascii=False, sort_keys=True) for value in actual[field])
        for serialized, count in (expected_values - actual_values).items(): errors.append(f"Missing {field[:-1]} ({count}): {json.loads(serialized)!r}")
    return {"valid": not errors, "errors": errors}


def _status(validation: dict[str, Any] | None) -> str:
    return "PASS" if validation and validation.get("valid") else "FAIL"


def validate_project_exports(project_dir: Path) -> tuple[Path, Path]:
    project_dir = project_dir.expanduser().resolve(); document = load_normalized(project_dir)
    review_status = str(document.get("review", {}).get("status", "needs_review"))
    report_dir = project_dir / "output" / "reports"; report_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {"schema_version": "pdf-to-web-export-validation-v1", "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "project": str(project_dir), "review_status": review_status, "formats": {}, "warnings": [], "errors": []}
    if review_status == "conversion_blocked":
        html_path = export_project(project_dir, "html")[0]; markup = html_path.read_text(encoding="utf-8")
        report["formats"]["semantic_html"] = validate_semantic_html(document, markup)
        for target in ("gutenberg", "wordpress-xml"):
            try:
                export_project(project_dir, target); report["errors"].append(f"{target} unexpectedly exported conversion-blocked content")
            except PdfToWebError:
                report["formats"][target] = {"generated": False, "blocked_as_expected": True, "valid": True}
    else:
        config = load_project(project_dir).get("export", {}); expected = model_semantics(document)
        report["content_counts"] = {key: len(expected[key]) for key in ("headings", "paragraphs", "lists", "links", "tables", "footnotes", "images")}
        html_markup = html.render_document(document); generic_markup = gutenberg.render_document(document, "generic", config); wsu_markup = gutenberg.render_document(document, "wsuwp", config)
        report["artifacts"] = [str(path) for path in export_project(project_dir, "all", "generic")]
        semantic_validation = validate_semantic_html(document, html_markup); semantic_validation["equivalence"] = compare_semantics(expected, html_semantics(html_markup)); report["formats"]["semantic_html"] = semantic_validation
        for name, markup in (("gutenberg", generic_markup), ("gutenberg_wsu", wsu_markup)):
            validation = validate_gutenberg(document, markup)
            if name == "gutenberg" and "wp:wsuwp/section" in markup: validation["serialization_errors"].append("WSU section wrapper present by default"); validation["valid"] = False
            if name == "gutenberg_wsu" and config.get("wrap_in_section") and "wp:wsuwp/section" not in markup: validation["serialization_errors"].append("Configured WSU section wrapper missing"); validation["valid"] = False
            validation["equivalence"] = compare_semantics(expected, html_semantics(markup)); report["formats"][name] = validation
        item = {"key": slugify(expected["title"]), "title": expected["title"], "slug": slugify(expected["title"]), "post_type": "page", "status": "draft", "content": generic_markup}
        wxr_markup = wxr.render_wxr([item]); wxr_validation = validate_wxr(wxr_markup, [document]); extracted = ET.fromstring(wxr_markup).findtext(f"./channel/item/{{{CONTENT_NS}}}encoded", "")
        wxr_validation["equivalence"] = compare_semantics(expected, html_semantics(extracted)); wxr_validation["standalone_gutenberg_equivalent"] = compare_semantics(html_semantics(generic_markup), html_semantics(extracted)); report["formats"]["wxr"] = wxr_validation
        if preview_available():
            for name, markup in (("gutenberg_preview", generic_markup), ("gutenberg_wsu_preview", wsu_markup)):
                preview = render_gutenberg_preview(markup); equivalence = compare_semantics(expected, html_semantics(preview.html))
                report["formats"][name] = {"generated": True, "valid": not preview.unsupported_blocks and equivalence["valid"], "block_types": list(preview.block_types), "unsupported_blocks": list(preview.unsupported_blocks), "equivalence": equivalence}
        else: report["warnings"].append("WordPress Preview dependencies unavailable; preview validation skipped")
        if review_status == "needs_review": report["warnings"].append("Document is exportable but retains needs-review findings")
    for name, validation in report["formats"].items():
        if not validation.get("valid", False): report["errors"].append(f"{name} validation failed")
        equivalence = validation.get("equivalence")
        if equivalence and not equivalence.get("valid"): report["errors"].append(f"{name} semantic equivalence failed")
    report["result"] = "PASS" if not report["errors"] else "FAIL"
    json_path = report_dir / "export-validation.json"; md_path = report_dir / "export-validation.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["# Export Validation", "", f"Project: `{project_dir}`", f"Review status: `{review_status}`", "", "| Output | Generated | Structural | Equivalence | Result |", "| --- | --- | --- | --- | --- |"]
    for name, validation in report["formats"].items():
        equivalence = validation.get("equivalence"); passed = validation.get("valid") and (not equivalence or equivalence.get("valid")); lines.append(f"| {name.replace('_', ' ').title()} | {'Yes' if validation.get('generated') else 'No'} | {_status(validation)} | {_status(equivalence) if equivalence else 'N/A'} | {'PASS' if passed else 'FAIL'} |")
    lines.extend(["", f"Result: **{report['result']}**", ""])
    if report["warnings"]: lines.extend(["## Warnings", "", *(f"- {message}" for message in report["warnings"]), ""])
    if report["errors"]: lines.extend(["## Errors", "", *(f"- {message}" for message in report["errors"]), ""])
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def validate_export_corpus(project_root: Path, output_dir: Path | None = None) -> tuple[Path, Path]:
    project_root = project_root.expanduser().resolve()
    projects = sorted(path.parent for path in project_root.glob("*/project.json"))
    if not projects:
        raise PdfToWebError(f"No document projects found directly under {project_root}")
    documents: list[dict[str, Any]] = []
    for project in projects:
        json_path, _ = validate_project_exports(project)
        report = json.loads(json_path.read_text(encoding="utf-8"))
        formats = report.get("formats", {})
        documents.append(
            {
                "project": project.name,
                "review_status": report.get("review_status"),
                "semantic_html": _status(formats.get("semantic_html")),
                "gutenberg": _status(formats.get("gutenberg")),
                "gutenberg_preview": _status(formats.get("gutenberg_preview")),
                "wxr": _status(formats.get("wxr")),
                "equivalence": "PASS" if all(
                    not value.get("equivalence") or value["equivalence"].get("valid")
                    for value in formats.values()
                ) else "FAIL",
                "counts": report.get("content_counts", {}),
                "warnings": report.get("warnings", []),
                "errors": report.get("errors", []),
                "result": report.get("result", "FAIL"),
            }
        )
    output_dir = (output_dir or project_root).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    aggregate = {
        "schema_version": "pdf-to-web-export-validation-corpus-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "project_root": str(project_root),
        "documents": documents,
        "result": "PASS" if all(item["result"] == "PASS" for item in documents) else "FAIL",
    }
    json_path = output_dir / "export-validation-corpus.json"
    md_path = output_dir / "export-validation-corpus.md"
    json_path.write_text(json.dumps(aggregate, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["# Export Validation Corpus", "", "| Document project | Semantic | Gutenberg | Preview | WXR | Equivalence | Result |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for item in documents:
        lines.append(f"| {item['project']} | {item['semantic_html']} | {item['gutenberg']} | {item['gutenberg_preview']} | {item['wxr']} | {item['equivalence']} | {item['result']} |")
    lines.extend(["", f"Result: **{aggregate['result']}**", ""])
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path
