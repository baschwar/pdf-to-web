from __future__ import annotations

import math
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from .errors import PdfToWebError
from .project import load_project


@dataclass(frozen=True)
class SourceTextRegion:
    text: str
    box: list[float] | None
    legacy_box: list[float]
    font_size: float


def _point(matrix, x, y):
    return (matrix[0] * x + matrix[2] * y + matrix[4],
            matrix[1] * x + matrix[3] * y + matrix[5])


def _font_text_width(font, text):
    """Use the PDF's encoded glyph widths; Unicode code points are not CIDs."""
    try:
        # pypdf's own font reader handles CID widths and standard font metrics.
        # If this optional geometry API is unavailable, omit the outline rather
        # than guessing a location. Text extraction itself remains available.
        from pypdf._font import Font

        parsed = Font.from_font_resource(font)
        if not parsed.interpretable or str(font.get('/Encoding', '')).endswith('-V'):
            return None
        codes: dict[str, set[str]] = {}
        if parsed.character_map:
            for code, value in parsed.character_map.items():
                if isinstance(code, str) and isinstance(value, str) and len(value) == 1:
                    codes.setdefault(value, set()).add(code)
        elif isinstance(parsed.encoding, dict):
            for code, value in parsed.encoding.items():
                if isinstance(code, int) and isinstance(value, str) and len(value) == 1:
                    codes.setdefault(value, set()).add(chr(code))
        widths = []
        for char in text:
            values = {parsed.get_text_width(code) for code in codes.get(char, ())}
            if len(values) != 1:
                return None
            widths.append(values.pop())
        return sum(widths) / 1000
    except Exception:
        return None


def source_text_regions(page) -> tuple[str, list[SourceTextRegion]]:
    """Read text positions in PDF user space, without saving or normalizing."""
    regions = []
    widths = {}

    def collect(text, cm, tm, font, size):
        value = " ".join(text.split())
        if not value or font is None:
            return
        first_char = int(font.get('/FirstChar', 0))
        legacy_widths = font.get('/Widths') or []
        if hasattr(legacy_widths, 'get_object'):
            legacy_widths = legacy_widths.get_object()
        legacy_width = sum(float(legacy_widths[ord(char) - first_char])
                           if 0 <= ord(char) - first_char < len(legacy_widths) else 500.0
                           for char in value)
        font_size = float(size) * math.hypot(float(tm[0]), float(tm[1]))
        x, baseline = float(tm[4]), float(tm[5])
        legacy_box = [x, baseline - font_size * .25,
                      x + legacy_width * font_size / 1000, baseline + font_size]
        key = (id(font), value)
        if key not in widths:
            widths[key] = _font_text_width(font, value)
        width = widths[key]
        box = None
        # A visitor can flush several lines or return unresolved form positions.
        # Only a single line with finite, invertible transforms is trustworthy.
        matrices = [float(v) for v in (*cm, *tm)]
        if (width is not None and width > 0 and size > 0
                and len([line for line in text.splitlines() if line.strip()]) <= 1
                and all(math.isfinite(v) for v in matrices)
                and abs(cm[0] * cm[3] - cm[1] * cm[2]) > 1e-9
                and abs(tm[0] * tm[3] - tm[1] * tm[2]) > 1e-9):
            corners = [_point(cm, *_point(tm, u, v))
                       for u, v in ((0, -size * .25), (width * size, -size * .25),
                                    (0, size), (width * size, size))]
            box = [min(p[0] for p in corners), min(p[1] for p in corners),
                   max(p[0] for p in corners), max(p[1] for p in corners)]
        regions.append(SourceTextRegion(value, box, legacy_box, font_size))

    text = page.extract_text(visitor_text=collect) or ''
    return text, regions


