from __future__ import annotations

import html
import json
import os
import secrets
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from . import __version__
from .errors import PdfToWebError
from .export import export_project
from .exporters import gutenberg as gutenberg_exporter
from .exporters import html as html_exporter
from .extraction import run_extraction
from .normalize import extraction_summary, normalize_project
from .project import create_project, import_pdf, load_project, save_project, slugify
from .recent_projects import (
    RecentProject,
    default_recent_projects_path,
    load_recent_projects,
    remember_project,
    remove_recent_project,
)
from .review_state import (
    BLOCK_TYPES,
    ensure_review_document,
    merge_with_next,
    move_block,
    review_progress,
    split_block,
    table_summary,
    undo_last,
    update_block,
    update_complex_visual,
)
from .source_pages import render_source_page, source_page_size
from .wordpress_preview import render_gutenberg_preview

try:
    from fastapi import Request
except ImportError:  # pragma: no cover - CLI remains available without app dependencies.
    Request = Any  # type: ignore

APP_NAME = "PDF to Web"
SESSION_COOKIE = "pdf_to_web_session"
CSRF_COOKIE = "pdf_to_web_csrf"
CSRF_HEADER = "x-csrf-token"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost"}
LOOPBACK_CLIENTS = {"127.0.0.1", "::1", "localhost", "testclient"}


@dataclass
class WebAppConfig:
    project: Path | None = None
    recent_projects: tuple[Path, ...] = ()
    projects_root: Path = field(default_factory=lambda: Path.home() / "Documents" / "PDF to Web Projects")
    recent_store: Path = field(default_factory=default_recent_projects_path)
    host: str = "127.0.0.1"
    port: int = 8765
    bootstrap_token: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    session_token: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    csrf_token: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    bootstrap_used: bool = False


@dataclass(frozen=True)
class ProjectSelection:
    token: str
    path: Path

    def public(self) -> dict[str, str]:
        return {"token": self.token, "name": self.path.name}


def parse_host_header(value: str) -> tuple[str, int | None]:
    if not value:
        return "", None
    if value.startswith("[") and "]" in value:
        host, _, remainder = value[1:].partition("]")
        return host, int(remainder[1:]) if remainder.startswith(":") else None
    if ":" in value:
        host, port = value.rsplit(":", 1)
        try:
            return host, int(port)
        except ValueError:
            return host, None
    return value, None


def is_allowed_host(value: str, port: int) -> bool:
    host, supplied_port = parse_host_header(value)
    return host in LOOPBACK_HOSTS and supplied_port == port


def is_allowed_origin(value: str | None, port: int) -> bool:
    if not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme == "http" and parsed.hostname in LOOPBACK_HOSTS and parsed.port == port


def browser_url(config: WebAppConfig) -> str:
    return f"http://{config.host}:{config.port}/bootstrap/{config.bootstrap_token}"


