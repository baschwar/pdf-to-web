"""Page-scoped staged permutations, conservative merges and recoverable origins."""
import copy
from urllib.parse import urlparse, unquote
from .exporters.common import is_excluded
from .image_review import review_token, validate_token
from .manual_reconstruction import managed_ids, marked_pages
from .output_pages import source_ranges, pages
from .project import load_project
from .publication import digest
from .review_state import ensure_review_document, save_review_document, review_write_lock, _walk, _set_status
from .source_pages import source_page_size, source_regions_for_blocks

MERGE_KEY = 'reading_order_merge'


def _page_numbers(block):
    return {n for start, end in source_ranges([block]) for n in range(start, end + 1)}


def _fingerprint(block):
    value = copy.deepcopy(block)
    value.setdefault('provenance', {}).pop(MERGE_KEY, None)
    for node in _walk([value]):
        node['_effective_excluded'] = is_excluded(node)
        review = node.get('review', {})
        node['review'] = {key: item for key, item in review.items() if key not in {'status', 'updated_at', 'content_sha256', 'decision_id', 'approval_evidence', 'reason'}}
    return digest(value)


def _owners(document, identity):
    return [page['id'] for page in pages(document) if identity in page['block_ids']]


def _safe_node(block):
    return not any(is_excluded(node) or node.get('footnote_body_id') or node.get('footnote_references')
                   or node.get('source_links') or node.get('caption_block_id') or node.get('complex_visual_id')
                   or node.get('export_as_part_of_image')
                   or any(not isinstance(run, dict) or run.get('type', 'text') != 'text' for run in (node.get('runs') or []))
                   for node in _walk([block]))


def merge_reason(block):
    if block.get('provenance', {}).get(MERGE_KEY):
        return 'Unmerge this row before merging it again.'
    if block.get('type') not in {'paragraph', 'list'}:
        return 'Select paragraphs together, or compatible list blocks. Images, headings and mixed types cannot merge.'
    if not _safe_node(block):
        return 'Links, formatting, notes, excluded items or associated content need separate review; this version cannot merge them safely.'
    if block['type'] == 'paragraph' and not _plain_text(block).strip():
        return 'Recover empty paragraph text before merging.'
    if block['type'] == 'paragraph' and block.get('children'):
        return 'Paragraphs with nested content cannot merge here.'
    if block['type'] == 'list':
        if not block.get('children') or any(child.get('type') != 'list_item' for child in block['children']):
            return 'Recover the list items before merging list blocks.'
        for node in _walk([block]):
            if node.get('type') not in {'list', 'list_item'}:
                return 'Only list items and nested lists can be joined here; associated figures or other nested content need separate review.'
            if node.get('type') == 'list_item' and any(child.get('type') != 'list' for child in node.get('children', [])):
                return 'Nested list items must be inside a nested list block. Repair the list hierarchy first.'
            if node.get('type') == 'list' and (not node.get('children') or any(child.get('type') != 'list_item' for child in node['children'])):
                return 'Recover every nested list before merging.'
    return ''


def _origins(document, block):
    record = block.get('provenance', {}).get(MERGE_KEY)
    if not isinstance(record, dict) or record.get('version') != 1 or not isinstance(record.get('originals'), list):
        raise ValueError('This row has no supported retained merge origins.')
    originals = record['originals']
    if digest(originals) != record.get('originals_digest'):
        raise ValueError('The retained original data changed. Use saved Undo to recover; no original data will be guessed.')
    if len(originals) < 2 or any(not isinstance(b, dict) for b in originals) or str(originals[0].get('id')) != str(block['id']):
        raise ValueError('The retained merge origins are invalid. Use saved Undo to recover.')
    identities = [str(b.get('id', '')) for b in _walk(originals)]
    outside = {str(b['id']) for b in _walk([b for b in document['blocks'] if b is not block])}
    if not all(identities) or len(set(identities)) != len(identities) or outside.intersection(identities):
        raise ValueError('Original identities conflict with current content. Resolve the conflict before unmerging.')
    if _fingerprint(block) != record.get('result_fingerprint'):
        raise ValueError('This merged content or source data was edited. Unmerge would discard those edits. Use saved Undo or review a manual split; no content will be discarded here.')
    return originals


