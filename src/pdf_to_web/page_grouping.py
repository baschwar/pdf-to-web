"""Read-only arrangement proposals over stable reviewed block references.

Applying and saving a proposal belongs to the review-state transaction layer.
Empty pages and reconstruction holds are intentionally allowed in a proposal;
this module does not establish publication readiness.
"""
from __future__ import annotations

import copy
import hashlib
import re
import unicodedata

from . import output_pages as op


def auto_slug(title, used=()):
    """Return a bounded, unique ASCII filename slug without changing ``used``."""
    normalized = unicodedata.normalize('NFKD', str(title)).encode('ascii', 'ignore').decode()
    base = re.sub(r'[^a-z0-9]+', '-', normalized.lower()).strip('-') or 'page'
    base = base[:100].rstrip('-')
    reserved = set(used) | {'contents', 'publications'}
    slug, number = base, 2
    while slug in reserved:
        suffix = f'-{number}'
        slug = base[:100-len(suffix)].rstrip('-') + suffix
        number += 1
    return slug


def _identity(document, method, key):
    project = document.get('output_pages', {}).get('project_id') or 'legacy'
    digest = hashlib.sha256(f'{project}:{method}:{key}'.encode()).hexdigest()[:32]
    return 'page-' + digest


def group_title(document, refs, fallback):
    """First included H1/H2 in reviewed reading order, including nested content."""
    wanted = set(refs)
    for block in op.visible_walk([b for b in document.get('blocks', []) if str(b['id']) in wanted]):
        if block.get('type') == 'heading' and block.get('level') in (1, 2):
            text = ' '.join(str(block.get('content') or '').split())
            if text:
                return text
    return fallback


def generated_title(document, page):
    """Recognize tracked generation or the exact prior source-builder default."""
    if page.get('title_mode') == 'custom' or page.get('manual_reconstruction_source_page'):
        return False
    if 'title_mode' in page or 'generated_title' in page:
        return page.get('title_mode') == 'auto' and page.get('generated_title') == page.get('title')
    n = page.get('source_page_group')
    if not n:
        return False
    legacy = f"{document.get('metadata', {}).get('title') or 'Document'} — Page {n}"
    identity = _identity(document, 'source', str(n) + ':' + ','.join(page.get('block_ids', [])))
    return page.get('title') == legacy and page.get('id') == identity


def _bundles(document):
    """Transitive top-level semantic closure, including excluded restoration refs."""
    blocks = document.get('blocks', [])
    identities = [str(b['id']) for b in blocks]
    parents = {identity: identity for identity in identities}
    def root(identity):
        while parents[identity] != identity:
            identity = parents[identity]
        return identity
    units = op.semantic_units(document)
    # Captions remain attached even if either side is currently excluded.
    units += [{str(b['id']), str(b['caption_block_id'])} for b in blocks if b.get('caption_block_id')]
    for unit in units:
        members = [i for i in identities if i in unit]
        for identity in members[1:]:
            parents[root(identity)] = root(members[0])
    groups = {}
    for identity in identities:
        groups.setdefault(root(identity), []).append(identity)
    return list(groups.values())


def _sources(blocks):
    # Boolean values are not physical page numbers.
    values = set()
    for b in op.walk(blocks):
        provenance = b.get('provenance', {})
        for value in [provenance.get('source_page'), *provenance.get('merged_source_pages', [])]:
            if isinstance(value, int) and not isinstance(value, bool):
                values.add(value)
    return sorted(values)


