# Future Features

This is a backlog, not a release commitment. Entries below are proposed or
observed issues; they are not implemented unless explicitly marked complete.
Implementation requires a scoped directive and verification. Keep private
project snapshots, screenshots and assessment output untracked under `build/`.

## Discoverable manual WordPress media mapping

Recorded 2026-10-04 at the user's request. **Locally implemented; verification
recorded in PHASE3B_ACCEPTANCE.md.** A visible entry point beside XML matching
opens the existing CSV tools. XML errors and unmatched/ambiguous results reveal
them and provide recovery links. Detailed instructions remain in Help. Exact
block/asset identities, authored decisions, validation and Undo are preserved.
This changes discovery, not the attachment-ID refresh policy.

## Quit PDF to Web from the app

Recorded 2026-10-04 at the user's request. **Locally implemented; actual Windows
and Terminal-window closing remain external checks.** Quit confirms current-tab
unsaved fields and warns about all tabs. It refuses during admitted requests,
downloads and queued/running generation, then gracefully stops only the owned
server. Dedicated launcher processes end normally; shared prompts and Terminal
windows may remain according to profile settings. Externally managed servers
refuse this action. No process lookup, PID killing or Terminal automation occurs.
Disposable checks cover Cancel/Escape, failure/retry, admission races, full streamed
responses and actual owned-process exit. The live app is not quit or restarted.

## Image description preparation discovery

**Locally implemented.** Structure's optional drafting tools precede Reading order
and open initially when image reviews or draft requests/results make them useful.
The user's summary action remembers open/closed per project in browser storage.
Direct links reveal tools for the visit without replacing that preference. No
mandatory page, provider transmission, review approval or automatic editor collapse
is introduced. Storage denial falls back to the useful default.

## Dedicated multi-page export round-trip acceptance

Recorded 2026-10-04 at the user's request. **Future acceptance; not executed this
round.** Test representative multi-page publications from arrangement through
package download and actual WordPress import, editing, save and reopen. Cover
splits, page order, navigation/internal links, page-local footnotes/backlinks,
image mapping, heading structure and template/content titles on every page.
Compare complete source/reviewed content against every package output and imported
page to detect loss, duplication, missing assignments and broken references.
Record the actual WordPress/theme/plugin versions and human observations.
Existing synthetic arranged-package artifact and browser checks establish local
implementation evidence; they do not fulfill this dedicated human or
production-authoritative multi-page round-trip acceptance.

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
An isolated nested-list reconstruction demonstrates a/b/i nesting while retaining
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