def open_browser_when_ready(url: str, host: str, port: int, *, timeout: float = 10.0) -> None:
    """Open the bootstrap URL after the local server begins accepting connections."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.25):
                webbrowser.open(url)
                return
        except OSError:
            time.sleep(0.05)


def choose_project_folder() -> Path:
    if sys.platform == "darwin":
        script = 'POSIX path of (choose folder with prompt "Select a PDF to Web project")'
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, timeout=300, check=False
        )
        if result.returncode != 0:
            raise ValueError("No project folder was selected.")
        return Path(result.stdout.strip()).expanduser().resolve()
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Native folder selection is unavailable on this system") from exc
    root = tk.Tk()
    root.withdraw()
    try:
        selected = filedialog.askdirectory(title="Select a PDF to Web project")
    finally:
        root.destroy()
    if not selected:
        raise ValueError("No project folder was selected.")
    return Path(selected).expanduser().resolve()


def choose_pdf_file() -> Path:
    if sys.platform == "darwin":
        script = 'POSIX path of (choose file with prompt "Select a PDF to convert" of type {"com.adobe.pdf"})'
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, timeout=300, check=False
        )
        if result.returncode != 0:
            raise ValueError("No PDF was selected.")
        return Path(result.stdout.strip()).expanduser().resolve()
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Native file selection is unavailable on this system") from exc
    root = tk.Tk()
    root.withdraw()
    try:
        selected = filedialog.askopenfilename(
            title="Select a PDF to convert", filetypes=(("PDF files", "*.pdf"),)
        )
    finally:
        root.destroy()
    if not selected:
        raise ValueError("No PDF was selected.")
    return Path(selected).expanduser().resolve()


def static_path(name: str) -> Path:
    root = (Path(__file__).parent / "static").resolve()
    path = (root / name).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError("Static path is outside the application package") from exc
    return path


def safe_project_file(project_dir: Path, relative: str) -> Path:
    if not relative or Path(relative).is_absolute():
        raise ValueError("Project file path must be relative")
    root = project_dir.resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError("Project file path escapes the active project") from exc
    return path


def _walk(blocks: list[dict[str, Any]]):
    for block in blocks:
        yield block
        yield from _walk(block.get("children", []))


def _list_text(block: dict[str, Any]) -> str:
    return "\n".join(str(child.get("content", "")) for child in block.get("children", []))


def document_model(project_dir: Path) -> dict[str, Any]:
    project = load_project(project_dir)
    document = ensure_review_document(project_dir)
    summary = extraction_summary(document)
    blocks = list(_walk(document.get("blocks", [])))
    counts = Counter(str(block.get("type", "unknown")) for block in blocks)
    return {
        "project": project,
        "document": document,
        "summary": summary,
        "counts": dict(counts),
        "progress": review_progress(document),
    }


def _status_label(value: str) -> str:
    return value.replace("_", " ").title()


def _nav(active: str, selected: bool) -> str:
    items = [("Projects", "/"), ("Document", "/document"), ("Structure", "/structure"), ("Preview", "/preview"), ("Export", "/export")]
    links = []
    for label, href in items:
        disabled = not selected and href != "/"
        current = ' aria-current="page"' if active == label.lower() else ""
        links.append(
            f'<li><a href="{href}"{current}>{label}</a></li>' if not disabled else f'<li><span aria-disabled="true">{label}</span></li>'
        )
    return f'<nav aria-label="Primary"><ul><li><strong>{APP_NAME}</strong></li></ul><ul>{"".join(links)}</ul></nav>'


def _page(title: str, active: str, body: str, *, selected: bool = True) -> str:
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} | {APP_NAME}</title><link rel="icon" href="data:,"><link rel="stylesheet" href="/static/pico.min.css"><link rel="stylesheet" href="/static/app.css"></head>
<body><header class="app-header"><div class="container">{_nav(active, selected)}</div></header>
<main class="container">{body}</main><footer class="app-footer"><div class="container">{APP_NAME} v{html.escape(__version__)}</div></footer><div id="app-status" class="visually-hidden" role="status" aria-live="polite"></div>
<script src="/static/app.js"></script></body></html>'''


def _status_banner(status: str, issues: list[dict[str, Any]]) -> str:
    messages = "".join(f"<li>{html.escape(str(issue.get('message', issue.get('code', 'Issue'))))}</li>" for issue in issues)
    return f'''<section class="status-banner status-{html.escape(status)}" aria-labelledby="document-status-heading">
<h2 id="document-status-heading">{html.escape(_status_label(status))}</h2>
<p>{len(issues)} unresolved diagnostic issue{'s' if len(issues) != 1 else ''}.</p>{f'<ul>{messages}</ul>' if messages else ''}</section>'''


def _projects_page(
    config: WebAppConfig,
    selections: list[tuple[ProjectSelection, RecentProject]],
    selected: Path | None,
) -> str:
    recent = "".join(
        f'''<li><div><strong>{html.escape(record.title)}</strong>
<code>{html.escape(record.path)}</code><small>Last opened <time datetime="{html.escape(record.last_opened, quote=True)}">{html.escape(record.last_opened.replace("T", " ").replace("+00:00", " UTC"))}</time></small></div>
<div class="recent-actions"><button type="button" class="open-project" data-project-token="{selection.token}">Open</button>
<button type="button" class="secondary remove-project" data-project-token="{selection.token}" aria-label="Remove {html.escape(record.title, quote=True)} from recent projects">Remove</button></div></li>'''
        for selection, record in selections
    ) or "<li>No recent projects are available.</li>"
    current = f"<p>Current project: <strong>{html.escape(selected.name)}</strong></p>" if selected else "<p>No project is open.</p>"
    body = f'''<h1>Projects</h1>{current}
<div class="project-actions"><section aria-labelledby="new-heading"><h2 id="new-heading">New project</h2>
<p>Create a project and choose its source PDF. Conversion runs locally.</p>
<form id="new-project-form"><label>Project name<input name="title" required maxlength="120" placeholder="Annual report"></label>
<button type="submit">Choose PDF and create project</button></form></section>
<section aria-labelledby="open-heading"><h2 id="open-heading">Open project</h2>
<p>Open an existing PDF to Web project folder.</p><button id="choose-project" type="button" class="secondary">Choose project folder</button></section></div>
<section aria-labelledby="recent-heading"><h2 id="recent-heading">Recent projects</h2><ul class="project-list">{recent}</ul>
<p id="project-message" role="status" aria-live="polite"></p></section>'''
    return _page("Projects", "projects", body, selected=selected is not None)


def _document_page(model: dict[str, Any]) -> str:
    project, document = model["project"], model["document"]
    source, extraction = project.get("source", {}), project.get("extraction", {})
    status = document.get("review", {}).get("status", "needs_review")
    counts, progress = model["counts"], model["progress"]
    mode = "Structure tree" if extraction.get("use_struct_tree") else "Heuristic"
    body = f'''<h1>Document</h1>{_status_banner(status, document.get("review", {}).get("issues", []))}
<dl class="metadata-grid">
<div><dt>Source</dt><dd>{html.escape(str(source.get("original_filename") or "Not imported"))}</dd></div>
<div><dt>Project source</dt><dd><code>{html.escape(str(source.get("path") or "Not available"))}</code></dd></div>
<div><dt>Pages</dt><dd>{source.get("page_count") or "Unknown"}</dd></div>
<div><dt>Classification</dt><dd>{html.escape(str(source.get("classification") or "Unknown"))}</dd></div>
<div><dt>Extraction mode</dt><dd>{mode}</dd></div><div><dt>Extraction</dt><dd>{_status_label(str(extraction.get("status", "unknown")))}</dd></div>
<div><dt>Normalized</dt><dd>Available</dd></div><div><dt>Review status</dt><dd>{_status_label(status)}</dd></div>
</dl>
<section aria-labelledby="content-summary"><h2 id="content-summary">Content summary</h2>
<div class="metrics"><span><strong>{progress['total']}</strong> blocks</span><span><strong>{counts.get('heading',0)}</strong> headings</span><span><strong>{counts.get('paragraph',0)}</strong> paragraphs</span><span><strong>{counts.get('list',0)}</strong> lists</span><span><strong>{counts.get('table',0)}</strong> tables</span><span><strong>{counts.get('image',0)}</strong> images</span><span><strong>{counts.get('unknown',0)}</strong> unknown</span></div></section>
<section aria-labelledby="review-progress"><h2 id="review-progress">Review progress</h2><p>Reviewed {progress['reviewed']} / {progress['total']} blocks</p>
<progress value="{progress['reviewed']}" max="{max(1,progress['total'])}">{progress['reviewed']} of {progress['total']}</progress>
<p>Approved {progress['approved']} · Needs review {progress['needs_review']} · Unreviewed {progress['unreviewed']} · Excluded {progress['excluded']}</p></section>
<p><a href="/structure" role="button">Review structure</a></p>'''
    return _page("Document", "document", body)


def _block_card(block: dict[str, Any], index: int, *, total: int, can_edit: bool = True) -> str:
    block_id = html.escape(str(block.get("id", "")), quote=True)
    block_type = str(block.get("type", "unknown"))
    provenance = block.get("provenance", {})
    page = provenance.get("source_page") or "Unknown"
    review_status = str(block.get("review", {}).get("status", "unreviewed"))
    content = _list_text(block) if block_type == "list" else str(block.get("content", ""))
    options = "".join(f'<option value="{kind}"{" selected" if kind == block_type else ""}>{kind.replace("_", " ").title()}</option>' for kind in sorted(BLOCK_TYPES))
    states = "".join(f'<option value="{state}"{" selected" if state == review_status else ""}>{_status_label(state)}</option>' for state in ("unreviewed", "approved", "needs_review", "excluded"))
    level = int(block.get("level", 2))
    levels = "".join(f'<option value="{value}"{" selected" if value == level else ""}>H{value}</option>' for value in range(1, 7))
    issue_text = " ".join(str(issue.get("message", "")) for issue in block.get("review", {}).get("issues", []))
    source_type = str(provenance.get("source_type") or "Unknown")
    bbox = provenance.get("bounding_box")
    bbox_value = html.escape(json.dumps(bbox), quote=True) if isinstance(bbox, list) and len(bbox) == 4 else ""
    table = ""
    if block_type == "table":
        stats = table_summary(block)
        rows = "".join("<tr>" + "".join(f"<td>{html.escape(str(cell.get('content','') if isinstance(cell,dict) else cell))}</td>" for cell in row) + "</tr>" for row in block.get("rows", []))
        table = f'<p>{stats["rows"]} rows, {stats["columns"]} columns, {stats["spans"]} spanning cells</p><div class="table-scroll"><table><tbody>{rows}</tbody></table></div>'
    editable = block_type in BLOCK_TYPES
    editor = f'''<form class="block-form" data-block-id="{block_id}"><div class="form-grid">
<label>Block type<select name="type">{options}</select></label>
<label class="heading-level"{"" if block_type == "heading" else " hidden"}>Heading level<select name="level"{"" if block_type == "heading" else " disabled"}>{levels}</select></label>
<label>Review state<select name="review_status">{states}</select></label></div>
<label>Text<textarea name="content" rows="3">{html.escape(content)}</textarea></label>
<button type="submit" aria-label="Save block {index}">Save block</button></form>''' if editable and can_edit else ""
    include_label = "Include" if review_status == "excluded" else "Exclude"
    actions = f'''<footer class="block-actions" aria-label="Actions for block {index}">
<button type="button" class="secondary block-action" data-action="start" data-block-id="{block_id}" aria-label="Move block {index} to start"{" disabled" if index == 1 else ""}>Move to start</button>
<button type="button" class="secondary block-action" data-action="up" data-block-id="{block_id}" aria-label="Move block {index} up"{" disabled" if index == 1 else ""}>Move up</button>
<button type="button" class="secondary block-action" data-action="down" data-block-id="{block_id}" aria-label="Move block {index} down"{" disabled" if index == total else ""}>Move down</button>
<button type="button" class="secondary block-action" data-action="end" data-block-id="{block_id}" aria-label="Move block {index} to end"{" disabled" if index == total else ""}>Move to end</button>
<button type="button" class="secondary block-action" data-action="merge" data-block-id="{block_id}" aria-label="Merge block {index} with next block">Merge next</button>
<button type="button" class="secondary block-action" data-action="split" data-block-id="{block_id}" aria-label="Split block {index}">Split</button>
<button type="button" class="secondary block-action" data-action="toggle-excluded" data-block-id="{block_id}" data-current-status="{review_status}" aria-label="{include_label} block {index}">{include_label}</button>
<button type="button" class="secondary block-action" data-action="approve" data-block-id="{block_id}" aria-label="Approve block {index}">Approve</button>
<button type="button" class="secondary block-action" data-action="flag" data-block-id="{block_id}" aria-label="Mark block {index} as needs review">Needs review</button></footer>''' if can_edit else '<footer><strong>Inspection only while conversion is blocked.</strong></footer>'
    return f'''<article class="block-card status-{html.escape(review_status)}" id="block-{block_id}" tabindex="-1" data-page="{page}" data-bbox="{bbox_value}" data-block-index="{index}" data-source-type="{html.escape(source_type, quote=True)}" aria-labelledby="block-{block_id}-heading">
<header><div><span class="order">{index}</span> <h3 id="block-{block_id}-heading">{html.escape(block_type.replace("_", " ").title())}{f' H{level}' if block_type == 'heading' else ''}</h3></div><span>Page {page} · {_status_label(review_status)}</span></header>
<p class="source-provenance">OpenDataLoader source: {html.escape(source_type)}{f' · Source region available' if bbox_value else ''}</p>{f'<p class="block-issue">{html.escape(issue_text)}</p>' if issue_text else ''}{table}{editor}
{actions}</article>'''


def _complex_visual_card(visual: dict[str, Any], *, can_edit: bool) -> str:
    visual_id = html.escape(str(visual.get("id", "")), quote=True)
    ratio = visual.get("text_recovery_ratio")
    recovery = f"{ratio:.1%}" if ratio is not None else "Unknown"
    assets = visual.get("asset_references", [])
    asset_list = "".join(f"<li><code>{html.escape(str(asset))}</code></li>" for asset in assets)
    asset_image = f'<img src="/review-asset/{html.escape(str(assets[0]), quote=True)}" alt="Extracted visual asset from source page {visual.get("source_page")}">' if assets else ""
    status = str(visual.get("status", "needs_text_equivalent"))
    form = f'''<form class="complex-visual-form" data-visual-id="{visual_id}"><div class="form-grid">
<label>Classification<input name="type" value="{html.escape(str(visual.get('type','infographic')), quote=True)}"></label>
<label>Review state<select name="status"><option value="needs_text_equivalent"{" selected" if status == "needs_text_equivalent" else ""}>Keep flagged</option><option value="reclassified"{" selected" if status == "reclassified" else ""}>Reclassified</option><option value="excluded"{" selected" if status == "excluded" else ""}>Excluded</option></select></label></div>
<label>Recovered text<textarea name="recovered_text" rows="8">{html.escape(str(visual.get('recovered_text','')))}</textarea></label><button type="submit">Save complex visual review</button></form>''' if can_edit else "<p><strong>Inspection only while conversion is blocked.</strong></p>"
    return f'''<article class="complex-visual" id="visual-{visual_id}"><h3>Complex visual - review required</h3><p>Source page {visual.get('source_page')} · Text recovery {recovery} · {_status_label(status)}</p>{asset_image}<details><summary>Extracted assets and recovered text</summary><ul>{asset_list or '<li>No separate assets were retained.</li>'}</ul><p>{html.escape(str(visual.get('recovered_text','')))}</p></details>{form}</article>'''


def _structure_page(model: dict[str, Any]) -> str:
    document = model["document"]
    status = document.get("review", {}).get("status", "needs_review")
    can_edit = status != "conversion_blocked"
    progress = model["progress"]
    blocks = document.get("blocks", [])
    page_count = int(model["project"].get("source", {}).get("page_count") or 1)
    cards = "".join(_block_card(block, index, total=len(blocks), can_edit=can_edit) for index, block in enumerate(blocks, 1))
    visuals = "".join(_complex_visual_card(visual, can_edit=can_edit) for visual in document.get("review", {}).get("complex_visuals", []))
    body = f'''<h1>Structure</h1>{_status_banner(status, document.get("review", {}).get("issues", [])) if not can_edit else ''}<div class="review-toolbar"><p><strong>{_status_label(status)}</strong> · Reviewed {progress['reviewed']} / {progress['total']}</p>{'<button id="undo-action" type="button" class="secondary">Undo last action</button>' if can_edit else ''}</div>
{f'<section class="complex-warning" aria-labelledby="complex-heading"><h2 id="complex-heading">Complex visuals</h2>{visuals}</section>' if visuals else ''}
<div class="structure-layout"><section class="source-pane" aria-labelledby="source-heading" data-page-count="{page_count}"><h2 id="source-heading">Source page</h2><form id="source-page-controls" class="source-page-controls"><button id="source-page-previous" type="button" class="secondary" disabled aria-label="Previous source page">Previous</button><label>Page <input id="source-page-number" type="number" min="1" max="{page_count}" value="1" inputmode="numeric" aria-describedby="source-page-total"></label><span id="source-page-total">of {page_count}</span><button id="source-page-next" type="button" class="secondary"{(' disabled' if page_count <= 1 else '')} aria-label="Next source page">Next</button></form><p id="source-page-label" aria-live="polite">Select a block to view and outline its source region.</p><div class="source-image-stage"><img id="source-image" src="/source-page/1.png" alt="Rendered source PDF page 1"><span id="source-highlight" hidden aria-hidden="true"></span></div><p><a id="open-source-page" href="/source.pdf#page=1" target="_blank" rel="noopener">Open source PDF page 1</a></p></section>
<section class="blocks-pane" aria-labelledby="blocks-heading"><div class="reading-order-header"><h2 id="blocks-heading">Reading order</h2><div class="block-navigation" role="group" aria-label="Selected block navigation"><button id="previous-block" type="button" class="secondary" disabled>Previous block</button><span id="selected-block-position" aria-live="polite">No block selected</span><button id="next-block" type="button" class="secondary"{(' disabled' if not blocks else '')}>Next block</button></div></div><p>Use the movement controls on each block to correct reading order. Changes save immediately.</p>{cards or '<p>No normalized blocks are available.</p>'}</section></div>'''
    return _page("Structure", "structure", body)


def _preview_page(project: dict[str, Any]) -> str:
    selected_profile = str(project.get("export", {}).get("wordpress_profile", "generic"))
    profile_options = "".join(
        f'<option value="{value}"{" selected" if value == selected_profile else ""}>{label}</option>'
        for value, label in (("generic", "Generic Gutenberg"), ("wsuwp", "WSUWP"))
    )
    body = f'''<h1>Preview</h1>
<div class="preview-toolbar">
<div class="segmented-control" role="group" aria-label="Preview mode"><button type="button" class="preview-mode" data-mode="semantic" aria-pressed="true">Semantic HTML</button><button type="button" class="secondary preview-mode" data-mode="wordpress" aria-pressed="false">WordPress Preview</button></div>
<label class="preview-profile" hidden>WordPress profile<select id="preview-profile">{profile_options}</select></label>
<div class="preview-controls" role="group" aria-label="Preview width"><button type="button" class="preview-width" data-width="desktop">Desktop</button><button type="button" class="secondary preview-width" data-width="mobile">Narrow</button></div></div>
<p id="preview-description">Semantic Preview shows the reviewed document independently of WordPress.</p>
<div class="preview-shell" id="preview-shell"><iframe title="Semantic HTML preview" sandbox="allow-same-origin" src="/api/preview/html"></iframe></div>'''
    return _page("Preview", "preview", body)


def _export_page(model: dict[str, Any]) -> str:
    document = model["document"]
    status = str(document.get("review", {}).get("status", "needs_review"))
    progress = model["progress"]
    unknown = model["counts"].get("unknown", 0)
    complex_count = len(document.get("review", {}).get("complex_visuals", []))
    blocked = status == "conversion_blocked"
    body = f'''<h1>Export</h1>{_status_banner(status, document.get("review", {}).get("issues", []))}
<section aria-labelledby="readiness-heading"><h2 id="readiness-heading">Export readiness</h2><ul><li>{progress['needs_review']} blocks need review</li><li>{progress['unreviewed']} blocks are unreviewed</li><li>{unknown} unknown blocks remain</li><li>{complex_count} complex visual warnings remain</li></ul></section>
<form id="export-form" data-conversion-blocked="{str(blocked).lower()}"><div class="form-grid"><label>Format<select name="target"><option value="html">Semantic HTML</option><option value="gutenberg">Gutenberg</option><option value="wordpress-xml">WXR/XML</option></select></label>
<label>WordPress profile<select name="profile"><option value="generic">Generic Gutenberg</option><option value="wsuwp">WSUWP</option></select></label>
<label>Content type<select name="post_type"><option value="page">Page</option><option value="post">Post</option></select></label></div><p>WordPress exports are created as Drafts.</p>
<button type="submit">Export reviewed document</button><p class="blocked-export-note"{"" if blocked else " hidden"}>Conversion-blocked projects may export diagnostic HTML only.</p></form><div id="export-result" role="status" aria-live="polite"></div>'''
    return _page("Export", "export", body)


def create_app(config: WebAppConfig):
    try:
        from fastapi import Cookie, FastAPI, Header, HTTPException
        from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
        from fastapi.staticfiles import StaticFiles
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install PDF to Web application dependencies first") from exc

    app = FastAPI(title=APP_NAME)
    active_project = config.project.expanduser().resolve() if config.project else None
    selections: dict[str, ProjectSelection] = {}
    recent = load_recent_projects(config.recent_store)

    def issue(path: Path) -> ProjectSelection:
        load_project(path)
        selection = ProjectSelection(secrets.token_urlsafe(32), path.resolve())
        selections[selection.token] = selection
        return selection

    def remember(path: Path) -> None:
        nonlocal recent
        recent = remember_project(config.recent_store, path, recent)

    for path in reversed(config.recent_projects):
        if (path.expanduser().resolve() / "project.json").is_file():
            remember(path)
    if active_project:
        remember(active_project)

    def require_session(session: str | None) -> None:
        if session != config.session_token:
            raise HTTPException(status_code=401, detail="Session required")

    def require_change(request: Request, session: str | None, csrf: str | None) -> None:
        require_session(session)
        if not is_allowed_origin(request.headers.get("origin"), config.port):
            raise HTTPException(status_code=403, detail="Origin rejected")
        if csrf != config.csrf_token:
            raise HTTPException(status_code=403, detail="CSRF token rejected")

    def current() -> Path:
        if active_project is None:
            raise HTTPException(status_code=400, detail="Choose a project first")
        load_project(active_project)
        return active_project

    def require_editable_document() -> None:
        if ensure_review_document(current()).get("review", {}).get("status") == "conversion_blocked":
            raise HTTPException(status_code=409, detail="Document is inspection-only while conversion is blocked")

    def error_response(exc: Exception, status: int = 400):
        return JSONResponse({"status": "error", "error": str(exc)}, status_code=status)

    @app.middleware("http")
    async def loopback_only(request: Request, call_next):
        if not is_allowed_host(request.headers.get("host", ""), config.port):
            return JSONResponse({"detail": "Host header rejected"}, status_code=400)
        if request.client and request.client.host not in LOOPBACK_CLIENTS:
            return JSONResponse({"detail": "Client address rejected"}, status_code=403)
        return await call_next(request)

    app.mount("/static", StaticFiles(directory=static_path(".").resolve()), name="static")

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "app": APP_NAME}

    @app.get("/bootstrap/{token}")
    async def bootstrap(token: str):
        if config.bootstrap_used or token != config.bootstrap_token:
            raise HTTPException(status_code=403, detail="Bootstrap token rejected")
        config.bootstrap_used = True
        response = RedirectResponse("/", status_code=303)
        response.set_cookie(SESSION_COOKIE, config.session_token, httponly=True, samesite="strict", path="/")
        response.set_cookie(CSRF_COOKIE, config.csrf_token, httponly=False, samesite="strict", path="/")
        return response

    @app.get("/", response_class=HTMLResponse)
    async def projects(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        project_selections = [(issue(record.project_path), record) for record in recent]
        return _projects_page(config, project_selections, active_project)

    @app.post("/api/picker/project")
    async def pick_project(request: Request, session: str | None = Cookie(default=None, alias=SESSION_COOKIE), csrf: str | None = Header(default=None, alias=CSRF_HEADER)):
        require_change(request, session, csrf)
        try:
            selection = issue(choose_project_folder())
            return {"status": "ok", "selection": selection.public()}
        except Exception as exc:
            return error_response(exc)

    @app.post("/api/projects/open")
    async def open_project(request: Request, session: str | None = Cookie(default=None, alias=SESSION_COOKIE), csrf: str | None = Header(default=None, alias=CSRF_HEADER)):
        nonlocal active_project
        require_change(request, session, csrf)
        try:
            data = await request.json()
            selection = selections.get(str(data.get("selection_token", "")))
            if selection is None:
                raise ValueError("Project selection token is invalid or expired")
            load_project(selection.path)
            active_project = selection.path
            remember(active_project)
            ensure_review_document(active_project)
            return {"status": "ok", "project": {"name": active_project.name}}
        except Exception as exc:
            return error_response(exc)

    @app.post("/api/projects/remove-recent")
    async def remove_recent(request: Request, session: str | None = Cookie(default=None, alias=SESSION_COOKIE), csrf: str | None = Header(default=None, alias=CSRF_HEADER)):
        nonlocal recent
        require_change(request, session, csrf)
        try:
            data = await request.json()
            selection = selections.get(str(data.get("selection_token", "")))
            if selection is None:
                raise ValueError("Project selection token is invalid or expired")
            recent = remove_recent_project(config.recent_store, selection.path, recent)
            return {"status": "ok"}
        except Exception as exc:
            return error_response(exc)

    @app.post("/api/projects/create")
    async def new_project(request: Request, session: str | None = Cookie(default=None, alias=SESSION_COOKIE), csrf: str | None = Header(default=None, alias=CSRF_HEADER)):
        nonlocal active_project
        require_change(request, session, csrf)
        project_dir: Path | None = None
        try:
            data = await request.json()
            title = str(data.get("title", "")).strip()
            if not title:
                raise ValueError("Enter a project name.")
            source_pdf = choose_pdf_file()
            project_dir = config.projects_root.expanduser().resolve() / slugify(title)
            create_project(project_dir, title)
            import_pdf(project_dir, source_pdf)
            run_extraction(project_dir, False)
            normalize_project(project_dir)
            active_project = project_dir
            remember(project_dir)
            return {"status": "ok", "project": {"name": project_dir.name}}
        except Exception as exc:
            if project_dir is not None and (project_dir / "project.json").is_file():
                remember(project_dir)
            return error_response(exc)

    @app.get("/document", response_class=HTMLResponse)
    async def document_page(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        return _document_page(document_model(current()))

    @app.get("/structure", response_class=HTMLResponse)
    async def structure_page(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        return _structure_page(document_model(current()))

    @app.get("/preview", response_class=HTMLResponse)
    async def preview_page(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        return _preview_page(load_project(current()))

    @app.get("/export", response_class=HTMLResponse)
    async def export_page(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        return _export_page(document_model(current()))

    @app.get("/source.pdf")
    async def source_pdf(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        root = current()
        source_data = load_project(root).get("source", {})
        source = source_data.get("path")
        path = safe_project_file(root, str(source or ""))
        if not path.is_file() or path.suffix.lower() != ".pdf":
            raise HTTPException(status_code=404, detail="Source PDF is unavailable")
        return FileResponse(
            path,
            media_type="application/pdf",
            filename=str(source_data.get("original_filename") or path.name),
            content_disposition_type="inline",
        )

    @app.get("/source-page/{page}.png")
    async def source_page(page: int, session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        try:
            return FileResponse(render_source_page(current(), page), media_type="image/png")
        except (PdfToWebError, ValueError) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/source-page/{page}")
    async def source_page_metadata(page: int, session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        try:
            width, height = source_page_size(current(), page)
            return {"page": page, "width": width, "height": height}
        except (PdfToWebError, ValueError, IndexError) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/preview/images/{name}")
    async def preview_image(name: str, session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        if Path(name).name != name or Path(name).suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
            raise HTTPException(status_code=404, detail="Preview asset is unavailable")
        path = safe_project_file(current(), f"extraction/raw/images/{name}")
        if not path.is_file():
            raise HTTPException(status_code=404, detail="Preview asset is unavailable")
        return FileResponse(path)

    @app.get("/review-asset/{name}")
    async def review_asset(name: str, session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        if Path(name).name != name or Path(name).suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
            raise HTTPException(status_code=404, detail="Review asset is unavailable")
        path = safe_project_file(current(), f"extraction/assets/images/{name}")
        if not path.is_file():
            raise HTTPException(status_code=404, detail="Review asset is unavailable")
        return FileResponse(path)

    @app.get("/favicon.ico")
    async def favicon():
        return Response(status_code=204)

    @app.get("/api/document")
    async def api_document(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        return document_model(current())

    @app.get("/api/preview/html", response_class=HTMLResponse)
    async def preview_html(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        return HTMLResponse(
            html_exporter.render_document(ensure_review_document(current())),
            headers={
                "Content-Security-Policy": "default-src 'none'; img-src 'self' data: http: https:; style-src 'self' 'unsafe-inline'; frame-ancestors 'self'"
            },
        )

    @app.get("/api/preview/wordpress", response_class=HTMLResponse)
    async def preview_wordpress(
        profile: str = "generic",
        session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    ):
        require_session(session)
        if profile not in {"generic", "wsuwp"}:
            raise HTTPException(status_code=400, detail="Unsupported WordPress preview profile")
        root = current()
        document = ensure_review_document(root)
        status = document.get("review", {}).get("status")
        title = html.escape(str(document.get("metadata", {}).get("title", "WordPress Preview")))
        diagnostics = ""
        try:
            if status == "conversion_blocked":
                raise PdfToWebError(
                    "WordPress Preview is unavailable while Gutenberg export is blocked"
                )
            config_data = load_project(root).get("export", {})
            markup = gutenberg_exporter.render_document(document, profile, config_data)
            preview = render_gutenberg_preview(markup)
            if preview.unsupported_blocks:
                names = "".join(
                    f"<li><code>{html.escape(name)}</code></li>"
                    for name in preview.unsupported_blocks
                )
                diagnostics = (
                    '<aside class="preview-diagnostics"><strong>Unsupported preview blocks</strong>'
                    f"<ul>{names}</ul></aside>"
                )
            content = preview.html
        except PdfToWebError as exc:
            content = (
                '<div class="preview-error" role="alert"><strong>WordPress Preview unavailable</strong>'
                f"<p>{html.escape(str(exc))}</p></div>"
            )
        page = (
            "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>{title} - WordPress Preview</title>"
            '<link rel="stylesheet" href="/static/wordpress-preview.css"></head>'
            f"<body><main>{diagnostics}{content}</main></body></html>"
        )
        return HTMLResponse(
            page,
            headers={
                "Content-Security-Policy": "default-src 'none'; img-src 'self' data: http: https:; style-src 'self'; frame-ancestors 'self'",
                "X-Content-Type-Options": "nosniff",
            },
        )

    @app.get("/api/preview/MEDIA_URL_REQUIRED")
    async def preview_missing_media(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        return Response(
            content=(
                '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="180" '
                'role="img" aria-label="Media URL required">'
                '<rect width="100%" height="100%" fill="#f1f3f5"/>'
                '<text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle" '
                'font-family="system-ui, sans-serif" font-size="18" fill="#343a40">'
                'Media URL required</text></svg>'
            ),
            media_type="image/svg+xml",
        )

    @app.post("/api/blocks/{block_id}")
    async def edit_block(block_id: str, request: Request, session: str | None = Cookie(default=None, alias=SESSION_COOKIE), csrf: str | None = Header(default=None, alias=CSRF_HEADER)):
        require_change(request, session, csrf)
        require_editable_document()
        try:
            update_block(current(), block_id, await request.json())
            return {"status": "ok", "progress": review_progress(ensure_review_document(current()))}
        except Exception as exc:
            return error_response(exc)

    @app.post("/api/blocks/{block_id}/{action}")
    async def block_action(block_id: str, action: str, request: Request, session: str | None = Cookie(default=None, alias=SESSION_COOKIE), csrf: str | None = Header(default=None, alias=CSRF_HEADER)):
        require_change(request, session, csrf)
        require_editable_document()
        try:
            data = await request.json()
            if action in {"start", "up", "down", "end"}:
                move_block(current(), block_id, action)
            elif action == "merge":
                merge_with_next(current(), block_id)
            elif action == "split":
                split_block(current(), block_id, int(data.get("offset", 0)))
            elif action in {"approve", "flag", "exclude", "include"}:
                state = {"approve": "approved", "flag": "needs_review", "exclude": "excluded", "include": "unreviewed"}[action]
                update_block(current(), block_id, {"review_status": state})
            else:
                raise ValueError("Unsupported block action")
            return {"status": "ok"}
        except Exception as exc:
            return error_response(exc)

    @app.post("/api/review/undo")
    async def undo(request: Request, session: str | None = Cookie(default=None, alias=SESSION_COOKIE), csrf: str | None = Header(default=None, alias=CSRF_HEADER)):
        require_change(request, session, csrf)
        require_editable_document()
        try:
            undo_last(current())
            return {"status": "ok"}
        except Exception as exc:
            return error_response(exc)

    @app.post("/api/complex-visuals/{visual_id}")
    async def edit_complex_visual(visual_id: str, request: Request, session: str | None = Cookie(default=None, alias=SESSION_COOKIE), csrf: str | None = Header(default=None, alias=CSRF_HEADER)):
        require_change(request, session, csrf)
        if ensure_review_document(current()).get("review", {}).get("status") == "conversion_blocked":
            return error_response(ValueError("Complex visual editing is unavailable while conversion is blocked"), 409)
        try:
            update_complex_visual(current(), visual_id, await request.json())
            return {"status": "ok"}
        except Exception as exc:
            return error_response(exc)

    @app.post("/api/export")
    async def run_export(request: Request, session: str | None = Cookie(default=None, alias=SESSION_COOKIE), csrf: str | None = Header(default=None, alias=CSRF_HEADER)):
        require_change(request, session, csrf)
        try:
            data = await request.json()
            target = str(data.get("target", ""))
            profile = str(data.get("profile", "generic"))
            post_type = str(data.get("post_type", "page"))
            if target not in {"html", "gutenberg", "wordpress-xml"}:
                raise ValueError("Unsupported export format")
            if profile not in {"generic", "wsuwp"} or post_type not in {"page", "post"}:
                raise ValueError("Unsupported WordPress export setting")
            project = load_project(current())
            project.setdefault("export", {})["wordpress_profile"] = profile
            wordpress = project["export"].setdefault("wordpress", {})
            wordpress.update({"post_type": post_type, "status": "draft"})
            save_project(current(), project)
            paths = export_project(current(), target, profile)
            return {
                "status": "ok",
                "files": [str(path.relative_to(current())) for path in paths],
                "project_root": str(current()),
                "review": ensure_review_document(current()).get("review", {}),
            }
        except Exception as exc:
            return error_response(exc)

    app.state.project_selections = selections
    app.state.get_active_project = lambda: active_project
    return app


def run_server(project: Path | None, host: str, port: int, *, open_browser: bool = True) -> None:
    if host not in {"127.0.0.1", "localhost"}:
        raise PdfToWebError("The review application may only bind to loopback")
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover
        raise PdfToWebError("Install FastAPI and Uvicorn to run the review application") from exc
    config = WebAppConfig(project=project, host=host, port=port, recent_projects=(project,) if project else ())
    url = browser_url(config)
    print(f"Open PDF to Web: {url}", flush=True)
    if open_browser:
        threading.Thread(
            target=open_browser_when_ready,
            args=(url, host, port),
            daemon=True,
            name="pdf-to-web-browser-launcher",
        ).start()
    uvicorn.run(create_app(config), host=host, port=port, log_level="info")
