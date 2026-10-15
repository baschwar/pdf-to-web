"""Reversible source-page holds; retained fragments never count as completion."""
import copy

from .image_review import validate_token
from .output_pages import new_page, source_ranges
from .publication import content_digest


def marked_pages(document):
    return document.get('review', {}).get('manual_reconstruction_pages', {})


def managed_ids(document):
    return {identity for entry in marked_pages(document).values() for identity in entry['blocks']}


def require_unmanaged(document, identity):
    if str(identity) in managed_ids(document):
        raise ValueError('This block is held for manual reconstruction. Uncheck its source-page toggle before editing or changing its review state.')


def sync_placeholders(document):
    """Keep one stable placeholder per hold, including after explicit regrouping."""
    group = document['output_pages']['pages']
    active = marked_pages(document)
    for p in group:
        number = p.get('manual_reconstruction_source_page')
        if number and str(number) not in active and p.get('source_page_group') == number and p.get('block_ids'):
            p.pop('manual_reconstruction_source_page')
            if p.get('title') == f'Source page {number} — needs manual reconstruction':
                p['title'] = f'Source page {number}'
                if p.get('slug_mode') == 'auto':
                    from .page_grouping import auto_slug
                    p['slug'] = auto_slug(p['title'], {other.get('slug') for other in group if other is not p})
            p['approval'] = {'status': 'needs_review', 'note': p.get('approval', {}).get('note', '')}
    group[:] = [p for p in group if not p.get('manual_reconstruction_source_page') or str(p['manual_reconstruction_source_page']) in active]
    lookup = {str(b['id']): b for b in document.get('blocks', [])}
    for number, entry in active.items():
        matches = [p for p in group if p.get('manual_reconstruction_source_page') == int(number)]
        if matches:
            entry['placeholder'] = copy.deepcopy(matches[0])
            group[:] = [p for p in group if p not in matches[1:]]
            continue
        placeholder = copy.deepcopy(entry['placeholder'])
        assigned = {ref for p in group for ref in p.get('block_ids', [])}
        placeholder['block_ids'] = [ref for ref in placeholder.get('block_ids', []) if ref not in assigned]
        # Insert beside the page containing retained references, or before the
        # first later source range. Do not split or rewrite an existing page.
        index = next((i + 1 for i, p in enumerate(group) if not p.get('manual_reconstruction_source_page') and set(p['block_ids']) & set(entry['blocks'])), None)
        if index is None:
            index = next((i for i, p in enumerate(group) if any(start > int(number) for start, end in source_ranges([lookup[r] for r in p['block_ids'] if r in lookup]))), len(group))
        neighbor = group[min(index, len(group)-1)] if group else None
        placeholder['navigation_order'] = neighbor.get('navigation_order', 0) if neighbor else 0
        group.insert(index, placeholder)


def toggle(project_dir, page, enabled, token):
    from .review_state import ensure_review_document, save_review_document
    from .project import load_project
    document = ensure_review_document(project_dir)
    validate_token(document, token)
    count = load_project(project_dir).get('source', {}).get('page_count') or 1
    if isinstance(page, bool) or not isinstance(page, int) or not 1 <= page <= count or not isinstance(enabled, bool):
        raise ValueError('Choose an existing source page and a checked or unchecked state.')
    active = marked_pages(document)
    number = str(page)
    if (number in active) == enabled:
        return document
    document.setdefault('review', {})['manual_reconstruction_pages'] = active
    if enabled:
        ids = [str(b['id']) for b in document['blocks']]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate block identities must be resolved before holding a page.')
        snapshots, shared = {}, []
        for block in document['blocks']:
            ranges = source_ranges([block])
            pages = {n for start, end in ranges for n in range(start, end+1)}
            if page not in pages:
                continue
            if pages != {page}:
                shared.append(str(block['id']))
                continue
            snapshots[str(block['id'])] = {'review_present': 'review' in block,
                'review': copy.deepcopy(block.get('review')), 'content_digest': content_digest(block)}
            block.setdefault('review', {})['status'] = 'excluded'
        placeholder = new_page(f'Source page {page} — needs manual reconstruction',
                               manual_reconstruction_source_page=page)
        active[number] = {'blocks': snapshots, 'shared_block_ids': shared, 'placeholder': placeholder}
    else:
        entry = active[number]
        lookup = {str(b['id']): b for b in document['blocks']}
        for identity, snapshot in entry['blocks'].items():
            block = lookup.get(identity)
            if block is None or content_digest(block) != snapshot['content_digest'] or block.get('review', {}).get('status') != 'excluded':
                raise ValueError('Held content changed or is missing. Use Undo or recover it before restoring this page; no partial restoration was saved.')
        for identity, snapshot in entry['blocks'].items():
            if snapshot['review_present']:
                lookup[identity]['review'] = copy.deepcopy(snapshot['review'])
            else:
                lookup[identity].pop('review', None)
        del active[number]
    sync_placeholders(document)
    return save_review_document(project_dir, document)
