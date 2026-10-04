from __future__ import annotations

import html
import asyncio
import copy
import hashlib
import json
import math
import re
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
from urllib.parse import quote, urlparse

from . import __version__
from .accessibility import assess_document, write_reports, visual_readiness
from .image_review import descriptions_for, review_token, description_owner
from . import output_pages as op
from . import image_drafts as drafts
from . import image_draft_ui
from .app_lifecycle import LifecycleMiddleware, OwnedServerLifecycle, QuitUnavailable
from .output_page_export import export_pages, contents_html
from .review_state import update_output_pages
from .errors import PdfToWebError
from .export import export_project, _write_media_manifest, media_prefix, validate_media_prefix, _wordpress_media_values
from .exporters import gutenberg as gutenberg_exporter
from .exporters import html as html_exporter
from .exporters.common import has_unstructured_list_text, is_excluded, is_footnote_body, list_render_items
from .extraction import run_extraction
from .normalize import extraction_summary, normalize_project
from .media_mapping import apply_media_mapping, apply_wordpress_media_export
from .project import create_project, import_pdf, load_project, save_project, slugify, utc_now, validate_project_destination
from .recent_projects import (
    RecentProject,
    default_recent_projects_path,
    load_recent_projects,
    remember_project,
    remove_recent_project,
)
from .review_state import (
    BLOCK_TYPES,
    block_review_reason,
    ensure_review_document,
    merge_with_next,
    merge_next_reason,
    move_block,
    review_progress,
    split_block,
    table_summary,
    undo_last,
    update_block,
    update_accessibility_decision,
    update_complex_visual,
    save_review_document,
    review_path,
)
from .source_pages import render_source_page, source_page_size
from .project_outputs import output_locations, preserve_previous_outputs, open_output_folder
from .wordpress_preview import render_gutenberg_preview

try:
    from fastapi import Request
except ImportError:  # pragma: no cover - CLI remains available without app dependencies.
    Request = Any  # type: ignore

APP_NAME = "PDF to Web"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SESSION_COOKIE = "pdf_to_web_session"
CSRF_COOKIE = "pdf_to_web_csrf"
CSRF_HEADER = "x-csrf-token"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost"}
LOOPBACK_CLIENTS = {"127.0.0.1", "::1", "localhost", "testclient"}


def _commit_hash() -> str:
    override = os.environ.get("PDF_TO_WEB_COMMIT")
    if override:
        return override[:12]
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            check=True,
            text=True,
            timeout=2,
        )
        return result.stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _display_project_path(path: Path, projects_root: Path) -> str:
    canonical = path.expanduser().resolve(strict=False)
    for root in (REPOSITORY_ROOT, projects_root.expanduser().resolve(strict=False)):
        try:
            relative = canonical.relative_to(root)
        except ValueError:
            continue
        suffix = f"/{relative.as_posix()}" if relative.parts else ""
        return f"/{root.name}{suffix}"
    return f"/{canonical.parent.name}/{canonical.name}"


def _document_with_local_preview_media(document: dict[str, Any], *, semantic: bool = False) -> dict[str, Any]:
    preview = copy.deepcopy(document)
    stack = list(preview.get("blocks", []))
    while stack:
        block = stack.pop()
        stack.extend(block.get("children", []))
        if block.get("type") != "image" or (block.get("wordpress_url") and not semantic):
            continue
        source = Path(str(block.get("src") or ""))
        if source.name == str(source) or source.parts[:1] == ("images",) or str(source).startswith(("extraction/raw/", "extraction/assets/images/")):
            block["wordpress_url"] = f"/api/image-drafts/asset?path={quote(str(source))}" if str(source).startswith("extraction/") else f"/api/preview/images/{quote(source.name)}"
            if semantic:
                block['src'] = block['wordpress_url']
    return preview


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


def choose_project_folder(*, destination: bool = False) -> Path:
    prompt = "Choose the folder for the new project’s files" if destination else "Select a PDF to Web project"
    if sys.platform == "darwin":
        script = f'POSIX path of (choose folder with prompt "{prompt}")'
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
        selected = filedialog.askdirectory(title=prompt, mustexist=True)
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
    return "\n".join(str(child.get("content", "")) for child in list_render_items(block))


def _list_has_nested_content(block: dict[str, Any]) -> bool:
    return any(child.get("children") for child in block.get("children", []))


def _list_structure_preview(block: dict[str, Any]) -> str:
    tag = "ol" if block.get("ordered") else "ul"
    attrs = ""
    marker_types = {"lower-alpha": "a", "upper-alpha": "A", "lower-roman": "i", "upper-roman": "I"}
    if block.get("ordered") and block.get("marker_style") in marker_types:
        attrs += f' type="{marker_types[block["marker_style"]]}"'
    if block.get("ordered") and int(block.get("start", 1)) != 1:
        attrs += f' start="{int(block["start"])}"'
    items = []
    for child in list_render_items(block):
        nested = "".join(
            _list_structure_preview(grandchild)
            if grandchild.get("type") == "list"
            else f'<p>{html.escape(str(grandchild.get("content", "")))}</p>'
            for grandchild in child.get("children", [])
        )
        items.append(f'<li>{html.escape(str(child.get("content", "")))}{nested}</li>')
    return f'<{tag}{attrs}>{"".join(items)}</{tag}>'


def document_model(project_dir: Path) -> dict[str, Any]:
    project = load_project(project_dir)
    document = ensure_review_document(project_dir)
    summary = extraction_summary(document)
    blocks = list(_walk(document.get("blocks", [])))
    counts = Counter(str(block.get("type", "unknown")) for block in blocks)
    source = project_dir / str(project.get("source", {}).get("path") or "")
    try:
        source_stat = source.stat()
        source_identity = f"{project_dir.resolve()}\0{source.resolve()}\0{source_stat.st_mtime_ns}\0{source_stat.st_size}"
    except OSError:
        source_identity = str(project_dir.resolve())
    source_preview_key = hashlib.sha256(source_identity.encode("utf-8")).hexdigest()[:16]
    return {
        "project": project,
        "document": document,
        "summary": summary,
        "counts": dict(counts),
        "progress": review_progress(document),
        "can_undo": any((project_dir / "review" / "revisions").glob("*.json")),
        "accessibility": assess_document(document),
        "source_preview_key": source_preview_key,
        "project_dir": project_dir,
    }


def _status_label(value: str) -> str:
    return value.replace("_", " ").title()


def _nav(active: str, selected: bool) -> str:
    items = [("Projects", "/"), ("Document", "/document"), ("Structure", "/structure"), ("Accessibility", "/accessibility"), ("Arrange Pages", "/output-pages"), ("Preview", "/preview"), ("Export", "/export"), ("Help", "/help")]
    links = []
    for label, href in items:
        disabled = not selected and href not in {"/", "/help"}
        current = ' aria-current="page"' if active == ('output-pages' if href == '/output-pages' else label.lower().replace(' ', '-')) else ''
        links.append(
            f'<li><a href="{href}"{current}>{label}</a></li>' if not disabled else f'<li><span aria-disabled="true">{label}</span></li>'
        )
    return f'<nav aria-label="Primary"><ul><li><strong>{APP_NAME}</strong></li></ul><ul>{"".join(links)}<li><button type="button" id="quit-open" class="neutral-action" aria-haspopup="dialog">Quit PDF to Web</button></li></ul></nav>'


def _page(title: str, active: str, body: str, *, selected: bool = True, project=None, project_path=None) -> str:
    # Contextual help must keep unsaved authoring fields open in their tab.
    body = re.sub(r'<a href="(/help#[^"]+)">(.*?)</a>',
                  r'<a href="\1" target="_blank" rel="noopener">\2<span class="visually-hidden"> (opens a new tab)</span></a>', body)
    name = str((project or {}).get('source', {}).get('original_filename') or (project or {}).get('title') or '')
    document_reference = f'<p class="current-document">Working on: <strong>{html.escape(name)}</strong></p>' if name else ''
    if project_path is not None:
        document_reference += f'<p class="project-location">Project folder: <code>{html.escape(str(project_path))}</code></p>'
    tab_title = ' | '.join(filter(None, [title, name, APP_NAME]))
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(tab_title)}</title><link rel="icon" href="data:,"><link rel="stylesheet" href="/static/pico.min.css"><link rel="stylesheet" href="/static/app.css"></head>
<body data-project-root="{html.escape(str(project_path or ''), quote=True)}"><header class="app-header" id="app-top" tabindex="-1"><div class="container">{_nav(active, selected)}</div></header>
<main class="container">{document_reference}{body}</main><footer class="app-footer"><div class="container">{APP_NAME} v{html.escape(__version__)} · commit {html.escape(_commit_hash())}<p><a href="/help#acceptance">Accessibility review limits</a></p></div></footer><div id="app-status" class="visually-hidden" role="status" aria-live="polite"></div>
<button type="button" id="back-to-top" class="back-to-top" hidden><span aria-hidden="true">&uarr;</span> Back to top</button>
<dialog id="quit-dialog" aria-labelledby="quit-heading" aria-describedby="quit-warning"><article><h2 id="quit-heading">Quit PDF to Web?</h2><p id="quit-warning">This stops the app for every open tab. Save unsaved edits in all tabs first. Project files already saved are kept.</p><p id="quit-edits"></p><p id="quit-status" role="status" aria-live="polite"></p><div id="quit-actions" class="button-row"><button type="button" id="quit-cancel" class="neutral-action">Keep working</button><button type="button" id="quit-confirm" class="review-exclude" disabled>Quit PDF to Web</button></div><p id="quit-launcher-note">Its dedicated launcher process will end. A Terminal window or shared command prompt may stay open according to its settings; you can close this browser tab afterward.</p></article></dialog>
{'<script src="/static/accessibility-scan.js"></script>' if active == 'accessibility' else ''}<script src="/static/app.js"></script></body></html>'''


def _status_banner(status: str, issues: list[dict[str, Any]], document=None) -> str:
    if document is not None:
        report = assess_document(document)
        issues = [i for i in report['items'] if i['category'] == 'diagnostics' and i['status'] == 'unresolved']
        if status != 'conversion_blocked':
            status = 'review_ready' if report['summary']['unresolved'] == 0 else 'needs_review'
    messages = "".join(f"<li>{html.escape(str(issue.get('message', issue.get('code', 'Issue'))))}</li>" for issue in issues)
    return f'''<section class="status-banner status-{html.escape(status)}" aria-labelledby="document-status-heading">
<h2 id="document-status-heading">{html.escape(_status_label(status))}</h2>
<p>{len(issues)} unresolved diagnostic issue{'s' if len(issues) != 1 else ''}.</p>{f'<ul>{messages}</ul>' if messages else ''}</section>'''


def _help_page(*, selected=False, project=None, project_path=None):
    body = '''<h1>Help</h1><p>Workflow explanations and review limits.</p>
<nav class="help-topics" aria-label="Help topics"><ul>
<li><a href="#project-files">Project files and setup</a></li><li><a href="#review-counts">Review counts</a></li>
<li><a href="#image-descriptions">Image descriptions</a></li><li><a href="#bulk-review">Bulk review</a></li>
<li><a href="#html-checks">Automated HTML checks</a></li><li><a href="#wordpress-media">WordPress media and approvals</a></li>
<li><a href="#wordpress-preview">WordPress preview</a></li><li><a href="#title-export">Title export</a></li>
<li><a href="#quit-app">Quit the app</a></li><li><a href="#acceptance">Accessibility and platform acceptance</a></li></ul></nav>
<section id="project-files"><h2>Project files and setup</h2><p>Folder I choose uses the exact selected folder. Default location creates a named folder under Documents/PDF to Web Projects. Existing loose files are preserved. The input PDF may be elsewhere; its source copy, extraction, review history, source-page cache and exports stay in the project folder.</p><p>Source-page rendering needs Poppler separately from Python dependencies. On a Mac with Homebrew already set up, install with <code>brew install poppler</code>. If pdftoppm is missing, finish setup and relaunch the app. Recreating the project is unnecessary. Extracted images and cached source pages are different; cached pages can display without Poppler. A Pillow extraction error is a separate dependency issue.</p></section>
<section id="review-counts"><h2>Review counts</h2><p>Block and image approvals measure reviewed content. Each image with linked descriptions counts once; included descriptions are shown for context. Document accessibility findings cover judgments such as link purpose and extraction diagnostics. Automated HTML checks inspect rendered markup. These scopes overlap and their counts are not added together.</p><p>Resolved extraction notes retain the original diagnostic for reference. They do not add pending tasks. A diagnostic may point to a block already counted in content review.</p></section>
<section id="image-descriptions"><h2>Image descriptions</h2><p>Review linked descriptions with the image alt and caption in Reading order. Save and approve covers every displayed included description. No separate description needed records a Not applicable decision; exclusion keeps the content recoverable. Genuine authored edits require review again.</p><p>Provide a long description or adjacent text equivalent. Adjacent text is written text, not a reference to another block. Decorative images use empty alt text and need no separate description. Extraction flags pages with at least five retained images or assets as possible complex visuals; the reviewer decides whether a longer description is needed. Standalone descriptions keep their own editor.</p><p>The preparation tools precede Reading order. They open initially when images need review or drafts exist. Your summary choice remembers open or closed per project in this browser. Direct drafting links reveal them for that visit without replacing your preference. Defaults never move focus or generate drafts.</p><h3>Manual drafting with Codex or ChatGPT</h3><ol><li>In Structure, choose Manual exchange as the drafting method. In Images to export, choose All pending images or Selected images, then Export image-draft ZIP. Pending uses saved review needs and skips generating, ready or rejected requests; Selected uses your checkboxes and an empty scope cannot export. Open the output folder and attach the saved ZIP directly. Optional browser copy makes an extra copy wherever your browser saves downloads.</li><li>Choose Copy instructions for Codex/ChatGPT. Attach that ZIP in your chosen tool, paste the instructions and run the request. Copying preserves unsaved fields; if it fails, select the displayed instructions and copy them manually.</li><li>The package contains INSTRUCTIONS.txt, request.json, response-template.json, review-sheet.csv and the image files. The included response-template.json is blank. Ask your drafting tool to write usable alt text for every image and return the completed JSON as a downloadable file; uploading the unchanged template imports nothing. Preserve document_id, block_id, asset_hash, context_hash and request_id exactly. The CSV is a review companion, not an import format.</li><li>Open Import manual responses, choose the returned JSON and Validate responses. Inspect the findings, then choose Import drafts into image fields. Review each image before approving it. Existing authored text is preserved; Apply deliberately replaces it. Optional captions and long descriptions may be null. Imported drafts never approve content automatically.</li></ol></section>
<section id="bulk-review"><h2>Bulk review</h2><p>Pending only is the default. Completed and All records expose earlier decisions. Classification and visibility filters define the exact selectable scope; changing either clears selections. Block approvals, description reviews and accessibility decisions have different permitted states. Image rows include their linked descriptions.</p><p>Saved-record counts can overlap image tasks and are not added to content progress. Confirmation applies only the displayed selection. One Undo restores the whole batch; a stale project or incomplete description prevents partial approval.</p></section>
<section id="html-checks"><h2>Automated HTML checks</h2><p>Local axe-core checks use WCAG 2.2 A/AA rules on the saved semantic HTML. The scan is bound to the displayed saved revision. Passed counts rules with passing elements, not WCAG success criteria. Not applicable means no matching content was found. A rule can have different results for different elements, so rule counts are not a total of distinct WCAG criteria. Zero detected issues do not resolve human document judgments. Test the final WordPress page separately because the production theme and plugins can change markup and accessibility.</p></section>
<section id="wordpress-media"><h2>WordPress media and approvals</h2><p>Media XML matching uses exact filenames. WordPress-renamed or duplicate filenames need manual CSV mapping. Use manual CSV mapping is visible beside XML matching. Unmatched or ambiguous results and XML errors reveal the tools and offer direct links. Prepare images first, download the current mapping CSV, edit wordpress_url and optionally wordpress_attachment_id, and keep block_id and asset_filename unchanged. Verify the correct image for each URL before importing. Existing validation and Undo apply; opening these tools does not change mappings or approval. Pasting Gutenberg requires mapped image URLs; importing content WXR is optional and does not upload or map images.</p><p>Adding only WordPress URLs, attachment IDs or routing metadata preserves content approval. Re-uploaded unchanged images can have new attachment IDs: select the explicit same-reviewed-images refresh option to update IDs only for a unique exact filename and the same saved URL. Missing, duplicate or different-URL entries keep existing mappings. XML cannot verify image bytes. Changed images need fresh alt and description review; mapping never approves pending content. Genuine source, alt, caption and description edits require review. Matching invalidates earlier publication files; generate fresh content afterward.</p><p>For approvals lost to an earlier media-only change, Preview recorded approvals shows the exact eligible images and original approval dates. Confirm restore restores recorded decisions only when retained history proves unchanged authored content and descriptions through every intervening revision. Newer approvals remain intact. Missing, ambiguous or changed history requires manual review. Restoration supports one Undo and keeps current media mappings. Before confirmation, the Undo notice explains that Undo returns images to pending review and consumes a saved snapshot. Another restoration may be unavailable because the retained history has a gap; manually review the pending images before export in that case.</p></section>
<section id="wordpress-preview"><h2>WordPress preview</h2><p>WordPress Preview is an approximate content and structure preview using local minimal CSS. Selecting WSUWP changes the exported block profile; it does not fetch the production WSU theme CSS. The actual theme and plugin versions determine the final design. Semantic Preview shows the reviewed content independently of WordPress.</p></section>
<section id="title-export"><h2>Title export</h2><p>When My WordPress template supplies the page title (H1) is checked, Gutenberg and WXR omit the title heading. Semantic HTML also provides a body file for pasting into a template; its standalone file retains one H1. Copy page title fills the separate WordPress title field and does not change review decisions.</p></section>
<section id="quit-app"><h2>Quit the app</h2><p>Quit PDF to Web opens a confirmation on every screen. Keep working or Escape preserves edits. The dialog checks this tab for unsaved fields and choices; save your work in all open tabs before confirming. Quit without saving explicitly leaves those edits unsaved. Already saved project files and review decisions are kept.</p><p>Processing, saves, downloads and queued/running generation must finish before Quit is available. The server also refuses a busy request even if another tab starts work after confirmation opens. Only the server owned by pdf-to-web serve is stopped. An externally managed server must be stopped through its own launcher. Failure feedback allows retry. After an accepted Quit and repeated unavailable local health checks, confirmation changes to PDF to Web has stopped, with a safe-to-close message and no active Quit/Keep working controls. Offline, HTTP-error or timeout checks cannot establish success and keep uncertainty/retry feedback.</p><p>The dedicated launcher process ends with the server. Terminal and shared command-prompt windows may remain according to their settings. Unrelated sessions and processes are not terminated. Actual Windows and host-window closing checks remain pending.</p></section>
<section id="acceptance"><h2>Accessibility and platform acceptance</h2><p>Review and automated checks do not certify WCAG conformance. Human VoiceOver review means a person listens and interacts with representative workflows and output using macOS VoiceOver, checking announcements, reading order, controls, focus and recovery.</p><p>Production-authoritative WSU WordPress/plugin imports, human VoiceOver review and actual Windows hardware verification remain separate acceptance steps. Local automated tests and browser checks establish local implementation readiness.</p></section>'''
    return _page('Help', 'help', body, selected=selected, project=project, project_path=project_path)


def _projects_page(
    config: WebAppConfig,
    selections: list[tuple[ProjectSelection, RecentProject]],
    selected: Path | None,
    warning: str | None = None,
) -> str:
    recent = "".join(
        f'''<li><div><strong>{html.escape(record.title)}</strong>
