# Phase 2 Review Application

## Architecture

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
- The QPR research poster made reading order and full-page source context
  especially important.
- The four-year sample program contained multiple real tables; compact table
  inspection is useful, while editing them as ordinary text would be unsafe.
- The heart-failure infographic demonstrated both `needs_review` and
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
