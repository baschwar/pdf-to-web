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

- No bounding-box source highlighting.
- No drag-and-drop reordering; keyboard-operable Move up/down controls are the
  supported method.
- No spreadsheet-like table editor.
- No alt-text or long-description remediation workflow.
- Complex visuals can be retained, excluded, reclassified, or have recovered
  text corrected, but cannot be fully remediated here.
- Undo is session-oriented and restores persisted snapshots; there is no visual
  revision browser.
- WSUWP output remains validated against fixtures and the documented shim, not
  against production plugin versions.

## Verification

Run the route and model test suite with:

```sh
python -m unittest discover -s tests -v
```

The Playwright-based browser and accessibility scripts under `tools/` are
developer checks. Their Node dependencies are already part of the existing
WordPress round-trip tooling and are not application runtime dependencies.