def plan(document, page_count, method, selected=None, choices=None):
    """Propose source groups or selected heading groups; never mutate input.

    Source choices map a bundle's first block ID to a physical page number.
    Heading selection uses zero-based indexes from ``groups``. An empty heading
    selection keeps the complete existing arrangement unchanged.
    """
    selected, choices = list(selected or []), dict(choices or {})
    result = {'method': method, 'pages': [], 'groups': [], 'moves': [],
              'effects': [], 'exceptions': [], 'errors': [], 'notes': []}
    old = copy.deepcopy(document.get('output_pages', {}).get('pages', []))
    blocks = document.get('blocks', [])
    ids = [str(b.get('id', '')) for b in blocks]
    if len(ids) != len(set(ids)) or any(not i for i in ids):
        result['errors'].append('Resolve missing or duplicate block identities before grouping.')
    old_ids = [p['id'] for p in old]
    old_refs = [ref for p in old for ref in p.get('block_ids', [])]
    if len(old_ids) != len(set(old_ids)):
        result['errors'].append('Resolve duplicate output page identities before grouping.')
    if len(old_refs) != len(set(old_refs)):
        result['errors'].append('Resolve duplicate block assignments before grouping.')
    missing_refs = [ref for ref in old_refs if ref not in ids]
    if missing_refs:
        result['errors'].append('Recover missing block references with Undo before grouping: ' + ', '.join(missing_refs))
    if method not in {'source', 'headings', 'titles'}:
        result['errors'].append('Choose source pages, heading sections or generated title refresh.')
    if isinstance(page_count, bool) or not isinstance(page_count, int) or page_count < 1:
        result['errors'].append('Choose a valid physical source page count.')
    if result['errors']:
        result['pages'] = old
        result['can_apply'] = False
        return result
    lookup = dict(zip(ids, blocks))
    bundles = _bundles(document)
    used = {p.get('slug', '') for p in old}
    claimed = set()

    def refresh_title(p, title):
        before = {key: p.get(key) for key in ('title', 'slug')}
        if p['title'] != title:
            p['title'] = title
            if p.get('slug_mode') == 'auto':
                reserved = used - {p['slug']} if sum(item.get('slug') == p['slug'] for item in old) == 1 else used
                p['slug'] = auto_slug(title, reserved)
                used.add(p['slug'])
            result['effects'].append({'page_id': p['id'], 'title': before['title'], 'action': 'refresh_title',
                'fields': {key: {'before': before[key], 'after': p[key]} for key in before if before[key] != p[key]}})
        p['title_mode'], p['generated_title'] = 'auto', title

    if method == 'titles':
        result['pages'] = old
        for i, p in enumerate(old):
            if not generated_title(document, p):
                result['notes'].append(f"Keep existing title and slug: {p['title']}.")
                continue
            n = p.get('source_page_group')
            title = group_title(document, p['block_ids'], f'Source page {n}' if n else f'Page {i + 1}')
            refresh_title(p, title)
        result['can_apply'] = bool(result['effects'])
        if not result['can_apply']:
            result['notes'].append('No recognized generated page titles need updating. Custom titles and slugs remain unchanged.')
        return result

    def candidate(title, refs, key, order):
        matches = [p for p in old if not p.get('manual_reconstruction_source_page')
                   and p['id'] not in claimed and set(p.get('block_ids', [])) == set(refs)
                   and (refs or (method == 'source' and p.get('source_page_group') == int(key)))]
        if len(matches) == 1:
            p = copy.deepcopy(matches[0])
            claimed.add(p['id'])
            p['block_ids'] = list(refs)
            if generated_title(document, p):
                refresh_title(p, title)
        else:
            slug = auto_slug(title, used)
            used.add(slug)
            p = {'id': _identity(document, method, key+':'+','.join(refs)), 'title': str(title),
                 'slug': slug, 'slug_mode': 'auto', 'type': 'page', 'parent': None,
                 'title_mode': 'auto', 'generated_title': str(title),
                 'navigation_order': order, 'block_ids': list(refs),
                 'approval': {'status': 'needs_review', 'note': ''}}
        return p

    held = document.get('review', {}).get('manual_reconstruction_pages', {})
    if method == 'source':
        assignments = {n: [] for n in range(1, page_count+1)}
        managed = {identity: int(number) for number, entry in held.items()
                   for identity in entry.get('blocks', {})}
        for bundle in bundles:
            source = _sources([lookup[i] for i in bundle])
            hold_pages = {managed[i] for i in bundle if i in managed}
            destination = next(iter(hold_pages)) if len(hold_pages) == 1 and all(i in managed for i in bundle) else None
            if destination is None and len(source) == 1 and 1 <= source[0] <= page_count and str(source[0]) not in held:
                destination = source[0]
            if destination is None:
                chosen = choices.get(bundle[0])
                if isinstance(chosen, int) and not isinstance(chosen, bool) and chosen in assignments and str(chosen) not in held and not hold_pages:
                    destination = chosen
                reason = 'Shared source pages' if len(source) > 1 else 'No source page' if not source else 'Source page unavailable or held'
                exception = {'key': bundle[0], 'label': f'{reason}: {bundle[0]}',
                             'block_ids': bundle, 'source_pages': source, 'reason': reason,
                             'destination': destination, 'resolved': destination is not None,
                             'held_source_pages': sorted(hold_pages)}
                result['exceptions'].append(exception)
                if destination is None:
                    result['errors'].append(f'Choose an available source page for {bundle[0]}.')
            if destination in assignments:
                assignments[destination].extend(bundle)
        for n, refs in assignments.items():
            refs.sort(key=ids.index)
            entry = held.get(str(n))
            if entry:
                p = next((copy.deepcopy(p) for p in old if p.get('manual_reconstruction_source_page') == n), None)
                p = p or copy.deepcopy(entry['placeholder'])
                p['block_ids'] = refs
                claimed.add(p['id'])
                result['notes'].append(f'Source page {n} remains an unfinished reconstruction placeholder. Restoration retains its fragments on an ordinary output page.')
            else:
                title = group_title(document, refs, f'Source page {n}')
                p = candidate(title, refs, str(n), n-1)
            if p['id'] in claimed and p.get('navigation_order') != n-1:
                result['effects'].append({'page_id': p['id'], 'title': p['title'], 'action': 'source_order',
                    'fields': {'navigation_order': {'before': p.get('navigation_order'), 'after': n-1}}})
            p['navigation_order'] = n-1
            p['source_page_group'] = n
            result['pages'].append(p)
            result['groups'].append({'key': str(n), 'index': n-1, 'title': p['title'],
                'source_pages': [n], 'block_ids': refs, 'page_id': p['id'], 'selected': True})
        for p in old:
            if not p.get('block_ids') and p['id'] not in claimed and not p.get('manual_reconstruction_source_page'):
                extra = copy.deepcopy(p)
                order = len(result['pages'])
                if extra.get('navigation_order') != order:
                    result['effects'].append({'page_id': extra['id'], 'title': extra['title'], 'action': 'source_order',
                        'fields': {'navigation_order': {'before': extra.get('navigation_order'), 'after': order}}})
                extra['navigation_order'] = order
                result['pages'].append(extra)
                claimed.add(p['id'])
                result['notes'].append(f"Existing empty page retained: {p['title']}.")
        remaining_ids = {p['id'] for p in result['pages']}
        for p in result['pages']:
            if p.get('parent') and p['parent'] not in remaining_ids:
                result['effects'].append({'page_id': p['id'], 'title': p['title'], 'action': 'reset_parent', 'fields': {'parent': {'before': p['parent'], 'after': None}}})
                p['parent'] = None
        for p in old:
            if p['id'] not in remaining_ids:
                result['effects'].append({'page_id': p['id'], 'title': p['title'], 'action': 'replace',
                    'fields': {k: {'before': copy.deepcopy(p.get(k)), 'after': None} for k in ('title', 'slug', 'type', 'parent', 'navigation_order', 'approval')}})
    else:
        # Existing heading policy supplies suggestion boundaries. Associate
        # excluded refs with their nearest preceding suggested group, without
        # dropping them when a group is selected.
        suggestions = op.suggest(copy.deepcopy(document))
        held_ids = {identity for entry in held.values() for identity in entry.get('blocks', {})}
        group_of = {ref: i for i, s in enumerate(suggestions) for ref in s['block_ids'] if ref not in held_ids}
        cursor = 0
        for identity in ids:
            if identity in held_ids:
                continue
            if identity in group_of:
                cursor = group_of[identity]
            elif suggestions:
                group_of[identity] = cursor
        proposals = [[i for i in ids if group_of.get(i) == n] for n in range(len(suggestions))]
        for n, (s, refs) in enumerate(zip(suggestions, proposals)):
            title = group_title(document, refs, f'Page {n + 1}')
            result['groups'].append({'key': str(n), 'index': n, 'title': title,
                'source_pages': _sources([lookup[i] for i in refs]), 'block_ids': refs, 'selected': n in selected})
        if any(isinstance(i, bool) or not isinstance(i, int) or not 0 <= i < len(proposals) for i in selected) or len(selected) != len(set(selected)):
            result['errors'].append('Select each existing heading group at most once.')
            selected = []
        moving = {ref for n in selected for ref in proposals[n]}
        for bundle in bundles:
            targets = {group_of.get(i) if i in moving else 'unchanged' for i in bundle}
            if len(targets) > 1 and any(i in moving for i in bundle):
                result['errors'].append('Keep semantic bundle together: ' + ', '.join(bundle))
        if moving & held_ids:
            result['errors'].append('Restore held source pages before grouping their fragments.')
        result['pages'] = copy.deepcopy(old)
        for n in selected:
            p = candidate(group_title(document, proposals[n], f'Page {n + 1}'), proposals[n], str(n)+':'+','.join(proposals[n]), len(old)+n)
            result['groups'][n]['page_id'] = p['id']
            if p['id'] in {item['id'] for item in old}:
                result['pages'] = [p if item['id'] == p['id'] else item for item in result['pages']]
                continue
            for item in result['pages']:
                item['block_ids'] = [i for i in item.get('block_ids', []) if i not in proposals[n]]
            result['pages'].append(p)
        # Residual pages retain every metadata field, even when emptied.
        for p in result['pages']:
            previous = next((item for item in old if item['id'] == p['id']), None)
            if previous and previous.get('block_ids') != p.get('block_ids'):
                result['effects'].append({'page_id': p['id'], 'title': p['title'], 'action': 'assignments_changed',
                    'fields': {'block_ids': {'before': previous.get('block_ids', []), 'after': p.get('block_ids', [])}}})

    before = {ref: p['id'] for p in old for ref in p.get('block_ids', [])}
    after = {ref: p['id'] for p in result['pages'] for ref in p.get('block_ids', [])}
    titles = {p['id']: p['title'] for p in old + result['pages']}
    for identity in ids:
        if before.get(identity) != after.get(identity):
            result['moves'].append({'block_id': identity, 'from_page_id': before.get(identity),
                'to_page_id': after.get(identity), 'from_title': titles.get(before.get(identity), 'Unassigned'),
                'to_title': titles.get(after.get(identity), 'Unassigned')})
    assigned = [ref for p in result['pages'] for ref in p.get('block_ids', [])]
    if len(assigned) != len(set(assigned)):
        result['errors'].append('Duplicate block assignments must be resolved before applying.')
    missing = [i for i in ids if not op.is_excluded(lookup[i]) and i not in after]
    if missing:
        result['errors'].append('Unassigned included content: ' + ', '.join(missing))
    for p in result['pages']:
        refs = p.get('block_ids', [])
        if not p.get('manual_reconstruction_source_page') and not any(i in lookup and not op.is_excluded(lookup[i]) for i in refs):
            result['notes'].append(f"{p['title']}: no included content; page publication remains incomplete.")
    if method == 'headings' and not selected:
        result['notes'].append('Select at least one heading suggestion to apply.')
    result['can_apply'] = not result['errors'] and (method != 'headings' or bool(selected))
    return result
