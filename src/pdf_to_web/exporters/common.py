from __future__ import annotations

import html
from typing import Any


def is_excluded(block: dict[str, Any]) -> bool:
    return block.get("review", {}).get("status") == "excluded" or bool(block.get("excluded"))


def render_inline(block: dict[str, Any]) -> str:
    runs = block.get("runs")
    if not isinstance(runs, list):
        return html.escape(str(block.get("content", "")))
    rendered: list[str] = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        value = html.escape(str(run.get("text", "")))
        run_type = run.get("type", "text")
        if run_type == "strong":
            rendered.append(f"<strong>{value}</strong>")
        elif run_type == "emphasis":
            rendered.append(f"<em>{value}</em>")
        elif run_type == "link":
            href = html.escape(str(run.get("url", "")), quote=True)
            rendered.append(f'<a href="{href}">{value}</a>')
        else:
            rendered.append(value)
    return "".join(rendered)


def image_src(block: dict[str, Any]) -> str:
    return html.escape(str(block.get("src") or "MEDIA_URL_REQUIRED"), quote=True)


def table_cell(cell: Any) -> tuple[str, int, int]:
    if isinstance(cell, dict):
        return (
            str(cell.get("content", "")),
            int(cell.get("row_span", 1) or 1),
            int(cell.get("column_span", 1) or 1),
        )
    return str(cell), 1, 1