def matched_source_text_box(text: str, regions: list[SourceTextRegion]) -> list[float] | None:
    """Require one spatial association; coincident overprints may share it."""
    target = ' '.join(str(text).split())
    if not target:
        return None
    matches = []
    for index in range(len(regions)):
        joined = ''
        boxes = []
        for region in regions[index:index + 8]:
            joined = (joined + ' ' + region.text).strip()
            if not target.startswith(joined):
                break
            boxes.append(region.box)
            if joined == target:
                if any(box is None for box in boxes):
                    return None
                box = [min(b[0] for b in boxes), min(b[1] for b in boxes),
                       max(b[2] for b in boxes), max(b[3] for b in boxes)]
                if not any(all(abs(a - b) <= .5 for a, b in zip(box, existing))
                           for existing in matches):
                    matches.append(box)
                break
    return matches[0] if len(matches) == 1 else None


def display_source_box(page, box) -> list[float] | None:
    """Map PDF user coordinates to the rotated MediaBox used by pdftoppm."""
    if (not isinstance(box, (list, tuple)) or len(box) != 4
            or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in box)):
        return None
    media = page.mediabox
    width, height = float(media.width), float(media.height)
    rotation = int(page.rotation or 0) % 360
    if width <= 0 or height <= 0 or rotation not in (0, 90, 180, 270):
        return None
    x0, x1 = sorted((float(box[0]) - float(media.left), float(box[2]) - float(media.left)))
    y0, y1 = sorted((float(box[1]) - float(media.bottom), float(box[3]) - float(media.bottom)))
    x0, x1 = max(0, x0), min(width, x1)
    y0, y1 = max(0, y0), min(height, y1)
    if x0 >= x1 or y0 >= y1:
        return None
    def rotate(x, y):
        return {0: (x, y), 90: (y, width - x),
                180: (width - x, height - y), 270: (height - y, x)}[rotation]
    points = [rotate(x, y) for x, y in ((x0, y0), (x0, y1), (x1, y0), (x1, y1))]
    return [min(p[0] for p in points), min(p[1] for p in points),
            max(p[0] for p in points), max(p[1] for p in points)]


def source_regions_for_blocks(project_dir: Path, blocks: list[dict[str, Any]]) -> dict[str, dict]:
    """Build a read-only display overlay; never repair the saved document."""
    overlay = {}
    recovered_types = {'recovered first-page header', 'recovered first-page subtitle'}
    unavailable = ('Source outline unavailable: this text could not be matched confidently '
                   'to the source PDF. The text remains in Reading order; open the source PDF to review it.')
    try:
        project = load_project(project_dir)
        source = Path(project_dir) / str(project.get('source', {}).get('path') or '')
        reader = PdfReader(source)
    except Exception:
        return {str(b['id']): {'regions': [], 'coverage': unavailable}
                for b in blocks if b.get('provenance', {}).get('source_type') in recovered_types}
    text_regions = {}
    for block in blocks:
        provenance = block.get('provenance', {})
        try:
            page_number = int(provenance.get('source_page'))
            if page_number < 1 or page_number > len(reader.pages):
                if provenance.get('source_type') in recovered_types:
                    overlay[str(block['id'])] = {'regions': [], 'coverage': unavailable}
                continue
            page = reader.pages[page_number - 1]
        except (ValueError, TypeError):
            if provenance.get('source_type') in recovered_types:
                overlay[str(block['id'])] = {'regions': [], 'coverage': unavailable}
            continue
        recovered = provenance.get('source_type') in recovered_types
        if recovered:
            if page_number not in text_regions:
                try:
                    text_regions[page_number] = source_text_regions(page)[1]
                except Exception:
                    text_regions[page_number] = []
            box = matched_source_text_box(block.get('content', ''), text_regions[page_number])
            # Positions well outside the MediaBox signal unresolved PDF forms.
            if box and (box[0] < float(page.mediabox.left) - 1 or box[1] < float(page.mediabox.bottom) - 1
                        or box[2] > float(page.mediabox.right) + 1 or box[3] > float(page.mediabox.top) + 1):
                box = None
            region = display_source_box(page, box)
            overlay[str(block['id'])] = {'regions': [region] if region else [],
                                         'coverage': '' if region else unavailable}
        else:
            boxes = []
            def descendants(node):
                from .exporters.common import is_excluded, is_footnote_body, has_unstructured_list_text
                for child in node.get('children', []):
                    if is_excluded(child) or is_footnote_body(child) or child.get('export_as_part_of_image'):
                        continue
                    if (child.get('provenance', {}).get('source_page') == page_number
                            and (child.get('type') in {'list_item', 'paragraph', 'heading', 'quote', 'caption', 'callout', 'unknown'}
                                 or has_unstructured_list_text(child))):
                        boxes.append(child.get('provenance', {}).get('bounding_box'))
                    descendants(child)
            if block.get('type') == 'list':
                descendants(block)
            if not any(display_source_box(page, box) for box in boxes):
                boxes = [provenance.get('bounding_box')]
            regions = [region for box in boxes if (region := display_source_box(page, box))]
            overlay[str(block['id'])] = {'regions': [list(box) for box in dict.fromkeys(tuple(r) for r in regions)],
                                         'coverage': ('Recorded source coordinates cannot be outlined on this rendered page. '
                                                      'Open the source PDF to review this content.'
                                                      if any(box is not None for box in boxes) and not regions else '')}
    return overlay