<code>{html.escape(str(record.project_path))}</code><small>Last opened <time datetime="{html.escape(record.last_opened, quote=True)}">{html.escape(record.last_opened.replace("T", " ").replace("+00:00", " UTC"))}</time></small></div>
<div class="recent-actions"><button type="button" class="open-project" data-project-token="{selection.token}">Open</button>
<button type="button" class="secondary remove-project" data-project-token="{selection.token}" aria-label="Remove {html.escape(record.title, quote=True)} from recent projects">Remove</button></div></li>'''
        for selection, record in selections
    ) or "<li>No recent projects are available.</li>"
    ready = selected is not None and ((selected / 'review/current.json').is_file() or (selected / 'extraction/normalized/document.json').is_file())
    current = "" if selected else "<p>No project is open.</p>"
    if selected and not ready:
        project = load_project(selected)
        detail = str(project.get('extraction', {}).get('last_error') or 'Extraction and normalization have not finished.')
        current = f'<section role="status"><h2>Conversion incomplete</h2><p>{html.escape(detail)}</p><p>Files are retained in the project folder shown above. Correct the reported problem, import the PDF with the CLI if its source copy is missing, then complete extraction and normalization before opening the review workflow. Do not create another project in this folder.</p></section>'
    notice = f'<p class="status-banner" role="status">{html.escape(warning)}</p>' if warning else ''
    body = f'''<h1>Projects</h1>{notice}{current}
<div class="project-actions"><section aria-labelledby="new-heading"><h2 id="new-heading">New project</h2>
<p>Create a project and choose its source PDF. Conversion runs locally.</p>
<form id="new-project-form" data-default-root="{html.escape(str(config.projects_root.expanduser().resolve()), quote=True)}"><label>Project name<input name="title" required maxlength="120" placeholder="Annual report"></label>
<fieldset><legend>Project folder</legend>
<label><input type="radio" name="destination_mode" value="default" checked> Default location</label>
<label><input type="radio" name="destination_mode" value="chosen"> Folder I choose</label>
<button id="choose-project-destination" type="button" class="neutral-action">Choose destination folder</button>
<input type="hidden" name="destination_token" value="">
<p id="project-destination-path" role="status" aria-live="polite" class="project-location">Default project folder: <code>{html.escape(str(config.projects_root.expanduser().resolve() / 'document'))}</code></p>
<small>Choose where project files will be saved. The original PDF is copied and preserved. <a href="/help#project-files">Project folder help</a>.</small></fieldset>
<button type="submit">Choose PDF and create project</button></form></section>
<section aria-labelledby="open-heading"><h2 id="open-heading">Open project</h2>
<p>Open an existing PDF to Web project folder.</p><button id="choose-project" type="button" class="secondary">Choose project folder</button></section></div>
<p id="project-message" role="status" aria-live="polite"></p>
<section aria-labelledby="recent-heading"><h2 id="recent-heading">Recent projects</h2><ul class="project-list">{recent}</ul></section>'''
    return _page("Projects", "projects", body, selected=ready, project=load_project(selected) if selected else None, project_path=selected)


def _document_page(model: dict[str, Any]) -> str:
    project, document = model["project"], model["document"]
    source, extraction = project.get("source", {}), project.get("extraction", {})
    status = document.get("review", {}).get("status", "needs_review")
    counts, progress = model["counts"], model["progress"]
    mode = "Structure tree" if extraction.get("use_struct_tree") else "Heuristic"
    completion = _structure_completion(document, structure_path="/structure")
    structure_complete = 'id="structure-review-complete"' in completion
    review_label = "Conversion blocked" if status == "conversion_blocked" else "Structure reviewed" if structure_complete else "Review in progress"
    body = f'''<h1>Document</h1>
<section class="document-review-progress" aria-labelledby="review-progress"><h2 id="review-progress">Review progress</h2>{f'<p><strong>{review_label}</strong></p>' if not structure_complete else ''}
{_review_task_summary(document, progress)}
{_document_diagnostics(model)}
<progress aria-label="Resolved block decisions" value="{progress['approved'] + progress['excluded']}" max="{max(1,progress['total'])}">{progress['approved'] + progress['excluded']} of {progress['total']}</progress>
<p class="button-row workflow-next"><a href="/structure" role="button" class="{'secondary' if structure_complete else 'review-approve'}">Review structure</a></p></section>
{completion}
<dl class="metadata-grid">
<div><dt>Source</dt><dd>{html.escape(str(source.get("original_filename") or "Not imported"))}</dd></div>
<div><dt>Project source</dt><dd><code>{html.escape(str(source.get("path") or "Not available"))}</code></dd></div>
<div><dt>Pages</dt><dd>{source.get("page_count") or "Unknown"}</dd></div>
<div><dt>Classification</dt><dd>{html.escape(str(source.get("classification") or "Unknown"))}</dd></div>
<div><dt>Extraction mode</dt><dd>{mode}</dd></div><div><dt>Extraction</dt><dd>{_status_label(str(extraction.get("status", "unknown")))}</dd></div>
<div><dt>Normalized</dt><dd>Available</dd></div>
</dl>
<section aria-labelledby="content-summary"><h2 id="content-summary">Content summary</h2>
<div class="metrics">{''.join(f'<span><strong>{count}</strong> {name}{"s" if count != 1 else ""}</span>' for name, count in [('block', progress['total']), ('heading', counts.get('heading', 0)), ('paragraph', counts.get('paragraph', 0)), ('list', counts.get('list', 0)), ('table', counts.get('table', 0)), ('image', counts.get('image', 0))])}<span><strong>{counts.get('unknown',0)}</strong> unknown</span></div></section>'''
    return _page("Document", "document", body, project=model["project"], project_path=model["project_dir"])


def _valid_source_box(box):
    return (isinstance(box, list) and len(box) == 4
            and all(isinstance(value, (int, float)) and math.isfinite(value) for value in box)
            and box[0] != box[2] and box[1] != box[3])


def _source_text_descendants(block):
    for child in block.get('children', []):
        if is_excluded(child) or is_footnote_body(child) or child.get('export_as_part_of_image'):
            continue
        if child.get('type') in {'list_item', 'paragraph', 'heading', 'quote', 'caption', 'callout', 'unknown'} or has_unstructured_list_text(child):
            yield child
        yield from _source_text_descendants(child)


def _source_region_coverage(block):
    page = block.get('provenance', {}).get('source_page')
    missing = sum(not _valid_source_box(child.get('provenance', {}).get('bounding_box'))
                  for child in _source_text_descendants(block)
                  if child.get('provenance', {}).get('source_page') in (None, page))
    return f'{missing} nested text element(s) have no recorded source region. Unoutlined text may still be present in this block.' if missing else ''


def _source_regions(block: dict[str, Any]) -> list[list[float]]:
    provenance = block.get("provenance", {})
    page = provenance.get("source_page")
    if block.get("type") == "list":
        regions = [
            child.get("provenance", {}).get("bounding_box")
            for child in _source_text_descendants(block)
            if child.get("provenance", {}).get("source_page") == page
            and _valid_source_box(child.get("provenance", {}).get("bounding_box"))
        ]
        if regions:
            return [list(box) for box in dict.fromkeys(tuple(box) for box in regions)]
    bbox = provenance.get("bounding_box")
    return [bbox] if _valid_source_box(bbox) else []


def _block_card(block: dict[str, Any], index: int, *, total: int, can_edit: bool = True, draft_controls: str = "", long_description: str = "", following=None, document=None) -> str:
    from .publication import effective_block_status
    block_id = html.escape(str(block.get("id", "")), quote=True)
    block_type = str(block.get("type", "unknown"))
    provenance = block.get("provenance", {})
    page = provenance.get("source_page") or "Unknown"
    review_status = effective_block_status(block, document)
    content = _list_text(block) if block_type == "list" else str(block.get("content", ""))
    options = "".join(f'<option value="{kind}"{" selected" if kind == block_type else ""}>{kind.replace("_", " ").title()}</option>' for kind in sorted(BLOCK_TYPES))
    states = "".join(f'<option value="{state}"{" selected" if state == review_status else ""}>{_status_label(state)}</option>' for state in ("unreviewed", "approved", "needs_review", "excluded"))
    level = int(block.get("level", 2))
    levels = "".join(f'<option value="{value}"{" selected" if value == level else ""}>H{value}</option>' for value in range(1, 7))
    issue_text = " ".join(str(issue.get("message", "")) for issue in block.get("review", {}).get("issues", []))
    approval_reason = block_review_reason(block, document)
    source_type = str(provenance.get("source_type") or "Unknown")
    bbox = provenance.get("bounding_box")
    bbox_value = html.escape(json.dumps(bbox), quote=True) if isinstance(bbox, list) and len(bbox) == 4 else ""
    source_regions = _source_regions(block)
    regions_value = html.escape(json.dumps(source_regions), quote=True) if source_regions else ""
    inferred_order = provenance.get("visual_order_reason") == "heading_table_association"
    table = ""
    if block_type == "table":
        stats = table_summary(block)
        rows = "".join("<tr>" + "".join(f"<td>{html.escape(str(cell.get('content','') if isinstance(cell,dict) else cell))}</td>" for cell in row) + "</tr>" for row in block.get("rows", []))
        table = f'<p>{stats["rows"]} rows, {stats["columns"]} columns, {stats["spans"]} spanning cells</p><div class="table-scroll"><table><tbody>{rows}</tbody></table></div>'
    editable = block_type in BLOCK_TYPES
    nested_list = block_type == "list" and _list_has_nested_content(block)
    save_and_approve = f'<button type="submit" class="review-approve" data-save-and-approve aria-label="Save and approve block {index}">Save and approve</button>'
    text_editor = f'''<form class="block-form" data-block-id="{block_id}"><div class="form-grid">
<label>Block type<select name="type">{options}</select></label>
<label class="heading-level"{"" if block_type == "heading" else " hidden"}>Heading level<select name="level"{"" if block_type == "heading" else " disabled"}>{levels}</select></label>
<label>Review state<select name="review_status">{states}</select></label></div>
<label>Text<textarea name="content" rows="3">{html.escape(content)}</textarea></label>
<div class="button-row"><button type="submit" aria-label="Save block {index}">Save block</button>{save_and_approve}</div></form>''' if editable and can_edit and not nested_list else ""
    if has_unstructured_list_text(block) and text_editor:
        text_editor = '<p class="block-issue">The retained text is shown below. Save block recovers it as one list item and requires review. This does not reconstruct nested steps. A blank save is blocked.</p>' + text_editor
    if nested_list and can_edit:
        text_editor = f'''<div class="list-structure-preview" aria-label="Nested list structure">{_list_structure_preview(block)}</div>
