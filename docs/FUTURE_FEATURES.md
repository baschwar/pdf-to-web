# Future Features

This is a backlog, not a release commitment. Entries below are proposed or
observed issues; they are not implemented unless explicitly marked complete.
Implementation requires a scoped directive and verification. Keep private
project snapshots, screenshots and assessment output untracked under `build/`.

## Apply reviewed reading order and element tags to a PDF

Recorded 2026-10-12 at the user's request. **Deferred concept; no PDF-writing
implementation or project fork is authorized.** Explore using the drag-and-drop
reading-order review and reviewed block classifications to produce a separately
saved remediated PDF that preserves the source's visual layout. This could reduce
manual reading-order and block-tagging work in Adobe Acrobat. Preserve the original
PDF unchanged and keep processing local.

Consider a project fork or a separate PDF-remediation project before extending
PDF to Web's product scope. Reuse the review interface, stable block identities,
source provenance and authored semantics where appropriate; choose the project
boundary after a feasibility investigation rather than committing to it now.

A first proof of concept should use a synthetic or approved, already-tagged PDF:
match reviewed blocks to existing PDF content/tag associations, apply their order
to the logical tag structure, and save a separate output. Source-page bounding
boxes alone do not establish those associations. Report missing, ambiguous or
partial matches rather than guessing or declaring the output complete.

Creating tags for untagged or badly tagged PDFs is a larger follow-on problem.
Account for nested lists, table cells and headers, figures and alternatives,
links/annotations, artifacts and content spanning pages. Web-authored content
edits may no longer match the original PDF; define that behavior explicitly.
Web exclusion decisions must not automatically become PDF artifact decisions.

Future acceptance must verify unchanged visual appearance, correct content/tag
associations, logical order and semantic nesting, Acrobat inspection, appropriate
PDF accessibility validation and human screen-reader review. Automated validator
results alone do not establish usable reading order or PDF/UA conformance.
Implementation requires a later scoped directive; this entry is not a release
commitment or a change to current exports.

## Vector artwork and QR destination review

Recorded 2026-10-09. **Deferred by the user; no vector recovery or project repair
implemented.** Source-page inspection can reveal vector QR artwork absent from
raster image extraction. A future scoped warning could identify a decoded QR on
the rendered source page without a corresponding extracted asset, show its exact
destination locally, and require review against nearby printed text. Do not follow
the URL, insert blocks or approve a replacement automatically. The preferred web
treatment is a descriptive text link once the intended destination is confirmed;
printed text alone does not guarantee either a clickable link or a matching QR
destination. Any detection feature needs false-positive and source-page tests.

## Re-review and starting over

Recorded 2026-10-08. **Deferred by the user for a future review; no reset feature
or project reset is authorized.** Review Structure currently reopens saved edits
and valid approvals. Consider clearer View reviewed structure / Continue structure
review labels and distinguish four intentions:

- Reopen and recheck the saved review without clearing decisions.
- Require review again while keeping edited content, IDs, reading order and
  exclusions, with an explicit scope for approval decisions.
- Restore the saved original extracted content, replacing authored edits; keep
  this separate from rerunning extraction.
- Create a new independent project for a new PDF or a clean conversion run.

A future proposal must account for Accessibility decisions, table and image
description reviews, arranged-page approvals, media associations and stale exports.
Show affected counts, preserve a dated project backup and provide recovery before
replacing content. Existing Needs review / Bulk review controls allow rechecking
without discarding edits; a new project in a separate folder remains the current
clean-run option. Implementation requires a later scoped decision.

## Refresh README screenshot and silent walkthrough

Recorded 2026-10-04 at the user's request. **Noncritical documentation follow-up;
not a 0.7.1 release blocker.** The existing Structure screenshot and 54-second
silent walkthrough were added on 2026-09-18, before the expanded navigation,
review controls and export workflow. Refresh both using a synthetic demonstration
project. Keep the walkthrough silent, with readable step captions and enough time
to follow each action; its duration can exceed 54 seconds.

