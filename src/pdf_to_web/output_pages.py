"""Persistent page references and local grouping; content remains in reviewed blocks."""
from __future__ import annotations

import copy
import re
import uuid
from typing import Any

from .accessibility import assess_document
from .exporters.common import is_excluded, standalone_description_blocks
from .project import slugify

SCHEMA = 'pdf-to-web-output-pages-v1'


def walk(blocks):
    for block in blocks:
        yield block
        yield from walk(block.get('children', []))


def visible_walk(blocks):
    for block in blocks:
        if is_excluded(block):
            continue
        yield block
        yield from visible_walk(block.get('children', []))


def new_page(title, block_ids=(), **metadata):
    return {'id': 'page-' + uuid.uuid4().hex, 'title': str(title), 'slug': slugify(str(title))[:100].rstrip('-'),
            'type': 'page', 'parent': None, 'navigation_order': 0,
            'block_ids': list(block_ids), 'approval': {'status': 'needs_review', 'note': ''}, **metadata}


def ensure_pages(document):
    if 'output_pages' in document:
        if document['output_pages'].get('schema_version') != SCHEMA:
            raise ValueError('Unsupported output-page schema')
        if not document['output_pages'].get('project_id'):
            document['output_pages']['project_id'] = 'project-' + uuid.uuid4().hex
            return True
        return False
    document['output_pages'] = {'schema_version': SCHEMA, 'project_id': 'project-' + uuid.uuid4().hex, 'pages': [new_page(
        document.get('metadata', {}).get('title') or 'Document',
        [str(b['id']) for b in document.get('blocks', [])])]}
    return True


def pages(document):
    ensure_pages(document)
    return document['output_pages']['pages']


def page_by_id(document, page_id):
    return next((p for p in pages(document) if p['id'] == page_id), None)


def included(document):
    return [b for b in document.get('blocks', []) if not is_excluded(b)]


def source_ranges(blocks):
    values = set()
    for block in walk(blocks):
        provenance = block.get('provenance', {})
        for value in [provenance.get('source_page'), *provenance.get('merged_source_pages', [])]:
            if isinstance(value, int) and value > 0:
                values.add(value)
    ranges = []
    for value in sorted(values):
        if ranges and value == ranges[-1][1] + 1:
            ranges[-1][1] = value
        else:
            ranges.append([value, value])
    return ranges


def semantic_units(document):
    """Top-level reference sets that must travel together."""
    units = []
    for b in included(document):
        if b.get('caption_block_id'):
            units.append({str(b['id']), str(b['caption_block_id'])})
    for visual in document.get('review', {}).get('complex_visuals', []):
        if visual.get('status') == 'excluded':
            continue
        images = [b for b in included(document) if b.get('type') == 'image' and (str(b['id']) == visual['source_block_id'] if visual.get('source_block_id') else b.get('provenance', {}).get('source_page') == visual.get('source_page'))]
        unit = {str(b['id']) for b in images}
        unit.update(str(b['caption_block_id']) for b in images if b.get('caption_block_id'))
        if unit:
            units.append(unit)
    return units


def validate(document):
    errors = []
    group = pages(document)
    ids = [p['id'] for p in group]
    slugs = [p.get('slug') for p in group]
    blocks = {str(b['id']): b for b in document.get('blocks', [])}
    required = {str(b['id']) for b in included(document)}
    assigned = []
    for p in group:
        label = p.get('title') or p['id']
        if not str(p.get('title', '')).strip():
            errors.append(f'{label}: enter a title')
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', str(p.get('slug', ''))) or len(p.get('slug', '')) > 100:
            errors.append(f'{label}: use a slug of at most 100 lowercase letters, digits and hyphens')
        if p.get('slug') in {'contents', 'publications'}:
            errors.append(f'{label}: this slug is reserved for package files')
        if p.get('type') not in {'page', 'post'}:
            errors.append(f'{label}: choose Page or Article')
        if not isinstance(p.get('navigation_order'), int) or p.get('navigation_order', 0) < 0:
            errors.append(f'{label}: contents order must be a nonnegative integer')
        refs = p.get('block_ids', [])
        assigned.extend(refs)
        if not any(ref in required for ref in refs):
            errors.append(f'{label}: assign included content or merge this empty page')
        for ref in refs:
            if ref not in blocks:
                errors.append(f'{label}: missing block {ref}; recover with Undo or remove its reference')
        parent = p.get('parent')
        if parent:
            target = page_by_id(document, parent)
            if p.get('type') != 'page' or not target or target.get('type') != 'page':
                errors.append(f'{label}: parents must be internal Pages; Articles have no parent')
            visited = {p['id']}
            while target:
                if target['id'] in visited:
                    errors.append(f'{label}: parent cycle')
                    break
                visited.add(target['id'])
                target = page_by_id(document, target.get('parent'))
    if len(ids) != len(set(ids)):
        errors.append('Duplicate page identities')
    if len(slugs) != len(set(slugs)):
        errors.append('Duplicate slugs; give each page a unique slug')
    if len(assigned) != len(set(assigned)):
        errors.append('Duplicate block assignments; assign each block once')
    owners = {ref: p['id'] for p in group for ref in p['block_ids']}
    for b in blocks.values():
        caption = b.get('caption_block_id')
        if caption in required and str(b['id']) in required and owners.get(str(b['id'])) != owners.get(caption):
            errors.append(f'Keep image {b["id"]} and caption {caption} on the same page')
    for unit in semantic_units(document):
        active = unit & required
        if len({owners.get(ref) for ref in active}) > 1:
            errors.append('Keep the complex visual and its descriptions together: ' + ', '.join(sorted(active)))
    missing = required - set(assigned)
    if missing:
        errors.append('Unassigned content: ' + ', '.join(sorted(missing)))
    if not group:
        errors.append('Create an output page')
    return errors