<p><small>This nested list is shown hierarchically. Whole-list text editing is disabled to preserve its structure.</small></p>
<form class="block-form nested-list-review-form" data-block-id="{block_id}"><label>Review state<select name="review_status">{states}</select></label>
<div class="button-row"><button type="submit" aria-label="Save review state for block {index}">Save review state</button>{save_and_approve}</div></form>'''
    image_editor = ""
    if block_type == "image" and can_edit:
        image_src = str(block.get("src") or "")
        image_name = Path(image_src).name
        preview = f'<img class="image-block-preview" src="/api/preview/images/{quote(image_name)}" alt="">' if image_name else '<p>Extracted image preview unavailable.</p>'
        if image_src.startswith("extraction/"):
            preview = f'<img class="image-block-preview" src="/api/image-drafts/asset?path={quote(image_src)}" alt="">'
        decorative = bool(block.get("decorative"))
        accessibility_warning = "" if decorative or str(block.get("alt") or "").strip() else '<p class="block-issue" role="alert">Accessibility decision required: add alt text or mark this image as decorative.</p>'
        description_records = descriptions_for(document, block) if document else []
        description_fields = ''
        for record_index, visual in enumerate(description_records):
            readiness = visual_readiness(document, visual)
            fields = visual.get('accessibility', {})
            inline_id = 'visual-' + str(visual['id']) if description_owner(document, visual) is block else 'image-' + str(block['id']) + '-visual-' + str(visual['id'])
            disposition = visual.get('status') if visual.get('status') in {'excluded', 'not_applicable'} else 'include'
            use_options = ''.join(f'<option value="{value}"'+(' selected' if value == disposition else '')+f'>{label}</option>' for value, label in [('include', 'Use this description'), ('not_applicable', 'No separate description needed'), ('excluded', 'Exclude this description')])
            description_fields += f'''<fieldset class="image-description-record" id="{html.escape(inline_id, quote=True)}" tabindex="-1" aria-labelledby="{html.escape(inline_id, quote=True)}-heading" aria-describedby="{html.escape(inline_id, quote=True)}-reason {html.escape(inline_id, quote=True)}-action" data-visual-id="{html.escape(str(visual['id']), quote=True)}"><legend id="{html.escape(inline_id, quote=True)}-heading">Description {record_index + 1} · {html.escape(str(visual.get('type') or 'image'))}</legend><p class="image-description-state">{html.escape(readiness['label'])}</p><p class="image-description-reason" id="{html.escape(inline_id, quote=True)}-reason">{html.escape(readiness['reason'])}</p><p id="{html.escape(inline_id, quote=True)}-action"><a href="/help#image-descriptions">Description review help</a></p><label>Description use<select name="description_{record_index}_use" data-description-field="disposition">{use_options}</select></label><label>Long description<textarea name="description_{record_index}_long" data-description-field="long_description" rows="6">{html.escape(str(fields.get('long_description') or ''))}</textarea></label><label>Adjacent text equivalent (optional when long description is provided)<textarea name="description_{record_index}_adjacent" data-description-field="adjacent_text" rows="4">{html.escape(str(fields.get('adjacent_text') or ''))}</textarea></label><small>Provide either field. Recorded description decision: <span class="image-description-decision">{html.escape(str(visual.get('status') or 'needs_text_equivalent'))}</span>.</small><details><summary>Classification and source text (optional)</summary><label>Classification<input name="description_{record_index}_type" data-description-field="type" value="{html.escape(str(visual.get('type') or ''), quote=True)}"></label><label>Recovered source text (optional)<textarea name="description_{record_index}_recovered" data-description-field="recovered_text" rows="4">{html.escape(str(visual.get('recovered_text') or ''))}</textarea></label><label>Reviewer note (optional)<textarea name="description_{record_index}_note" data-description-field="review_note" rows="2">{html.escape(str(visual.get('review_note') or ''))}</textarea></label></details></fieldset>'''
        if not description_records:
            description_fields = f'''<label>Long description (optional for a simple image)<textarea name="long_description" rows="6">{html.escape(long_description)}</textarea><small>Use for information that needs more detail than alt text.</small></label>'''
        image_scope = 'This action approves this image and every included description shown here. Existing exclusions remain. Material edits require fresh review. Decorative images need no separate description.'
        image_editor = f'''{accessibility_warning}<p><a href="#image-description-tools" class="draft-workflow-link">Draft image descriptions</a></p><form class="block-form image-block-form" data-block-id="{block_id}">{preview}<div class="form-grid">
<label>Alt text<textarea name="alt" rows="3"{" disabled" if decorative else ""}>{html.escape(str(block.get("alt") or ""))}</textarea><small>Describe the image's purpose or information.</small></label>
<label>Caption<textarea name="caption" rows="3">{html.escape(str(block.get("caption") or ""))}</textarea></label>
{description_fields}<input type="hidden" name="expected_review_token" value="{review_token(document) if document else ''}">
</div>
<label class="image-decorative"><input type="checkbox" name="decorative"{" checked" if decorative else ""}> Decorative image</label>
<small>Decorative images export with an empty alt attribute and do not require alt text.</small><p class="image-approval-scope">{image_scope}</p>
<div class="button-row"><button type="submit" aria-label="Save image block {index}">Save image block</button>{save_and_approve}</div></form>'''
    table_editor = ""
    if block_type == "table" and can_edit:
        table_accessibility = block.get("table_accessibility", {})
        table_editor = f'''<form class="block-form table-accessibility-form" data-block-id="{block_id}"><div class="form-grid">
<label>Table caption<input name="table_caption" value="{html.escape(str(block.get('caption') or ''), quote=True)}"></label>
<label class="checkbox-label"><input type="checkbox" name="table_header_row"{" checked" if table_accessibility.get('header_row', True) else ""}> First row contains column headers</label>
<label class="checkbox-label"><input type="checkbox" name="table_header_column"{" checked" if table_accessibility.get('header_column') else ""}> First column contains row headers</label>
<label class="checkbox-label"><input type="checkbox" name="table_reviewed"{" checked" if table_accessibility.get('reviewed') else ""}> I reviewed the table structure</label></div>
<div class="button-row"><button type="submit" aria-label="Save table accessibility for block {index}">Save table accessibility</button>{save_and_approve}</div></form>'''
    link_editors = []
    def linked_runs(node):
        for run_index, run in enumerate(node.get('runs', [])):
            if run.get('type') == 'link' and (run.get('url') or run.get('href')):
                yield node, run_index, run
        for child in node.get('children', []):
            yield from linked_runs(child)
    if can_edit:
        for node, run_index, run in linked_runs(block):
            link_editors.append(f'''<form class="block-form link-text-form" data-block-id="{block_id}">
<input type="hidden" name="link_block_id" value="{html.escape(str(node['id']), quote=True)}"><input type="hidden" name="expected_review_token" value="{review_token(document) if document else ''}">
<input type="hidden" name="link_index" value="{run_index}">
<label>Link text<input name="link_text" required value="{html.escape(str(run.get('text') or ''), quote=True)}"></label>
<p><small>Destination: {html.escape(str(run.get('url') or run.get('href')))}</small></p>
<div class="button-row"><button type="submit">Save link text</button>{save_and_approve}</div><small>Save link text keeps the destination and marks the block for review. Save and approve saves this label and approves the displayed block in one step; other unresolved link findings remain.</small></form>''')
    editor = (image_editor or table_editor or text_editor) + ''.join(link_editors) + draft_controls
    include_label = "Include" if review_status == "excluded" else "Exclude"
    merge_reason = merge_next_reason(block, following)
    actions = f'''<footer class="block-actions" aria-label="Actions for block {index}">
<button type="button" class="secondary block-action" data-action="start" data-block-id="{block_id}" aria-label="Move block {index} to start"{" disabled" if index == 1 else ""}>Move to start</button>
<button type="button" class="secondary block-action" data-action="up" data-block-id="{block_id}" aria-label="Move block {index} up"{" disabled" if index == 1 else ""}>Move up</button>
<button type="button" class="secondary block-action" data-action="down" data-block-id="{block_id}" aria-label="Move block {index} down"{" disabled" if index == total else ""}>Move down</button>
<button type="button" class="secondary block-action" data-action="end" data-block-id="{block_id}" aria-label="Move block {index} to end"{" disabled" if index == total else ""}>Move to end</button>
<button type="button" class="secondary block-action" data-action="merge" data-block-id="{block_id}" aria-label="Merge block {index} with next block"{f' disabled aria-describedby="merge-help-{block_id}"' if merge_reason else ''}>Merge next</button>
<button type="button" class="secondary block-action" data-action="split" data-block-id="{block_id}" aria-label="Split block {index}">Split</button>
{f'<small id="merge-help-{block_id}" class="merge-help">{html.escape(merge_reason)}</small>' if merge_reason else ''}<p class="block-action-message" role="status" aria-live="polite" hidden></p></footer>''' if can_edit else '<footer><strong>Inspection only while conversion is blocked.</strong></footer>'
    review_actions = f'''<div class="block-review-actions" role="group" aria-label="Review block {index}">
<button type="button" class="block-action review-needs" data-action="flag" data-block-id="{block_id}" aria-label="Mark block {index} as needs review">Needs review</button>
<button type="button" class="block-action review-exclude" data-action="toggle-excluded" data-block-id="{block_id}" data-current-status="{review_status}" aria-label="{include_label} block {index}">{include_label}</button>
{("" if block_type == "image" else f'<button type="button" class="block-action review-approve" data-action="approve" data-block-id="{block_id}" aria-label="Approve block {index}"' + (' disabled' if review_status == 'approved' else '') + '>Approve</button>')}</div>''' if can_edit else ""
    return f'''<article class="block-card status-{html.escape(review_status)}" id="block-{block_id}" tabindex="-1" data-page="{page}" data-bbox="{bbox_value}" data-bboxes="{regions_value}" data-source-coverage="{html.escape(_source_region_coverage(block), quote=True)}" data-block-index="{index}" data-review-status="{html.escape(review_status)}" data-source-type="{html.escape(source_type, quote=True)}" aria-labelledby="block-{block_id}-heading">
{review_actions}<header><div><span class="order">{index}</span> <h3 id="block-{block_id}-heading">{html.escape(block_type.replace("_", " ").title())}{f' H{level}' if block_type == 'heading' else ''}</h3></div><span class="block-status status-{html.escape(review_status)}">{_status_label(review_status)}</span></header>
{f'<p class="block-review-reason">{html.escape(approval_reason)}</p>' if approval_reason else ''}<p class="source-provenance">OpenDataLoader source: {html.escape(source_type)}{f' · Source region available' if bbox_value else ''}{' · Reading order inferred from layout' if inferred_order else ''}</p>{f'<p class="block-issue">{html.escape(issue_text)}</p>' if issue_text else ''}{table}{editor}
{actions}</article>'''


def _visual_image_url(root: Path, document: dict[str, Any], visual: dict[str, Any]) -> str:
    """Use the explicitly associated image, or the exact retained asset path."""
    source_id = visual.get("source_block_id")
    if source_id:
        try:
            block = drafts.image(document, str(source_id))
            path = drafts.asset_for(root, document, block)
            return "/api/image-drafts/asset?path=" + quote(str(path.relative_to(root.resolve())))
        except (ValueError, KeyError):
            return ""
    for reference in visual.get("asset_references", []):
        ref = str(reference or "")
        if ref.startswith("extraction/"):
            path = root / ref
        elif ref.startswith("images/"):
            path = root / "extraction/raw" / ref
        elif Path(ref).name == ref:
            path = root / "extraction/assets/images" / ref
        else:
            continue
        try:
            path = drafts.confined(root, path)
            return "/api/image-drafts/asset?path=" + quote(str(path.relative_to(root.resolve())))
        except ValueError:
            continue
    return ""


def _complex_visual_card(visual: dict[str, Any], *, can_edit: bool, root: Path, document: dict[str, Any]) -> str:
    visual_id = html.escape(str(visual.get("id", "")), quote=True)
    ratio = visual.get("text_recovery_ratio")
    recovery = f"{ratio:.1%}" if ratio is not None else "Unknown"
    assets = visual.get("asset_references", [])
    asset_list = "".join(f"<li><code>{html.escape(str(asset))}</code></li>" for asset in assets)
    image_url = _visual_image_url(root, document, visual)
    asset_image = f'<img class="image-block-preview" src="{html.escape(image_url, quote=True)}" alt="">' if image_url else '<p>Image preview unavailable. Verify the retained image association.</p>'
    source_id = str(visual.get("source_block_id") or "")
    linked_block = next((b for b in drafts._walk(document.get("blocks", [])) if str(b.get("id")) == source_id), None)
    status = str(visual.get("status", "needs_text_equivalent"))
    accessibility = dict(visual.get("accessibility", {}))
    if linked_block:
        accessibility["short_alt"] = linked_block.get("alt") or ""
    readiness = visual_readiness(document, visual)
    title = 'Image description' if source_id else 'Complex visual'
    context = _description_context(document, visual)
    state_options = ''.join(f'<option value="{value}"'+(' selected' if status == value else '')+f'>{label}</option>' for value, label in [
        ('needs_text_equivalent', 'Text provided — awaiting review' if readiness['text_complete'] else 'Needs a text equivalent'), ('reclassified', 'Reclassified'),
        ('reviewed', 'Reviewed — also approves linked image' if source_id else 'Reviewed'),
        ('not_applicable', 'Not applicable — no separate description needed'), ('excluded', 'Exclude this description')])
    form = f'''<form class="complex-visual-form" data-visual-id="{visual_id}" data-block-id="{html.escape(source_id, quote=True)}"><input type="hidden" name="expected_review_token" value="{review_token(document)}"><div class="form-grid">
