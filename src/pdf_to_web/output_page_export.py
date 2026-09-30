"""Transactional local output-page packages, through established serializers."""
from __future__ import annotations

import copy
import hashlib
import html as escaping
import json
import shutil
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from . import __version__
from .errors import PdfToWebError
from .export import _write_media_manifest, _local_image_path
from .exporters import html, gutenberg, wxr
from .output_pages import page_document, pages, status, validate
from .project import load_project
from .review_state import ensure_review_document
from .validation import validate_semantic_html, validate_gutenberg, _SemanticParser

MANIFEST_SCHEMA = 'pdf-to-web-page-manifest-v1'


def contents_html(document):
    group = sorted(pages(document), key=lambda p: p['navigation_order'])
    def children(parent, trail):
        items = []
        for p in group:
            if p.get('parent') == parent and p['id'] not in trail:
                items.append('<li><a href="' + escaping.escape(p['slug'], quote=True) + '.html">' + escaping.escape(p['title']) + '</a>' + children(p['id'], trail | {p['id']}) + '</li>')
        return '<ol>' + ''.join(items) + '</ol>' if items else ''
    return '<!doctype html><html lang="en"><meta charset="utf-8"><title>Contents</title><main><h1>Contents</h1>' + children(None, set()) + '</main></html>'