def suggest(document):
    result = []
    used = set()
    for block in included(document):
        boundary = (block.get('type') == 'heading' and int(block.get('level', 2)) <= 2) or block.get('section_boundary')
        if not result or boundary:
            title = block.get('content') if boundary else document.get('metadata', {}).get('title', 'Document')
            base = slugify(str(title or 'Section'))[:96].rstrip('-')
            slug = base
            number = 2
            while slug in used:
                slug = f'{base}-{number}'
                number += 1
            used.add(slug)
            result.append({'title': title or 'Section', 'slug': slug, 'block_ids': [], 'source_ranges': []})
        result[-1]['block_ids'].append(str(block['id']))
    for unit in semantic_units(document):
        indexes = [i for i, item in enumerate(result) if unit.intersection(item['block_ids'])]
        if len(indexes) > 1:
            start, end = min(indexes), max(indexes)
            result[start]['block_ids'] = [ref for item in result[start:end + 1] for ref in item['block_ids']]
            del result[start + 1:end + 1]
    lookup = {str(b['id']): b for b in included(document)}
    for item in result:
        item['source_ranges'] = source_ranges([lookup[i] for i in item['block_ids']])
    return result


def reconcile(document, previous):
    """Track Structure split/merge/move, retain excluded refs for restore, flag deletions."""
    ensure_pages(document)
    old_blocks = {str(b['id']): b for b in previous.get('blocks', [])}
    blocks = document.get('blocks', [])
    current_ids = {str(b['id']) for b in blocks}
    for p in pages(document):
        for block in blocks:
            changes = block.get('provenance', {}).get('review_changes', [])
            for change in changes:
                source = str(change.get('source_block_id', ''))
                if change.get('action') == 'split' and source in p['block_ids'] and str(block['id']) not in p['block_ids']:
                    p['block_ids'].insert(p['block_ids'].index(source) + 1, str(block['id']))
                merged = str(change.get('merged_block_id', ''))
                if change.get('action') == 'merge' and merged not in current_ids and merged in p['block_ids']:
                    p['block_ids'].remove(merged)
        # Reading order follows Structure, independently of contents order.
        positions = {str(b['id']): i for i, b in enumerate(blocks)}
        p['block_ids'].sort(key=lambda i: positions.get(i, len(positions)))
        old_page = page_by_id(previous, p['id'])
        changed = old_page is None or any(old_page.get(k) != p.get(k) for k in ('title', 'slug', 'type', 'parent', 'navigation_order', 'block_ids'))
        relevant = set(p['block_ids']) | set((old_page or {}).get('block_ids', []))
        changed |= any(old_blocks.get(i) != next((b for b in blocks if str(b['id']) == i), None) for i in relevant)
        if old_page and not changed:
            def ancestors(doc, item):
                result, visited = [], set()
                while item and item.get('parent') not in visited:
                    visited.add(item.get('parent'))
                    item = page_by_id(doc, item.get('parent'))
                    if item:
                        result.append({k: item.get(k) for k in ('id', 'title', 'slug', 'type', 'parent', 'navigation_order')})
                return result
            changed |= ancestors(previous, old_page) != ancestors(document, p)
            # Slug/assignment changes on another page can change links on this page.
            changed |= page_document(previous, p['id']).get('output_link_mappings') != page_document(document, p['id']).get('output_link_mappings')
            changed |= page_document(previous, p['id']).get('output_unresolved_targets') != page_document(document, p['id']).get('output_unresolved_targets')
        # Document-level diagnostics and human decisions apply to every page.
        changed |= previous.get('review') != document.get('review') or previous.get('accessibility_review') != document.get('accessibility_review')
        changed |= previous.get('publication') != document.get('publication')
        if changed:
            p['approval'] = {'status': 'needs_review', 'note': p.get('approval', {}).get('note', '')}