<label>Classification<input name="type" value="{html.escape(str(visual.get('type','infographic')), quote=True)}"></label>
<label>Review state<select name="status">{state_options}</select></label></div>
<label>Short alt text (required unless decorative or excluded)<textarea name="short_alt" rows="3">{html.escape(str(accessibility.get('short_alt','')))}</textarea></label>
<label>Long description (or adjacent text)<textarea name="long_description" rows="6">{html.escape(str(accessibility.get('long_description','')))}</textarea><small>Provide this or an adjacent text equivalent; both are not required.</small></label>
<label>Adjacent text equivalent (optional when a long description is provided)<textarea name="adjacent_text" rows="6">{html.escape(str(accessibility.get('adjacent_text','')))}</textarea></label>
<label>Recovered source text (optional)<textarea name="recovered_text" rows="8">{html.escape(str(visual.get('recovered_text','')))}</textarea></label>
<label>Reviewer note (optional)<textarea name="review_note" rows="2">{html.escape(str(visual.get('review_note','')))}</textarea></label><button type="submit">Save complex visual review</button><p class="visual-save-message" role="status" aria-live="polite"></p></form>''' if can_edit else "<p><strong>Inspection only while conversion is blocked.</strong></p>"
    block_link = f'<p><a href="/structure#block-{quote(source_id)}">Open linked image block</a> — <span class="linked-image-status">{_status_label(str(linked_block.get("review", {}).get("status", "unreviewed")))}</span></p>' if linked_block else ''
    return f'''<article class="complex-visual {'visual-complete' if readiness['complete'] else 'visual-pending'}" id="visual-{visual_id}" tabindex="-1" aria-labelledby="visual-{visual_id}-heading" aria-describedby="visual-{visual_id}-reason visual-{visual_id}-action"><p class="description-selection-notice" hidden>Selected description for review</p><h3 id="visual-{visual_id}-heading">{html.escape(title)}</h3><p>Source page {visual.get('source_page')} · <span class="visual-state">{html.escape(readiness['label'])}</span></p><p class="description-context">{html.escape(context)}</p><p class="description-review-reason" id="visual-{visual_id}-reason"{' hidden' if not readiness['reason'] else ''}>{html.escape(readiness['reason'])}</p><p class="description-review-action" id="visual-{visual_id}-action"{' hidden' if not readiness['action'] else ''}>{html.escape(readiness['action'])}</p>{block_link}{asset_image}<details><summary>Extracted assets and recovered text</summary>{f'<p>Text recovered: {recovery}</p>' if ratio is not None else ''}<ul>{asset_list or '<li>No separate assets were retained.</li>'}</ul><p>{html.escape(str(visual.get('recovered_text','')))}</p></details>{form}</article>'''


def _description_context(document, visual):
    source = next((block for block in _walk(document.get('blocks', [])) if str(block.get('id')) == str(visual.get('source_block_id'))), None)
    return str((source or {}).get('alt') or (source or {}).get('caption') or visual.get('type') or 'Image description')[:100]


def _review_task_summary(document, progress=None):
    progress = progress or review_progress(document)
    linked = progress.get('linked_pending_descriptions', 0)
    detail = f"{linked} description review{'s' if linked != 1 else ''} included in the image reviews; {progress.get('standalone_pending_descriptions', 0)} standalone description reviews" if linked else f"{progress['pending_descriptions']} description review{'s' if progress['pending_descriptions'] != 1 else ''}"
    owner_counts = f"{progress['pending_images']} image review{'s' if progress['pending_images'] != 1 else ''} · {progress['pending_blocks'] - progress['pending_images']} other block reviews" if linked else f"{progress['pending_blocks']} block review{'s' if progress['pending_blocks'] != 1 else ''}"
    return f'''<div class="review-task-summary" id="review-summary" aria-label="Block and image approval progress"><p id="review-counts">Blocks reviewed {progress['approved']} · Excluded {progress['excluded']} · Total {progress['total']} block{'s' if progress['total'] != 1 else ''}</p><p id="review-task-counts" role="status" aria-live="polite">Block and image approvals: <strong>Pending {progress['pending_tasks']} review task{'s' if progress['pending_tasks'] != 1 else ''}</strong> · {owner_counts} · {detail}</p></div>'''


def _diagnostic_detail(model, item, *, accessibility=False):
    """Explain the existing diagnostic and link only to recorded review targets."""
    document = model['document']
    code = item['id'].split(':', 2)[1]
    issue = next((issue for issue in document.get('review', {}).get('issues', [])
                  if f"diagnostic:{issue.get('code') or 'diagnostic'}:{issue.get('page', 'document')}" == item['id']), {})
    requested = {str(value) for value in issue.get('block_ids', [])}
    if issue.get('block_id') is not None:
        requested.add(str(issue['block_id']))
    owners = {}
    nodes = {}
    for position, owner in enumerate(document.get('blocks', []), 1):
        for node in _walk([owner]):
            owners[str(node.get('id'))] = (position, owner)
            nodes[str(node.get('id'))] = node
    from .publication import effective_block_status
    links = []
    pending_owners = set()
    target_owners = set()
    for identity in sorted(requested, key=lambda key: owners.get(key, (float('inf'),))[0]):
        if identity not in owners:
            continue
        position, owner = owners[identity]
        target = str(owner['id'])
        if effective_block_status(owner) not in {'approved', 'excluded'}:
            pending_owners.add(target)
        if target in target_owners:
            continue
        target_owners.add(target)
        flagged = [node for key, node in nodes.items() if key in requested and owners[key][1] is owner]
        reasons = list(dict.fromkeys(str(reason.get('message') or '') for node in flagged
                                    for reason in node.get('review', {}).get('issues', []) if reason.get('message')))
        preview = (_list_text(owner) if owner.get('type') == 'list' else str(owner.get('content') or owner.get('alt') or owner.get('caption') or ''))[:160]
        label = f"Review source page {owner.get('provenance', {}).get('source_page') or 'unknown'} · Block {position}: {owner.get('type', 'content')} · {_status_label(effective_block_status(owner))}"
        if preview:
            label += ' — ' + preview
        links.append(f'<li><a href="/structure#block-{quote(target, safe="")}">{html.escape(label)}</a>'
                     + (f'<p>{html.escape(" ".join(reasons))}</p>' if reasons else '') + '</li>')
    visual = next((v for v in document.get('review', {}).get('complex_visuals', [])
                   if issue.get('complex_visual_id') is not None and str(v.get('id')) == str(issue['complex_visual_id'])), None)
    if visual:
        links.append(f'<li><a href="/structure#visual-{quote(str(visual["id"]), safe="")}">Review description on source page {html.escape(str(visual.get("source_page") or "unknown"))}</a></li>')
    message = html.escape(str(item.get('message') or 'The extraction check needs inspection.'))
    if pending_owners:
        impact = f"{len(pending_owners)} affected block review{'s are' if len(pending_owners) != 1 else ' is'} already included in the pending tasks above. Review and approve the saved content, or deliberately exclude it, before publication. This diagnostic does not add another block review."
    elif visual and not visual_readiness(document, visual)['complete']:
        impact = 'This description review is already included in the pending tasks above. Complete its manual review before publication.'
    elif document.get('review', {}).get('status') == 'conversion_blocked':
        impact = 'Conversion is blocked. Recover the conversion before editing or publishing; recording a diagnostic decision does not unblock it.'
    else:
        impact = 'This extraction note needs inspection but does not independently block publication. Current block and description approvals still control publication.'
    if document.get('review', {}).get('status') == 'conversion_blocked' and (pending_owners or visual):
        impact += ' Conversion is also blocked; recover the conversion before editing or publishing.'
    recovery = ''
    if links and requested - owners.keys():
        recovery = '<p>Some referenced content is no longer available. Compare the source PDF with the remaining content and review this diagnostic in Accessibility; no target is invented for the missing content.</p>'
    if not links:
        page = item.get('source_page')
        scope = ('The referenced content is no longer available; there is no valid block target.' if requested else
                 f'This check identifies source page {page}, but no single block.' if page else
                 'This is a document-wide extraction check; no single block was identified.')
        actions = {
            'incomplete_text_recovery': 'Some source text may be missing. Compare the original PDF with Structure, recover or correct missing content, and review the diagnostic in Accessibility.',
            'incomplete_page_coverage': 'Some source pages have no extracted elements. Compare the original pages with Structure and recover any missing content.',
            'invalid_text_characters': 'Some extracted characters may be unreadable. Compare the original PDF and correct the text in Structure, or recover the extraction if conversion is blocked.',
        }
        recovery = f'<p>{html.escape(scope)} {html.escape(actions.get(code, "Compare the source PDF with the extracted content and review this diagnostic in Accessibility. The diagnostic does not identify an automatic repair."))}</p>'
        source = model['project'].get('source', {}).get('path')
        try:
            source_available = source and safe_project_file(model['project_dir'], source).is_file()
        except (ValueError, OSError):
            source_available = False
        if source_available:
            fragment = f'#page={page}' if isinstance(page, int) and page > 0 else ''
            recovery += f'<p><a href="/source.pdf{fragment}" target="_blank" rel="noopener">Open source PDF</a></p>'
        else:
            recovery += '<p>Source PDF is unavailable. Check the project folder shown above and restore the project’s source copy before comparing the extraction.</p>'
    if not accessibility:
        recovery += f'<p><a href="/accessibility#finding-{quote(item["id"], safe="")}">Review diagnostic in Accessibility</a></p>'
    return f'<p>{message}</p><p>{html.escape(impact)}</p>' + ('<ul>' + ''.join(links) + '</ul>' if links else '') + recovery


def _document_diagnostics(model):
    active = [item for item in model['accessibility']['items'] if item['category'] == 'diagnostics' and item['status'] == 'unresolved']
    if not active:
        return ''
    details = ''.join('<li>' + _diagnostic_detail(model, item) + '</li>' for item in active)
    return f'<div class="document-diagnostics"><h3>Extraction diagnostics</h3><p>{len(active)} unresolved diagnostic issue{"s" if len(active) != 1 else ""}. Diagnostic notes are listed separately from review tasks; their affected blocks or descriptions are not counted twice.</p><ul>{details}</ul></div>'


def _structure_completion(document, *, structure_path=""):
    progress = review_progress(document)
    unresolved_visuals = [v for v in document.get('review', {}).get('complex_visuals', []) if not visual_readiness(document, v)['complete']]
    complete = document.get('review', {}).get('status') != 'conversion_blocked' and progress['total'] > 0 and progress['approved'] + progress['excluded'] == progress['total']
    if complete and unresolved_visuals:
        links = ''.join(f'<li><a href="{structure_path}#visual-{quote(str(v["id"]))}">Review description on source page {html.escape(str(v.get("source_page") or "unknown"))}: {html.escape(_description_context(document, v))}</a></li>' for v in unresolved_visuals)
        return f'<section class="status-banner status-needs_review"><h2>Review standalone visuals</h2><p>These visuals have no single Reading order image owner. Review their text and decision here or in Accessibility.</p><ul>{links}</ul></section>'
    return '''<section id="structure-review-complete" class="structure-review-complete" role="status" tabindex="-1" aria-labelledby="structure-complete-heading">
<h2 id="structure-complete-heading">Structure review complete</h2>
<p>Continue to Accessibility for document and HTML checks.</p>
<p class="button-row workflow-next"><a href="/accessibility" role="button" class="review-approve">Continue to Accessibility</a></p></section>''' if complete else ''


def _structure_page(model: dict[str, Any]) -> str:
    document = model["document"]
    status = document.get("review", {}).get("status", "needs_review")
    can_edit = status != "conversion_blocked"
    progress = model["progress"]
    blocks = document.get("blocks", [])
    page_count = int(model["project"].get("source", {}).get("page_count") or 1)
    source_preview_key = html.escape(str(model["source_preview_key"]), quote=True)
    cards = "".join(_block_card(block, index, total=len(blocks), following=blocks[index] if index < len(blocks) else None, document=document, can_edit=can_edit, long_description=str((drafts.visual_for(document, block) or {}).get("accessibility", {}).get("long_description") or ""), draft_controls=image_draft_ui.controls(model["project_dir"], document, block) if can_edit and block.get("type") == "image" else "") for index, block in enumerate(blocks, 1))
    visual_records = [v for v in document.get("review", {}).get("complex_visuals", []) if description_owner(document, v) is None]
    pending_visuals = sum(not visual_readiness(document, visual)['complete'] for visual in visual_records)
    visuals = "".join(_complex_visual_card(visual, can_edit=can_edit, root=model["project_dir"], document=document) for visual in visual_records)
    undo_control = f'''<details class="review-history"><summary>Saved review history</summary><p>Undo restores the previous saved change, including changes from earlier sessions.</p><button id="undo-action" type="button" class="secondary"{' disabled' if not model['can_undo'] else ''}>Undo last action</button>{'<p class="undo-empty">No saved actions to undo.</p>' if not model['can_undo'] else ''}</details>''' if can_edit else ''
    reading_order_undo = f'''<button id="reading-order-undo" type="button" class="neutral-action" title="Restore the most recent saved project change, including changes from earlier sessions."{' disabled' if not model['can_undo'] else ''}>Undo last saved change</button>''' if can_edit else ''
    completion_message = _structure_completion(document)
    review_label = "Conversion blocked" if not can_edit else "Structure reviewed" if 'id="structure-review-complete"' in completion_message else "Review in progress"
    draft_useful = progress['pending_images'] > 0 or bool(drafts.state(document)['active'])
    drafting_tools = ('<section class="image-draft-workflow" aria-labelledby="image-draft-heading"><h2 id="image-draft-heading" tabindex="-1">Image description drafts</h2>'
        '<p>Prepare image descriptions here before reviewing the image blocks below. Drafting is optional; you can author descriptions directly.</p>'
        f'<details id="image-description-tools" class="review-tools"{" open" if draft_useful else ""}><summary>Drafting tools (optional)</summary>'
        + image_draft_ui.toolbar(document) + '</details></section>') if can_edit and any(b.get('type') == 'image' for b in blocks) else ''
    body = f'''<h1>Structure</h1><div class="review-toolbar"><p class="review-overall-status"{' hidden' if not can_edit or 'id="structure-review-complete"' in completion_message else ''}><strong>{review_label}</strong></p>{_review_task_summary(document, progress)}{undo_control}</div><div id="structure-completion-region">{completion_message}</div>{_status_banner(status, document.get("review", {}).get("issues", []), document) if not can_edit else ''}
{drafting_tools}
{f'<details id="visual-description-tools" class="visual-descriptions review-tools"><summary>Standalone visual descriptions · <span id="visual-description-counts">{pending_visuals} to review · {len(visual_records) - pending_visuals} complete or not applicable</span></summary><h2 id="complex-heading">Standalone visual descriptions</h2><p>Add a long description or adjacent text, then choose Reviewed. Choose Not applicable if short alt text is sufficient. <a href="/help#image-descriptions">Image description help</a>.</p>{visuals}</details>' if visuals else ''}
<div class="structure-layout"><section class="source-pane" aria-labelledby="source-heading" data-page-count="{page_count}" data-source-key="{source_preview_key}"><h2 id="source-heading">Source page</h2><form id="source-page-controls" class="source-page-controls"><button id="source-page-previous" type="button" class="secondary" disabled aria-label="Previous source page">Previous</button><label>Page <input id="source-page-number" type="number" min="1" max="{page_count}" value="1" inputmode="numeric" aria-describedby="source-page-total"></label><span id="source-page-total">of {page_count}</span><button id="source-page-next" type="button" class="secondary"{(' disabled' if page_count <= 1 else '')} aria-label="Next source page">Next</button></form><p id="source-page-label" aria-live="polite">Select a block to view and outline its source region.</p><p id="source-page-render-status" role="status" aria-live="polite">Loading source page 1…</p><button id="source-page-retry" type="button" class="neutral-action" hidden>Retry source page</button><div class="source-image-stage" aria-busy="true"><img id="source-image" data-source-url="/source-page/1.png?v={source_preview_key}" alt="Rendered source PDF page 1" hidden><span id="source-highlights" aria-hidden="true"></span></div><p><a id="open-source-page" href="/source.pdf?v={source_preview_key}#page=1" target="_blank" rel="noopener">Open source PDF page 1</a></p></section>
<section class="blocks-pane" aria-labelledby="blocks-heading"><div class="reading-order-header"><h2 id="blocks-heading">Reading order</h2>{reading_order_undo}<div class="block-navigation" role="group" aria-label="Selected block navigation"><button id="previous-block" type="button" class="secondary" disabled>Previous block</button><span class="block-navigation-position" aria-live="polite"><span id="selected-block-page">No block selected</span><span id="selected-block-position">No block selected</span></span><button id="next-block" type="button" class="secondary"{(' disabled' if not blocks else '')}>Next block</button></div><div class="block-filter"><div id="block-review-filter" role="group" aria-label="Show blocks"><span>Show:</span> <a href="#blocks-heading" data-filter="all" aria-current="true">All <span data-filter-count>({progress['total']})</span></a> <a href="#blocks-heading" data-filter="approved">Approved <span data-filter-count>({progress['approved']})</span></a> <a href="#blocks-heading" data-filter="pending">Needing review <span data-filter-count>({progress['unreviewed'] + progress['needs_review']})</span></a> <a href="#blocks-heading" data-filter="excluded">Excluded <span data-filter-count>({progress['excluded']})</span></a><span id="block-filter-count" role="status" aria-live="polite">{progress['total']} of {progress['total']} blocks</span></div></div><p id="block-filter-empty" class="block-filter-empty" hidden><span id="block-filter-empty-message" role="status" aria-live="polite"></span> <a id="show-all-blocks" href="#blocks-heading" aria-controls="block-review-filter">Show all blocks</a></p></div><p>Use the movement controls on each block to correct reading order. Changes save immediately.</p>{cards or '<p>No normalized blocks are available.</p>'}</section></div>'''
    return _page("Structure", "structure", body, project=model["project"], project_path=model["project_dir"])


def _bulk_review_controls(document, root):
    from .bulk_review import records, STATES
    if document.get('review', {}).get('status') == 'conversion_blocked':
        return ''
    rows = records(document)
    esc = lambda value: html.escape(str(value or ''), quote=True)
    groups = {}
    def image_text(block):
        url = _visual_image_url(root, document, {'source_block_id': str(block['id'])})
        preview = f'<img class="image-block-preview" src="{esc(url)}" alt="">' if url else '<p>Image preview unavailable; inspect the source in the linked editor.</p>'
        return preview + f'<p>Image alt: {esc(block.get("alt"))}</p><p>Caption: {esc(block.get("caption"))}</p><p>Decorative: {"Yes" if block.get("decorative") else "No"}</p>'
    def description_text(visual):
        state = visual_readiness(document, visual)
        a = visual.get('accessibility', {})
        return f'<div class="bulk-description"><p><strong>Description {esc(visual["id"])} · {esc(visual.get("type"))} · {esc(state["label"])}</strong></p><p class="review-text">Long description: {esc(a.get("long_description"))}</p><p class="review-text">Adjacent equivalent: {esc(a.get("adjacent_text"))}</p><p>{esc(state["reason"])}</p></div>'
    for row in rows:
        related = []
        if row['kind'] == 'block':
            block = row['block']
            related = descriptions_for(document, block) if block.get('type') == 'image' else []
            content = image_text(block) + ''.join(description_text(v) for v in related) if block.get('type') == 'image' else '<div class="bulk-content">' + re.sub(r'<(/?)h[1-6]', r'<\1h4', html_exporter._block(block) or f'<p>{esc(block.get("content"))}</p>') + '</div>'
            target = '/structure#block-' + quote(row['target_id'])
        elif row['kind'] == 'description':
            visual = row['visual']
            block = next((b for b in _walk(document.get('blocks', [])) if str(b.get('id')) == str(visual.get('source_block_id'))), None)
            content = (image_text(block) if block else f'<p>Short alt: {esc(visual.get("accessibility", {}).get("short_alt"))}</p>') + description_text(visual)
            target = '/structure#visual-' + quote(row['target_id'])
        else:
            content = f'<p>{esc(row["item"]["message"])}</p>'
            target = '#finding-' + quote(row['target_id'])
        selection = f'<label class="bulk-row-select"><input type="checkbox" class="bulk-review-select" value="{esc(row["id"])}" data-kind="{row["kind"]}" data-states="{esc(json.dumps(STATES[row["kind"]]))}" data-description-count="{len(related)}"> Select {esc(row["label"])}</label>'
        pill_state, pill_label, recorded_decision = row['state'], _status_label(row['state']), ''
        if row['kind'] == 'description':
            pill_label = visual_readiness(document, row['visual'])['label']
            pill_state = 'needs_review' if row['pending'] else 'excluded' if pill_label == 'Excluded' else 'not_applicable' if pill_label == 'Decorative image' else row['state']
            recorded_decision = f'<small>Recorded description decision: {esc(_status_label(row["state"]))}</small>'
        groups.setdefault(row['classification'], []).append(f'<article class="bulk-review-row" data-classification="{esc(row["classification"])}" data-pending="{str(row["pending"]).lower()}"{(" hidden" if not row["pending"] else "")}>{selection}<p>Current state: <span class="block-status status-{esc(pill_state)}">{esc(pill_label)}</span></p>{recorded_decision}{content}<a href="{esc(target)}">Open exact review editor</a></article>')
    options = ''.join(f'<option value="{esc(group)}">{esc(group)}</option>' for group in groups)
    pending_count = sum(row['pending'] for row in rows)
    pending_groups = {row['classification'] for row in rows if row['pending']}
    sections = ''.join(f'<section class="bulk-review-group" data-classification="{esc(group)}" aria-labelledby="bulk-group-{index}"{(" hidden" if group not in pending_groups else "")}><h3 id="bulk-group-{index}">{esc(group)}</h3>{"".join(cards)}</section>' for index, (group, cards) in enumerate(groups.items()))
    return f'''<details id="bulk-review-tools"><summary>Bulk review (optional) · {pending_count} pending saved records</summary><section id="bulk-review" data-project-id="{esc(document['output_pages']['project_id'])}" data-review-token="{review_token(document)}" aria-labelledby="bulk-review-heading"><h2 id="bulk-review-heading" tabindex="-1">Bulk review</h2><p>Select records for one batch decision. Image rows include their descriptions. One Undo restores the batch. <a href="/help#bulk-review">Bulk review and record counts</a>.</p><div class="bulk-review-toolbar"><label>Show records<select id="bulk-review-visibility"><option value="pending">Pending only</option><option value="completed">Completed</option><option value="all">All records</option></select></label><label>Classification filter<select id="bulk-review-filter"><option value="">All classifications</option>{options}</select></label><label><input type="checkbox" id="bulk-review-select-all"> Select all visible records</label><label>Review state options<select id="bulk-review-state" disabled><option value="">Select records first</option></select></label><button type="button" id="bulk-review-apply" disabled>Apply</button><button type="button" id="bulk-review-undo">Undo last action</button></div><p id="bulk-review-visible-count" role="status" aria-live="polite">{pending_count} of {len(rows)} saved records shown · Pending only</p><p id="bulk-review-empty"{(" hidden" if pending_count else "")}>No pending saved records in this view. Completed records remain available in Show records.</p><p id="bulk-review-selection" role="status" aria-live="polite">0 selected</p><p id="bulk-review-confirmation" hidden></p><button type="button" id="bulk-review-confirm" hidden>Confirm selected review changes</button><p id="bulk-review-message" role="status" aria-live="polite"></p>{sections}</section></details>'''


def _accessibility_page(model: dict[str, Any]) -> str:
    report = model["accessibility"]
    summary = report["summary"]
    block_positions = {str(block['id']): index for index, block in enumerate(model['document'].get('blocks', []), 1)}
    category_labels = {
        "structure": "Structure",
        "images": "Images",
        "complex_visuals": "Complex visuals",
        "tables": "Tables",
        "headings": "Headings",
        "links": "Links",
        "unresolved_content": "Unresolved content",
        "diagnostics": "Diagnostics",
    }
    groups: list[str] = []
    resolved_diagnostics = []
    reviewed_findings = []
    for category in category_labels:
        items = [item for item in report["items"] if item["category"] == category]
        if not items:
            continue
        cards = []
        for item in items:
            item_id = html.escape(item["id"], quote=True)
            location = f"Source page {item['source_page']}" if item.get("source_page") else "Document-level"
            position = block_positions.get(str(item.get('block_id')))
            if position:
                location += f" · Block {position}"
            return_query = '?return_to=accessibility&amp;finding=' + quote(item['id'], safe='')
            block_link = f' <a href="/structure{return_query}#block-{quote(str(item["block_id"]))}" role="button" class="secondary compact-action">Open block</a>' if item.get("block_id") else ""
            if item.get('visual_id'):
                block_link = f' <a href="/structure{return_query}#visual-{quote(str(item["visual_id"]))}" role="button" class="secondary compact-action">Open description</a>'
            if category == 'images' and model['document'].get('review', {}).get('status') != 'conversion_blocked':
                block_link += ' <a href="/structure#image-description-tools" class="draft-workflow-link">Draft image descriptions</a>'
            related = item.get("related_blocks", [])
            related_markup = ""
            if related:
                links = "".join(
                    f'<li class="accessibility-related-block"><span>{html.escape("Source page " + str(block["source_page"]) if block["source_page"] else "Source page unknown")}'
                    f' · Block {block["position"]} · {html.escape(block["type"])}'
                    f' · {_status_label(block["status"])}'
                    f'{": " + html.escape(block["preview"]) if block["preview"] else ""}</span>'
                    f'<a href="/structure{return_query}#block-{quote(block["id"])}" role="button" class="secondary compact-action">Open block {block["position"]}: {html.escape(block["type"])}</a></li>'
                    for block in related
                )
                related_markup = f'<p>Recorded during extraction. Current block statuses:</p><ul>{links}</ul>'
            if item["decision_allowed"]:
                statuses = "".join(
                    f'<option value="{value}"{" selected" if item["status"] == value else ""}>{_status_label(value)}</option>'
                    for value in ("unresolved", "approved", "not_applicable")
                )
                decision_control = f'''<form class="accessibility-decision-form" data-item-id="{item_id}"><div class="form-grid"><label>Decision<select name="status">{statuses}</select></label><label>Reviewer note<textarea name="note" rows="2">{html.escape(item['note'])}</textarea></label></div><button type="submit">Save decision</button></form>'''
            else:
                decision_control = ''
            message_markup = '<p>' + html.escape(item['message']) + '</p>'
            if category == 'diagnostics' and item['status'] == 'unresolved':
                message_markup = _diagnostic_detail(model, item, accessibility=True)
                related_markup = ''
            card = f'''<article id="finding-{item_id}" tabindex="-1" class="accessibility-item status-{html.escape(item['status'])}"><header><div><h3>{html.escape(item['title'])}</h3><p>{html.escape(location)}</p></div><div class="accessibility-item-actions"><span class="block-status status-{html.escape(item['status'])}">{_status_label(item['status'])}</span>{block_link}</div></header>
{message_markup}{related_markup}{decision_control}</article>'''
            if category == 'diagnostics' and item['status'] != 'unresolved':
                original = f'<p>Original extraction note: {html.escape(item["original_message"])}</p>' if item.get('original_message') else ''
                card = f'<details class="resolved-findings"><summary>Resolved extraction note — {_status_label(item["status"])}</summary>{original}{card}</details>'
                resolved_diagnostics.append(card)
                continue
            if item['status'] != 'unresolved':
                reviewed_findings.append(card)
                continue
            cards.append(card)
        if cards:
            groups.append(f'<section aria-labelledby="accessibility-{category}"><h2 id="accessibility-{category}">{category_labels[category]} <small>({len(cards)})</small></h2>{"".join(cards)}</section>')
    history = f'<details class="diagnostic-history"><summary>Resolved extraction notes ({len(resolved_diagnostics)})</summary><p>No action is needed. These notes record the original extraction and your saved decisions. They are retained for reference and can be reopened if the decision needs to change.</p>{"".join(resolved_diagnostics)}</details>' if resolved_diagnostics else ''
    reviewed_history = f'<details class="reviewed-findings"><summary>Reviewed document findings ({len(reviewed_findings)})</summary><p>Earlier decisions remain editable here.</p>{"".join(reviewed_findings)}</details>' if reviewed_findings else ''
    empty = '<section class="status-banner"><h2>No findings</h2><p>The current deterministic checks found no items requiring a decision.</p></section>' if not groups else ""
    from .image_review import review_token
    token = review_token(model['document'])
    revision = model['document'].get('review_session', {}).get('revision', 0)
    body = f'''<h1>Accessibility</h1>{_review_task_summary(model['document'], model['progress'])}