def unmerge_reason(document, block):
    if not block.get('provenance', {}).get(MERGE_KEY):
        return ''
    try:
        _origins(document, block)
        if len(_owners(document, str(block['id']))) > 1:
            raise ValueError('Resolve duplicate page assignments before unmerging.')
    except ValueError as exc:
        return str(exc)
    return ''


def _plain_text(block):
    runs = block.get('runs')
    return ''.join(str(run.get('text') or '') for run in runs) if isinstance(runs, list) else str(block.get('content') or '')


def _preview(block):
    if block.get('type') == 'list':
        return {'kind': 'list', 'ordered': bool(block.get('ordered')), 'start': block.get('start', 1),
                'marker_style': block.get('marker_style'), 'items': [
                    {'text': _plain_text(child), 'children': [_preview(n) for n in child.get('children', [])]}
                    for child in block.get('children', [])]}
    return {'kind': 'text', 'text': _plain_text(block)}


def _scope(document, page):
    ids = [str(b.get('id', '')) for b in _walk(document.get('blocks', []))]
    if not all(ids) or len(ids) != len(set(ids)):
        raise ValueError('Missing or duplicate block identities must be resolved before repairing reading order.')
    rows, excluded, segment = [], [], 0
    held = managed_ids(document)
    for index, block in enumerate(document.get('blocks', [])):
        source_pages = _page_numbers(block)
        if page not in source_pages:
            continue
        identity = str(block['id'])
        text = _plain_text(block) or str(block.get('caption') or block.get('alt') or '')
        if not text:
            text = '\n'.join(str(child.get('content') or '') for child in _walk(block.get('children', [])) if not is_excluded(child))
        reason = 'Held for manual reconstruction' if identity in held else 'Shared across source pages — fixed boundary' if source_pages != {page} else ''
        record = block.get('provenance', {}).get(MERGE_KEY, {})
        record = record if isinstance(record, dict) else {}
        originals = record.get('originals', [])
        originals = originals if isinstance(originals, list) else []
        row = {'id': identity, 'number': index + 1, 'index': index, 'type': block.get('type', 'unknown'),
               'text': text, 'locked': bool(reason), 'reason': reason, 'segment': segment,
               'merge_reason': reason or merge_reason(block), 'merge_count': len(originals),
               'unmerge_reason': unmerge_reason(document, block), 'preview': _preview(block), 'owners': _owners(document, identity),
               'originals': [{'id': b['id'], 'type': b['type'], 'preview': _preview(b)} for b in originals if isinstance(b, dict) and b.get('id') and b.get('type')]}
        if is_excluded(block):
            excluded.append(row)
        else:
            rows.append(row)
            if reason:
                segment += 1
    return rows, excluded


def _validate_page(root, page):
    count = int(load_project(root).get('source', {}).get('page_count') or 1)
    if isinstance(page, bool) or not isinstance(page, int) or not 1 <= page <= count:
        raise ValueError('Choose an existing source page.')


def _view(root, document, page):
    rows, excluded = _scope(document, page)
    movable = {row['id'] for row in rows if not row['locked']}
    regions = source_regions_for_blocks(root, [b for b in document['blocks'] if str(b['id']) in movable])
    try:
        size = source_page_size(root, page)
    except Exception:
        size = None
    for row in rows:
        row['regions'] = regions.get(row['id'], {}).get('regions', []) if size and not row['locked'] else []
    return {'transaction_version': 1, 'project_id': document['output_pages']['project_id'], 'page': page,
            'rows': rows, 'excluded': excluded, 'size': size, 'held': str(page) in marked_pages(document)}


def snapshot(root, page):
    _validate_page(root, page)
    document = ensure_review_document(root)
    return {**_view(root, document, page), 'review_token': review_token(document)}