def mutate(document, action, data):
    group = pages(document)
    p = page_by_id(document, data.get('page_id'))
    if action == 'single_page':
        p = p or (group[0] if group else new_page(document.get('metadata', {}).get('title') or 'Document'))
        p['block_ids'] = [str(b['id']) for b in document.get('blocks', [])]
        p['parent'], p['navigation_order'] = None, 0
        document['output_pages']['pages'] = [p]
        return p['id']
    if action == 'apply_suggestions':
        document['output_pages']['pages'] = [new_page(s['title'], s['block_ids'], slug=s['slug'], navigation_order=i) for i, s in enumerate(suggest(document))]
        return document['output_pages']['pages'][0]['id'] if group else None
    if action == 'create':
        p = new_page(data.get('title') or 'New page', navigation_order=len(group))
        # Creation is explicit; an empty page stays visible and blocks export.
        group.append(p)
        return p['id']
    if p is None:
        raise ValueError('Select an existing output page')
    if action == 'assign_unassigned':
        assigned = {ref for item in group for ref in item['block_ids']}
        for block in included(document):
            if str(block['id']) not in assigned:
                mutate(document, 'assign', {'page_id': p['id'], 'block_id': block['id']})
    elif action == 'metadata':
        for key in ('title', 'slug', 'type', 'parent', 'navigation_order'):
            if key in data:
                p[key] = int(data[key]) if key == 'navigation_order' else data[key] or (None if key == 'parent' else '')
    elif action == 'assign':
        ref = str(data.get('block_id'))
        if ref not in {str(b['id']) for b in document.get('blocks', [])}:
            raise ValueError('Select a complete top-level content block')
        related = {ref}
        for b in document['blocks']:
            if str(b['id']) == ref and b.get('caption_block_id'):
                related.add(b['caption_block_id'])
            if b.get('caption_block_id') == ref:
                related.add(str(b['id']))
        for unit in semantic_units(document):
            if unit.intersection(related):
                related.update(unit)
        for item in group:
            item['block_ids'] = [i for i in item['block_ids'] if i not in related]
        p['block_ids'].extend(str(b['id']) for b in document['blocks'] if str(b['id']) in related)
    elif action == 'remove_reference':
        ref = str(data.get('block_id'))
        if ref in {str(b['id']) for b in document.get('blocks', [])}:
            raise ValueError('Move existing content to another page instead')
        p['block_ids'] = [i for i in p['block_ids'] if i != ref]
    elif action == 'split':
        ref = str(data.get('block_id'))
        if ref not in p['block_ids'] or p['block_ids'].index(ref) == 0:
            raise ValueError('Split before an assigned block after the first block')
        index = p['block_ids'].index(ref)
        for unit in semantic_units(document):
            if unit.intersection(p['block_ids'][:index]) and unit.intersection(p['block_ids'][index:]):
                raise ValueError('Split outside the image and caption or complex visual to keep descriptions intact')
        for b in document['blocks']:
            caption = b.get('caption_block_id')
            if str(b['id']) in p['block_ids'] and caption in p['block_ids']:
                a, z = sorted([p['block_ids'].index(str(b['id'])), p['block_ids'].index(caption)])
                if a < index <= z:
                    raise ValueError('Split before the image to keep its caption intact')
        block = next(b for b in document['blocks'] if str(b['id']) == ref)
        title = block.get('content') if block.get('type') == 'heading' else p['title'] + ' continued'
        new = new_page(title, p['block_ids'][index:], parent=p.get('parent'), navigation_order=p['navigation_order'] + 1)
        base = new['slug']
        n = 2
        while new['slug'] in {item['slug'] for item in group}:
            new['slug'] = f'{base}-{n}'
            n += 1
        p['block_ids'] = p['block_ids'][:index]
        group.insert(group.index(p) + 1, new)
        return new['id']
    elif action == 'merge':
        other = page_by_id(document, data.get('other_id'))
        if other is None or other is p:
            raise ValueError('Choose a different page to merge into this page')
        p['block_ids'].extend(other['block_ids'])
        if p.get('parent') == other['id']:
            p['parent'] = other.get('parent')
        for item in group:
            if item.get('parent') == other['id']:
                item['parent'] = p['id']
        group.remove(other)
    elif action == 'reorder':
        index = group.index(p)
        target = index + (-1 if data.get('direction') == 'up' else 1)
        if target < 0 or target >= len(group):
            raise ValueError('Page is already at that boundary')
        group.insert(target, group.pop(index))
        for i, item in enumerate(group):
            item['navigation_order'] = i
    elif action == 'approve':
        p['approval'] = {'status': 'reviewed', 'note': str(data.get('note') or '')}
    else:
        raise ValueError('Unsupported output-page action')
    return p['id']


