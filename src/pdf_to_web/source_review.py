"""Saved page-scoped Structure review status, independent of UI filters."""
from .accessibility import visual_readiness
from .exporters.common import is_excluded
from .manual_reconstruction import marked_pages
from .output_pages import source_ranges
from .publication import effective_block_status, readiness_findings


def page_reviews(document, page_count):
    blocks = document.get('blocks', [])
    roots = {str(block['id']): block for block in blocks}
    node_owners = {}
    def visit(node, owner, excluded=False):
        excluded = excluded or is_excluded(node)
        node_owners[str(node['id'])] = (owner, excluded)
        for child in node.get('children', []):
            visit(child, owner, excluded)
    for block in blocks:
        visit(block, str(block['id']))
    pending = {identity for identity, block in roots.items()
               if effective_block_status(block, document) not in {'approved', 'excluded'}}
    # Existing publication validators catch missing alternatives, nested images,
    # association conflicts and malformed content even with an earlier approval.
    for finding in readiness_findings(document):
        target = node_owners.get(str(finding.get('block_id') or ''))
        if target and not target[1]:
            pending.add(target[0])
    associated = {}
    for node in _nodes(blocks):
        if node.get('complex_visual_id'):
            associated.setdefault(str(node['complex_visual_id']), []).append(node_owners[str(node['id'])])
    standalone = []
    for visual in document.get('review', {}).get('complex_visuals', []):
        readiness = visual_readiness(document, visual)
        target = node_owners.get(str(visual.get('source_block_id') or ''))
        if not target:
            candidates = associated.get(str(visual.get('id')), [])
            if len(candidates) == 1:
                target = candidates[0]
        if target:
            if not target[1] and not readiness['complete']:
                pending.add(target[0])  # Image + its descriptions are one task.
        else:
            standalone.append((visual.get('source_page'), readiness['complete']))
    memberships = {identity: {n for start, end in source_ranges([block]) for n in range(start, end + 1)}
                   for identity, block in roots.items()}
    held = marked_pages(document)
    result = {}
    for page in range(1, max(1, int(page_count or 1)) + 1):
        identities = [identity for identity in roots if page in memberships[identity]]
        excluded = sum(is_excluded(roots[identity]) for identity in identities)
        unfinished = sum(identity in pending and not is_excluded(roots[identity]) for identity in identities)
        approved = len(identities) - excluded - unfinished
        descriptions = [complete for source, complete in standalone if source == page]
        completed = approved + excluded + sum(descriptions)
        total = len(identities) + len(descriptions)
        remaining = unfinished + sum(not complete for complete in descriptions)
        reason = ''
        if document.get('review', {}).get('status') == 'conversion_blocked':
            reason = 'Conversion is blocked. Resolve the Document diagnostic before completing page review.'
        elif str(page) in held:
            reason = 'This page needs manual reconstruction; its unfinished content prevents completed review.'
        elif not identities:
            reason = 'No extracted blocks are recorded on this page. Inspect the source PDF; absence alone is not completed review.'
        state = 'needs' if reason or completed == 0 else 'partial' if remaining else 'reviewed'
        label = {'needs': 'Needs review', 'partial': 'Partially Reviewed', 'reviewed': 'Reviewed'}[state]
        detail = (f'Source page {page}: {label}. {approved} reviewed blocks, {excluded} excluded, '
                  f'{unfinished} pending block reviews; {sum(not complete for complete in descriptions)} pending standalone descriptions.')
        if reason:
            detail += ' ' + reason
        elif identities and excluded == len(identities):
            detail += ' All recorded blocks are intentionally excluded; this does not mean content is ready to export.'
        detail += ' Based on saved decisions for the whole page, regardless of filters; this is not export readiness.'
        result[str(page)] = {'state': state, 'label': label, 'detail': detail, 'blocks': len(identities),
                             'approved': approved, 'excluded': excluded, 'pending': remaining,
                             'completed_tasks': completed, 'total_tasks': total}
    return result


def _nodes(blocks):
    for block in blocks:
        yield block
        yield from _nodes(block.get('children', []))