<section aria-labelledby="document-review-heading"><h2 id="document-review-heading" tabindex="-1">Document accessibility findings</h2><div class="accessibility-summary"><span><strong>{summary['unresolved']}</strong> unresolved accessibility findings</span><span><strong>{summary['approved']}</strong> approved decisions</span><span><strong>{summary['not_applicable']}</strong> not applicable</span></div>
<p>Correct content in the linked editor or record a decision where allowed. Required corrections cannot be waived. <a href="/help#review-counts">How review counts differ</a>.</p>{empty}{''.join(groups)}{reviewed_history}{history}</section>
{_bulk_review_controls(model['document'], model['project_dir'])}
<section aria-labelledby="automated-heading"><h2 id="automated-heading">Automated HTML checks</h2>
<p>Checks the saved HTML; document judgments above remain separate. <a href="/help#html-checks">What these checks cover</a>.</p>
<p id="axe-status" role="status" aria-live="polite">Checking rendered HTML…</p><div id="axe-results"></div>
<iframe id="axe-preview" title="HTML used for automated accessibility checks" sandbox="allow-same-origin allow-scripts" aria-hidden="true" tabindex="-1" data-review-token="{token}" data-review-revision="{revision}" src="/api/accessibility/preview?expected_review_token={token}"></iframe></section>
<section id="accessibility-complete" class="structure-review-complete" data-document-ready="{str(summary['unresolved'] == 0 and model['progress']['total'] > 0 and model['document'].get('review', {}).get('status') != 'conversion_blocked').lower()}" hidden><h2>Accessibility review complete</h2><p>Document findings are resolved and the current HTML scan has no detected issues or checks awaiting human review.</p><p class="button-row workflow-next"><a href="/output-pages" role="button" class="review-approve">Continue to Arrange Pages</a></p></section>'''
    return _page("Accessibility", "accessibility", body, project=model["project"], project_path=model["project_dir"])


def _output_pages_page(model, selected_id=None):
    document = model['document']
    group = op.pages(document)
    selected = op.page_by_id(document, selected_id) or (group[0] if group else None)
    esc = lambda value: html.escape(str(value or ''), quote=True)
    errors = op.validate(document)
    validation = '<ul>' + ''.join('<li>' + esc(e) + '</li>' for e in errors) + '</ul>' if errors else '<p>Every included block is assigned once.</p>'
    assigned = {ref for p in group for ref in p['block_ids']}
    unassigned = [b for b in op.included(document) if str(b['id']) not in assigned]
    if unassigned and selected:
        validation += f'<p>{len(unassigned)} included block(s) have no output page. Export is blocked to prevent omitted content.</p><button type="button" data-page-action="assign_unassigned">Include unassigned content in this page</button>'
    export_disabled = ' disabled' if errors else ''
    from .publication import findings
    individual_disabled = ' disabled' if errors or not selected or findings(document, [selected]) else ''
    package_disabled = ' disabled' if errors or findings(document, group) else ''
    listing = []
    for p in sorted(group, key=lambda p: p['navigation_order']):
        state = op.status(document, p['id'])
        ranges = ', '.join(str(a) if a == b else f'{a}–{b}' for a, b in state['source_ranges']) or 'No source pages'
        unresolved = state['accessibility']['summary']['unresolved'] + len(state['unresolved_targets'])
        listing.append(f'<li><a href="/output-pages?page_id={esc(p["id"])}">{esc(p["title"])}</a><br><small>Source {ranges} · {len(p["block_ids"])} blocks · Structure: {esc(state["structural"].replace("_", " "))} · {unresolved} findings · Page decision: {esc(p["approval"]["status"].replace("_", " "))}</small></li>')
    suggestions = op.suggest(document)
    proposals = ''.join(f'<li>{esc(p["title"])} — {len(p["block_ids"])} blocks; source {esc(p["source_ranges"])}; starts at {esc(p["block_ids"][0])}</li>' for p in suggestions)
    editor = '<p>Create a page and assign content to begin.</p>'
    if selected:
        p = selected
        options = '<option value="">No parent</option>' + ''.join(f'<option value="{esc(i["id"])}"'+(' selected' if p.get('parent') == i['id'] else '')+f'>{esc(i["title"])}</option>' for i in group if i['id'] != p['id'] and i['type'] == 'page')
        targets = ''.join(f'<option value="{esc(i["id"])}">{esc(i["title"])}</option>' for i in group if i['id'] != p['id'])
        outline = []
        for b in document.get('blocks', []):
            ref = str(b['id'])
            owner = next((i for i in group if ref in i['block_ids']), None)
            assigned = owner is p
            label = str(b.get('content') or b.get('caption') or b.get('type'))[:160]
            state = 'Excluded' if op.is_excluded(b) else (owner['title'] if owner else 'Unassigned')
            controls = f'<button type="button" data-page-action="assign" data-block-id="{esc(ref)}">Move here</button>' if not assigned else f'<button type="button" data-page-action="split" data-block-id="{esc(ref)}"'+(' disabled' if p['block_ids'].index(ref) == 0 else '')+'>Split before</button>'
            outline.append(f'<li><strong>{esc(b.get("type"))}</strong> {esc(label)}<br><small>{esc(state)} · {esc(ref)}</small> {controls}</li>')
        for ref in p['block_ids']:
            if ref not in {str(b['id']) for b in document.get('blocks', [])}:
                outline.append(f'<li>Missing {esc(ref)} <button type="button" data-page-action="remove_reference" data-block-id="{esc(ref)}">Remove missing reference</button></li>')
        state = op.status(document, p['id'])
        target_findings = ''.join('<li>Unresolved link target: ' + esc(i['target']) + '</li>' for i in state['unresolved_targets'])
        findings = target_findings + ''.join(f'<li>{esc(i["title"])}: {esc(i["message"])} — {esc(i["status"])} {esc(i["note"])}</li>' for i in state['accessibility']['items'])
        editor = f'''<section id="page-editor" tabindex="-1" data-page-id="{esc(p['id'])}"><h2>{esc(p['title'])}</h2>
