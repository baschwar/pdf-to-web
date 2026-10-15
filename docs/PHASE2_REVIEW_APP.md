# Phase 2 Review Application

## Architecture

### Page-scoped reading-order repair

`reading_order.py` derives editable top-level IDs from current source-page
membership. Shared-page blocks form fixed segment boundaries; excluded, nested,
other-page and unlocated blocks are not replaced. GET is read-only. Apply checks
project identity and exact review token, the complete ID permutation and segment
membership under the shared reentrant review-write lock. Active provider jobs
and manual reconstruction holds prevent conflicting edits. The existing
`save_review_document(expected_review_token=...)` makes one revision/Undo
snapshot and reconciles output references. No stored schema migration is needed.
The browser stages changes with a pinned local dnd-kit DOM/sortable bundle,
retains explicit Move to, and destroys drag resources on rerender/close.
Confirmed Apply reloads authoritative state; rejected requests retain the draft,
and uncertain writes require reload before retry. Structure headings/toolbars
share sizing and responsive layout; source-note reserved space and manual help
popover behavior remain intact.

### Source-page saved review projection

`source_review.page_reviews` derives a read-only map using existing effective
block status, publication findings, visual readiness, current source ranges and
manual holds. It traverses current blocks/children, never provenance originals.
Each top-level block owns its nested/image-description requirements; standalone
visual decisions add separate tasks. Shared blocks retain whole-block semantics
on each source page. Exclusions resolve tasks; no extracted blocks, conversion
blocks and manual reconstruction override completion. The title/accessibility
label distinguishes intentional all-excluded review from export readiness.

Structure embeds one complete saved page map. Navigation synchronously selects
its entry before source-image work, so old-page status cannot survive a new page.
Confirmed async review patches replace the map without replacing the source pane.
Structural/merge/reconstruction/Undo responses also provide the updated projection
before their existing reload. Unknown or uncertain write/display results show
Needs review with confirmation guidance. Unsaved local fields do not change this
saved-decision projection. No extra polling, project mutation or schema change
is added by the pill.

### Staged merge transaction and origins

The page editor posts a sequence of order/merge/unmerge steps. Its authenticated,
CSRF-protected preview endpoint validates the current project/review token and
executes the plan on a deep copy without persistence. Apply replays the same
validated plan under the shared review lock, then saves once with an expected-token
check. No intermediate merge/reorder writes, revisions or approvals occur.
Compatibility validates physical adjacency in complete staged document order,
source-page/fixed boundaries, exclusions, plain paragraph/list semantics, ordered
continuation, item nesting, associated/incoming links and output-page ownership.

Each new merged block retains its first stable ID and full original block objects
in optional `provenance.reading_order_merge` version 1, including an integrity
digest, original assignments and a result fingerprint. Plain-run text remains
export-authoritative. Originals retain item IDs, review decisions and provenance;
new merged content is Needs review. Recorded regions derive independently from
originals, including recovered source text, without inventing enclosing boxes.
Output references reconcile through the existing saved-state mechanism.

Persistent Unmerge replaces one unchanged row with its retained original objects
at the current position/assignment. Live ID collisions, corrupted origins, material
content/source/custom-review edits and changed exclusions refuse restoration.
Normal approval changes are allowed. This additive provenance field uses the
existing serializer and optional versioned reader; old projects require no schema
rewrite or re-extraction. Unsupported origin versions fail closed for Unmerge.
Legacy Merge next and manual Split have no new exact Unmerge promise.

### Drafting disclosure preferences

The Structure default is derived from retained image request history. Successful
generation/manual import (including older ready/rejected or retained draft data)
collapses preparation on subsequent visits, even when image review remains pending.
Generating/failed requests retain a useful open default; visible status outside
the disclosure remains available when an explicit preference closes it. Per-project
browser choice wins over defaults, with session storage fallback. Status polling
never changes disclosure state or focus; unrelated review patches leave it mounted.
Direct links reveal tools for the visit without overwriting the explicit choice.

### Stable source feedback

Source metadata and region notes occupy reserved helper-text space. Same-page
review updates retain the rendered image while refreshing the outline; unavailable
geometry gets explicit feedback. Image-response and region-metadata waits are
bounded to 30 and 10 seconds respectively. Reconstruction status exists only for
an active warning or failure. Its explanation uses a manual popover with hover,
focus/touch, outside dismissal and Escape, without shifting the source stage.
Positioning follows the visual viewport at zoom and narrow widths; the help text
is associated with its controls for assistive technology.

