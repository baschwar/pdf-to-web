# Future Features

This is a backlog, not a release commitment. Entries below are proposed or
observed issues; they are not implemented unless explicitly marked complete.
Implementation requires a scoped directive and verification. Keep private
project snapshots, screenshots and assessment output untracked under `build/`.

## Review and Source-Recovery Edge Cases

Recorded 2026-10-02. Read-only assessment evidence:
`build/page7-page8-assessment-20261002/`. Subsequent authorized implementation
and disposable reconstruction evidence: `build/list-repair-20261002/`.
The actual project has not been automatically repaired.

### Existing nested text omitted from the source outline

**Status: locally implemented correction; release and external acceptance pending.**

The earlier source outline collected descendant `list_item` boxes,
omitting a nested paragraph's recorded box. The paragraph remained visible in
the list preview and HTML output. Next/Previous navigates top-level block cards,
not every nested element. This is distinct from missing extracted text.

Implemented correction: include valid, same-page source regions for rendered text
descendants, retaining recorded provenance and avoiding duplicate boxes. Never
invent a region for a node without one. Explain that the selected block can
contain several nested elements; provide a useful cue when region coverage is
partial. Tests cover nested paragraphs, nested lists, missing boxes, other-page
children and unchanged content. No content is duplicated or recovery block added.

### Text converted to a list without list items

**Status: locally implemented safeguards; existing-project repair remains explicit.**

Earlier, changing a text block's type to List while leaving its text unchanged could retain
text in `content` without building list-item children. The earlier editor and
HTML list renderer used those children, hiding the retained text from their
presentation. Approval alone did not fix
this structural mismatch.

Unchanged-text conversion now creates one item, preserving rich text, links,
footnotes and source provenance. Previously malformed lists display retained
text, reject blank saves and block approval/publication. Explicitly saving that
text recovers one item with Undo and fresh review; no automatic migration occurs.
An isolated step 11 reconstruction demonstrates a/b/i nesting while retaining
the original IDs, substantive text and output-page assignment; the actual project
remains for the author to review and apply. Evidence and review copy:
`build/list-repair-20261002/`. Joining mixed blocks generally additionally needs an
agreed preview of item boundaries, heading treatment and nesting; it is not
ordinary Merge next. Use synthetic fixtures for regression tests and inspect
actual output, not only stored `content`.

### Missing text inside an existing block

**Status: proposed recovery workflow; not implemented.**

First show All blocks and compare the source to distinguish filtered, excluded,
nested or genuinely absent text. Existing editable text blocks can be corrected
and reviewed. A nested paragraph may be retained yet lack its own UI editor;
whole-list editing is disabled for nested lists to protect their structure.
Provide a focused nested-text editor without flattening children or changing
their identities. Preserve links, footnote positions, provenance and parent
review invalidation. Verify save/reopen, Undo, source comparison and export.
The observed outline issue above is not evidence of missing text.

### Insert a missing block or nested item

**Status: proposed; not implemented.**

Start with Add before/after for a text block or heading, an explicit reading-order
anchor, verified text and a validated source page. Support an empty document.
Use stable IDs and explicit manually recovered provenance; do not fabricate
extraction confidence, source coordinates or approval. Preserve source files
and existing content. Save through existing revision/Undo mechanisms, focus the
new content and require review. Resolve output-page assignment explicitly or
retain a visible unassigned finding that prevents package completion.

Nested-item insertion is a separate extension: choose the owning list/item and
position, preserve ordered-list style/start and existing nested children, and
invalidate the affected owner's approval. Test duplicate labels, links,
footnotes, exclusions, save/reopen, Undo and all export formats. Do not use a
split or bulk type conversion as an implicit missing-content recovery.

### Optional manual source-region marking

**Status: proposed later extension; not implemented; not OCR.**

Allow an optional box associated with a specific source page and block. Store
canonical PDF coordinates; account for rotation, page origins, displayed image
bounds, resizing and any future zoom. Validate finite, in-bounds coordinates
and reject stale selections after a page/source change. Reuse saved provenance
for highlighting; label the association as manually marked.

Provide a keyboard-accessible way to enter or adjust the region and a Skip
region path. Text insertion must work without pointer drawing or a renderer.
A later crop preview should remain a source aid, not silently become a new
publication asset. Marking a box does not read its text: OCR and automatic
region extraction require a separate directive and dependency decision.

## Connected WordPress Publishing

Add an optional authenticated WordPress connection after the manual media
mapping workflow is proven in production.

Potential scope:

- Connect over HTTPS using a revocable WordPress Application Password or an
  institution-approved authentication mechanism.
- Test site capabilities and permissions before attempting writes.
- Upload extracted images through the WordPress Media REST API.
- Capture authoritative attachment IDs, source URLs, generated sizes, and CDN
  rewrites instead of predicting upload paths.
- Apply alt text and captions from the reviewed document.
- Regenerate Gutenberg and WXR with resolved `core/image` blocks.
- Optionally create or update a draft page or post only after explicit user
  confirmation.
- Never store a normal WordPress login password in a PDF to Web project.

This is intentionally deferred. The current supported workflow is local asset
export followed by manual Media Library upload and CSV mapping import.