Cover opening a chosen project folder, source comparison, the two Structure
filters, Save and approve, Accessibility review, previews, Export readiness,
saved outputs, Copy and Quit. Show optional image-draft ZIP/import, Arrange Pages
and WordPress media matching as separate steps where appropriate. Longer steps
can use chapters or short companion clips rather than rushing the demonstration.

Use neutral demonstration paths and synthetic content. Exclude private project
names, source publications, attachment IDs and actual project screenshots.
Check legibility, captions, alternative text and README artifact links. Publish
the refreshed media in a later documentation update; preserve the 0.7.1 tag.

## Explicit source-header title recovery

Recorded 2026-10-05. **Automatic detection remains a limitation; manual arranged
page recovery is locally verified.** A source can have a small repeated running
header omitted from raw extraction while the largest-font heuristic selects a
body section as the title. The author's sample assessment was positive apart
from this missing H1. Inspection confirmed that the header has no extracted block
ID and that the committed baseline makes the same title choice.

A bounded preservation fix prevents reopening from adding a replacement source
title after saved heading decisions. On a disposable copy, demoting the wrong H1
and setting an explicit Arrange Pages title produced one semantic H1, preserved
tables and links, exported saved artifacts and supported Undo. No actual project
was repaired or re-extracted. A future source-title choice should display source
candidates, let the author select or enter the title, preserve existing text and
IDs, record provenance only when verified and require review. Do not silently
treat every running header or largest-font line as the document title. Private
evidence is in `build/bloodborne-title-readonly-20261005/`.

## Preserve verified PDF bold and italic spans

Recorded 2026-10-05. **Low-priority proposal; not implemented or a release blocker.**
Read-only source, raw-extraction, model and saved-export comparison confirmed that
font metadata can survive in provenance while normalized table cells lose their
mixed styles. Existing paragraph/list strong and emphasis runs render correctly
in HTML, Gutenberg and WXR content. General font-to-run normalization, styled
table-cell output and Markdown formatting remain gaps. Some raw elements combine
different PDF fonts under one font value, so a whole-element font label cannot
reliably describe every span. Private evidence is in
`build/inline-style-readonly-20261005/`; no real project was changed.

A bounded first implementation should preserve unambiguous ordered source spans
in newly processed paragraphs, list items and table cells. Use explicit font
metadata and exact text/region correspondence; ambiguous PDF associations remain
for review. Visual weight or slant alone does not establish semantic importance
or emphasis. Preserve structural headings and table header scope rather than
turning every bold label into strong text. Define presentation styling separately
from author-confirmed strong/em semantics before changing the run contract.

Combined bold/italic, styled links and footnote references need a deliberate run
composition plan. Extend shared rendering across HTML, Gutenberg and WXR, and
define Markdown behavior. Preserve table spans, IDs, reading order, destinations,
footnote backlinks and approval fingerprints. Existing projects require an
explicit reversible action with fresh review, never automatic re-extraction or
approval. Acceptance should cover mixed/combined runs, links, footnotes, lists,
table cells, editing, Undo, save/reopen, arranged pages and saved artifacts.

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

## Multi-select merge inside reading-order repair

Recorded 2026-10-12. The initial assessment below preceded implementation approval.
**A constrained first version is now implemented locally**: adjacent plain
paragraphs or compatible lists, exact confirmation, staged ordering/merges, one
Apply/Undo, retained original provenance and persistent Unmerge for unchanged
results. See README and the acceptance ledger for actual verification. Edited
results refuse Unmerge rather than silently losing changes. Rich/associated cases,
numbering restarts, re-merging an existing merged row and automatic hyphen removal
remain unsupported. Original assessment follows as design rationale; it is not a
claim that all future variants are implemented.

