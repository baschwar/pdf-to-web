from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .project import load_project

RECENT_PROJECTS_SCHEMA = "pdf-to-web-recent-projects-v1"
RECENT_PROJECT_LIMIT = 10


@dataclass(frozen=True)
class RecentProject:
    title: str
    path: str
    last_opened: str

    @property
    def project_path(self) -> Path:
        return canonical_path(Path(self.path))


def canonical_path(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def default_config_dir() -> Path:
    override = os.environ.get("PDF_TO_WEB_CONFIG_DIR")
    if override:
        return canonical_path(Path(override))
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "PDF to Web"
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "PDF to Web"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "pdf-to-web"


def default_recent_projects_path() -> Path:
    return default_config_dir() / "recent-projects.json"


def _is_project(path: Path) -> bool:
    return (path / "project.json").is_file()


def load_recent_projects(path: Path) -> list[RecentProject]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(data, dict) or data.get("schema_version") != RECENT_PROJECTS_SCHEMA:
        return []
    records: list[RecentProject] = []
    seen: set[Path] = set()
    for value in data.get("projects", []):
        if not isinstance(value, dict):
            continue
        try:
            record = RecentProject(
                title=str(value["title"]),
                path=str(value["path"]),
                last_opened=str(value["last_opened"]),
            )
        except KeyError:
            continue
        canonical = record.project_path
        if canonical in seen or not _is_project(canonical):
            continue
        seen.add(canonical)
        records.append(RecentProject(record.title, str(canonical), record.last_opened))
        if len(records) == RECENT_PROJECT_LIMIT:
            break
    return records


def save_recent_projects(path: Path, records: list[RecentProject]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(
            {
                "schema_version": RECENT_PROJECTS_SCHEMA,
                "projects": [asdict(record) for record in records[:RECENT_PROJECT_LIMIT]],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def remember_project(
    config_path: Path,
    project_path: Path,
    records: list[RecentProject] | None = None,
    *,
    opened_at: str | None = None,
) -> list[RecentProject]:
    canonical = canonical_path(project_path)
    project = load_project(canonical)
    current = list(records if records is not None else load_recent_projects(config_path))
    current = [record for record in current if record.project_path != canonical]
    current.insert(
        0,
        RecentProject(
            title=str(project.get("title") or canonical.name),
            path=str(canonical),
            last_opened=opened_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        ),
    )
    current = current[:RECENT_PROJECT_LIMIT]
    save_recent_projects(config_path, current)
    return current


def remove_recent_project(
    config_path: Path, project_path: Path, records: list[RecentProject] | None = None
) -> list[RecentProject]:
    canonical = canonical_path(project_path)
    current = list(records if records is not None else load_recent_projects(config_path))
    current = [record for record in current if record.project_path != canonical]
    save_recent_projects(config_path, current)
    return current