def page_document(document, page_id):
    p = page_by_id(document, page_id)
    if p is None:
        raise ValueError('Output page was not found')
    result = copy.deepcopy(document)
    lookup = {str(b['id']): b for b in document.get('blocks', [])}
    result['blocks'] = [copy.deepcopy(lookup[i]) for i in p['block_ids'] if i in lookup and not is_excluded(lookup[i])]
    result.setdefault('metadata', {})['title'] = p['title']
    # An output title is the H1; retain a matching first heading identity, otherwise add a projection-only H1.
    first = result['blocks'][0] if result['blocks'] else {}
    if first.get('type') == 'heading' and first.get('content') == p['title']:
        first['level'] = 1
    else:
        result['blocks'].insert(0, {'id': p['id'] + '-title', 'type': 'heading', 'level': 1, 'content': p['title'], 'review': {'status': 'approved'}})
    refs = [ref for b in visible_walk(result['blocks']) for ref in b.get('footnote_references', [])]
    result['footnotes'] = []
    for note in document.get('footnotes', []):
        bodies = [b for b in walk(document.get('blocks', [])) if b.get('footnote_body_id') == note['id']]
        visible_body_ids = {str(b['id']) for b in visible_walk(document.get('blocks', []))}
        if bodies and not any(str(b['id']) in visible_body_ids for b in bodies):
            continue
        matching = [r for r in refs if r.get('footnote_id') == note['id']]
        body_ids = {str(b['id']) for b in result['blocks']}
        has_live_reference = any(r.get('footnote_id') == note['id'] for b in visible_walk(included(document)) for r in b.get('footnote_references', []))
        owned_body = any(b.get('footnote_body_id') == note['id'] for b in walk(result['blocks'])) or bool(body_ids.intersection(str(i) for i in note.get('source_block_ids', []))) or str(note.get('source_block_id')) in body_ids
        if matching or (not has_live_reference and (owned_body or p is pages(document)[0])):
            n = copy.deepcopy(note)
            n['references'] = copy.deepcopy(matching)
            result['footnotes'].append(n)
    prefix = p['id'] + '-'
    for ref in refs:
        ref['id'] = prefix + str(ref['id'])
        ref['footnote_id'] = prefix + str(ref['footnote_id'])
    for note in result['footnotes']:
        note['id'] = prefix + str(note['id'])
        for ref in note['references']:
            ref['id'] = prefix + str(ref['id'])
            ref['footnote_id'] = prefix + str(ref['footnote_id'])
    ranges = source_ranges(result['blocks'])
    source_pages = {n for start, end in ranges for n in range(start, end + 1)}
    result_ids = {str(b['id']) for b in visible_walk(result['blocks'])}
    result['review']['complex_visuals'] = [v for v in result.get('review', {}).get('complex_visuals', []) if (v['source_block_id'] in result_ids if v.get('source_block_id') else v.get('source_page') in source_pages or not v.get('source_page'))]
    result['review']['issues'] = [i for i in result.get('review', {}).get('issues', []) if not i.get('page') or i.get('page') in source_pages]
    result['blocks'].extend(standalone_description_blocks(result, prefix=prefix))
    result['output_anchor_ids'] = [str(b['id']) for b in visible_walk(result['blocks'])]
    result['output_link_mappings'] = []
    result['output_unresolved_targets'] = []
    owners = {str(b['id']): item for item in pages(document) for i in item['block_ids'] if i in lookup and not is_excluded(lookup[i]) for b in visible_walk([lookup[i]])}
    for b in visible_walk(result['blocks']):
        for run in b.get('runs', []):
            url = str(run.get('url') or run.get('href') or '')
            target = str(run.get('target_block_id') or (url[1:] if url.startswith('#') else ''))
            if not target:
                continue
            owner = owners.get(target)
            if owner:
                resolved = ('#' if owner['id'] == p['id'] else owner['slug'] + '.html#') + target
                run['url'] = resolved
                result['output_link_mappings'].append({'block_id': b['id'], 'target_block_id': target, 'target_page_id': owner['id'], 'url': resolved})
            else:
                result['output_unresolved_targets'].append({'block_id': b['id'], 'target': target})
    known_notes = {n['id'] for n in result['footnotes']}
    for ref in refs:
        if ref['footnote_id'] not in known_notes:
            result['output_unresolved_targets'].append({'target': ref['footnote_id'], 'kind': 'footnote'})
    return result


def status(document, page_id):
    projected = page_document(document, page_id)
    report = assess_document(projected)
    unresolved = projected['output_unresolved_targets']
    return {'structural': 'reviewed' if all(b.get('review', {}).get('status') == 'approved' for b in projected['blocks']) else 'needs_review',
            'accessibility': report, 'approval': copy.deepcopy(page_by_id(document, page_id)['approval']),
            'unresolved_targets': unresolved, 'source_ranges': source_ranges(projected['blocks'])}