def _guard(document, page, token, project_id):
    validate_token(document, token)
    if project_id != document['output_pages']['project_id']:
        raise ValueError('The active project changed. Reopen Repair reading order in the current project.')
    if document.get('review', {}).get('status') == 'conversion_blocked':
        raise ValueError('Conversion is blocked. Resolve the document diagnostic before reordering.')
    if str(page) in marked_pages(document):
        raise ValueError('This source page is held for manual reconstruction. Restore it before reordering.')
    store = document.get('image_description_drafts', {})
    if any(e.get('provider') != 'manual' and e.get('status') in {'requested', 'generating'}
           for key in store.get('active', {}).values() if (e := store.get('requests', {}).get(key))):
        raise ValueError('Image generation is active. Wait for completion or cancel it before reordering.')


def _order(document, page, identities):
    rows, _ = _scope(document, page)
    movable = [row for row in rows if not row['locked']]
    current = [row['id'] for row in movable]
    if (not isinstance(identities, list) or any(not isinstance(i, str) for i in identities)
            or len(identities) != len(current) or len(set(identities)) != len(identities) or set(identities) != set(current)):
        raise ValueError('Submit every movable block on this source page exactly once. Excluded, shared, nested and other-page blocks cannot be moved here.')
    lookup = {row['id']: row for row in movable}
    if any(lookup[identity]['segment'] != target['segment'] for identity, target in zip(identities, movable)):
        raise ValueError('Shared source-page blocks are fixed boundaries. Move blocks only within their section.')
    blocks = {str(b['id']): b for b in document['blocks']}
    for target, identity in zip(movable, identities):
        document['blocks'][target['index']] = blocks[identity]


def _merge(document, page, identities):
    if not isinstance(identities, list) or len(identities) < 2 or any(not isinstance(i, str) for i in identities) or len(set(identities)) != len(identities):
        raise ValueError('Select at least two distinct consecutive paragraphs or list blocks.')
    rows, _ = _scope(document, page)
    lookup = {r['id']: r for r in rows}
    if any(i not in lookup or lookup[i]['locked'] for i in identities):
        raise ValueError('Only included blocks on this source page can merge; shared and held blocks stay fixed.')
    indexes = [lookup[i]['index'] for i in identities]
    if indexes != list(range(indexes[0], indexes[0] + len(indexes))):
        raise ValueError('Select consecutive blocks in staged document order. Excluded, other-page and unselected content cannot be skipped.')
    blocks = document['blocks'][indexes[0]:indexes[-1] + 1]
    for block in blocks:
        if reason := merge_reason(block):
            raise ValueError(reason)
    kind = blocks[0]['type']
    for offset, block in enumerate(blocks):
        if block['type'] != kind:
            raise ValueError(f"Block {indexes[0] + 1} is a {kind}, but Block {indexes[0] + offset + 1} is a {block['type']}. "
                             'Mixed types cannot merge. Check their classification against the source; '
                             'merge paragraphs with paragraphs or compatible lists with lists.')
    removed = set(identities[1:])
    for node in _walk(document['blocks']):
        for run in node.get('runs') or []:
            if not isinstance(run, dict):
                continue
            target = str(run.get('target_block_id') or unquote(urlparse(str(run.get('url') or run.get('href') or '')).fragment))
            if target in removed:
                raise ValueError('Another link targets an absorbed block ID. Preserve or resolve that link before merging.')
        if str(node.get('caption_block_id') or '') in removed:
            raise ValueError('An image caption association targets an absorbed block. Resolve the association before merging.')
    if any(str(visual.get('source_block_id') or '') in removed for visual in document.get('review', {}).get('complex_visuals', [])):
        raise ValueError('A description is associated with an absorbed block. Resolve it before merging.')
    if any(removed.intersection(str(identity) for identity in note.get('source_block_ids', [])) or str(note.get('source_block_id') or '') in removed
           for note in document.get('footnotes', [])):
        raise ValueError('A footnote association targets an absorbed block. Resolve it before merging.')
    owners = [_owners(document, b['id']) for b in blocks]
    if any(len(owner) > 1 or owner != owners[0] for owner in owners):
        raise ValueError('The selected blocks have different or duplicate Arrange Pages assignments. Assign them together before merging.')
    if kind == 'list':
        first = blocks[0]
        next_start = first.get('start', 1)
        for block in blocks:
            if bool(block.get('ordered')) != bool(first.get('ordered')) or (block.get('marker_style') or 'decimal') != (first.get('marker_style') or 'decimal'):
                raise ValueError('Ordered/unordered kinds and list marker styles must match.')
            if first.get('ordered'):
                if type(block.get('start', 1)) is not int or block.get('start', 1) < 1 or block.get('start', 1) != next_start:
                    raise ValueError('Ordered lists must continue their recorded numbering; restarts cannot be silently renumbered.')
                next_start += len(block['children'])
    originals = copy.deepcopy(blocks)
    result = copy.deepcopy(blocks[0])
    if kind == 'paragraph':
        # A reviewer sees this exact joining space in the confirmation preview.
        result['content'] = ' '.join(_plain_text(b).strip() for b in blocks)
        result.pop('runs', None)
    else:
        result['children'] = [copy.deepcopy(child) for b in blocks for child in b['children']]
        result['content'] = '\n'.join(_plain_text(child) for child in result['children'])
    provenance = result.setdefault('provenance', {})
    provenance.setdefault('review_changes', []).extend({'action': 'merge', 'merged_block_id': b['id']} for b in blocks[1:])
    provenance[MERGE_KEY] = {'version': 1, 'originals': originals, 'originals_digest': digest(originals), 'assignments': {b['id']: owner for b, owner in zip(blocks, owners)}}
    _set_status(result, 'needs_review')
    provenance[MERGE_KEY]['result_fingerprint'] = _fingerprint(result)
    document['blocks'][indexes[0]:indexes[-1] + 1] = [result]
    for output in pages(document):
        output['block_ids'] = [i for i in output['block_ids'] if i not in identities[1:]]