def source_page_size(project_dir: Path, page: int) -> tuple[float, float]:
    project_dir = project_dir.expanduser().resolve()
    project = load_project(project_dir)
    page_count = int(project.get("source", {}).get("page_count") or 0)
    if page < 1 or (page_count and page > page_count):
        raise ValueError(f"Source page must be between 1 and {page_count or 1}")
    source = project_dir / str(project.get("source", {}).get("path") or "")
    if not source.is_file() or source.suffix.lower() != ".pdf":
        raise PdfToWebError("Source PDF is unavailable")
    pdf_page = PdfReader(source).pages[page - 1]
    width = float(pdf_page.mediabox.width)
    height = float(pdf_page.mediabox.height)
    if int(pdf_page.rotation or 0) % 180:
        width, height = height, width
    return width, height


def render_source_page(project_dir: Path, page: int) -> Path:
    project_dir = project_dir.expanduser().resolve()
    project = load_project(project_dir)
    page_count = int(project.get("source", {}).get("page_count") or 0)
    if page < 1 or (page_count and page > page_count):
        raise ValueError(f"Source page must be between 1 and {page_count or 1}")
    source = project_dir / str(project.get("source", {}).get("path") or "")
    if not source.is_file() or source.suffix.lower() != ".pdf":
        raise PdfToWebError("Source PDF is unavailable")
    cache = project_dir / "review" / "source-pages"
    output = cache / f"page-{page:04d}.png"
    if output.is_file():
        return output
    executable = shutil.which("pdftoppm")
    if not executable:
        raise PdfToWebError("Poppler pdftoppm was not found on the app’s PATH. Install Poppler PDF utilities, then restart PDF to Web.")
    cache.mkdir(parents=True, exist_ok=True)
    prefix = cache / f"page-{page:04d}"
    try:
        completed = subprocess.run(
            [
                executable,
                "-f",
                str(page),
                "-l",
                str(page),
                "-singlefile",
                "-r",
                "120",
                "-png",
                str(source),
                str(prefix),
            ],
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise PdfToWebError(f"Source page {page} rendering timed out") from exc
    except OSError as exc:
        raise PdfToWebError(f"Could not start the PDF renderer: {exc}. Check the Poppler installation, then restart PDF to Web.") from exc
    if completed.returncode != 0 or not output.is_file():
        detail = completed.stderr.strip() or "pdftoppm did not create a page image"
        raise PdfToWebError(f"Could not render source page {page}: {detail}")
    return output