Optimize for orphan paragraph fragments and PDF extraction splits in lists.
Allow homogeneous **paragraph** selections or compatible **list blocks** only.
Disable images, headings, tables, mixed types, excluded/held/shared-page content,
and unsafe rich/footnote cases with a concrete reason. Joining list blocks appends
existing items; it must not turn separate items into one concatenated text item.
Keep Move to as the explicit keyboard/screen-reader alternative to dragging.
Up/down is useful for a single quick move in ordinary Structure, but need not be
repeated in the compact drag editor. Document start/end has a different scope.

Suggested UI: labelled selection checkboxes independent of drag handles; a live
selection count; Merge selected near Cancel/Apply with its disabled reason.
Confirmation previews originals in staged reading order and the resulting content,
including list markers/start numbers, before staging a merge. Replace selected
rows with one draggable row showing first five words and a “Merged · 3 paragraphs”
or “Merged · 2 lists / 6 items” badge. Expand Full text for result and original
fragments. Draft Undo and Unmerge restore original rows. Cancel discards ordering
and merge drafts; Apply commits their validated result as **one** saved action.

Require consecutive eligible selections in the complete staged document order,
not simply adjacent cards in a page projection. Excluded, other-page, unlocated,
shared boundaries or intervening unselected blocks must not disappear from the
adjacency test. A reviewer can move eligible fragments together before merging,
but only within existing page/segment limits. Bind the transaction to current
project identity, review token, exact origin IDs and source-page scope.

Paragraph merge produces one semantic paragraph. Show the boundary policy in
preview: retain the extracted boundary, use a joining space, or explicitly join a
split word. Do not silently remove visible hyphens, infer missing words, or guess
whether a line break is intentional. Keep original text recoverable and require
review of the resulting paragraph. Rich links, formatting and footnote offsets
need exact preservation or an explicit unsupported reason.

For lists, require the same ordered/unordered kind and compatible marker style.
Preserve child IDs, nesting, item order, formatting and footnotes without flattening.
Unordered compatible lists can append items. Ordered lists require compatible
start/continuation numbers; a deliberate restart is a separate list and must not
be silently renumbered. Mixed kinds/styles, conflicting numbering or ambiguous
hierarchy remain disabled until a separately scoped authoring decision exists.

Reuse existing content validation, output-page reference reconciliation and saved
Undo, but not repeated calls to today's immediate Merge next. That function only
joins two adjacent same-type plain text blocks (including several nonparagraph
text types), refuses lists, keeps the first ID, inserts a blank-line boundary,
records the second ID/source-page membership, deletes its live row and marks the
result Needs review. Undo restores the preceding complete snapshot. It does not
retain a dedicated full original bundle or a persistent Unmerge command. Its
text merge also retains the first bounding box rather than all original boxes.

A transactional merger must retain complete original block objects, stable IDs,
reading positions, per-page source boxes, approval metadata, exclusions and output
assignments. Keep the first reviewed ID as the resulting row and retain a mapping
for absorbed IDs; validate duplicate IDs and conflicting page assignments. Render
all recorded source regions, never a fabricated enclosing box. Reconcile affected
output references and page approvals; mark the merged result Needs review instead
of carrying approval over to changed content. Retain unaffected blocks/decisions.
Persist origins if Unmerge must work after later saves/reopen; a revision-level
Undo alone cannot safely unmerge one older operation. If merged content has since
been edited, explain that original restoration cannot apportion those edits
without a separate review decision. Do not claim Split is an inverse: it makes
new IDs and does not reconstruct original provenance or approvals.

Feasibility: checkboxes and one resulting card are a modest UI change. The safe
work is a medium-sized model/transaction feature: pure in-memory reorder/merge
planning, list compatibility, provenance/origin persistence, output-reference
mapping, conflict validation and reversible commit. Start with plain adjacent
paragraphs and compatible lists; defer mixed/rich unsupported cases. Acceptance
must cover Cancel/no-write, one Apply/Undo revision, stage Undo/Unmerge, save/reopen,
original IDs and all boxes, list nesting/numbering, failed validation rollback,
stale/double submission, exports and keyboard/touch/screen-reader flows.
