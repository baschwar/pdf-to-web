"""Explicit approval of synthetic fixtures used for publication positive controls."""
from pdf_to_web.review_state import _set_status, _walk, ensure_review_document, save_review_document, update_output_pages


def stamp_fixture_approvals(document):
    for block in reversed(list(_walk(document.get('blocks', [])))):
        if block.get('review', {}).get('status') == 'approved':
            _set_status(block, 'approved')


def approve_publication_fixture(root):
    document = ensure_review_document(root)
    for block in _walk(document.get('blocks', [])):
        if block.get('type') == 'image' and not block.get('decorative'):
            block['alt'] = block.get('alt') or 'Synthetic reviewed image'
        if block.get('review', {}).get('status') != 'excluded' and not block.get('excluded'):
            block.setdefault('review', {})['status'] = 'approved'
    for visual in document.get('review', {}).get('complex_visuals', []):
        if visual.get('status') == 'excluded':
            continue
        a = visual.setdefault('accessibility', {})
        a['short_alt'] = a.get('short_alt') or 'Synthetic reviewed visual'
        a['long_description'] = a.get('long_description') or 'Synthetic reviewed description.'
        visual['status'] = 'reviewed'
    for note in document.get('footnotes', []):
        note['review'] = {'status': 'approved'}
    stamp_fixture_approvals(document)
    from pdf_to_web.output_pages import mutate
    for page in document['output_pages']['pages']:
        mutate(document, 'approve', {'page_id': page['id']})
    save_review_document(root, document, snapshot=False)
    return ensure_review_document(root)
