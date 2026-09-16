from __future__ import annotations

import importlib.metadata
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from .wordpress_preview import preview_available


@dataclass
class Check:
    name: str
    status: str
    detail: str
    action: str | None = None


def _java_major(java: Path) -> int | None:
    try:
        result = subprocess.run(
            [str(java), "-version"], capture_output=True, text=True, timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.search(r'version "(?:(1)\.)?(\d+)', result.stderr + result.stdout)
    if not match:
        return None
    return int(match.group(2))


def find_supported_java() -> tuple[Path | None, int | None]:
    candidates: list[Path] = []
    current = shutil.which("java")
    if current:
        candidates.append(Path(current))
    candidates.extend(
        Path(path)
        for path in (
            "/opt/homebrew/opt/openjdk@21/bin/java",
            "/opt/homebrew/opt/openjdk@17/bin/java",
            "/opt/homebrew/opt/openjdk/bin/java",
            "/usr/local/opt/openjdk@21/bin/java",
            "/usr/local/opt/openjdk@17/bin/java",
            "/usr/local/opt/openjdk/bin/java",
        )
    )
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen or not candidate.is_file():
            continue
        seen.add(candidate)
        major = _java_major(candidate)
        if major is not None and major >= 11:
            return candidate.resolve(), major
    return None, None


def java_environment() -> dict[str, str]:
    java, _ = find_supported_java()
    if java is None:
        return dict(os.environ)
    env = dict(os.environ)
    env["JAVA_HOME"] = str(java.parent.parent)
    env["PATH"] = f"{java.parent}{os.pathsep}{env.get('PATH', '')}"
    return env


def run_checks(project_dir: Path | None = None) -> list[Check]:
    checks: list[Check] = []
    version = sys.version_info
    checks.append(
        Check(
            "Python",
            "PASS" if version >= (3, 10) else "FAIL",
            f"{version.major}.{version.minor}.{version.micro}",
            None if version >= (3, 10) else "Install Python 3.10 or newer.",
        )
    )

    java, java_major = find_supported_java()
    checks.append(
        Check(
            "Java",
            "PASS" if java else "FAIL",
            f"Java {java_major} at {java}" if java else "Java 11+ not found",
            None
            if java
            else "Install a Java 11 or newer runtime and run pdf-to-web doctor again.",
        )
    )

    try:
        odl_version = importlib.metadata.version("opendataloader-pdf")
    except importlib.metadata.PackageNotFoundError:
        odl_version = None
    checks.append(
        Check(
            "OpenDataLoader PDF",
            "PASS" if odl_version else "FAIL",
            odl_version or "not installed",
            None
            if odl_version
            else "Install the project dependencies with: python -m pip install -e .",
        )
    )

    missing_renderers = [name for name in ("pdfinfo", "pdftoppm") if not shutil.which(name)]
    checks.append(
        Check(
            "PDF rendering tools",
            "PASS" if not missing_renderers else "FAIL",
            "pdfinfo and pdftoppm available"
            if not missing_renderers
            else f"missing: {', '.join(missing_renderers)}",
            None if not missing_renderers else "Install Poppler PDF utilities.",
        )
    )

    node = shutil.which("node")
    node_version = None
    if node:
        try:
            result = subprocess.run(
                [node, "--version"], capture_output=True, text=True, timeout=5
            )
            node_version = result.stdout.strip().lstrip("v")
        except (OSError, subprocess.SubprocessError):
            pass
    node_major_text = node_version.split(".", 1)[0] if node_version else ""
    node_major = int(node_major_text) if node_major_text.isdigit() else 0
    wordpress_preview_ok = node_major >= 18 and preview_available()
    checks.append(
        Check(
            "WordPress Preview",
            "PASS" if wordpress_preview_ok else "REVIEW",
            f"Node {node_version}; local converter available"
            if wordpress_preview_ok
            else "optional local Gutenberg preview dependencies are unavailable",
            None
            if wordpress_preview_ok
            else "Install Node.js 18.12 or newer and run npm install. Semantic Preview remains available.",
        )
    )

    target = (project_dir or Path.cwd()).expanduser().resolve()
    writable_target = target if target.exists() else target.parent
    writable = writable_target.exists() and os.access(writable_target, os.W_OK)
    checks.append(
        Check(
            "Project directory",
            "PASS" if writable else "FAIL",
            f"writable: {writable_target}" if writable else f"not writable: {writable_target}",
            None if writable else "Choose a writable local project directory.",
        )
    )

    try:
        free = shutil.disk_usage(writable_target).free
        free_gib = free / (1024**3)
        disk_ok = free_gib >= 1
        detail = f"{free_gib:.1f} GiB free"
    except OSError:
        disk_ok = False
        detail = "could not determine available space"
    checks.append(
        Check(
            "Disk space",
            "PASS" if disk_ok else "REVIEW",
            detail,
            None if disk_ok else "Keep at least 1 GiB free for extraction artifacts.",
        )
    )

    if project_dir:
        source = target / "source" / "original.pdf"
        checks.append(
            Check(
                "Source PDF",
                "PASS" if source.is_file() and os.access(source, os.R_OK) else "FAIL",
                str(source),
                None if source.is_file() else "Import a PDF into this project first.",
            )
        )
    return checks


def checks_as_dicts(project_dir: Path | None = None) -> list[dict[str, str | None]]:
    return [asdict(check) for check in run_checks(project_dir)]