<form id="output-page-metadata"><div class="form-grid"><label>Title<input name="title" value="{esc(p['title'])}" required></label><label>Slug<input name="slug" value="{esc(p['slug'])}" required></label><label>Type<select name="type"><option value="page"{' selected' if p['type']=='page' else ''}>Page</option><option value="post"{' selected' if p['type']=='post' else ''}>Article</option></select></label><label>Parent<select name="parent">{options}</select></label><label>Contents order<input type="number" min="0" name="navigation_order" value="{p['navigation_order']}"></label></div><button>Save page</button></form>
<p><button type="button" data-page-action="reorder" data-direction="up">Move page up</button> <button type="button" data-page-action="reorder" data-direction="down">Move page down</button></p>
<form id="output-page-merge"><label>Merge into this page<select name="other_id">{targets}</select></label><button{' disabled' if not targets else ''}>Merge pages</button></form>
<details id="content-outline"><summary>Arrange content across pages (optional)</summary><p>Use this outline only to split or move content between web pages. Reading order follows Structure. Tables and image descriptions stay intact.</p><ol>{''.join(outline)}</ol></details>
<h3>Review</h3><p>Structure: {esc(state['structural'])}. Page decision: {esc(p['approval']['status'])}. Page decisions are recorded separately from block review.</p><ul>{findings}</ul>
<form id="output-page-approval"><label>Page reviewer note<textarea name="note">{esc(p['approval'].get('note'))}</textarea></label><button>Mark page reviewed</button></form>
<h3>Preview and export</h3><label>WordPress profile<select id="output-page-profile"><option value="generic">Generic</option><option value="wsuwp">WSUWP (approximate preview)</option></select></label>
<p>Approximate WordPress preview. <a href="/help#wordpress-preview">Preview appearance help</a>.</p>
<p>For WordPress images, <a href="/export#media-export-heading">prepare and map media first</a>, then return here to export your arrangement.</p>
<div class="workflow-actions"><div class="button-row"><button type="button" id="output-page-preview">Preview page</button> <button type="button" id="output-page-wordpress-preview">WordPress Preview</button></div><div class="button-row workflow-next"><button type="button" data-page-export="individual"{individual_disabled}>Export page</button> <button type="button" data-page-export="package"{package_disabled}>Export complete package</button></div></div>
<iframe id="output-page-frame" title="Output page preview" sandbox="allow-same-origin" src="/output-preview/{esc(p['slug'])}.html"></iframe></section>'''
    body = f'''<h1>Arrange Pages</h1>{_review_task_summary(document, model['progress'])}<p>Optional: arrange several web pages or articles. For one long page, go directly to <a href="/preview">Preview</a> and <a href="/export">Export</a>.</p>
<div id="output-page-message" role="status" aria-live="polite"></div><section aria-label="Arrangement validation">{validation}</section>
<div class="workflow-actions"><div class="button-row" role="group" aria-label="Page arrangement actions"><button type="button" data-page-action="single_page">Keep everything on one page</button> <button type="button" data-page-action="create">Create page</button> <button type="button" id="output-page-undo" class="neutral-action">Undo last action</button> <a href="/output-pages-contents" target="_blank" rel="noopener" role="button" class="review-approve">Preview contents</a></div><p class="button-row workflow-next"><a href="/preview" role="button" class="review-approve">Continue to Preview</a></p></div><p>Keeping everything on one page replaces the arrangement, includes all content that is not excluded, and supports Undo.</p>
<details><summary>Grouping suggestions</summary><p>Heading levels 1 and 2 and explicit section boundaries propose groups. Applying replaces the current arrangement and can be undone.</p><ol>{proposals}</ol><button type="button" data-page-action="apply_suggestions"{' disabled' if not suggestions else ''}>Apply replacement arrangement</button></details>
<div class="output-pages-layout"><aside aria-label="Output pages"><ol>{''.join(listing)}</ol></aside>{editor}</div>'''
    return _page('Arrange Pages', 'output-pages', body, project=model['project'], project_path=model['project_dir'])


def _preview_page(project: dict[str, Any], document=None, project_path=None) -> str:
    selected_profile = str(project.get("export", {}).get("wordpress_profile", "generic"))
    profile_options = "".join(
        f'<option value="{value}"{" selected" if value == selected_profile else ""}>{label}</option>'
        for value, label in (("generic", "Generic Gutenberg"), ("wsuwp", "WSUWP (approximate preview)"))
    )
    next_step = '<p class="button-row workflow-next"><a href="/export" role="button" class="review-approve">Continue to Export</a></p>'
    body = f'''<h1>Preview</h1>{_review_task_summary(document) if document is not None else ''}{next_step}
<div class="preview-toolbar">
<div class="segmented-control" role="group" aria-label="Preview mode"><button type="button" class="preview-mode" data-mode="semantic" aria-pressed="true">Semantic HTML</button><button type="button" class="secondary preview-mode" data-mode="wordpress" aria-pressed="false">WordPress Preview</button></div>
<label class="preview-profile" hidden>WordPress profile<select id="preview-profile">{profile_options}</select></label>
<div class="preview-controls" role="group" aria-label="Preview width"><button type="button" class="preview-width" data-width="desktop">Desktop</button><button type="button" class="secondary preview-width" data-width="mobile">Narrow</button></div></div>
<p id="preview-description">Semantic Preview shows the reviewed document independently of WordPress.</p>
<div class="preview-shell" id="preview-shell"><iframe title="Semantic HTML preview" sandbox="allow-same-origin" src="/api/preview/html"></iframe></div>{next_step}'''
    return _page("Preview", "preview", body, project=project, project_path=project_path)


def _export_review_state(model: dict[str, Any]) -> dict[str, Any]:
    document = model["document"]
    status = str(document.get("review", {}).get("status", "needs_review"))
    progress = model["progress"]
    unknown = sum(b.get('type') == 'unknown' for b in op.visible_walk(document.get('blocks', [])))
    blocked = status == "conversion_blocked"
    from .publication import readiness_findings
    publication_findings = readiness_findings(document)
    from .media_review_recovery import plan_recovery
    recovery = plan_recovery(model['project_dir'], document)
    recoverable_ids = {row['block_id'] for row in recovery['rows']}
    active_findings = [item for item in model['accessibility']['items'] if item['status'] == 'unresolved']
    diagnostics = [item for item in active_findings if item['category'] == 'diagnostics']
    banner = _status_banner(status, document.get('review', {}).get('issues', []), document) if blocked or diagnostics else ''
    readiness_items = f'<li>{unknown} unknown blocks remain</li>' if unknown else ''
    other_findings = [item for item in active_findings if item['category'] in {'links', 'headings', 'tables', 'images'}]
    if publication_findings:
        owners = {str(block['id']): (index, block) for index, block in enumerate(document.get('blocks', []), 1)}
        visuals = {str(visual['id']): visual for visual in document.get('review', {}).get('complex_visuals', [])}
        grouped_findings = {}
        for finding in publication_findings:
            key = ('visual', finding['visual_id']) if finding.get('visual_id') else ('block', finding['block_id']) if finding.get('block_id') else ('other', finding['message'])
            grouped_findings.setdefault(key, []).append(finding)
        for group in grouped_findings.values():
            finding = group[0]
            visual = visuals.get(str(finding.get('visual_id', '')))
            owner = owners.get(str(finding.get('block_id', '')))
            if visual:
                source = next((block for block in _walk(document.get('blocks', [])) if str(block.get('id')) == str(visual.get('source_block_id', ''))), None)
                preview = str((source or {}).get('alt') or (source or {}).get('caption') or visual.get('visual_type') or 'Image description')[:100]
                label = f"Description on source page {visual.get('source_page') or 'unknown'}: {preview}"
                target = '#visual-' + quote(str(visual['id']), safe='')
                guidance = visual_readiness(document, visual)
                reason = guidance['reason'] + ' ' + guidance['action']
            elif owner:
                position, block = owner
                preview = (_list_text(block) if block.get('type') == 'list' else str(block.get('content') or block.get('alt') or block.get('caption') or ''))[:100].replace('\n', ' ')
                label = f"Source page {block.get('provenance', {}).get('source_page') or 'unknown'} · Block {position}: {str(block.get('type', 'content')).replace('_', ' ')}"
                if preview:
                    label += ' — ' + preview
                target = '#block-' + quote(str(block['id']), safe='')
                reasons = {'block_review_pending': 'Review and approve this block.',
                           'block_approval_changed': 'This block changed since approval. Review and approve the saved content.',
                           'image_alternative_pending': 'Add alt text or mark this image decorative.',
                           'footnote_source_pending': 'Review the source body for this footnote.'}
                reason = ' '.join(dict.fromkeys(block_review_reason(block) if issue['code'] in {'legacy_approval_unverified', 'block_approval_changed', 'block_review_pending'} and block_review_reason(block) else reasons.get(issue['code'], issue['message']) for issue in group))
                if str(block['id']) in recoverable_ids:
                    reason = 'Recorded approval can be restored using the preview above.'
            else:
                readiness_items += '<li>' + html.escape(finding['message']) + '</li>'
                continue
            readiness_items += f'<li><a href="/structure{target}">{html.escape(label)}</a> — {html.escape(reason)}</li>'
    if other_findings:
        readiness_items += f'<li><a href="/accessibility">{len(other_findings)} Accessibility findings need attention</a></li>'
    images = [b for b in op.visible_walk(document.get('blocks', [])) if b.get('type') == 'image']
    unresolved = sum(not b.get('decorative') and not _wordpress_media_values(b)[0] for b in images)
    mapping_message = f'{unresolved} images still need WordPress URLs. Unmapped images appear as upload placeholders in Gutenberg and WXR.' if unresolved else 'All included images that need WordPress URLs are mapped.'
    missing_media = ''.join(f'<li><a href="/structure#block-{quote(str(b["id"]))}">Image on source page {html.escape(str(b.get("provenance", {}).get("source_page") or "unknown"))}</a>: {html.escape(str(b.get("alt") or b.get("caption") or b.get("src") or b["id"]))}</li>' for b in images if not b.get('decorative') and not _wordpress_media_values(b)[0])
    ready = not publication_findings
    recovery_html = ''
    if recovery['rows']:
        count = len(recovery['rows'])
        recovery_html = f'<p>{count} recorded image approvals are eligible for restoration after a media-only change.</p><button type="button" id="media-review-recovery-preview" class="neutral-action">Preview recorded approvals</button>'
    readiness = f'''<section aria-labelledby="readiness-heading"><h2 id="readiness-heading" tabindex="-1">Export readiness</h2>
{recovery_html}<div id="media-review-recovery-result" role="status" aria-live="polite"></div><div id="media-review-recovery-selection" hidden></div>
<p>{('Required content reviews are complete.' if ready else 'Restore recorded approvals or review the pending content below before exporting.' if recoverable_ids else 'Resolve the required content reviews below before exporting.')}</p>
{f'<ul>{readiness_items}</ul>' if readiness_items else ''}<p>{mapping_message}</p>
<p id="readiness-mapping-feedback" hidden><a href="#media-mapping-result">View media matching results</a></p>
<p><a href="#content-export-heading">Continue to Export and copy content</a></p></section>'''
    return {
        'html': _review_task_summary(document, progress) + banner + readiness,
        'publication_ready': ready,
        'mapping_message': mapping_message,
        'unmapped_html': '<p>These images need URLs before pasting content into WordPress:</p><ul>' + missing_media + '</ul>' if missing_media else '',
        'announcement': 'Ready to export.' if ready else 'Review is required before exporting. Follow the links in Export readiness.',
    }


def _export_page(model: dict[str, Any]) -> str:
    document = model['document']
    blocked = document.get('review', {}).get('status') == 'conversion_blocked'
    state = _export_review_state(model)
    prefix = html.escape(media_prefix(document), quote=True)
    images = [b for b in op.visible_walk(document.get('blocks', [])) if b.get('type') == 'image']
    settings = document.get('publication', {})
    from .exporters.common import publication_document
    page_title = html.escape(publication_document(document).get('publication_title', ''), quote=True)
    mapping_message = state['mapping_message']
    mapping_issues = '<div id="unmapped-media">' + state['unmapped_html'] + '</div>'
    mapping_csv_available = (Path(model['project_dir']) / 'output/wordpress/reports/media-mapping.csv').is_file()
    body = f'''<h1>Export</h1><div id="export-review-state">{state["html"]}</div>