### In-place review confirmation

The top action combines only edited review-authoring forms for its displayed
block. Block fields and nested link-label edits are applied in memory using
existing validators before final approval and one save/revision. The shared
reentrant write lock and final expected-token check protect read/validate/write.
Image description IDs bind approval to the displayed records. Text/link overlaps
that cannot preserve both edits are rejected atomically. Static JavaScript checks
new server-markup capability before posting a combined payload, avoiding silent
approval of old saved content when an earlier server is still running.

Dirty block fields show a live Unsaved changes explanation immediately below the
top review actions, associated with Approve through aria-describedby. This includes
heading-level-only edits. Reversion and confirmed saves clear the explanation;
The top action becomes Save & Approve for dirty fields, restores Approve after reversion, and enables editing of previously approved blocks. Guidance updates
compare each editor once, avoiding a per-card scan across all editors.

Review writes use a 30-second response timeout. An abort clears busy/request state
but retains the uncertain-save guard because a write may already have succeeded.
No retry is automatic. Failed display refresh after confirmation is reported as
Saved with reload instructions. Normalize browser abort exceptions so their
read-only messages do not suppress the recovery text. Reload loads static code;
changed server markup/validation requires relaunching PTW before reloading.

Image cards include Approve in their top review actions. This submits the current
snapshot and displayed description IDs, using the existing atomic image approval
validator on saved content. Missing alternatives/equivalents reject without writes;
decorative images resolve descriptions as not applicable. Dirty authoring switches
the same top control to Save & Approve. Lower controls retain ordinary save and
a focus-return link, with no duplicate approval.

Structure Save, Save & Approve, and direct review actions request bounded review
fragments after the existing validated write. Changed cards, counts, filters,
completion and review tokens update in place; the document and source pane stay
mounted. Dirty editors outside the submitted forms are preserved. Only a confirmed
save advances to the next pending item; overlapping requests and double-click
spillover are blocked. Known validation failures retain editable fields. Uncertain
network results or failure to display a confirmed write require reload before
another mutation, avoiding duplicate approval. Structure responses use no-store
so history navigation does not reuse old tokens with restored form values. Undo
and structural operations retain the existing navigation and snapshot behavior.

Source-page reconstruction controls track the displayed page independently of
native form restoration and delayed requests. A response for a former page does
not select it again or apply its checked state to the newly displayed page.

### Compact image authoring and source-page holds

Image authoring uses compact alt/caption fields, readable smaller field type and
full-width long descriptions. Decorative choice precedes the fields; save actions
follow them without floating over content. Optional per-image drafting controls
and bottom-of-card source provenance use native disclosures. Existing requests
remain discoverable, and drafts are preserved when disclosures change.

Needs manual reconstruction below Source Page is an explicit reversible hold in
the existing review document. It snapshots prior block review state and excludes
only complete top-level blocks whose provenance belongs exclusively to that page.
Shared/merged page blocks remain intact. Held content is read-only; stale requests
and conflicting restores fail atomically. Unchecking restores prior decisions,
including exclusions, without approving anything new. Both directions use the
existing review snapshot and Undo mechanisms. No schema migration or extraction
is required for projects that do not use the optional state.

Persistent output-page placeholders carry source identity and remain unfinished.
Reordering is allowed; authoring, merging, approval and export are unavailable
for the placeholder. Replacement grouping retains one placeholder per active
hold. Reversal removes an empty placeholder. A populated source-built placeholder
instead becomes an ordinary unfinished output page with its identity and block
references retained. Regrouping never duplicates references across placeholders
and ordinary pages. Publication readiness and
Accessibility retain an unresolved page-level finding even when fragments are
excluded. Restoration precedes manual editing/replacement; this feature does not
provide OCR or automatically author a replacement page.

Standalone visual-description findings with no associated image show their
actual source page as whole-page context, with full-size/PDF links and retry
feedback. Automated possible-complex-visual classification is a review prompt,
not confirmation of an infographic. The source pane links to pending whole-page
checks independently of block filters and approvals. Explicit description
decisions update these warnings and the source-page review pill without changing
block approval. Preview loading does not discard unsaved description text.

