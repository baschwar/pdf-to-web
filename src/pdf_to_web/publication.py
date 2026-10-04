"""Source review eligibility and freshness of local publication artifacts."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

from .errors import PdfToWebError
from .exporters.common import is_excluded, has_unstructured_list_text


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def content_digest(block, *, include_media_mapping=False):
    value = copy.deepcopy(block)
    value.pop('review', None)
    def clean(nodes):
        for node in nodes:
            if node.get('type') == 'image' and not include_media_mapping:
                for field in ('wordpress_url', 'wordpress_attachment_id', 'wordpress_media'):
                    node.pop(field, None)
            if 'review' in node:
                node['review'] = {'status': node['review'].get('status')}
            clean(node.get('children', []))
    clean([value])
    return digest(value)


def approval_stamp_matches(block):
    stamp = block.get('review', {}).get('content_sha256')
    # Existing stamps that include unchanged routing metadata remain valid.
    return stamp in {content_digest(block), content_digest(block, include_media_mapping=True)}


def pending_descendants(block):
    return any(not is_excluded(child) and (child.get('review', {}).get('status') == 'needs_review' or pending_descendants(child))
               for child in block.get('children', []))


def block_review_issue(block):
    malformed = list_structure_issue(block)
    if malformed:
        return malformed
    review = block.get('review', {})
    identity = str(block.get('id'))
    if review.get('status') != 'approved':
        return {'code': 'block_review_pending', 'message': f'Block {identity} needs review'}
    if review.get('content_sha256') and not approval_stamp_matches(block):
        return {'code': 'block_approval_changed', 'message': f'Block {identity} changed since approval'}
    if not review.get('content_sha256') and pending_descendants(block):
        return {'code': 'legacy_approval_unverified', 'message': f'Block {identity}: earlier approval cannot be verified for pending nested items'}
    return None


def list_structure_issue(block):
    if is_excluded(block):
        return None
    if has_unstructured_list_text(block):
        return {'code': 'list_items_missing', 'message': f'Block {block.get("id")}: stored list text has no list items. Recover the list structure before approving; retained text remains available for review.'}
    return next((issue for child in block.get('children', []) if (issue := list_structure_issue(child))), None)


def effective_block_status(block, document=None):
    if is_excluded(block):
        return 'excluded'
    status = block.get('review', {}).get('status', 'unreviewed')
    if document is not None and block.get('type') == 'image' and status == 'approved':
        from .image_review import association_issue, pending_descriptions_for
        if association_issue(document, block) or pending_descriptions_for(document, block):
            return 'needs_review'
    return 'needs_review' if status == 'approved' and block_review_issue(block) else status


def readiness_findings(document, selected_pages=None):
    """Visible source blocks own nested edits; derived markup cannot approve them."""
    issues = []
    owners = {}
    nodes = {}
    def add(code, message, block=None, visual=None, page=None):
        issue = {'code': code, 'message': message}
        if block is not None:
            issue.update(block_id=str(block.get('id')), source_page=block.get('provenance', {}).get('source_page'))
        if visual is not None:
            issue.update(visual_id=str(visual.get('id')), source_page=visual.get('source_page'))
        if page is not None:
            issue['page_id'] = str(page.get('id'))
        issues.append(issue)
    def visit(block, owner):
        if is_excluded(block):
            return
        nodes[str(block.get('id'))] = block
        owners[str(block.get('id'))] = owner
        for child in block.get('children', []):
            visit(child, owner)
    for block in document.get('blocks', []):
        if is_excluded(block):
            continue
        identity = str(block.get('id'))
        visit(block, block)
        issue = block_review_issue(block)
        if issue:
            add(issue['code'], issue['message'], block)
    if document.get('review', {}).get('status') == 'conversion_blocked':
        issues.insert(0, {'code': 'conversion_blocked', 'message': 'Conversion is blocked'})
    if not owners:
        add('no_content', 'There is no included content to publish')
    for identity, block in nodes.items():
        if block.get('type') == 'image':
            from .image_review import association_issue
            problem = association_issue(document, block)
            if problem:
                add('image_description_association_invalid', problem, owners[identity])
        if block.get('type') == 'image' and not block.get('decorative') and not str(block.get('alt') or '').strip():
            add('image_alternative_pending', f'Image {identity} needs alt text or a decorative decision', owners[identity])
    from .accessibility import visual_readiness
    for visual in document.get('review', {}).get('complex_visuals', []):
        if visual.get('status') == 'excluded':
            continue
        source = str(visual.get('source_block_id') or '')
        if source and source not in nodes:
            from .accessibility import _walk_visibility
            if not any(str(b.get('id')) == source for b, _ in _walk_visibility(document.get('blocks', []))):
                add('description_source_missing', f'Description {visual.get("id")} references missing image {source}; restore or correct its association before publication', visual=visual)
            continue
        if source and nodes[source].get('decorative'):
            continue
        if not visual_readiness(document, visual)['complete']:
            add('description_review_pending', f'Description {visual.get("id")} needs review', visual=visual)
    for note in document.get('footnotes', []):
        body_ids = {str(note.get('source_block_id') or ''), *map(str, note.get('source_block_ids', []))}
        matches = [b for key, b in nodes.items() if key in body_ids or b.get('footnote_body_id') == note.get('id')]
        if not matches and note.get('review', {}).get('status') != 'approved':
            add('footnote_source_missing', f'Footnote {note.get("id")} has no reviewed source body')
        for body in matches:
            owner = owners[str(body['id'])]
            if effective_block_status(owner) != 'approved':
                add('footnote_source_pending', f'Footnote {note.get("id")} source block {owner.get("id")} needs review', owner)
    for page in selected_pages or []:
        if page.get('approval', {}).get('status') != 'reviewed':
            add('output_page_review_pending', f'Output page {page.get("id")} needs review', page=page)
    return list({issue['message']: issue for issue in issues}.values())


def findings(document, selected_pages=None):
    return [issue['message'] for issue in readiness_findings(document, selected_pages)]


def require_ready(document, selected_pages=None):
    pending = findings(document, selected_pages)
    if pending:
        raise PdfToWebError('Publication requires current review: ' + '; '.join(pending))


def is_public_path(relative):
    parts = Path(relative).parts
    if len(parts) < 2 or parts[0] != 'output':
        return False
    return (parts[1] in {'html', 'markdown', 'pages', 'pages.zip'}
            or bool(re.fullmatch(r'page-\d+(?:\.zip)?', parts[1]))
            or len(parts) > 2 and parts[1] == 'wordpress' and parts[2] in {'blocks', 'wxr'})


def state_digest(document, project):
    return digest({'document': document, 'export': project.get('export', {}), 'source': project.get('source', {}), 'title': project.get('title')})


def register_artifacts(root, document, project, paths):
    """Use the existing export manifest, retaining stamps for other formats."""
    path = root / 'output/reports/export-manifest.json'
    data = json.loads(path.read_text()) if path.is_file() else {'schema_version': 'pdf-to-web-export-manifest-v1'}
    stamp = state_digest(document, project)
    entries = data.setdefault('publication_artifacts', {})
    for file in paths:
        relative = str(file.relative_to(root))
        if is_public_path(relative) and file.is_file():
            entries[relative] = {'source_sha256': stamp, 'file_sha256': hashlib.sha256(file.read_bytes()).hexdigest()}
    from .review_state import _atomic_write
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(path, data)


def require_current_artifact(root, relative):
    if not is_public_path(relative):
        return
    from .normalize import load_normalized
    from .project import load_project
    document = load_normalized(root)
    group = document.get('output_pages', {}).get('pages', [])
    package = Path(relative).parts[1]
    individual = re.fullmatch(r'page-(\d+)(?:\.zip)?', package)
    selected = group[int(individual[1]) - 1:int(individual[1])] if individual else group if package in {'pages', 'pages.zip'} else None
    require_ready(document, selected)
    path = root / 'output/reports/export-manifest.json'
    try:
        data = json.loads(path.read_text())
        entry = data.get('publication_artifacts', {}).get(relative, {})
        file = root / relative
        matches = entry.get('source_sha256') == state_digest(document, load_project(root)) and entry.get('file_sha256') == hashlib.sha256(file.read_bytes()).hexdigest()
    except (OSError, ValueError):
        matches = False
    if not matches:
        raise PdfToWebError('This publication export is outdated. Review current content and generate a fresh export.')
