"""Current, explicitly displayed image/description approval scope."""
from .publication import digest


def review_token(document):
    return digest(document)


def descriptions_for(document, block):
    identity = str(block.get('id'))
    reference = str(block.get('complex_visual_id') or '')
    return [v for v in document.get('review', {}).get('complex_visuals', [])
            if str(v.get('source_block_id') or '') == identity
            or reference and str(v.get('id') or '') == reference]


def description_owner(document, visual):
    """One unambiguous top-level image owns its inline description review."""
    matches = [b for b in document.get('blocks', []) if b.get('type') == 'image'
               and visual in descriptions_for(document, b)]
    return matches[0] if len(matches) == 1 and not association_issue(document, matches[0]) else None


def pending_descriptions_for(document, block):
    from .accessibility import visual_readiness
    return [v for v in descriptions_for(document, block) if not visual_readiness(document, v)['complete']]


def validate_associations(document, block):
    from .accessibility import _walk
    records = descriptions_for(document, block)
    if records and block.get('type') != 'image':
        raise ValueError('The description target is not an image. Verify the association before approval.')
    all_records = document.get('review', {}).get('complex_visuals', [])
    reference = str(block.get('complex_visual_id') or '')
    if reference and not any(str(v.get('id')) == reference for v in records):
        raise ValueError('The image description reference is missing. Verify the association before approval.')
    for visual in records:
        identity = str(visual.get('id') or '')
        owners = [b for b in _walk(document.get('blocks', [])) if str(b.get('complex_visual_id') or '') == identity]
        source = str(visual.get('source_block_id') or '')
        if not identity or sum(str(v.get('id')) == identity for v in all_records) != 1:
            raise ValueError('Duplicate or missing description identity. Verify the association before approval.')
        if source and source != str(block['id']) or any(str(b['id']) != str(block['id']) for b in owners):
            raise ValueError(f'Description {identity} has conflicting image associations. No approval was saved.')
    return records


def association_issue(document, block):
    try:
        validate_associations(document, block)
    except ValueError as exc:
        return str(exc)
    return ''


def validate_token(document, token):
    if not isinstance(token, str) or token != review_token(document):
        raise ValueError('The project changed or the review snapshot is missing. Reload and review the current content before saving or approving.')


def invalidate_image_edit(document, block, previous_records):
    previous = {str(v.get('id')): v for v in previous_records}
    for visual in descriptions_for(document, block):
        old = previous.get(str(visual.get('id')), {})
        visual.setdefault('accessibility', {})['short_alt'] = block.get('alt') or ''
        if old.get('status') in {'reviewed', 'not_applicable'}:
            visual['status'] = 'reclassified'
            visual['review_reason'] = 'changed_after_approval'
            visual['review_change_fields'] = sorted(set(visual.get('review_change_fields', [])) | {'image'})


def approve_descriptions(document, block, displayed_ids):
    from .accessibility import visual_readiness
    from .project import utc_now
    records = validate_associations(document, block)
    ids = [str(v['id']) for v in records]
    if not isinstance(displayed_ids, list) or len(displayed_ids) != len(set(displayed_ids)) or set(displayed_ids) != set(ids):
        raise ValueError('The displayed description selection does not match this image. Reload; no hidden description can be approved.')
    for visual in records:
        if visual.get('status') in {'excluded', 'not_applicable'}:
            continue
        visual.setdefault('accessibility', {})['short_alt'] = block.get('alt') or ''
        if not block.get('decorative') and not visual_readiness(document, visual)['text_complete']:
            raise ValueError(f'Description {visual["id"]}: add alt text and a long description or adjacent text equivalent before approval.')
        visual['status'] = 'not_applicable' if block.get('decorative') else 'reviewed'
        visual['reviewed_at'] = utc_now()
        visual.pop('review_reason', None)
        visual.pop('review_change_fields', None)