### Source-page renderer setup

Source comparison requires system Poppler (`pdfinfo` and `pdftoppm`), separately
from Python extraction dependencies. With Homebrew already installed on macOS,
run `brew install poppler`, verify `command -v pdftoppm` and `pdftoppm -v`, then
run `.venv/bin/pdf-to-web doctor`. See [README setup](../README.md#development-setup)
for Linux/Windows and troubleshooting. The macOS launcher includes both standard
Homebrew bin directories; custom installations must be on the launching PATH.
Stop and relaunch after setup, then reopen the same project. Do not regenerate
extraction or move project data to solve a missing renderer.

Existing page PNGs in `review/source-pages/` can work without an installed
renderer; uncached pages require Poppler. Extracted image assets
are not source-page renders. Missing Pillow during supplemental asset extraction
is a separate issue and does not explain missing `pdftoppm`. Structure keeps
the original PDF link and a Retry action when rendering fails.

The local browser application is a thin review layer over the existing project
and export modules:

```text
OpenDataLoader raw extraction
  -> immutable normalized original
  -> reviewed/current document plus revision snapshots
  -> existing HTML, Gutenberg, and WXR exporters
```

`pdf_to_web.web` owns HTTP/session behavior and rendering. `review_state` owns
all review mutations and persistence. `source_pages` renders read-only PDF page
images through Poppler. Route handlers do not extract PDF content and do not
reimplement exporters.

The Preview screen has two independent paths. Semantic Preview renders the
reviewed model through the HTML exporter. WordPress Preview renders the reviewed
model through the Gutenberg exporter, then converts that exact Gutenberg markup
with the local `wp-block-to-html` worker. This keeps Gutenberg/profile defects
distinguishable from normalized-model or semantic-export defects.

Secondary explanations opt into the shared `helper-text` class rather than a
global paragraph or `small` rule. It uses `.75rem` with a 14px minimum, a 1.5 line
height and the existing dark muted color. Live merge blockers retain their prior
status size; warnings, validation, review decisions, form controls, primary
workflow instructions and publication content retain their existing typography.

## Saved block content preview

Paragraph/list cards share one Edit / Preview area. Edit is the initial mode;
Preview is a lazy, sandboxed saved-content display with no save, revision or
approval action. Switching keeps all editor fields intact. An unsaved-change
notice distinguishes draft values from saved rendering. Return to Edit to use
the existing Save block / top Save & Approve workflow. Nested-list review controls
and the whole-list text-edit safeguard remain available in Edit.

Saved literal line breaks render as escaped text with explicit HTML breaks,
including blank lines, through the shared inline renderer. This also applies to
document previews and HTML/Gutenberg/WXR exports; note offsets are located in raw
text before escaping or inserting breaks. The simple-list editor retains its
one-line-per-item convention. The borderless preview measures its rendered body
and resizes as content or available width changes, without a fixed-height inner
scrolling area. No saved state or block IDs change during resizing.

The public HTML block renderer reuses export semantics without a document-title
projection and includes only relevant footnotes/backlinks. IDs are isolated in
each iframe. An explicit preview allowlist and CSP permit confined local media,
exclude scripts/handlers and make destination links inactive; in-fragment note
links retain normal keyboard navigation. Preview styling is independent of app
and destination themes. No editor library, model field or migration is added.

Recognized reference markers are placed within styled runs before HTML escaping.
Legacy explicit associations without an in-text marker retain their prior trailing
placement. Unassociated numeric text remains plain. A References/Bibliography
heading followed by a reference list triggers one nonblocking manual-review notice
on Structure and Export. Native paragraph/list Gutenberg wrappers remain; the
existing endnotes Custom HTML block is unchanged. Additional citation association
and footnote ARIA authoring are deferred until native-block compatibility is
verified; local checks do not establish human VoiceOver acceptance.

## Review data

- `extraction/raw/`: immutable extraction output.
- `extraction/normalized/document.json`: immutable normalized original.
- `review/current.json`: current reviewed state consumed by the CLI and UI.
- `review/revisions/*.json`: snapshots created before mutations, capped at 50.
- `review/source-pages/*.png`: local rendered-page cache.

Each editable block retains source provenance and has one review status:
`unreviewed`, `approved`, `needs_review`, or `excluded`. Regenerating normalized
content archives an existing reviewed document before initializing a new review
state.

## Security boundary

- Uvicorn accepts only `127.0.0.1` or `localhost` binding.
- Middleware rejects non-loopback clients and unexpected Host headers.
- A one-use bootstrap token creates an HttpOnly same-site session cookie.
- State changes require a same-loopback Origin and a matching CSRF header.
- Native folder selection occurs server-side; the browser receives an opaque,
  short-lived selection token and project name, never an arbitrary path API.
- Source and asset routes confine paths to the active project and allow only
  expected file types.
- No review feature requires an external network service.

This is defense in depth for a single-user local application. It is not intended
to be exposed on a LAN or public interface.

## Real corpus findings

- The policy document was a useful straightforward text and list case.
- The multi-column poster made reading order and full-page source context
  especially important.
- The four-year sample program contained multiple real tables; compact table
  inspection is useful, while editing them as ordinary text would be unsafe.
- The designed infographic demonstrated both `needs_review` and
  `conversion_blocked` outcomes across extraction modes. Low recovered-text
  percentages must stay prominent, and WordPress export must remain blocked.
- Some image blocks intentionally have no publishable media URL. The review
  preview renders a local placeholder while exported HTML continues to report
  `MEDIA_URL_REQUIRED`.

## Current limitations

- No drag-and-drop reordering; keyboard-operable Move up/down controls are the
  supported method.
- No spreadsheet-like table editor.
- Undo is session-oriented and restores persisted snapshots; there is no visual
  revision browser.
- WSUWP output remains validated against fixtures and the documented shim, not
  against production plugin versions.

Bounding-box source highlighting, image alt-text decisions, table semantic
review, and complex-visual text-equivalent authoring were added during the
stabilization and Phase 3A work. See `docs/PHASE3_ACCESSIBILITY.md`.

## Phase 2 closeout

Phase 2 is complete as of version 0.6.0. A user can open or create a project,
compare reviewed blocks with source pages, edit structure and content, merge,
split, reorder, include or exclude blocks, persist and undo changes, reopen a
project, preview both supported output paths, and export reviewed HTML,
Gutenberg, and WXR without modifying raw extraction.

Production WSUWP plugin compatibility and a human listening pass with VoiceOver
remain external acceptance checks. Neither changes the completed local review
architecture, and neither is represented as an automated accessibility result.

## Verification

Run the route and model test suite with:

```sh
python -m unittest discover -s tests -v
```

The Playwright-based browser and accessibility scripts under `tools/` are
developer checks. Their Node dependencies are already part of the existing
WordPress round-trip tooling and are not application runtime dependencies.

## Structure completion message — 2026-09-30

Structure displays **All blocks have been reviewed** and **Continue to
Accessibility** once every top-level review card is approved or excluded. It uses
the existing review-progress model; Needs review does not count as completion
even though it counts as a recorded decision in the toolbar. Empty documents and
blocked conversions do not show the message. No approval is inferred for complex
visuals or Accessibility findings.

After a final approval/exclusion, or saving a final approved review state, the
normal reload focuses and reveals the message rather than returning to the last
block. It is an inline status message, not an automatic navigation or a modal.
Existing provider-toolbar focus protection remains. The message persists on
reopen and disappears after Undo or renewed pending block review. It requires no
new stored state or schema migration.

Local evidence: baseline 191 tests passed; final suite 196 passed. Five new
regressions cover completion, exclusions, pending decisions, empty/blocked
documents, and final approval/Undo. Seven Chrome checks passed without page
errors: pending-message absence, keyboard final approval/message focus, keyboard
Accessibility navigation, return persistence, Undo, final form-save focus, and
390-pixel layout without horizontal scrolling. Evidence is under
`build/image-drafts/structure-completion-browser-report.json`,
`structure-complete.png`, and `structure-complete-narrow.png`; repeat with
`tools/structure-completion-browser-check.js BOOTSTRAP_URL` against a disposable
fixture. No user project, WordPress site, or external provider was changed. Human
VoiceOver, production WSUWP, and actual Windows hardware acceptance remain
pending. No push or release. Restart the local app to load the new rendering.