def _unmerge(document, page, identity):
    rows, _ = _scope(document, page)
    row = next((row for row in rows if row['id'] == identity and not row['locked']), None)
    if not row:
        raise ValueError('Choose an included merged row on this source page.')
    block = document['blocks'][row['index']]
    originals = copy.deepcopy(_origins(document, block))
    owners = _owners(document, identity)
    if len(owners) > 1:
        raise ValueError('Resolve duplicate page assignments before unmerging.')
    document['blocks'][row['index']:row['index'] + 1] = originals
    for output in pages(document):
        if output['id'] in owners:
            at = output['block_ids'].index(identity)
            output['block_ids'][at:at + 1] = [b['id'] for b in originals]


def _plan(document, page, operations):
    if not isinstance(operations, list) or len(operations) > 1000:
        raise ValueError('Submit a supported staged reading-order plan (at most 1000 steps).')
    result = copy.deepcopy(document)
    for operation in operations:
        if not isinstance(operation, dict):
            raise ValueError('Invalid staged reading-order step.')
        action = operation.get('action')
        if action in {'order', 'merge'} and set(operation) == {'action', 'block_ids'}:
            (_order if action == 'order' else _merge)(result, page, operation['block_ids'])
        elif action == 'unmerge' and set(operation) == {'action', 'block_id'} and isinstance(operation['block_id'], str):
            _unmerge(result, page, operation['block_id'])
        else:
            raise ValueError('Choose a supported order, merge or unmerge step.')
    return result


def preview(root, page, operations, token, project_id):
    _validate_page(root, page)
    with review_write_lock:
        document = ensure_review_document(root)
        _guard(document, page, token, project_id)
        return {**_view(root, _plan(document, page, operations), page), 'review_token': token}


def apply(root, page, identities, token, project_id, *, operations=None):
    _validate_page(root, page)
    with review_write_lock:
        document = ensure_review_document(root)
        _guard(document, page, token, project_id)
        result = _plan(document, page, operations if operations is not None else [{'action': 'order', 'block_ids': identities}])
        if result == document:
            return document
        result.setdefault('review_session', {})['manual_order_override'] = True
        return save_review_document(root, result, expected_review_token=token)
