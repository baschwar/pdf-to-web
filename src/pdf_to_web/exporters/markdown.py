from __future__ import annotations

from typing import Any

from .common import table_cell


def _block(block: dict[str, Any], depth: int = 0) -> str:
    if block.get("export_as_part_of_image"):
        return ""
    block_type = block.get("type")
    content = str(block.get("content", ""))
    if block_type == "heading":
        return f"{'#' * int(block.get('level', 2))} {content}"
    if block_type in {"paragraph", "caption", "callout"}:
        return content
    if block_type == "quote":
        return "\n".join(f"> {line}" for line in content.splitlines())
    if block_type == "list":
        lines: list[str] = []
        for number, child in enumerate(block.get("children", []), start=1):
            marker = f"{number}." if block.get("ordered") else "-"
            lines.append(f"{'  ' * depth}{marker} {child.get('content', '')}")
            for nested in child.get("children", []):
                lines.append(_block(nested, depth + 1))
        return "\n".join(lines)
    if block_type == "image":
        alt = "" if block.get("decorative") else block.get("alt", "")
        return f"![{alt}]({block.get('src') or 'MEDIA_URL_REQUIRED'})"
    if block_type == "table":
        rows = block.get("rows", [])
        if not rows:
            return "[Empty table]"
        lines = [
            "| " + " | ".join(table_cell(cell)[0] for cell in row) + " |" for row in rows
        ]
        lines.insert(1, "| " + " | ".join("---" for _ in rows[0]) + " |")
        return "\n".join(lines)
    if block_type == "page_break":
        return "---"
    return f"<!-- Unknown source element: {block.get('provenance', {}).get('source_type')} -->\n{content}"


def render_document(document: dict[str, Any]) -> str:
    return "\n\n".join(
        content for block in document.get("blocks", []) if (content := _block(block))
    ) + "\n"