<section aria-labelledby="media-export-heading"><h2 id="media-export-heading">1. Prepare images in this project</h2>
<p>{len(images)} included images. Choose a prefix before uploading them; original extracted files keep their names.</p>
<form id="media-export-form"><label>Image filename prefix<input name="image_prefix" value="{prefix}" placeholder="citi-training-" required aria-describedby="image-prefix-help"></label>
<small id="image-prefix-help">For example: citi-training-image1.png, citi-training-image2.png. Leave the document-based prefix or choose your own. Changing it after upload requires matching the uploaded filenames manually.</small>
<div class="button-row"><button type="submit" class="review-approve"{' disabled' if blocked else ''}>Prepare images ZIP and mapping CSV</button>
<button type="button" class="neutral-action" id="media-export-undo"{' disabled' if blocked else ''}>Undo last change</button></div></form><div id="media-export-result" role="status" aria-live="polite"></div></section>
<section aria-labelledby="media-mapping-heading"><h2 id="media-mapping-heading">2. Map WordPress media</h2>
<p id="media-mapping-status" role="status" aria-live="polite">{mapping_message}</p>{mapping_issues}
<p>WordPress renamed files or XML left images unmatched? Map their URLs with the CSV.</p><div class="button-row"><button type="button" id="open-manual-media" class="neutral-action" aria-controls="manual-media-tools">Use manual CSV mapping</button></div>
<ol><li>Open the project output folder and unzip output/wordpress/media-upload.zip.</li><li>Upload the images to your WordPress Media Library.</li><li>In WordPress, choose Tools &gt; Export &gt; Media and download the XML file.</li><li>Choose that XML file below and select Match WordPress media.</li><li>Review any unmatched images listed in the result, then export your content in step 3.</li></ol><p><a href="/help#wordpress-media">Matching rules and WordPress import help</a>.</p>
<form id="media-wxr-form" class="inline-file-form"><label>WordPress media export<input type="file" name="media_wxr" accept=".xml,application/xml,text/xml" required></label>
<button type="submit" class="review-approve">Match WordPress media</button><div><label><input id="refresh-existing-media" type="checkbox" name="refresh_existing" aria-describedby="refresh-existing-media-help"> These are the same reviewed images; refresh existing attachment IDs</label><small id="refresh-existing-media-help">Choose the XML first, then check this option for re-uploaded unchanged images. Choosing another XML clears this confirmation. Only unique exact filenames with the same saved URL can refresh. XML cannot verify image contents. If images changed, review their alt text and descriptions first; use manual CSV mapping for different URLs.</small><p id="media-refresh-selection-notice" role="status" aria-live="polite" hidden></p></div></form>
<details id="manual-media-tools"><summary>Map images manually with a CSV</summary><h3 id="manual-media-heading" tabindex="-1">Manual media mapping</h3><p id="manual-media-notice" role="status" aria-live="polite">Prepare the images ZIP and mapping CSV in step 1. Fill in wordpress_url and optionally wordpress_attachment_id for each image; keep block_id and asset_filename unchanged. Use full WordPress URLs and verify the correct image before importing. <a href="/help#wordpress-media">Manual mapping help</a>.</p><p><button type="button" class="neutral-action" data-open-project-output>Open output folder</button></p><details><summary>Optional browser copy of mapping CSV</summary><p>The original CSV is saved in output/wordpress/reports/. This makes an extra copy wherever your browser saves downloads.</p><p><a id="manual-media-download" href="/download/output/wordpress/reports/media-mapping.csv" download{"" if mapping_csv_available else " hidden"}>Save browser copy of current mapping CSV</a></p></details>
<form id="media-mapping-form" class="inline-file-form"><label>Completed media mapping CSV<input type="file" name="mapping" accept=".csv,text/csv" required></label>
<button type="submit" class="review-approve">Import media mapping</button></form></details><section id="media-mapping-result" tabindex="-1" hidden aria-label="Media mapping results"><p id="media-mapping-announcement" role="status" aria-live="polite"></p><div id="media-mapping-details"></div></section></section>
<section aria-labelledby="content-export-heading"><h2 id="content-export-heading">3. Export and copy content</h2><p>This exports the whole reviewed document as one web page. Use <a href="/output-pages">Arrange Pages</a> only when arranging several pages.</p>
<form id="export-form" data-conversion-blocked="{str(blocked).lower()}" data-publication-ready="{str(state["publication_ready"]).lower()}"><div class="form-grid"><label>Format<select name="target"><option value="html">Semantic HTML</option><option value="gutenberg">Gutenberg</option><option value="wordpress-xml">WXR/XML</option></select></label>
<label>WordPress profile<select name="profile"><option value="generic">Generic Gutenberg</option><option value="wsuwp">WSUWP</option></select></label>
<label>Content type<select name="post_type"><option value="page">Page</option><option value="post">Post</option></select></label></div><label><input type="checkbox" name="wrap_in_section" value="true"> Wrap content in a WSU Section block</label><p>WordPress exports are created as Drafts.</p>
<label>Page title<input id="export-page-title" value="{page_title}" readonly></label>
<label><input type="checkbox" name="title_in_template"{' checked' if settings.get('title_in_template', True) else ''}> My WordPress template supplies the page title (H1)</label><p><a href="/help#title-export">Title export help</a></p>
<label>Body headings<select name="heading_style"><option value="sections"{' selected' if settings.get('heading_style', 'nested') == 'sections' else ''}>H2 section headings</option><option value="nested"{' selected' if settings.get('heading_style', 'nested') == 'nested' else ''}>Keep nested headings without skipped levels</option></select></label>
<div class="button-row workflow-next"><div class="copy-title-row"><button type="button" id="copy-page-title" class="neutral-action">Copy page title</button><span id="copy-page-title-status" role="status" aria-live="polite"></span></div><button type="submit" class="review-approve" aria-describedby="export-availability"{(' disabled' if not state['publication_ready'] else '')}>Export reviewed document</button></div><p id="export-availability" role="status" aria-live="polite"><span id="export-availability-message">{('Ready to export.' if state['publication_ready'] else 'Export is unavailable until the required content reviews are resolved.')}</span> <a id="export-readiness-link" href="#readiness-heading">View Export readiness</a></p><p class="blocked-export-note"{"" if blocked else " hidden"}>Conversion-blocked projects may export diagnostic HTML only.</p></form><div id="export-result" role="status" aria-live="polite"></div></section>'''
    if not images:
        start = body.index('<section aria-labelledby="media-export-heading">')
        end = body.index('<section aria-labelledby="content-export-heading">')
        body = body[:start] + '<p>No included images. Image drafting and WordPress media mapping are not needed.</p>' + body[end:]
        body = body.replace('3. Export and copy content', 'Export and copy content')
    return _page("Export", "export", body, project=model["project"], project_path=model["project_dir"])


def create_app(config: WebAppConfig, *, lifecycle: OwnedServerLifecycle | None = None):
    try:
        from fastapi import Cookie, FastAPI, Header, HTTPException
        from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
        from fastapi.staticfiles import StaticFiles
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install PDF to Web application dependencies first") from exc

    app = FastAPI(title=APP_NAME)
    lifecycle = lifecycle or OwnedServerLifecycle()
    active_project = config.project.expanduser().resolve() if config.project else None
    selections: dict[str, ProjectSelection] = {}
    destinations: dict[str, Path] = {}
    recent = load_recent_projects(config.recent_store)

    def issue(path: Path) -> ProjectSelection:
        load_project(path)
        selection = ProjectSelection(secrets.token_urlsafe(32), path.resolve())
        selections[selection.token] = selection
        return selection

    def remember(path: Path) -> None:
        nonlocal recent
        recent = remember_project(config.recent_store, path, recent)

    def remember_warning(path: Path) -> str | None:
        try:
            remember(path)
        except (OSError, PdfToWebError):
            return f'Your project files are saved at {path}, but the Recent projects list could not be updated at {config.recent_store}. Open the project folder directly next time.'
        return None

    startup_warning = None
    for path in reversed(config.recent_projects):
        if (path.expanduser().resolve() / "project.json").is_file():
            startup_warning = remember_warning(path) or startup_warning
    if active_project:
        startup_warning = remember_warning(active_project) or startup_warning

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
    app.add_middleware(LifecycleMiddleware, lifecycle=lifecycle)

    draft_tasks = set()
    draft_semaphore = asyncio.Semaphore(2)
    draft_epoch = 0

    def cancel_draft_jobs():
        nonlocal draft_epoch
        draft_epoch += 1
        if active_project and review_path(active_project).is_file():
            document = ensure_review_document(active_project)
            changed = False
            for entry in drafts.state(document)['requests'].values():
                if entry['status'] in {'requested', 'generating'} and entry['provider'] != 'manual':
                    entry.update(status='cancelled', updated_at=utc_now())
                    changed = True
            if changed:
                save_review_document(active_project, document, snapshot=False)

    # An interrupted server never silently resumes transmissions. Retry is explicit.
    if active_project:
        cancel_draft_jobs()

    async def generate_one(root, epoch, provider, entry):
        async with draft_semaphore:
            if epoch != draft_epoch or active_project != root or not drafts.begin(root, entry):
                return
            try:
                value = await asyncio.to_thread(provider.generate, entry, drafts.confined(root, entry['asset_path']))
                if epoch == draft_epoch and active_project == root:
                    drafts.complete(root, entry, value=value)
            except Exception:
                if epoch == draft_epoch and active_project == root:
                    drafts.complete(root, entry, error=True)

    @app.get('/api/image-drafts/asset')
    async def draft_asset(path: str, session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        root = current()
        try:
            if not path.startswith(('extraction/raw/', 'extraction/assets/images/')):
                raise ValueError('Unsupported asset path')
            return FileResponse(drafts.confined(root, path), headers={'Cache-Control': 'private, no-store'})
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get('/api/image-drafts')
    async def draft_status(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        root = current()
        document = ensure_review_document(root)
        store = drafts.state(document)
        entries = []
        for request_id in store['active'].values():
            entry = store['requests'][request_id]
            fields = {}
            try:
                block = drafts.image(document, entry['block_id'])
                fields = {key: block.get(key) or '' for key in ('alt', 'caption')}
                fields['long_description'] = (drafts.visual_for(document, block) or {}).get('accessibility', {}).get('long_description') or ''
            except (KeyError, ValueError):
                pass
            entries.append({'block_id': entry['block_id'], 'request_id': request_id,
                            'status': 'stale' if drafts.stale(root, document, entry) else entry['status'],
                            'error': entry.get('error'), 'image_fields': fields})
        return {'document_id': document['output_pages']['project_id'], 'entries': entries}

    @app.post('/api/image-drafts/{action}')
    async def draft_action(action: str, request: Request, session: str | None = Cookie(default=None, alias=SESSION_COOKIE), csrf: str | None = Header(default=None, alias=CSRF_HEADER)):
        require_change(request, session, csrf)
        require_editable_document()
        root = current()
        try:
            raw = await request.body()
            if len(raw) > 4 * 1024 * 1024:
                raise ValueError('Draft request exceeds 4 MiB')
            data = json.loads(raw)
            document = ensure_review_document(root)
            if data.get('document_id') != document['output_pages']['project_id']:
                raise ValueError('Project changed; reload this screen')
            if action in {'populate', 'settings', 'associate', 'edit', 'apply', 'reject', 'cancel'}:
                drafts.mutate(root, action, data)
                return {'status': 'ok'}
            if action == 'import':
                result = drafts.import_response(root, data.get('response'), commit=data.get('commit') is True)
                return {'status': 'ok', 'valid_count': len(result['valid']), 'findings': result['findings']}
            if action in {'export', 'generate', 'preflight'}:
                ids = data.get('block_ids')
                provider_name = data.get('provider', 'ollama-local')
                if action == 'export':
                    output_locations(root)
                    entries = drafts.prepare(root, ids, regenerate=data.get('regenerate') is True)
                    path = drafts.exchange_package(root, entries)
                    relative = str(path.relative_to(root))
                    return {'status': 'ok', **output_locations(root), 'url': '/download/' + quote(relative), 'filename': path.name, 'saved_path': str(path), 'relative_path': relative}
                if provider_name not in {'ollama-local', 'openai'}:
                    raise ValueError('Unknown generation provider')
                provider = drafts.OpenAIProvider() if provider_name == 'openai' else drafts.OllamaProvider(data.get('model', ''))
                if not isinstance(ids, list) or not ids or len(ids) > 100 or len(set(ids)) != len(ids):
                    raise ValueError('Select 1–100 distinct image blocks')
                contexts = [drafts.current_identity(root, document, i) for i in ids]
                consent_hash = drafts.digest({'requests': [{**identity, 'context': ctx} for identity, asset, ctx in contexts], 'provider': provider.name, 'model': provider.model, 'regenerate': bool(data.get('regenerate'))})
                if action == 'preflight':
                    return {'status': 'ok', 'consent_hash': consent_hash, 'requests': [{**identity, 'image_path': str(asset.relative_to(root)), 'context': ctx} for identity, asset, ctx in contexts]}
                if provider.name == 'openai' and (data.get('authorize_cloud') is not True or data.get('consent_hash') != consent_hash):
                    raise ValueError('Review the selected images/context and explicitly authorize this OpenAI request')
                if sum(not task.done() for task in draft_tasks) + len(ids) > 100:
                    raise ValueError('Generation queue is full; wait for results or cancel requests')
                entries = drafts.prepare(root, ids, provider.name, provider.model, bool(data.get('regenerate')))
                queued = 0
                for entry in entries:
                    if entry['status'] == 'requested':
                        queued += 1
                        if not lifecycle.start_work():
                            raise ValueError('PDF to Web is quitting; generation cannot start.')
                        task = asyncio.create_task(generate_one(root, draft_epoch, provider, entry))
                        draft_tasks.add(task)
                        task.add_done_callback(draft_tasks.discard)
                        task.add_done_callback(lambda _task: lifecycle.finish_work())
                return {'status': 'ok', 'queued': queued, 'preserved': len(entries) - queued}
            raise ValueError('Unsupported draft action')
        except Exception as exc:
            return error_response(exc)

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "app": APP_NAME}

    @app.get('/api/lifecycle')
    async def lifecycle_status(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        return {'status': 'ok', **lifecycle.status()}

    @app.post('/api/quit')
    async def quit_app(request: Request, session: str | None = Cookie(default=None, alias=SESSION_COOKIE), csrf: str | None = Header(default=None, alias=CSRF_HEADER)):
        require_change(request, session, csrf)
        from starlette.background import BackgroundTask
        try:
            data = await request.json()
            if not isinstance(data, dict) or data.get('confirm') is not True:
                raise ValueError('Confirm Quit after checking unsaved edits in all tabs.')
            lifecycle.prepare_quit()
        except QuitUnavailable as exc:
            return error_response(exc, status=409)
        except ValueError as exc:
            return error_response(exc)
        return JSONResponse({'status': 'ok', 'state': 'stopping'}, background=BackgroundTask(lifecycle.stop))

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
        return _projects_page(config, project_selections, active_project, startup_warning)

    @app.post("/api/picker/project")
    async def pick_project(request: Request, session: str | None = Cookie(default=None, alias=SESSION_COOKIE), csrf: str | None = Header(default=None, alias=CSRF_HEADER)):
        require_change(request, session, csrf)
        try:
            selection = issue(choose_project_folder())
            return {"status": "ok", "selection": selection.public()}
        except Exception as exc:
            return error_response(exc)

    @app.post('/api/picker/destination')
    async def pick_destination(request: Request, session: str | None = Cookie(default=None, alias=SESSION_COOKIE), csrf: str | None = Header(default=None, alias=CSRF_HEADER)):
        require_change(request, session, csrf)
        try:
            path = choose_project_folder(destination=True).expanduser().resolve()
            if not path.is_dir():
                raise ValueError('Choose an existing destination folder.')
            validate_project_destination(path)
            token = secrets.token_urlsafe(32)
            destinations[token] = path
            return {'status': 'ok', 'destination': {'token': token, 'path': str(path), 'has_existing_files': any(path.iterdir())}}
        except PermissionError:
            return error_response(ValueError('Cannot read this destination folder. Check its permissions or choose a different folder.'))
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
            ready = (selection.path / 'review/current.json').is_file() or (selection.path / 'extraction/normalized/document.json').is_file()
            if ready:
                ensure_review_document(selection.path)
            warning = remember_warning(selection.path)
            cancel_draft_jobs()
            active_project = selection.path
            return {"status": "ok", "project": {"name": active_project.name, "path": str(active_project)}, "next": '/document' if ready else '/', "warning": warning}
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
        created_here = False
        try:
            data = await request.json()
            title = str(data.get("title", "")).strip()
            if not title:
                raise ValueError("Enter a project name.")
            if 'destination_path' in data or 'project_path' in data:
                raise ValueError('Select the destination with Choose destination folder; a typed path is not accepted.')
            mode = data.get('destination_mode', 'default')
            if mode == 'chosen':
                project_dir = destinations.get(str(data.get('destination_token', '')))
                if project_dir is None:
                    raise ValueError('Choose a destination folder again; its selection is missing or expired. No default folder was used.')
            elif mode == 'default' and not data.get('destination_token'):
                project_dir = config.projects_root.expanduser().resolve() / slugify(title)
            elif mode == 'default':
                # UI clears the token when explicitly switching back to default.
                raise ValueError('Destination choice is inconsistent. Select the destination again.')
            else:
                raise ValueError('Choose Default location or Folder I choose.')
            validate_project_destination(project_dir)
            source_pdf = choose_pdf_file()
            if not source_pdf.is_file() or source_pdf.suffix.lower() != '.pdf':
                raise ValueError('Choose a readable PDF file. No project files were created.')
            create_project(project_dir, title)
            created_here = True
            import_pdf(project_dir, source_pdf)
            run_extraction(project_dir, False)
            normalize_project(project_dir)
            ensure_review_document(project_dir)
            warning = remember_warning(project_dir)
            cancel_draft_jobs()
            active_project = project_dir
            return {"status": "ok", "project": {"name": project_dir.name, "path": str(project_dir)}, "warning": warning}
        except Exception as exc:
            if isinstance(exc, PermissionError):
                message = f'Cannot write project files at {project_dir or "the selected folder"}. Check folder permissions or choose a different destination.'
            else:
                message = str(exc)
            result = {'status': 'error', 'error': message}
            if created_here and project_dir is not None:
                try:
                    project = load_project(project_dir)
                    project['extraction']['last_error'] = message
                    save_project(project_dir, project)
                    remember(project_dir)
                except (OSError, PdfToWebError):
                    pass
                result['error'] += f' Project files were retained at {project_dir}. The previous project remains open.'
                result['project'] = {'name': project_dir.name, 'path': str(project_dir)}
            return JSONResponse(result, status_code=400)

    @app.get('/help', response_class=HTMLResponse)
    async def help_page(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        ready = active_project is not None and ((active_project / 'review/current.json').is_file() or (active_project / 'extraction/normalized/document.json').is_file())
        return _help_page(selected=ready, project=load_project(active_project) if active_project else None, project_path=active_project)

    @app.get("/document", response_class=HTMLResponse)
    async def document_page(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        return _document_page(document_model(current()))

    @app.get("/structure", response_class=HTMLResponse)
    async def structure_page(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        return _structure_page(document_model(current()))

    @app.get("/accessibility", response_class=HTMLResponse)
    async def accessibility_page(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        return _accessibility_page(document_model(current()))

    @app.get('/output-pages', response_class=HTMLResponse)
    async def output_pages_page(page_id: str | None = None, session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        return _output_pages_page(document_model(current()), page_id)

    @app.get('/output-pages-contents', response_class=HTMLResponse)
    async def output_pages_contents(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        document = ensure_review_document(current())
        errors = op.validate(document)
        if errors:
            return HTMLResponse('<p>' + html.escape('; '.join(errors)) + '</p>', status_code=400)
        content = contents_html(document)
        content = content.replace('href="', 'href="/output-preview/')
        return HTMLResponse(content)

    @app.post('/api/output-pages/{action}')
    async def output_pages_action(action: str, request: Request, session: str | None = Cookie(default=None, alias=SESSION_COOKIE), csrf: str | None = Header(default=None, alias=CSRF_HEADER)):
        require_change(request, session, csrf)
        require_editable_document()
        try:
            data = await request.json()
            if action == 'export':
                preserve_previous_outputs(current())
                paths = export_pages(current(), data.get('page_id'), data.get('profile'))
                return {'status': 'ok', **output_locations(current()), 'downloads': [{'path': str(p.relative_to(current())), 'url': '/download/' + quote(str(p.relative_to(current())), safe='/')} for p in paths]}
            if action == 'undo':
                undo_last(current())
                cancel_draft_jobs()
                restored = ensure_review_document(current())
                selected = data.get('page_id')
                if not op.page_by_id(restored, selected):
                    selected = op.pages(restored)[0]['id'] if op.pages(restored) else None
            else:
                selected = update_output_pages(current(), action, data)
            return {'status': 'ok', 'page_id': selected}
        except (ValueError, KeyError, PdfToWebError, OSError) as exc:
            return error_response(exc)

    @app.get('/output-preview/{slug}.html', response_class=HTMLResponse)
    async def output_preview(slug: str, mode: str = 'semantic', profile: str = 'generic', session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        document = ensure_review_document(current())
        p = next((p for p in op.pages(document) if p['slug'] == slug), None)
        if p is None:
            raise HTTPException(status_code=404, detail='Output page was not found')
        if profile not in {'generic', 'wsuwp'}:
            raise HTTPException(status_code=400, detail='Unsupported profile')
        projected = op.page_document(document, p['id'])
        # Same page projection and serializers; preview assets use confined local routes.
        projected = _document_with_local_preview_media(projected, semantic=mode != 'wordpress')
        for b in op.walk(projected['blocks']):
            if b.get('type') == 'image' and b.get('wordpress_url', '').startswith(('/api/preview/images/', '/api/image-drafts/asset?')):
                b['src'] = b['wordpress_url']
        config_data = load_project(current()).get('export', {})
        if mode == 'wordpress':
            try:
                markup = gutenberg_exporter.render_document(projected, profile, config_data)
                content = render_gutenberg_preview(markup).html
            except Exception as exc:
                content = '<p role="alert">' + html.escape(str(exc)) + '</p>'
        else:
            content = html_exporter.render_document(projected)
        return HTMLResponse(content, headers={'Content-Security-Policy': "default-src 'none'; img-src 'self' data: http: https:; style-src 'self' 'unsafe-inline'; frame-ancestors 'self'"})

    @app.get("/preview", response_class=HTMLResponse)
    async def preview_page(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        return _preview_page(load_project(current()), ensure_review_document(current()), current())

    @app.get("/export", response_class=HTMLResponse)
    async def export_page(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        return _export_page(document_model(current()))

    @app.get("/download/{relative_path:path}")
    async def download_export(relative_path: str, session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        relative = Path(relative_path)
        if not relative.parts or relative.parts[0] != "output":
            raise HTTPException(status_code=404, detail="Export file is unavailable")
        path = safe_project_file(current(), relative_path)
        if not path.is_file():
            raise HTTPException(status_code=404, detail="Export file is unavailable")
        canonical = path.relative_to(current().resolve())
        if not canonical.parts or canonical.parts[0] != 'output' or canonical.parts[1:2] == ('history',):
            raise HTTPException(status_code=404, detail="Export file is unavailable")
        from .publication import require_current_artifact
        try:
            require_current_artifact(current(), str(canonical))
        except PdfToWebError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return FileResponse(path, filename=path.name, content_disposition_type="attachment", headers={'Cache-Control': 'private, no-store'})

    @app.post('/api/output-folder/open')
    async def open_saved_outputs(request: Request, session: str | None = Cookie(default=None, alias=SESSION_COOKIE), csrf: str | None = Header(default=None, alias=CSRF_HEADER)):
        require_change(request, session, csrf)
        root = current()
        try:
            data = await request.json()
            if data.get('project_root') != str(root.resolve()):
                raise ValueError('The active project changed. Reload this page before opening its outputs.')
            folder = open_output_folder(root)
            return {'status': 'ok', 'output_root': str(folder)}
        except Exception as exc:
            return error_response(exc)

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
            headers={"Cache-Control": "private, no-store"},
        )

    @app.get("/source-page/{page}.png")
    async def source_page(page: int, session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        try:
            return FileResponse(
                render_source_page(current(), page),
                media_type="image/png",
                headers={"Cache-Control": "private, no-store"},
            )
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
        model = document_model(current())
        model.pop("project_dir", None)
        return model

    @app.get("/api/accessibility/preview", response_class=HTMLResponse)
    async def accessibility_preview(expected_review_token: str | None = None, session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        saved = ensure_review_document(current())
        from .image_review import review_token
        token = review_token(saved)
        if expected_review_token is not None and expected_review_token != token:
            return HTMLResponse('<!doctype html><html><head><meta name="pdf-to-web-scan-error" content="The saved project changed after this page opened. Reload Accessibility to check the current snapshot."></head><body></body></html>', status_code=409, headers={'Cache-Control': 'no-store'})
        document = _document_with_local_preview_media(saved, semantic=True)
        metadata = f'<meta name="pdf-to-web-review-token" content="{token}"><script src="/static/axe.min.js"></script></head>'
        return HTMLResponse(html_exporter.render_document(document, annotate_blocks=True).replace("</head>", metadata), headers={
            "Cache-Control": "no-store",
            "Content-Security-Policy": "default-src 'none'; script-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; frame-ancestors 'self'"
        })

    @app.get("/api/preview/html", response_class=HTMLResponse)
    async def preview_html(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        projected = _document_with_local_preview_media(ensure_review_document(current()), semantic=True)
        return HTMLResponse(
            html_exporter.render_document(projected),
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
            markup = gutenberg_exporter.render_document(
                _document_with_local_preview_media(document), profile, config_data
            )
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
            document = update_block(current(), block_id, await request.json())
            from .review_state import _find_location
            block = _find_location(document.get('blocks', []), block_id)[2]
            return {"status": "ok", "block_status": block.get('review', {}).get('status'), "progress": review_progress(document)}
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
            elif action == "save-and-approve":
                document = update_block(current(), block_id, data, approve_after_save=True)
                return {"status": "ok", "block_status": "approved", "progress": review_progress(document)}
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
            cancel_draft_jobs()
            return {"status": "ok"}
        except Exception as exc:
            return error_response(exc)

    @app.post("/api/complex-visuals/{visual_id}")
    async def edit_complex_visual(visual_id: str, request: Request, session: str | None = Cookie(default=None, alias=SESSION_COOKIE), csrf: str | None = Header(default=None, alias=CSRF_HEADER)):
        require_change(request, session, csrf)
        if ensure_review_document(current()).get("review", {}).get("status") == "conversion_blocked":
            return error_response(ValueError("Complex visual editing is unavailable while conversion is blocked"), 409)
        try:
            document = update_complex_visual(current(), visual_id, await request.json())
            visual = next(v for v in document['review']['complex_visuals'] if str(v['id']) == visual_id)
            readiness = visual_readiness(document, visual)
            block = next((b for b in drafts._walk(document.get('blocks', [])) if str(b.get('id')) == str(visual.get('source_block_id'))), None)
            return {"status": "ok", 'reload_required': bool(block and len(descriptions_for(document, block)) > 1), 'visual': {**readiness, 'status': visual.get('status'), 'context': _description_context(document, visual)}, 'block_status': block.get('review', {}).get('status') if block else None,
                    'review_token': review_token(document), 'completion_html': _structure_completion(document), 'progress': review_progress(document), 'review_summary_html': _review_task_summary(document)}
        except Exception as exc:
            return error_response(exc)

    @app.post('/api/accessibility/bulk-review')
    async def bulk_accessibility_review(request: Request, session: str | None = Cookie(default=None, alias=SESSION_COOKIE), csrf: str | None = Header(default=None, alias=CSRF_HEADER)):
        require_change(request, session, csrf)
        require_editable_document()
        try:
            from .bulk_review import apply_batch
            document, count = apply_batch(current(), await request.json())
            return {'status': 'ok', 'applied': count, 'progress': review_progress(document)}
        except Exception as exc:
            return error_response(exc)

    @app.post("/api/accessibility/{item_id:path}")
    async def accessibility_decision(item_id: str, request: Request, session: str | None = Cookie(default=None, alias=SESSION_COOKIE), csrf: str | None = Header(default=None, alias=CSRF_HEADER)):
        require_change(request, session, csrf)
        require_editable_document()
        try:
            data = await request.json()
            update_accessibility_decision(
                current(), item_id, str(data.get("status", "unresolved")), str(data.get("note", ""))
            )
            return {"status": "ok", "accessibility": assess_document(ensure_review_document(current()))["summary"]}
        except Exception as exc:
            return error_response(exc)

    @app.post("/api/accessibility-report")
    async def accessibility_report(request: Request, session: str | None = Cookie(default=None, alias=SESSION_COOKIE), csrf: str | None = Header(default=None, alias=CSRF_HEADER)):
        require_change(request, session, csrf)
        try:
            preserve_previous_outputs(current())
            paths = write_reports(current(), ensure_review_document(current()))
            files = [str(path.relative_to(current())) for path in paths]
            return {
                "status": "ok",
                **output_locations(current()),
                "files": files,
                "downloads": [{"path": path, "url": f"/download/{quote(path, safe='/')}"} for path in files],
            }
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
            document = ensure_review_document(current())
            from .publication import require_ready
            require_ready(document)
            publication = document.get('publication', {}).copy()
            if 'heading_style' in data:
                if data['heading_style'] not in {'sections', 'nested'}:
                    raise ValueError('Choose H2 sections or nested headings')
                publication['heading_style'] = data['heading_style']
            if 'title_in_template' in data:
                publication['title_in_template'] = str(data['title_in_template']).lower() in {'true', 'on', '1'}
            if publication != document.get('publication', {}):
                require_editable_document()
                document['publication'] = publication
                save_review_document(current(), document)
            project = load_project(current())
            project.setdefault("export", {})["wordpress_profile"] = profile
            wordpress = project["export"].setdefault("wordpress", {})
            wordpress.update({"post_type": post_type, "status": "draft"})
            project["export"]["wrap_in_section"] = str(data.get("wrap_in_section", "")).lower() == "true"
            save_project(current(), project)
            preserve_previous_outputs(current())
            paths = export_project(current(), target, profile)
            files = [str(path.relative_to(current())) for path in paths]
            media_manifest_path = current() / "output" / "wordpress" / "reports" / "media-manifest.json"
            media = None
            if target in {"gutenberg", "wordpress-xml"} and media_manifest_path.is_file():
                media = json.loads(media_manifest_path.read_text(encoding="utf-8"))["summary"]
            return {
                "status": "ok",
                **output_locations(current()),
                "files": files,
                "downloads": [
                    {"path": path, "url": f"/download/{quote(path, safe='/')}", 'kind': 'template_body' if path.endswith('.body.html') else 'file'}
                    for path in files
                ],
                "project_root": str(current()),
                "media": media,
                "review": ensure_review_document(current()).get("review", {}),
            }
        except Exception as exc:
            return error_response(exc)

    @app.get('/api/media-review-recovery')
    async def preview_media_review_recovery(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
        require_session(session)
        try:
            from .media_review_recovery import plan_recovery
            document = json.loads(review_path(current()).read_bytes())
            plan = plan_recovery(current(), document)
            return {**plan, 'rows': [{key: row[key] for key in ('block_id', 'source_page', 'alt', 'caption', 'approved_at')} for row in plan['rows']]}
        except (ValueError, PdfToWebError, OSError) as exc:
            return error_response(exc)

    @app.post('/api/media-review-recovery')
    async def restore_media_review_recovery(request: Request, session: str | None = Cookie(default=None, alias=SESSION_COOKIE), csrf: str | None = Header(default=None, alias=CSRF_HEADER)):
        require_change(request, session, csrf)
        try:
            from .media_review_recovery import apply_recovery
            document = json.loads(review_path(current()).read_bytes())
            if document.get('review', {}).get('status') == 'conversion_blocked':
                raise PdfToWebError('Conversion-blocked projects cannot restore approvals.')
            _, restored = apply_recovery(current(), await request.json())
            model = document_model(current())
            images = [block for block in op.visible_walk(model['document'].get('blocks', [])) if block.get('type') == 'image']
            remaining = sum(not block.get('decorative') and not _wordpress_media_values(block)[0] for block in images)
            return {'status': 'ok', 'restored': restored, 'remaining': remaining,
                    'export_state': _export_review_state(model)}
        except (ValueError, PdfToWebError, OSError) as exc:
            return error_response(exc)

    @app.post('/api/media-export')
    async def prepare_media(request: Request, session: str | None = Cookie(default=None, alias=SESSION_COOKIE), csrf: str | None = Header(default=None, alias=CSRF_HEADER)):
        require_change(request, session, csrf)
        require_editable_document()
        try:
            data = await request.json()
            prefix = validate_media_prefix(str(data.get('image_prefix') or ''))
            document = ensure_review_document(current())
            previous = document.get('media_export', {}).copy()
            document.setdefault('media_export', {})['image_prefix'] = prefix
            preserve_previous_outputs(current())
            paths, manifest = _write_media_manifest(current(), document)
            if document['media_export'] != previous:
                save_review_document(current(), document)
            downloads = [p for p in paths if p.suffix in {'.zip', '.csv'}]
            return {'status': 'ok', **output_locations(current()), 'image_prefix': prefix, 'media': manifest['summary'], 'downloads': [
                {'path': str(p.relative_to(current())), 'url': '/download/' + quote(str(p.relative_to(current())), safe='/')}
                for p in downloads]}
        except (ValueError, PdfToWebError, OSError) as exc:
            return error_response(exc)

    @app.post('/api/media-export/undo')
    async def undo_media(request: Request, session: str | None = Cookie(default=None, alias=SESSION_COOKIE), csrf: str | None = Header(default=None, alias=CSRF_HEADER)):
        require_change(request, session, csrf)
        require_editable_document()
        try:
            undo_last(current())
            cancel_draft_jobs()
            model = document_model(current())
            document = model['document']
            images = [b for b in op.visible_walk(document.get('blocks', [])) if b.get('type') == 'image']
            remaining = sum(not b.get('decorative') and not _wordpress_media_values(b)[0] for b in images)
            from .exporters.common import publication_document
            return {'status': 'ok', 'image_prefix': media_prefix(document), 'remaining': remaining,
                    'publication': document.get('publication', {}),
                    'page_title': publication_document(document).get('publication_title', ''),
                    'export_state': _export_review_state(model)}
        except (ValueError, PdfToWebError, OSError) as exc:
            return error_response(exc)

    @app.post("/api/media-mapping")
    async def import_media_mapping(request: Request, session: str | None = Cookie(default=None, alias=SESSION_COOKIE), csrf: str | None = Header(default=None, alias=CSRF_HEADER)):
        require_change(request, session, csrf)
        require_editable_document()
        try:
            data = await request.json()
            csv_text = str(data.get("csv") or "")
            if not csv_text or len(csv_text.encode("utf-8")) > 2_000_000:
                raise ValueError("Choose a media mapping CSV smaller than 2 MB")
            result = apply_media_mapping(current(), csv_text)
            return {"status": "ok", **result, "export_state": _export_review_state(document_model(current()))}
        except Exception as exc:
            return error_response(exc)

    @app.post("/api/media-mapping-wxr")
    async def import_media_mapping_wxr(request: Request, session: str | None = Cookie(default=None, alias=SESSION_COOKIE), csrf: str | None = Header(default=None, alias=CSRF_HEADER)):
        require_change(request, session, csrf)
        require_editable_document()
        try:
            data = await request.json()
            xml_text = str(data.get("xml") or "")
            if not xml_text or len(xml_text.encode("utf-8")) > 20_000_000:
                raise ValueError("Choose a WordPress media XML file smaller than 20 MB")
            refresh_existing = data.get('refresh_existing', False)
            if not isinstance(refresh_existing, bool):
                raise ValueError('The existing-media refresh choice must be true or false')
            result = apply_wordpress_media_export(current(), xml_text, refresh_existing=refresh_existing)
            return {"status": "ok", **result, "export_state": _export_review_state(document_model(current()))}
        except Exception as exc:
            return error_response(exc)

    app.state.project_selections = selections
    app.state.lifecycle = lifecycle
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
    lifecycle = OwnedServerLifecycle()
    app = create_app(config, lifecycle=lifecycle)
    server = uvicorn.Server(uvicorn.Config(app, host=host, port=port, log_level="info"))
    lifecycle.bind(lambda: setattr(server, 'should_exit', True))
    server.run()
