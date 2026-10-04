"""Explicit restoration of recorded approvals lost to media routing changes.

Planning only reads retained local history. It never creates a review decision
or rewrites a project. Unknown history or a later authored edit fails closed.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

from .accessibility import visual_readiness
from .exporters.common import is_excluded
from .image_review import association_issue, descriptions_for
from .publication import approval_stamp_matches, content_digest, digest
from .review_state import REVIEW_SCHEMA, _review_time, _walk, review_path, save_review_document

MEDIA_FIELDS = {'wordpress_url', 'wordpress_attachment_id', 'wordpress_media'}


def _image(document, identity):
    ids = Counter(str(block.get('id')) for block in _walk(document.get('blocks', [])))
    matches = [block for block in document.get('blocks', [])
               if str(block.get('id')) == identity and block.get('type') == 'image']
    return matches[0] if len(matches) == 1 and ids[identity] == 1 else None


def _descriptions(document, block):
    if association_issue(document, block):
        return None
    records = descriptions_for(document, block)
    if any(not visual_readiness(document, record)['complete'] for record in records):
        return None
    result = []
    for record in records:
        value = copy.deepcopy(record)
        for key in ('reviewed_at', 'review_reason', 'review_change_fields', 'review_note'):
            value.pop(key, None)
        fields = value.setdefault('accessibility', {})
        fields.setdefault('short_alt', block.get('alt') or '')
        for key in ('long_description', 'adjacent_text'):
            fields.setdefault(key, '')
        result.append(value)
    return digest(result)


def _pending_decision(block):
    value = copy.deepcopy(block.get('review', {}))
    # Notes are not a decision; retain the current note when restoring.
    value.pop('note', None)
    return value


def plan_recovery(root: Path, document: dict) -> dict:
    root = Path(root).expanduser().resolve()
    project_id = document.get('output_pages', {}).get('project_id')
    result = {'rows': [], 'token': '', 'project_id': project_id or '',
              'notice': 'No recorded mapping-only approvals are eligible for restoration. Review remaining images individually.'}
    session = document.get('review_session', {})
    created_at = session.get('created_at')
    now = _review_time(session.get('updated_at'))
    if (not project_id or document.get('schema_version') != 'pdf-to-web-normalized-v1'
            or session.get('schema_version') != REVIEW_SCHEMA or not now or not _review_time(created_at)):
        return result
    directory = root / 'review/revisions'
    try:
        if (root / 'review').is_symlink() or directory.is_symlink() or review_path(root).is_symlink():
            return result
        project_bytes = (root / 'project.json').read_bytes()
        states, hashes = [], []
        prior_time = _review_time(created_at)
        for path in sorted(directory.glob('*.json')):
            if path.is_symlink() or not path.is_file() or path.resolve().parent != directory.resolve():
                return result
            raw = path.read_bytes()
            old = json.loads(raw)
            old_session = old.get('review_session', {})
            when = _review_time(old_session.get('updated_at'))
            if (old.get('schema_version') != document['schema_version']
                    or old_session.get('schema_version') != REVIEW_SCHEMA
                    or old.get('output_pages', {}).get('project_id') != project_id
                    or old_session.get('created_at') != created_at or not when
                    or when < prior_time or when > now):
                return result
            prior_time = when
            sha = hashlib.sha256(raw).hexdigest()
            states.append((old, {'snapshot': path.name, 'snapshot_sha256': sha}))
            hashes.append((path.name, sha))
        states.append((document, {'snapshot': 'current.json', 'snapshot_sha256': digest(document)}))
        result['token'] = digest({'root': str(root), 'document': document, 'history': hashes,
                                  'project_sha256': hashlib.sha256(project_bytes).hexdigest()})
        for block in document.get('blocks', []):
            identity = str(block.get('id'))
            review = block.get('review', {})
            if (block.get('type') != 'image' or _image(document, identity) is None or is_excluded(block)
                    or review.get('status') != 'needs_review' or review.get('reason') != 'changed_after_approval'
                    or not _review_time(review.get('updated_at')) or _descriptions(document, block) is None
                    or not block.get('decorative') and not str(block.get('alt') or '').strip()):
                continue
            # The newest transition is decisive. Older equal content cannot
            # override a later review decision, edit, deletion, or history gap.
            for index in range(len(states) - 1, 0, -1):
                before_doc, before_proof = states[index - 1]
                after_doc, after_proof = states[index]
                before, after = _image(before_doc, identity), _image(after_doc, identity)
                if not before or not after:
                    break
                if before.get('review', {}).get('status') != 'approved':
                    continue
                old_review = before.get('review', {})
                approved_at = _review_time(old_review.get('updated_at'))
                changed_at = _review_time(after.get('review', {}).get('updated_at'))
                changed = {key for key in set(before) | set(after) if before.get(key) != after.get(key)}
                description = _descriptions(before_doc, before)
                if (is_excluded(before) or not approved_at
                        or approved_at > _review_time(before_doc['review_session']['updated_at'])
                        or not changed_at or changed_at < _review_time(before_doc['review_session']['updated_at'])
                        or changed_at > _review_time(after_doc['review_session']['updated_at'])
                        or not approval_stamp_matches(before) or description is None
                        or not changed & MEDIA_FIELDS or changed - MEDIA_FIELDS - {'review'}
                        or content_digest(before) != content_digest(after)
                        or _pending_decision(after) != _pending_decision(block)):
                    break
                trace = states[index - 1:]
                valid = True
                for (earlier, _), (later, _) in zip(trace, trace[1:]):
                    if int(later['review_session']['revision']) != int(earlier['review_session']['revision']) + 1:
                        valid = False
                        break
                for later, _ in states[index:]:
                    image = _image(later, identity)
                    if (not image or is_excluded(image) or content_digest(image) != content_digest(before)
                            or _pending_decision(image) != _pending_decision(after)
                            or _descriptions(later, image) != description):
                        valid = False
                        break
                if valid:
                    result['rows'].append({'block_id': identity,
                        'source_page': block.get('provenance', {}).get('source_page'),
                        'alt': block.get('alt') or '', 'caption': block.get('caption') or '',
                        'approved_at': old_review['updated_at'], 'original_review': copy.deepcopy(old_review),
                        'proof': {'schema_version': 'pdf-to-web-media-mapping-approval-v1',
                                  **before_proof, 'mapping_snapshot': after_proof['snapshot'],
                                  'mapping_snapshot_sha256': after_proof['snapshot_sha256'],
                                  'approved_at': old_review['updated_at'], 'project_id': project_id}})
                break
    except (OSError, ValueError, TypeError, AttributeError, KeyError):
        result['rows'] = []
        result['token'] = ''
        result['notice'] = 'Retained history could not verify these approvals. Review remaining images individually.'
    if result['rows']:
        result['notice'] = ('Retained history records unchanged image content and descriptions. '
                            'Only WordPress media routing caused these approvals to become pending. '
                            'Restoration keeps the original approval dates, current mappings and newer decisions.')
    return result


def apply_recovery(root: Path, payload: dict) -> tuple[dict, int]:
    if not isinstance(payload, dict):
        raise ValueError('Preview recorded approvals before confirming a selection.')
    # Read raw saved state: a stale confirmation must not trigger load repairs.
    document = json.loads(review_path(root).read_bytes())
    plan = plan_recovery(root, document)
    ids = payload.get('block_ids')
    expected = [row['block_id'] for row in plan['rows']]
    if (not expected or not plan['token'] or payload.get('token') != plan['token']
            or payload.get('project_id') != plan['project_id'] or not isinstance(ids, list)
            or any(not isinstance(identity, str) for identity in ids)
            or len(ids) != len(set(ids)) or set(ids) != set(expected)):
        raise ValueError('The project or recorded approval selection changed. Preview recorded approvals again; nothing was restored.')
    for row in plan['rows']:
        block = _image(document, row['block_id'])
        review = block['review']
        review.update(status='approved', updated_at=row['approved_at'], content_sha256=content_digest(block),
                      approval_evidence=row['proof'])
        review.pop('reason', None)
        review.pop('decision_id', None)
    return save_review_document(Path(root), document), len(expected)
