from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .errors import PdfToWebError


@dataclass(frozen=True)
class WordPressPreview:
    html: str
    block_types: tuple[str, ...]
    unsupported_blocks: tuple[str, ...]


def worker_path() -> Path:
    return Path(__file__).parent / "node" / "wordpress_preview_worker.cjs"


def _node_environment() -> dict[str, str]:
    environment = dict(os.environ)
    candidates = [Path.cwd() / "node_modules"]
    candidates.extend(parent / "node_modules" for parent in worker_path().parents)
    existing = [str(path) for path in candidates if path.is_dir()]
    configured = environment.get("PDF_TO_WEB_NODE_MODULES")
    if configured:
        existing.insert(0, configured)
    if existing:
        environment["NODE_PATH"] = os.pathsep.join(existing)
    return environment


def preview_available() -> bool:
    node = shutil.which("node")
    if node is None or not worker_path().is_file():
        return False
    result = subprocess.run(
        [node, "-e", "require.resolve('wp-block-to-html');require.resolve('sanitize-html')"],
        cwd=worker_path().parent,
        env=_node_environment(),
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    return result.returncode == 0


def render_gutenberg_preview(markup: str) -> WordPressPreview:
    node = shutil.which("node")
    if node is None:
        raise PdfToWebError("WordPress Preview requires Node.js 20.19 or newer")
    if len(markup.encode("utf-8")) > 10_000_000:
        raise PdfToWebError("Gutenberg preview input exceeds the 10 MB local limit")
    try:
        result = subprocess.run(
            [node, str(worker_path())],
            input=json.dumps({"markup": markup}),
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
            env=_node_environment(),
        )
    except subprocess.TimeoutExpired as exc:
        raise PdfToWebError("WordPress Preview timed out") from exc
    if result.returncode != 0:
        detail = result.stderr.strip()
        if "Cannot find module" in detail:
            detail = "run npm install in the PDF to Web project"
        raise PdfToWebError(f"WordPress Preview is unavailable: {detail or 'conversion failed'}")
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise PdfToWebError("WordPress Preview returned invalid data") from exc
    return WordPressPreview(
        html=str(data.get("html", "")),
        block_types=tuple(str(value) for value in data.get("blockTypes", [])),
        unsupported_blocks=tuple(
            str(value) for value in data.get("unsupportedBlocks", [])
        ),
    )