def export_pages(project_dir: Path, page_id=None, profile=None):
    document = ensure_review_document(project_dir)
    errors = validate(document)
    if errors:
        raise PdfToWebError('Fix the output-page arrangement before exporting: ' + '; '.join(errors))
    if document.get('review', {}).get('status') == 'conversion_blocked':
        raise PdfToWebError('Conversion is blocked; output-page publication exports are unavailable')
    config = copy.deepcopy(load_project(project_dir).get('export', {}))
    profile = profile or config.get('wordpress_profile', 'generic')
    if profile not in {'generic', 'wsuwp'}:
        raise PdfToWebError('Choose generic or wsuwp')
    selected = [p for p in pages(document) if page_id is None or p['id'] == page_id]
    if not selected:
        raise PdfToWebError('Output page was not found')
    output = project_dir / 'output'
    output.mkdir(exist_ok=True)
    destination = output / ('pages' if page_id is None else 'page-' + str(pages(document).index(selected[0]) + 1))
    stage = Path(tempfile.mkdtemp(prefix='.pages-', dir=output))
    archive = destination.with_suffix('.zip')
    temp_zip = stage.with_suffix('.zip.tmp')
    try:
        media_files, media = _write_media_manifest(project_dir, document)
        (stage / 'assets').mkdir()
        dependencies = []
        for path in media_files:
            if path.is_file():
                relative = Path('media') / path.relative_to(output / 'wordpress')
                (stage / relative).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, stage / relative)
                dependencies.append(str(relative))
        manifest = {'schema_version': MANIFEST_SCHEMA, 'app_version': __version__,
                    'project': {'id': document['output_pages']['project_id'], 'title': load_project(project_dir)['title'], 'source': load_project(project_dir)['source'],
                                'identity': document.get('metadata', {}), 'review_revision': document.get('review_session', {}).get('revision')},
                    'export_settings': {**config, 'wordpress_profile': profile}, 'complete_package': page_id is None,
                    'pages': [], 'media_files': dependencies,
                    'manual_media_actions': [i for i in media['items'] if i['wordpress_status'] == 'unresolved']}
        items = []
        for p in selected:
            projected = page_document(document, p['id'])
            if any(i.get('kind') == 'footnote' for i in projected['output_unresolved_targets']):
                raise PdfToWebError('Recover missing footnote bodies before exporting this page')
            # Pack local semantic-preview assets; WordPress still uses explicit mapping/placeholder policy.
            for block in projected['blocks']:
                if block.get('type') == 'image':
                    source = _local_image_path(project_dir, str(block.get('src') or ''))
                    if source:
                        name = hashlib.sha256(source.read_bytes()).hexdigest()[:16] + source.suffix
                        shutil.copy2(source, stage / 'assets' / name)
                        block['src'] = 'assets/' + name
                        if block['src'] not in dependencies:
                            dependencies.append(block['src'])
            markup = gutenberg.render_document(projected, profile, config)
            files = {'html': p['slug'] + '.html', 'gutenberg': p['slug'] + '.gutenberg.html', 'wxr': p['slug'] + '.xml'}
            (stage / files['html']).write_text(html.render_document(projected), encoding='utf-8')
            (stage / files['gutenberg']).write_text(markup, encoding='utf-8')
            item = {'key': p['id'], 'title': p['title'], 'slug': p['slug'], 'post_type': p['type'],
                    'status': 'draft', 'parent': p.get('parent'), 'menu_order': p['navigation_order'],
                    'author': config.get('wordpress', {}).get('author', 'pdf-to-web'), 'content': markup}
            items.append(item)
            (stage / files['wxr']).write_text(wxr.render_wxr([item]), encoding='utf-8')
            page_status = status(document, p['id'])
            manifest['pages'].append({**copy.deepcopy(p), 'source_ranges': page_status['source_ranges'],
                                      'files': files, 'review': page_status,
                                      'media_dependencies': [b['id'] for b in projected['blocks'] if b.get('type') == 'image'],
                                      'required_page_dependencies': sorted({i['target_page_id'] for i in projected['output_link_mappings'] if i['target_page_id'] not in {page['id'] for page in selected}}),
                                      'internal_link_mappings': projected['output_link_mappings'],
                                      'unresolved_targets': projected['output_unresolved_targets'],
                                      'manual_parent_assignment': p.get('parent') if page_id else None})
        checks = {}
        for p in manifest['pages']:
            projected = page_document(document, p['id'])
            html_markup = (stage / p['files']['html']).read_text()
            block_markup = (stage / p['files']['gutenberg']).read_text()
            checks[p['id']] = {'html': validate_semantic_html(projected, html_markup), 'gutenberg': validate_gutenberg(projected, block_markup)}
            for check in checks[p['id']].values():
                if check.get('anchors', {}).get('duplicate_ids'):
                    raise PdfToWebError('Duplicate anchors in page ' + p['title'] + '; correct source identifiers before export')
            for link in p['internal_link_mappings']:
                if link['target_page_id'] in {i['id'] for i in manifest['pages']}:
                    target = next(i for i in manifest['pages'] if i['id'] == link['target_page_id'])
                    parser = _SemanticParser()
                    parser.feed((stage / target['files']['html']).read_text())
                    if link['target_block_id'] not in parser.ids:
                        raise PdfToWebError('Internal target was not rendered: ' + link['target_block_id'])
        manifest['validation'] = checks
        combined_xml = wxr.render_wxr(items)
        try:
            root = ET.fromstring(combined_xml)
            if len(root.findall('./channel/item')) != len(manifest['pages']):
                raise PdfToWebError('WXR item count differs from the page arrangement')
        except ET.ParseError as exc:
            raise PdfToWebError('WXR contains invalid XML text; remove control characters from content or metadata: ' + str(exc)) from exc
        (stage / 'publications.xml').write_text(combined_xml, encoding='utf-8')
        contents_document = copy.deepcopy(document)
        contents_document['output_pages']['pages'] = copy.deepcopy(selected)
        selected_ids = {p['id'] for p in selected}
        for p in contents_document['output_pages']['pages']:
            if p.get('parent') not in selected_ids:
                p['parent'] = None
        (stage / 'contents.html').write_text(contents_html(contents_document), encoding='utf-8')
        (stage / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        (stage / 'IMPORT.txt').write_text(
            'Import publications.xml with WordPress Tools > Import, or paste each Gutenberg file into a draft Page/Article.\n'
            'Package IDs are internal import references, never existing production parent IDs. Individual imports require manual parent assignment.\n'
            'Upload media/media-upload.zip contents; use media mapping CSV in PDF to Web and regenerate. Unresolved media remain placeholders.\n'
            'Individual exports may require sibling pages listed in required_page_dependencies. Use the complete package for a self-contained navigation set.\n'
            'Relative .html links work in this local package. After import, replace them with actual WordPress permalinks; no production URLs are guessed.\n'
            'Review manifest findings, page title/H1, hierarchy and content, then test in the destination editor and frontend.\n'
            'The manifest records review decisions; it does not certify WCAG or production WSUWP compatibility.\n', encoding='utf-8')
        # Finish the ZIP before promoting either artifact; failed writes retain the previous package.
        with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as bundle:
            for file in sorted(stage.rglob('*')):
                if file.is_file():
                    bundle.write(file, str(file.relative_to(stage)))
        backup = destination.with_name(destination.name + '.previous')
        if backup.exists():
            shutil.rmtree(backup)
        if destination.exists():
            destination.rename(backup)
        try:
            stage.rename(destination)
            temp_zip.replace(archive)
        except Exception:
            if destination.exists():
                shutil.rmtree(destination)
            if backup.exists():
                backup.rename(destination)
            raise
        if backup.exists():
            shutil.rmtree(backup)
        return [archive, destination / 'manifest.json', destination / 'contents.html', destination / 'publications.xml',
                *[destination / f for p in manifest['pages'] for f in p['files'].values()]]
    finally:
        temp_zip.unlink(missing_ok=True)
        if stage.exists():
            shutil.rmtree(stage)
