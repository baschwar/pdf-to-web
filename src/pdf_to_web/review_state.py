from __future__ import annotations

import copy
import hashlib
import json
import re
import uuid
from difflib import SequenceMatcher
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .errors import PdfToWebError
from .project import load_project, save_project, utc_now

REVIEW_SCHEMA = "pdf-to-web-review-v1"
BLOCK_TYPES = {"heading", "paragraph", "list", "quote", "caption", "callout", "unknown"}
BLOCK_REVIEW_STATES = {"unreviewed", "approved", "needs_review", "excluded"}
TEXT_BLOCK_TYPES = {"heading", "paragraph", "quote", "caption", "callout", "unknown"}


def review_path(project_dir: Path) -> Path:
    return project_dir.expanduser().resolve() / "review" / "current.json"


def original_path(project_dir: Path) -> Path:
    return project_dir.expanduser().resolve() / "extraction" / "normalized" / "document.json"


def _read_document(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PdfToWebError(f"Document data was not found: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise PdfToWebError(f"Could not read document data: {exc}") from exc
    if data.get("schema_version") != "pdf-to-web-normalized-v1":
        raise PdfToWebError(f"Unsupported normalized schema: {data.get('schema_version')!r}")
    return data


def _walk(blocks: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for block in blocks:
        yield block
        yield from _walk(block.get("children", []))


def _default_block_status(block: dict[str, Any]) -> str:
    if block.get("review", {}).get("status") == "excluded":
        return "excluded"
    if block.get("review", {}).get("status") == "needs_review":
        return "needs_review"
    if block.get("review_status") == "review_required" or block.get("type") == "unknown":
        return "needs_review"
    return "unreviewed"


def _prepare(document: dict[str, Any]) -> dict[str, Any]:
    prepared = copy.deepcopy(document)
    now = utc_now()
    prepared["review_session"] = {
        "schema_version": REVIEW_SCHEMA,
        "created_at": now,
        "updated_at": now,
        "revision": 0,
    }
    for block in _walk(prepared.get("blocks", [])):
        review = block.setdefault("review", {})
        review.setdefault("status", _default_block_status(block))
        review.setdefault("updated_at", now)
    return prepared


def ensure_review_document(project_dir: Path) -> dict[str, Any]:
    path = review_path(project_dir)
    if path.is_file():
        document = _read_document(path)
        previous = copy.deepcopy(document)
        from .normalize import _clean_list_markers, apply_source_supplemental_regions, apply_source_title, reconcile_visual_reading_order, repair_interleaved_images

        changed = apply_source_title(document, project_dir)
        changed = apply_source_supplemental_regions(document, project_dir) or changed
        changed = repair_interleaved_images(document) or changed
        session = document.get("review_session", {})
        if not session.get("manual_order_override") and int(session.get("revision", 0)) == 0:
            changed = reconcile_visual_reading_order(document) or changed
        before = json.dumps(document.get("blocks", []), sort_keys=True)
        _clean_list_markers(document.get("blocks", []))
        for block in _walk(document.get("blocks", [])):
            if (
                block.get("type") == "image"
                and not block.get("decorative")
                and not str(block.get("alt") or "").strip()
                and block.get("review", {}).get("status") == "approved"
            ):
                _set_status(block, "needs_review")
        changed = changed or before != json.dumps(document.get("blocks", []), sort_keys=True)
        if not document.get("footnotes"):
            from .normalize import _extract_footnotes

            _extract_footnotes(document)
            if document.get("footnotes"):
                changed = True
        from .output_pages import ensure_pages
        changed = ensure_pages(document) or changed
        from .image_drafts import ensure_state
        changed = ensure_state(document) or changed
        changed = _invalidate_changed_blocks(document, previous) or changed
        changed = _restore_legacy_owner_approvals(project_dir, document) or changed
        if changed:
            if "output_pages" in previous:
                from .output_pages import reconcile
                reconcile(document, previous)
            _atomic_write(path, document)
        return document
    document = _prepare(_read_document(original_path(project_dir)))
    from .output_pages import ensure_pages
    ensure_pages(document)
    from .image_drafts import ensure_state
    ensure_state(document)
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(path, document)
    project = load_project(project_dir)
    project["review_revision_at"] = document["review_session"]["updated_at"]
    save_project(project_dir, project)
    return document


def load_reviewed_document(project_dir: Path, *, initialize: bool = False) -> dict[str, Any]:
    path = review_path(project_dir)
    if path.is_file():
        return ensure_review_document(project_dir)
    return ensure_review_document(project_dir) if initialize else _read_document(original_path(project_dir))


def _atomic_write(path: Path, data: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def _snapshot(project_dir: Path, current: dict[str, Any]) -> Path:
    directory = project_dir / "review" / "revisions"
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    path = directory / f"{stamp}.json"
    _atomic_write(path, current)
    return path


def save_review_document(project_dir: Path, document: dict[str, Any], *, snapshot: bool = True) -> dict[str, Any]:
    project_dir = project_dir.expanduser().resolve()
    path = review_path(project_dir)
    original_bytes = path.read_bytes() if path.is_file() else None
    project_path = project_dir / 'project.json'
    project_bytes = project_path.read_bytes()
    revision_path = None
    if snapshot and path.is_file():
        previous = _read_document(path)
        _sync_footnote_bodies(document, previous)
        _invalidate_changed_blocks(document, previous)
        from .output_pages import reconcile
        reconcile(document, previous)
        revision_path = _snapshot(project_dir, previous)
    now = utc_now()
    session = document.setdefault("review_session", {})
    session["schema_version"] = REVIEW_SCHEMA
    session.setdefault("created_at", now)
    session["updated_at"] = now
    session["revision"] = int(session.get("revision", 0)) + 1
    try:
        _atomic_write(path, document)
        project = load_project(project_dir)
        project["review_revision_at"] = now
        save_project(project_dir, project)
    except Exception:
        # Retain both the current state and Undo history if either write fails.
        if original_bytes is not None and path.read_bytes() != original_bytes:
            restore = path.with_suffix('.rollback')
            restore.write_bytes(original_bytes)
            restore.replace(path)
        if project_path.read_bytes() != project_bytes:
            restore = project_path.with_suffix('.rollback')
            restore.write_bytes(project_bytes)
            restore.replace(project_path)
        if revision_path:
            revision_path.unlink(missing_ok=True)
        raise
    for stale in sorted((project_dir / 'review/revisions').glob('*.json'))[:-50]:
        stale.unlink(missing_ok=True)
    return document


def _invalidate_changed_blocks(document, previous):
    """Share approval invalidation between authoring saves and load-time repair."""
    from .publication import content_digest, approval_stamp_matches
    old_blocks = {str(b.get('id')): b for b in _walk(previous.get('blocks', []))}
    changed = False
    for block in _walk(document.get('blocks', [])):
        old = old_blocks.get(str(block.get('id')))
        review = block.get('review', {})
        current = content_digest(block)
        stamp = review.get('content_sha256')
        material_edit = old and content_digest(old) != current
        if (old and not material_edit and review.get('status') == 'approved'
                and old.get('review', {}).get('status') == 'approved'
                and stamp == old.get('review', {}).get('content_sha256')
                and stamp == content_digest(old, include_media_mapping=True)
                and content_digest(old, include_media_mapping=True) != content_digest(block, include_media_mapping=True)):
            # Preserve the same verified content decision when routing metadata
            # changes. This is not a new approval and does not change its date.
            review['content_sha256'] = current
        if review.get('status') == 'approved' and not approval_stamp_matches(block) and (stamp or material_edit):
            _set_status(block, 'needs_review')
            changed = True
            review['reason'] = 'changed_after_approval'
        elif material_edit and old.get('review', {}).get('status') == 'approved' and review.get('status') == 'needs_review':
            review['reason'] = 'changed_after_approval'
            changed = True
    return changed


def block_review_reason(block, document=None):
    from .publication import block_review_issue, list_structure_issue
    malformed = list_structure_issue(block)
    if malformed:
        return malformed['message']
    if document is not None and block.get('type') == 'image':
        from .image_review import association_issue
        problem = association_issue(document, block)
        if problem:
            return problem
        from .image_review import pending_descriptions_for
        pending = pending_descriptions_for(document, block)
        if pending:
            changed = any(v.get('review_reason') == 'changed_after_approval' for v in pending)
            cause = 'The image or its description changed after review.' if changed else ('The saved image approval does not include a current review of its associated description.' if block.get('review', {}).get('status') == 'approved' else 'The image and its associated description await review.')
            return cause + ' Review alt, caption and the displayed descriptions together, then use Save and approve once.'
    review = block.get('review', {})
    issue = block_review_issue(block) if review.get('status') == 'approved' else None
    if issue and issue['code'] == 'legacy_approval_unverified':
        return 'Earlier approval cannot be verified for these nested items. Review this list, then approve it.'
    if review.get('status') == 'needs_review' and review.get('reason') == 'changed_after_approval':
        return 'Needs approval because this block changed after approval. Review the saved content, then approve it.'
    return ''


def _review_time(value):
    try:
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo is not None else None
    except (ValueError, TypeError):
        return None


def _restore_legacy_owner_approvals(project_dir, document):
    """Add evidence for an existing decision, never a new approval decision."""
    from .publication import content_digest, pending_descendants
    from .exporters.common import is_excluded
    project_id = document.get('output_pages', {}).get('project_id')
    session = document.get('review_session', {})
    if not project_id or session.get('schema_version') != REVIEW_SCHEMA or not _review_time(session.get('created_at')) or not _review_time(session.get('updated_at')):
        return False
    all_ids = [str(b.get('id')) for b in _walk(document.get('blocks', []))]
    candidates = {}
    for block in document.get('blocks', []):
        review = block.get('review', {})
        identity = str(block.get('id'))
        approved_at = _review_time(review.get('updated_at'))
        if is_excluded(block) or review.get('status') != 'approved' or review.get('content_sha256') or not pending_descendants(block) or all_ids.count(identity) != 1:
            continue
        if not approved_at or approved_at > _review_time(session.get('updated_at')):
            continue
        if any(all_ids.count(str(child.get('id'))) != 1 for child in _walk(block.get('children', []))):
            continue
        def prior_children(nodes):
            for child in nodes:
                if is_excluded(child):
                    continue
                timestamp = _review_time(child.get('review', {}).get('updated_at'))
                if (child.get('review', {}).get('status') == 'needs_review' and not timestamp) or (timestamp and timestamp > approved_at) or not prior_children(child.get('children', [])):
                    return False
            return True
        if prior_children(block.get('children', [])):
            candidates[identity] = block
    if not candidates:
        return False
    changed = False
    directory = project_dir / 'review/revisions'
    if directory.is_symlink() or (project_dir / 'review').is_symlink():
        return False
    snapshots = []
    newer_time = _review_time(session.get('updated_at'))
    for path in sorted(directory.glob('*.json'), reverse=True)[:50]:
        try:
            if path.is_symlink() or not path.is_file() or path.resolve().parent != directory.resolve():
                return False
            raw = path.read_bytes()
            snapshot = json.loads(raw)
            prior_session = snapshot.get('review_session', {})
            if snapshot.get('schema_version') != 'pdf-to-web-normalized-v1' or prior_session.get('schema_version') != REVIEW_SCHEMA:
                return False
            if snapshot.get('output_pages', {}).get('project_id') != project_id or prior_session.get('created_at') != session['created_at']:
                continue
            recorded_at = _review_time(prior_session.get('updated_at'))
            if not recorded_at or recorded_at > newer_time:
                return False  # Filename and recorded chronology must agree.
            newer_time = recorded_at
            snapshots.append((path, raw, snapshot, recorded_at))
        except (OSError, ValueError, TypeError, AttributeError):
            return False  # Unknown history cannot prove an unchanged decision.
    for path, raw, snapshot, recorded_at in snapshots:
        if not candidates:
            break
        try:
            prior_ids = [str(b.get('id')) for b in _walk(snapshot.get('blocks', []))]
            owners = {str(b.get('id')): b for b in snapshot.get('blocks', [])}
            for identity, block in list(candidates.items()):
                previous = owners.get(identity)
                review = block['review']
                old_review = previous.get('review', {}) if previous else {}
                previous_nodes = [previous, *_walk(previous.get('children', []))] if previous else []
                ambiguous_identity = any(prior_ids.count(str(node.get('id'))) != 1 for node in previous_nodes)
                # The newest trusted state is decisive; older matches cannot
                # override a later change, revocation, or different decision.
                candidates.pop(identity)
                if not previous or ambiguous_identity or is_excluded(previous) or old_review.get('status') != 'approved' or old_review.get('updated_at') != review.get('updated_at') or recorded_at < _review_time(review['updated_at']) or content_digest(previous) != content_digest(block) or (old_review.get('content_sha256') and old_review['content_sha256'] != content_digest(previous)):
                    continue
                review['content_sha256'] = content_digest(block)
                review['approval_evidence'] = {'schema_version': 'pdf-to-web-legacy-owner-approval-v1', 'snapshot': path.name,
                    'snapshot_sha256': hashlib.sha256(raw).hexdigest(), 'approved_at': review['updated_at'], 'project_id': project_id}
                changed = True
        except (OSError, ValueError, TypeError, AttributeError):
            break  # Unreadable/invalid newer history makes older proof uncertain.
    return changed


def _sync_footnote_bodies(document, previous):
    """Keep the existing derived note text consistent with edited source bodies."""
    old_blocks = {str(b.get('id')): b for b in _walk(previous.get('blocks', []))}
    notes = {str(n.get('id')): n for n in document.get('footnotes', [])}
    from .normalize import _footnote_marker_and_text
    for block in _walk(document.get('blocks', [])):
        note = notes.get(str(block.get('footnote_body_id')))
        old = old_blocks.get(str(block.get('id')))
        if not note or not old or old.get('content') == block.get('content'):
            continue
        # Source raw fields are immutable evidence, not the current authored text.
        authored = {'content': block.get('content', '')}
        parsed = _footnote_marker_and_text(authored)
        original = _footnote_marker_and_text({'content': old.get('content', '')})
        marked_source = original and original[0] == str(note.get('marker'))
        if marked_source and parsed and parsed[0] != str(note.get('marker')):
            raise ValueError('Footnote marker changes require structural review; keep the existing marker while editing its body.')
        note['text'] = parsed[1] if parsed and parsed[0] == str(note.get('marker')) else str(block.get('content') or '').strip()


def _find_location(
    blocks: list[dict[str, Any]], block_id: str
) -> tuple[list[dict[str, Any]], int, dict[str, Any]]:
    for index, block in enumerate(blocks):
        if str(block.get("id")) == block_id:
            return blocks, index, block
        children = block.get("children")
        if isinstance(children, list):
            try:
                return _find_location(children, block_id)
            except KeyError:
                pass
    raise KeyError(f"Block was not found: {block_id}")


def _set_status(block: dict[str, Any], status: str) -> None:
    if status not in BLOCK_REVIEW_STATES:
        raise ValueError(f"Unsupported review status: {status}")
    review = block.setdefault("review", {})
    review["status"] = status
    if status == 'needs_review':
        # Distinguish an explicit new decision even within the same second.
        review['decision_id'] = uuid.uuid4().hex
    else:
        review.pop('decision_id', None)
    review.pop('approval_evidence', None)
    if status != 'needs_review':
        review.pop('reason', None)
    if status == 'approved':
        from .publication import content_digest
        review['content_sha256'] = content_digest(block)
    else:
        review.pop('content_sha256', None)
    review["updated_at"] = utc_now()


def _rewrite_inline(block: dict[str, Any], content: str) -> None:
    """Keep formatting/destinations for edits contained within a single run."""
    runs = block.get('runs')
    old = str(block.get('content') or '')
    if not isinstance(runs, list) or ''.join(str(r.get('text', '')) for r in runs) != old:
        block.pop('runs', None)
        block['content'] = content
        return
    spans, cursor = [], 0
    for run in runs:
        end = cursor + len(str(run.get('text', '')))
        spans.append((cursor, end, run))
        cursor = end
    for index, (start, end, run) in enumerate(spans):
        suffix = old[end:]
        if content.startswith(old[:start]) and content.endswith(suffix) and len(content) >= start + len(suffix):
            replacement = content[start:len(content) - len(suffix) if suffix else len(content)]
            block['runs'] = copy.deepcopy(runs)
            block['runs'][index]['text'] = replacement
            block['runs'] = [value for value in block['runs'] if value.get('text')]
            block['content'] = content
            return
    # A retained punctuation delimiter gives an exact label boundary even if
    # both the label and trailing prose changed (for example a parenthesized URL).
    links = [(a, b, r) for a, b, r in spans if r.get('type') == 'link']
    if len(links) == 1:
        start, end, run = links[0]
        boundary = re.match(r'[^\w\s]+', old[end:])
        if boundary and content.startswith(old[:start]):
            marker = boundary.group()
            tail = content[start:]
            if tail.count(marker) == 1:
                stop = start + tail.index(marker)
                index = next(i for i, (_, _, r) in enumerate(spans) if r is run)
                trailing = {'content': old[end:], 'runs': copy.deepcopy(runs[index + 1:])}
                _rewrite_inline(trailing, content[stop:])
                block['runs'] = [*copy.deepcopy(runs[:index]),
                                 {**copy.deepcopy(run), 'text': content[start:stop]},
                                 *trailing.get('runs', [{'type': 'text', 'text': content[stop:]}])]
                block['content'] = content
                return
            if tail.count(marker) > 1:
                raise ValueError('This edit has an ambiguous link boundary. Edit its link label separately, then edit the surrounding text.')
    updated = []
    def append(text, run=None):
        if not text:
            return
        value = {**(run or {'type': 'text'}), 'text': text}
        if updated and {k: v for k, v in updated[-1].items() if k != 'text'} == {k: v for k, v in value.items() if k != 'text'}:
            updated[-1]['text'] += text
        else:
            updated.append(value)
    for action, start, end, new_start, new_end in SequenceMatcher(None, old, content, autojunk=False).get_opcodes():
        if action == 'equal':
            for a, b, run in spans:
                lo, hi = max(a, start), min(b, end)
                if lo < hi:
                    append(old[lo:hi], run)
        elif action in {'replace', 'insert'}:
            owner = next((run for a, b, run in spans if (a <= start < end <= b if action == 'replace' else a < start < b)), None)
            if owner is None and any(a < end and b > start and run.get('type') == 'link' for a, b, run in spans):
                raise ValueError('This edit crosses a link boundary. Edit its link label separately, then edit the surrounding text.')
            append(content[new_start:new_end], owner)
    block['content'] = content
    block['runs'] = updated


def _mark_content_parents(document, block):
    def visit(nodes):
        for node in nodes:
            if node is block:
                return True
            if visit(node.get('children', [])):
                if node.get('type') == 'list':
                    node['content'] = '\n'.join(str(child.get('content') or '') for child in node.get('children', []))
                if node.get('review', {}).get('status') != 'excluded':
                    _set_status(node, 'needs_review')
                return True
        return False
    visit(document.get('blocks', []))


def restore_source_links(project_dir: Path, block_ids: list[str]) -> dict[str, Any]:
    """Explicitly recover selected lost links from immutable source evidence."""
    from .normalize import _apply_link_annotations
    original = _read_document(original_path(project_dir))
    annotations = original.get('source_links', [])
    if annotations:
        _apply_link_annotations(original, annotations)
    document = ensure_review_document(project_dir)
    for block_id in block_ids:
        _, _, source = _find_location(original.get('blocks', []), block_id)
        _, _, block = _find_location(document.get('blocks', []), block_id)
        if block.get('runs'):
            continue
        recovered = copy.deepcopy(source)
        _rewrite_inline(recovered, str(block.get('content') or ''))
        if not any(run.get('type') == 'link' for run in recovered.get('runs', [])):
            raise ValueError(f'No unambiguous retained link could be recovered for {block_id}')
        block['runs'] = recovered['runs']
        block['source_links'] = copy.deepcopy(recovered.get('source_links', []))
        if block.get('review', {}).get('status') != 'excluded' and not block.get('excluded'):
            _set_status(block, 'needs_review')
        _mark_content_parents(document, block)
    return save_review_document(project_dir, document)


def _approve_block(block: dict[str, Any]) -> None:
    from .publication import list_structure_issue
    if block.get('excluded'):
        raise ValueError('Include the block before approving it')
    _set_status(block, 'approved')
    malformed = list_structure_issue(block)
    if malformed:
        raise ValueError(malformed['message'])
    if block.get('type') == 'image' and not block.get('decorative') and not str(block.get('alt') or '').strip():
        raise ValueError('Add alt text or mark the image as decorative before approving it')


def update_block(project_dir: Path, block_id: str, changes: dict[str, Any], *, approve_after_save: bool = False) -> dict[str, Any]:
    document = ensure_review_document(project_dir)
    if 'expected_review_token' in changes:
        from .image_review import validate_token
        validate_token(document, changes['expected_review_token'])
    if 'link_block_id' in changes:
        # Link labels can belong to a nested item, while the displayed top-level
        # block owns its content review. Save both in one existing Undo snapshot.
        from .image_review import validate_token
        validate_token(document, changes.get('expected_review_token'))
        owner = _find_location(document.get('blocks', []), block_id)[2]
        target = changes.get('link_block_id')
        if not isinstance(target, str) or not any(str(node.get('id')) == target for node in _walk([owner])):
            raise ValueError('The displayed link does not belong to this block. Reload before saving.')
        allowed = {'link_block_id', 'link_index', 'link_text', 'expected_review_token'}
        if set(changes) - allowed:
            raise ValueError('Save other block fields separately from the link label.')
        edits = {key: changes[key] for key in ('link_index', 'link_text') if key in changes}
        _edit_block(document, target, edits, approve_after_save=approve_after_save and target == block_id)
        if approve_after_save and target != block_id:
            _edit_block(document, block_id, {}, approve_after_save=True)
    else:
        _edit_block(document, block_id, changes, approve_after_save=approve_after_save)
    return save_review_document(project_dir, document)


def _edit_block(document, block_id, changes, *, approve_after_save=False):
    _siblings, _index, block = _find_location(document.get("blocks", []), block_id)
    if block.get('type') == 'image' and 'expected_review_token' in changes and not approve_after_save:
        from .image_review import validate_token
        validate_token(document, changes['expected_review_token'])
    if (block.get('type') == 'image' or changes.get('type') == 'image') and approve_after_save:
        from .image_review import validate_token, validate_associations
        validate_token(document, changes.get('expected_review_token'))
        original_description_ids = [str(v['id']) for v in validate_associations(document, block)]
        submitted_ids = changes.get('displayed_description_ids')
        if not isinstance(submitted_ids, list) or len(submitted_ids) != len(set(submitted_ids)) or set(submitted_ids) != set(original_description_ids):
            raise ValueError('The displayed description selection does not match this image; reload before approval')
        from .exporters.common import is_excluded
        if is_excluded(block):
            raise ValueError('Include the image before saving and approving it')
    from .publication import content_digest
    previous_content = content_digest(block)
    from .exporters.common import has_unstructured_list_text, retained_list_text
    malformed_list = has_unstructured_list_text(block)
    retained_text = retained_list_text(block) if malformed_list else str(block.get('content') or '')
    converting_to_list = changes.get('type') == 'list' and block.get('type') != 'list'
    if converting_to_list and 'content' not in changes:
        changes = {**changes, 'content': str(block.get('content') or '')}
    if (malformed_list or converting_to_list and str(block.get('content') or '').strip()) and 'content' in changes and not str(changes['content']).strip():
        raise ValueError('This list retains text without items. A blank save would lose that text. Keep the displayed text or exclude the block; Undo can restore earlier changes.')
    if (malformed_list or converting_to_list) and block.get('footnote_references') and 'content' in changes and str(changes['content']) != retained_text:
        raise ValueError('Keep this text unchanged while recovering its footnote references. Review text edits separately so their positions remain accurate.')
    if malformed_list and 'content' in changes and not str(block.get('content') or '').strip():
        block['content'] = retained_text
    previous_alt = block.get('alt') or ''
    previous_descriptions = copy.deepcopy(document.get('review', {}).get('complex_visuals', []))
    description_dispositions = {}
    if "type" in changes:
        block_type = str(changes["type"])
        if block_type not in BLOCK_TYPES:
            raise ValueError(f"Unsupported editable block type: {block_type}")
        block["type"] = block_type
        if block_type == "heading":
            block["level"] = max(1, min(6, int(changes.get("level", block.get("level", 2)))))
    if "level" in changes:
        if block.get("type") != "heading":
            raise ValueError("Heading level can only be set on a heading block")
        block["level"] = max(1, min(6, int(changes["level"])))
    if "content" in changes:
        if block.get("type") not in TEXT_BLOCK_TYPES and block.get("type") != "list":
            raise ValueError("Text editing is not supported for this block type")
        content = str(changes["content"])
        old_content = str(block.get('content') or '')
        _rewrite_inline(block, content)
        if block.get("type") == "list" and not block.get('children') and content.strip() and (
                content == old_content or malformed_list or block.get('runs') or block.get('footnote_references') or block.get('source_links')):
            # A type change or explicit recovery keeps the whole text as one
            # item; line breaks do not prove semantic item boundaries.
            child = copy.deepcopy(block)
            child['id'] = f'{block_id}-item-{uuid.uuid4().hex[:12]}'
            child['type'] = 'list_item'
            child['children'] = []
            child.setdefault('normalization', {})['preserve_list_text'] = True
            for field in ('ordered', 'start', 'marker_style', 'level'):
                child.pop(field, None)
            child.setdefault('provenance', {}).setdefault('review_changes', []).append(
                {'action': 'recover_list_text' if malformed_list else 'convert_text_to_list', 'source_block_id': block_id, 'at': utc_now()})
            _set_status(child, 'needs_review')
            for field in ('runs', 'footnote_references', 'source_links'):
                block.pop(field, None)
            for note in document.get('footnotes', []):
                for reference in note.get('references', []):
                    if reference.get('block_id') == block_id:
                        reference['block_id'] = child['id']
            block['children'] = [child]
            block.setdefault('normalization', {})['manual_list_edit'] = True
        elif block.get("type") == "list" and content != old_content:
            block.setdefault('normalization', {})['manual_list_edit'] = True
            old_children = block.get("children", [])
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            old_labels = [str(child.get('content') or '') for child in old_children]
            if len(set(old_labels)) != len(old_labels) or len(set(lines)) != len(lines):
                raise ValueError('Repeated list text makes item identity ambiguous. Edit individual items instead.')
            by_label = {str(child.get('content') or ''): child for child in old_children}
            removed = [c for c in old_children if c.get('content') not in lines]
            inserted = [line for line in lines if line not in by_label]
            renamed = None
            if len(lines) == len(old_children) and len(removed) == len(inserted) == 1 and old_labels.index(removed[0]['content']) == lines.index(inserted[0]):
                renamed = removed.pop()
                by_label[inserted[0]] = renamed
            if any(c.get('children') or c.get('excluded') or c.get('review', {}).get('status') == 'excluded' for c in removed):
                raise ValueError('Edit individual items to preserve nested or excluded list content.')
            children = []
            for line in lines:
                child = copy.deepcopy(by_label[line]) if line in by_label else {
                    'id': f'{block_id}-item-{uuid.uuid4().hex[:12]}', 'type': 'list_item', 'content': line,
                    'children': [], 'provenance': {'review_changes': [{'action': 'author_insert', 'at': utc_now()}]}}
                if line not in by_label:
                    _set_status(child, 'needs_review')
                elif child.get('content') != line:
                    _rewrite_inline(child, line)
                    if child.get('review', {}).get('status') != 'excluded':
                        _set_status(child, 'needs_review')
                children.append(child)
            block['children'] = children
    if 'link_index' in changes or 'link_text' in changes:
        try:
            run_index = int(changes['link_index'])
            runs = block['runs']
            if run_index < 0:
                raise ValueError('Invalid link index')
            run = runs[run_index]
        except (KeyError, IndexError, TypeError, ValueError):
            raise ValueError('Choose an existing link to edit') from None
        if run.get('type') != 'link' or not (run.get('url') or run.get('href')):
            raise ValueError('Choose an existing link to edit')
        label = str(changes.get('link_text') or '').strip()
        if not label:
            raise ValueError('Link text cannot be empty')
        if label != run.get('text'):
            if block.get('footnote_references'):
                raise ValueError('Link text in a block with footnote offsets needs a structural review before editing')
            run['text'] = label
            block['content'] = ''.join(str(r.get('text', '')) for r in runs)
            _set_status(block, 'needs_review')
            _mark_content_parents(document, block)
    if any(field in changes for field in ("alt", "caption", "decorative", "long_description", "description_edits")):
        if block.get("type") != "image":
            raise ValueError("Image accessibility fields can only be set on an image block")
        for field in ('alt', 'caption', 'long_description'):
            if field in changes and not isinstance(changes[field], str):
                raise ValueError(f'{field.replace("_", " ").title()} must be text')
        previous_visual = copy.deepcopy(image_description_visual(document, block))
        if previous_visual:
            previous_visual.setdefault('accessibility', {})['short_alt'] = previous_alt
        if "decorative" in changes:
            value = changes["decorative"]
            decorative = value if isinstance(value, bool) else str(value).lower() in {"1", "true", "yes", "on"}
            if decorative != bool(block.get('decorative')):
                block['decorative'] = decorative
        if "alt" in changes:
            value = str(changes['alt']).strip()
            if value != (block.get('alt') or ''):
                block['alt'] = value
        if "caption" in changes:
            value = str(changes['caption']).strip()
            if value != (block.get('caption') or ''):
                block['caption'] = value
        if 'description_edits' in changes:
            from .image_review import validate_associations
            records = {str(v['id']): v for v in validate_associations(document, block)}
            edits = changes['description_edits']
            if records and 'long_description' in changes:
                raise ValueError('Conflicting description fields were submitted; use the displayed description record fields')
            if not isinstance(edits, list) or len(edits) != len(records) or {str(e.get('id')) for e in edits} != set(records):
                raise ValueError('Every associated description must be displayed; reload the image editor')
            for edit in edits:
                visual = records[str(edit['id'])]
                old = copy.deepcopy(visual)
                old.setdefault('accessibility', {})['short_alt'] = previous_alt
                for field in ('long_description', 'adjacent_text'):
                    if field not in edit or not isinstance(edit[field], str):
                        raise ValueError('The displayed description text is incomplete')
                    visual.setdefault('accessibility', {})[field] = edit[field].strip()
                for field in ('type', 'recovered_text', 'review_note'):
                    if field in edit:
                        if not isinstance(edit[field], str) or field == 'type' and visual.get('type') and not edit[field].strip():
                            raise ValueError(f'Description {field} must be valid text')
                        value = edit[field].strip() if field != 'recovered_text' else edit[field]
                        if value != visual.get(field, ''):
                            visual[field] = value
                if 'disposition' in edit:
                    if edit['disposition'] not in {'include', 'not_applicable', 'excluded'}:
                        raise ValueError('Unsupported description use')
                    description_dispositions[str(visual['id'])] = edit['disposition']
                visual['accessibility']['short_alt'] = block.get('alt') or ''
                _mark_visual_changes(visual, old)
        if "long_description" in changes and not changes.get('description_edits'):
            text = str(changes["long_description"]).strip()
            visual = image_description_visual(document, block, create=bool(text))
            if visual:
                visual.setdefault("accessibility", {})["long_description"] = text
        if block.get("decorative"):
            block["alt"] = ""
        visual = image_description_visual(document, block)
        if visual and visual.get("source_block_id") == str(block["id"]):
            visual.setdefault("accessibility", {})["short_alt"] = block.get("alt") or ""
            if previous_visual:
                _mark_visual_changes(visual, previous_visual)
    if any(field in changes for field in ("table_header_row", "table_header_column", "table_caption", "table_reviewed")):
        if block.get("type") != "table":
            raise ValueError("Table accessibility fields can only be set on a table block")
        table_review = block.setdefault("table_accessibility", {})
        for field in ("table_header_row", "table_header_column", "table_reviewed"):
            if field in changes:
                value = changes[field]
                key = field.removeprefix("table_")
                table_review[key] = value if isinstance(value, bool) else str(value).lower() in {"1", "true", "yes", "on"}
        if "table_caption" in changes:
            block["caption"] = str(changes["table_caption"]).strip()
    if "review_status" in changes:
        status = str(changes["review_status"])
        from .publication import list_structure_issue
        malformed = list_structure_issue(block)
        if status == 'approved' and malformed:
            raise ValueError(malformed['message'])
        if status == 'approved' and (content_digest(block) != previous_content or _description_content(document.get('review', {}).get('complex_visuals', []), block.get('alt')) != _description_content(previous_descriptions, previous_alt)):
            status = 'needs_review'
        if status == 'approved':
            _approve_block(block)
        else:
            _set_status(block, status)
    if block.get('type') == 'image' and content_digest(block) != previous_content:
        from .image_review import invalidate_image_edit
        invalidate_image_edit(document, block, previous_descriptions)
    if content_digest(block) != previous_content or _description_content(document.get('review', {}).get('complex_visuals', []), block.get('alt')) != _description_content(previous_descriptions, previous_alt):
        if block.get('review', {}).get('status') != 'excluded':
            _set_status(block, 'needs_review')
        _mark_content_parents(document, block)
    if approve_after_save:
        # Explicit combined author action approves the final edited content,
        # after recovery and invalidation, within the same saved Undo snapshot.
        if block.get('type') == 'image':
            for visual in document.get('review', {}).get('complex_visuals', []):
                disposition = description_dispositions.get(str(visual.get('id')))
                if disposition:
                    if disposition != 'include':
                        visual['status'] = disposition
                        visual['reviewed_at'] = utc_now()
                        visual.pop('review_reason', None)
                        visual.pop('review_change_fields', None)
                    elif visual.get('status') in {'excluded', 'not_applicable'}:
                        visual['status'] = 'reclassified'
            from .image_review import approve_descriptions
            approve_descriptions(document, block, original_description_ids or ([str(image_description_visual(document, block)['id'])] if image_description_visual(document, block) else []))
        _approve_block(block)
    return document


def move_block(project_dir: Path, block_id: str, direction: str) -> dict[str, Any]:
    document = ensure_review_document(project_dir)
    siblings, index, _block = _find_location(document.get("blocks", []), block_id)
    targets = {"start": 0, "up": index - 1, "down": index + 1, "end": len(siblings) - 1}
    if direction not in targets:
        raise ValueError(f"Unsupported move direction: {direction}")
    target = targets[direction]
    if target < 0 or target >= len(siblings):
        raise ValueError(f"Block cannot move {direction}")
    if target == index:
        return document
    block = siblings.pop(index)
    siblings.insert(target, block)
    document.setdefault("review_session", {})["manual_order_override"] = True
    return save_review_document(project_dir, document)


def merge_next_reason(block: dict[str, Any], following: dict[str, Any] | None) -> str:
    """Share merge limits between the controls and saved-state validation."""
    if following is None:
        return 'There is no following block to merge.'
    if block.get('type') == 'list' or following.get('type') == 'list':
        return 'List blocks cannot be merged here. Edit the list items separately.'
    if block.get('type') not in TEXT_BLOCK_TYPES or block.get('type') != following.get('type'):
        return 'Merge next only joins adjacent text blocks of the same type. It does not convert headings or paragraphs into list items.'
    if any(node.get('excluded') or node.get('review', {}).get('status') == 'excluded' for node in (block, following)):
        return 'Restore excluded content before merging; excluded content must remain recoverable.'
    if any(node.get('children') or node.get('footnote_body_id') or node.get('source_links')
           or any(not isinstance(run, dict) or run.get('type', 'text') != 'text' for run in (node.get('runs') or [])) for node in (block, following)):
        return 'These blocks contain links, formatting, notes or nested content that Merge next cannot preserve. Edit them separately.'
    for index, node in enumerate((block, following)):
        content = str(node.get('content') or '')
        leading = len(content) - len(content.lstrip()) if index else 0
        ending = len(content) if index else len(content.rstrip())
        for ref in node.get('footnote_references', []):
            if not isinstance(ref.get('start'), int) or not isinstance(ref.get('end'), int) or not leading <= ref['start'] < ref['end'] <= ending:
                return 'These footnote positions cannot be preserved by Merge next. Edit the blocks separately.'
    if block.get('type') == 'heading' and block.get('level') != following.get('level'):
        return 'These headings have different levels. Keep their hierarchy separate.'
    return ''


def merge_with_next(project_dir: Path, block_id: str, *, expected_review_token: str | None = None,
                    expected_next_block_id: str | None = None) -> dict[str, Any]:
    document = ensure_review_document(project_dir)
    if expected_review_token is not None:
        from .image_review import review_token
        if not isinstance(expected_review_token, str) or expected_review_token != review_token(document):
            raise ValueError('The document changed. Reload Structure and review both blocks before merging.')
    siblings, index, block = _find_location(document.get("blocks", []), block_id)
    following = siblings[index + 1] if index + 1 < len(siblings) else None
    if expected_next_block_id is not None and (following is None or following.get('id') != expected_next_block_id):
        raise ValueError('The next block changed. Reload Structure and review both blocks before merging.')
    reason = merge_next_reason(block, following)
    if reason:
        raise ValueError(reason)
    first = str(block.get("content", "")).rstrip()
    second = str(following.get("content", "")).lstrip()
    references = copy.deepcopy(block.get('footnote_references', []))
    offset = len(first) + (2 if first and second else 0) - (len(str(following.get('content', ''))) - len(second))
    for reference in copy.deepcopy(following.get('footnote_references', [])):
        reference['start'] += offset
        reference['end'] += offset
        references.append(reference)
    block["content"] = f"{first}\n\n{second}" if first and second else first or second
    if references:
        block['footnote_references'] = references
        for note in document.get('footnotes', []):
            for reference in note.get('references', []):
                if reference.get('block_id') == following.get('id'):
                    reference['block_id'] = block['id']
    block.pop("runs", None)
    provenance = block.setdefault("provenance", {})
    provenance.setdefault("review_changes", []).append(
        {"action": "merge", "merged_block_id": following.get("id"), "at": utc_now()}
    )
    provenance.setdefault("merged_source_pages", []).extend(
        [following.get("provenance", {}).get("source_page"), *following.get("provenance", {}).get("merged_source_pages", [])]
    )
    del siblings[index + 1]
    _set_status(block, "needs_review")
    return save_review_document(project_dir, document)


def split_block(project_dir: Path, block_id: str, offset: int) -> dict[str, Any]:
    document = ensure_review_document(project_dir)
    siblings, index, block = _find_location(document.get("blocks", []), block_id)
    if block.get("type") not in TEXT_BLOCK_TYPES:
        raise ValueError("Only text blocks can be split")
    content = str(block.get("content", ""))
    if offset <= 0 or offset >= len(content):
        raise ValueError("Split position must be inside the block text")
    left, right = content[:offset].rstrip(), content[offset:].lstrip()
    if not left or not right:
        raise ValueError("Both split blocks must contain text")
    block["content"] = left
    block.pop("runs", None)
    new_block = copy.deepcopy(block)
    base = re.sub(r"-split-\d+$", "", str(block.get("id", "block")))
    existing = {str(item.get("id")) for item in _walk(document.get("blocks", []))}
    number = 1
    while f"{base}-split-{number}" in existing:
        number += 1
    new_block["id"] = f"{base}-split-{number}"
    new_block["content"] = right
    new_block["provenance"] = copy.deepcopy(block.get("provenance", {}))
    new_block["provenance"].setdefault("review_changes", []).append(
        {"action": "split", "source_block_id": block_id, "at": utc_now()}
    )
    _set_status(block, "needs_review")
    _set_status(new_block, "needs_review")
    siblings.insert(index + 1, new_block)
    return save_review_document(project_dir, document)


def undo_last(project_dir: Path) -> dict[str, Any]:
    project_dir = project_dir.expanduser().resolve()
    revisions = sorted((project_dir / "review" / "revisions").glob("*.json"))
    if not revisions:
        raise ValueError("There are no review actions to undo")
    latest = revisions[-1]
    restored = _read_document(latest)
    saved = save_review_document(project_dir, restored, snapshot=False)
    latest.unlink()
    return saved


def image_description_visual(document, block, *, create=False):
    """Resolve by explicit image identity, never by page coincidence."""
    visuals = document.setdefault("review", {}).setdefault("complex_visuals", [])
    visual = next((v for v in visuals if str(v.get("id")) == block.get("complex_visual_id")), None)
    if visual is None and create:
        visual = {"id": "image-description-" + str(block["id"]), "type": "image",
                  "status": "needs_text_equivalent", "source_block_id": str(block["id"]),
                  "source_page": block.get("provenance", {}).get("source_page"),
                  "asset_references": [block.get("src")], "accessibility": {"short_alt": block.get("alt") or ""}}
        if any(v.get("id") == visual["id"] for v in visuals):
            raise ValueError("Image description identity already exists; verify association")
        visuals.append(visual)
        block["complex_visual_id"] = visual["id"]
    return visual


def _description_content(records, fallback_alt):
    """Compare material fields, ignoring decision metadata and reviewer notes."""
    return [(v.get('id'), v.get('type', ''), v.get('recovered_text', ''),
             tuple(str(v.get('accessibility', {}).get(field, fallback_alt if field == 'short_alt' else '') or '').strip()
                   for field in ('short_alt', 'long_description', 'adjacent_text')))
            for v in records]


def _mark_visual_changes(visual, previous):
    fields = [field for field in ('short_alt', 'long_description', 'adjacent_text')
              if str(previous.get('accessibility', {}).get(field) or '').strip() != str(visual.get('accessibility', {}).get(field) or '').strip()]
    fields += [field for field in ('type', 'recovered_text') if previous.get(field, '') != visual.get(field, '')]
    if fields and (previous.get('status') in {'reviewed', 'not_applicable'} or previous.get('review_reason') == 'changed_after_approval'):
        visual['review_reason'] = 'changed_after_approval'
        visual['review_change_fields'] = sorted(set(previous.get('review_change_fields', [])) | set(fields))
        visual['status'] = 'reclassified'


def update_complex_visual(
    project_dir: Path, visual_id: str, changes: dict[str, Any]
) -> dict[str, Any]:
    document = ensure_review_document(project_dir)
    visuals = document.get("review", {}).get("complex_visuals", [])
    visual = next((item for item in visuals if str(item.get("id")) == visual_id), None)
    if visual is None:
        raise KeyError(f"Complex visual was not found: {visual_id}")
    if 'expected_review_token' in changes:
        from .image_review import validate_token
        validate_token(document, changes['expected_review_token'])
    previous_records = copy.deepcopy(visuals)
    previous_visual = copy.deepcopy(visual)
    if visual.get('source_block_id'):
        source = _find_location(document.get('blocks', []), str(visual['source_block_id']))[2]
        previous_visual.setdefault('accessibility', {})['short_alt'] = source.get('alt') or ''
    if "status" in changes:
        status = str(changes["status"])
        if status not in {"needs_text_equivalent", "excluded", "reclassified", 'reviewed', 'not_applicable'}:
            raise ValueError(f"Unsupported complex visual status: {status}")
        visual["status"] = status
    if "type" in changes:
        visual_type = str(changes["type"]).strip()
        if not visual_type:
            raise ValueError("Complex visual type cannot be empty")
        visual["type"] = visual_type
    if "recovered_text" in changes:
        visual["recovered_text"] = str(changes["recovered_text"])
    accessibility = visual.setdefault("accessibility", {})
    previous_text = {field: str(previous_visual.get('accessibility', {}).get(field) or '').strip() for field in ('short_alt', 'long_description', 'adjacent_text')}
    for field in ("short_alt", "long_description", "adjacent_text"):
        if field in changes:
            accessibility[field] = str(changes[field]).strip()
    if visual.get("source_block_id"):
        block = _find_location(document.get("blocks", []), str(visual["source_block_id"]))[2]
        if block.get("type") != "image":
            raise ValueError("Image description must reference an image block")
        if "short_alt" in changes:
            block["alt"] = "" if block.get("decorative") else accessibility["short_alt"]
            accessibility["short_alt"] = block["alt"]
        changed_text = any(field in changes and previous_text[field] != accessibility.get(field, '') for field in previous_text)
        if changed_text and block.get("review", {}).get("status") != "excluded":
            _set_status(block, "needs_review")
    if 'review_note' in changes:
        visual['review_note'] = str(changes['review_note']).strip()
    if visual.get('source_block_id') and previous_text['short_alt'] != str(block.get('alt') or '').strip():
        from .image_review import invalidate_image_edit
        invalidate_image_edit(document, block, previous_records)
    _mark_visual_changes(visual, previous_visual)
    if visual.get('status') == 'reviewed':
        from .accessibility import visual_readiness
        if not visual_readiness(document, visual)['complete']:
            raise ValueError('Add short alt text and either a long description or adjacent text before marking the description reviewed')
        if previous_visual.get('status') != 'reviewed' and changes.get('status') == 'reviewed' and visual.get('source_block_id') and block.get('review', {}).get('status') != 'excluded':
            _set_status(block, 'approved')
    if visual.get('status') in {'reviewed', 'not_applicable', 'excluded'}:
        visual.pop('review_reason', None)
        visual.pop('review_change_fields', None)
    visual["reviewed_at"] = utc_now()
    return save_review_document(project_dir, document)


def update_accessibility_decision(
    project_dir: Path, item_id: str, status: str, note: str
) -> dict[str, Any]:
    from .accessibility import save_decision

    document = ensure_review_document(project_dir)
    save_decision(document, item_id, status, note)
    return save_review_document(project_dir, document)


def review_progress(document: dict[str, Any]) -> dict[str, int]:
    from .publication import effective_block_status
    counts = {state: 0 for state in BLOCK_REVIEW_STATES}
    blocks = list(document.get("blocks", []))
    for block in blocks:
        status = effective_block_status(block, document)
        counts[status if status in counts else "unreviewed"] += 1
    reviewed = counts["approved"] + counts["needs_review"] + counts["excluded"]
    from .accessibility import visual_readiness
    visuals = document.get('review', {}).get('complex_visuals', [])
    pending_blocks = counts['unreviewed'] + counts['needs_review']
    from .image_review import description_owner
    pending_visuals = [v for v in visuals if not visual_readiness(document, v)['complete']]
    pending_descriptions = len(pending_visuals)
    linked_descriptions = sum(description_owner(document, v) is not None for v in pending_visuals)
    standalone_descriptions = pending_descriptions - linked_descriptions
    pending_images = sum(b.get('type') == 'image' and effective_block_status(b, document) in {'unreviewed', 'needs_review'} for b in blocks)
    return {"total": len(blocks), "reviewed": reviewed, **counts,
            'pending_blocks': pending_blocks, 'pending_descriptions': pending_descriptions,
            'pending_tasks': pending_blocks + standalone_descriptions, 'description_total': len(visuals),
            'linked_pending_descriptions': linked_descriptions, 'standalone_pending_descriptions': standalone_descriptions,
            'pending_images': pending_images}


def archive_review_document(project_dir: Path, reason: str) -> Path | None:
    project_dir = project_dir.expanduser().resolve()
    path = review_path(project_dir)
    if not path.is_file():
        return None
    document = _read_document(path)
    document.setdefault("review_session", {})["archived_reason"] = reason
    archived = _snapshot(project_dir, document)
    path.unlink()
    return archived


def table_summary(block: dict[str, Any]) -> dict[str, int]:
    rows = block.get("rows", [])
    return {
        "rows": len(rows),
        "columns": max((sum(int(cell.get("column_span", 1)) if isinstance(cell, dict) else 1 for cell in row) for row in rows), default=0),
        "spans": sum(
            (int(cell.get("row_span", 1)) > 1 or int(cell.get("column_span", 1)) > 1)
            for row in rows
            for cell in row
            if isinstance(cell, dict)
        ),
    }


def update_output_pages(project_dir: Path, action: str, data: dict[str, Any]) -> str | None:
    from .output_pages import mutate
    document = ensure_review_document(project_dir)
    selected = mutate(document, action, data)
    save_review_document(project_dir, document)
    return selected
