"""Explicit, current Accessibility selections saved in one existing Undo revision."""
import copy

from .accessibility import assess_document, save_decision, visual_readiness
from .image_review import descriptions_for, review_token, validate_associations, validate_token
from .publication import effective_block_status

STATES = {
    'block': ('approved', 'needs_review', 'excluded'),
    'description': ('reviewed', 'reclassified', 'not_applicable', 'excluded'),
    'decision': ('approved', 'unresolved', 'not_applicable'),
}


def records(document):
    rows = []
    for index, block in enumerate(document.get('blocks', []), 1):
        rows.append({'id': 'block:' + str(block['id']), 'kind': 'block', 'target_id': str(block['id']),
                     'classification': 'Blocks · ' + str(block.get('type', 'unknown')),
                     'label': f'Block {index}: {block.get("type", "unknown")}' + (f' H{block.get("level", 2)}' if block.get('type') == 'heading' else ''),
                     'state': effective_block_status(block, document), 'block': block})
    for visual in document.get('review', {}).get('complex_visuals', []):
        rows.append({'id': 'description:' + str(visual['id']), 'kind': 'description', 'target_id': str(visual['id']),
                     'classification': 'Descriptions · ' + str(visual.get('type') or 'image'),
                     'label': 'Description ' + str(visual['id']), 'state': str(visual.get('status') or 'needs_text_equivalent'),
                     'visual': visual})
    for item in assess_document(document)['items']:
        if item['decision_allowed'] and not item.get('resolved_by_review'):
            rows.append({'id': 'decision:' + item['id'], 'kind': 'decision', 'target_id': item['id'],
                         'classification': 'Decisions · ' + item['category'], 'label': item['title'],
                         'state': item['status'], 'item': item})
    for row in rows:
        row['pending'] = (row['state'] in {'unreviewed', 'needs_review'} if row['kind'] == 'block'
                          else not visual_readiness(document, row['visual'])['complete'] if row['kind'] == 'description'
                          else row['state'] == 'unresolved')
    return rows


def visible_records(document, classification='', review_scope='pending'):
    if review_scope not in {'pending', 'completed', 'all'}:
        raise ValueError('Choose Pending, Completed or All review records.')
    return [row for row in records(document)
            if (not classification or row['classification'] == classification)
            and (review_scope == 'all' or row['pending'] == (review_scope == 'pending'))]


def apply_batch(project_dir, data):
    from .review_state import ensure_review_document, save_review_document, _edit_block, _approve_block, _find_location
    from .project import utc_now
    from .exporters.common import is_excluded
    if not isinstance(data, dict):
        raise ValueError('A current explicit review selection is required.')
    document = ensure_review_document(project_dir)
    validate_token(document, data.get('expected_review_token'))
    if data.get('project_id') != document['output_pages']['project_id']:
        raise ValueError('The selected project changed. Reload before applying review decisions.')
    rows = records(document)
    catalog = {row['id']: row for row in rows}
    if len(catalog) != len(rows):
        raise ValueError('Duplicate review identities prevent a safe batch. No changes were saved.')
    classification = data.get('classification', '')
    # Older clients submitted the whole catalog; the new UI explicitly sends its
    # pending/completed scope so hidden rows cannot enter a visible selection.
    review_scope = data.get('review_scope', 'all')
    visible = [row['id'] for row in visible_records(document, classification, review_scope)]
    submitted_visible = data.get('visible_ids')
    selected = data.get('selected_ids')
    if not isinstance(submitted_visible, list) or len(submitted_visible) != len(set(submitted_visible)) or set(submitted_visible) != set(visible):
        raise ValueError('The visible review scope changed. Reload and select the records again.')
    if not isinstance(selected, list) or not selected or any(not isinstance(v, str) for v in selected) or len(selected) != len(set(selected)):
        raise ValueError('Select distinct current review records before applying a state.')
    if not set(selected).issubset(set(visible)):
        raise ValueError('The selection includes hidden or missing records. No changes were saved.')
    kinds = {catalog[identity]['kind'] for identity in selected}
    if len(kinds) != 1:
        raise ValueError('Select one record type: block approvals, description reviews, or accessibility decisions. These states are separate.')
    kind = kinds.pop()
    status = data.get('status')
    if status not in STATES[kind]:
        raise ValueError(f'{status!r} is not a permitted state for {kind} records.')
    working = copy.deepcopy(document)
    errors = []
    for identity in selected:
        row = catalog[identity]
        try:
            if kind == 'block':
                block = _find_location(working['blocks'], row['target_id'])[2]
                if status == 'approved':
                    if is_excluded(block):
                        raise ValueError('Include this block before approving it')
                    if block.get('type') == 'image':
                        ids = [str(v['id']) for v in validate_associations(working, block)]
                        _edit_block(working, row['target_id'], {'expected_review_token': review_token(working),
                                    'displayed_description_ids': ids}, approve_after_save=True)
                    else:
                        if block.get('type') == 'table' and not block.get('table_accessibility', {}).get('reviewed'):
                            raise ValueError('Review and save the table structure in its editor before batch approval')
                        _approve_block(block)
                else:
                    _edit_block(working, row['target_id'], {'review_status': status})
            elif kind == 'description':
                visual = next(v for v in working['review']['complex_visuals'] if str(v['id']) == row['target_id'])
                block = _find_location(working['blocks'], str(visual['source_block_id']))[2] if visual.get('source_block_id') else None
                if status == 'reviewed':
                    if visual.get('status') == 'excluded' or block and is_excluded(block):
                        raise ValueError('Restore the excluded description/image before marking it Reviewed')
                    if block:
                        validate_associations(working, block)
                    candidate = copy.deepcopy(visual)
                    candidate['status'] = 'reclassified'
                    if not visual_readiness(working, candidate)['text_complete']:
                        raise ValueError('Text is missing: provide alt text and a long description or adjacent text equivalent')
                    if block:
                        _approve_block(block)
                visual['status'] = status
                visual['reviewed_at'] = utc_now()
                if status in {'reviewed', 'not_applicable', 'excluded'}:
                    visual.pop('review_reason', None)
                    visual.pop('review_change_fields', None)
            else:
                save_decision(working, row['target_id'], status, row['item'].get('note', ''))
        except (ValueError, KeyError) as exc:
            errors.append(f'{row["label"]}: {exc}')
    if errors:
        raise ValueError('No changes saved. ' + '; '.join(errors))
    save_review_document(project_dir, working)
    return working, len(selected)
